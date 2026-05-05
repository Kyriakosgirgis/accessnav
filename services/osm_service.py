import threading
import requests
from kivy.clock import Clock


class OSMService:
    """
    Fetch accessibility features (ramps, elevators, barriers)
    from the Overpass API on a background thread so the UI never freezes.
    """

    OVERPASS_URL  = "https://overpass-api.de/api/interpreter"
    LIMASSOL_BBOX = (33.00, 34.60, 33.10, 34.75)  # (min_lon, min_lat, max_lon, max_lat)

    def __init__(self):
        self._session = requests.Session()
        self._cancel  = False

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def fetch_accessibility_features(self, bbox=None, on_results=None, on_error=None):
        """
        Fetch accessibility features from Overpass API on a background thread.
        Results are delivered via on_results(list) on the Kivy main thread.
        """
        self._cancel = False

        if not bbox:
            bbox = self.LIMASSOL_BBOX

        thread = threading.Thread(
            target=self._do_fetch,
            args=(bbox, on_results, on_error),
            daemon=True,
        )
        thread.start()

    def cancel(self):
        self._cancel = True

    # ------------------------------------------------------------------ #
    #  Background fetch                                                    #
    # ------------------------------------------------------------------ #

    def _do_fetch(self, bbox, on_results, on_error):
        try:
            min_lon, min_lat, max_lon, max_lat = bbox

            print(f"[OSMService] Fetching POIs — bbox: {min_lat},{min_lon},{max_lat},{max_lon}")

            query = f"""
[out:json][timeout:25];
(
  node["wheelchair"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["wheelchair"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});

  node["ramp"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["ramp"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});

  node["highway"="elevator"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["highway"="elevator"]({min_lat},{min_lon},{max_lat},{max_lon});

  node["barrier"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["barrier"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out center;
"""

            response = self._session.post(
                self.OVERPASS_URL,
                data={"data": query},
                headers={"User-Agent": "AccessNav/1.0 (student project)"},
                timeout=20,
            )
            response.raise_for_status()

            if self._cancel:
                print("[OSMService] Cancelled after response")
                return

            elements = response.json().get("elements", [])
            print(f"[OSMService] Elements received: {len(elements)}")

            features = self._parse_features(elements)
            print(f"[OSMService] Parsed features: {len(features)}")

            # Fallback sample data so the map always shows something
            if not features:
                print("[OSMService] No real data — using sample markers")
                center_lat = (min_lat + max_lat) / 2
                center_lon = (min_lon + max_lon) / 2
                features = [
                    {"lat": center_lat + 0.001, "lon": center_lon + 0.001,
                     "type": "ramp",     "name": "Sample Ramp"},
                    {"lat": center_lat - 0.001, "lon": center_lon,
                     "type": "elevator", "name": "Sample Elevator"},
                    {"lat": center_lat,         "lon": center_lon - 0.001,
                     "type": "barrier",  "name": "Sample Barrier"},
                ]

            if on_results and not self._cancel:
                Clock.schedule_once(lambda dt: on_results(features), 0)

        except requests.exceptions.ConnectionError:
            self._deliver_error(on_error, "No internet connection.")
        except requests.exceptions.Timeout:
            self._deliver_error(on_error, "OSM request timed out.")
        except requests.exceptions.HTTPError as e:
            self._deliver_error(on_error, f"OSM HTTP error: {e}")
        except Exception as e:
            self._deliver_error(on_error, f"OSM fetch error: {e}")

    # ------------------------------------------------------------------ #
    #  Parsing                                                             #
    # ------------------------------------------------------------------ #

    def _parse_features(self, elements):
        features = []
        for el in elements:
            if el.get("type") not in ("node", "way"):
                continue

            if "center" in el:
                lat = el["center"]["lat"]
                lon = el["center"]["lon"]
            elif el.get("type") == "node":
                lat = el.get("lat")
                lon = el.get("lon")
            else:
                continue

            if lat is None or lon is None:
                continue

            tags  = el.get("tags", {})
            ftype = self._classify(tags)
            if not ftype:
                continue

            features.append({
                "lat":  lat,
                "lon":  lon,
                "type": ftype,
                "name": tags.get("name", ftype.title()),
            })
        return features

    def _classify(self, tags):
        if tags.get("highway") == "elevator":
            return "elevator"
        if tags.get("wheelchair") == "yes" or tags.get("ramp") == "yes":
            return "ramp"
        if tags.get("barrier"):
            return "barrier"
        return None

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _deliver_error(self, on_error, message):
        print(f"[OSMService] {message}")
        if on_error and not self._cancel:
            Clock.schedule_once(lambda dt: on_error(message), 0)