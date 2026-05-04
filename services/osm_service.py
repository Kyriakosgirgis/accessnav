import requests
from kivy.clock import Clock


class OSMService:
    """
    Fetch accessibility features (ramps, elevators, barriers)
    from Overpass API and return them as POI markers.
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    # Limassol bounding box (for safety + performance)
    LIMASSOL_BBOX = (33.00, 34.60, 33.10, 34.75)  # (min_lon, min_lat, max_lon, max_lat)

    def __init__(self):
        self._session = requests.Session()
        self._cancel = False

    # ------------------------------------------------------------------ #
    # PUBLIC API                                                         #
    # ------------------------------------------------------------------ #

    def fetch_accessibility_features(
        self,
        bbox=None,
        on_results=None,
        on_error=None
    ):
        """
        Fetch accessibility features from Overpass API.

        bbox: (min_lon, min_lat, max_lon, max_lat)
        """

        self._cancel = False

        # Default to Limassol if no bbox provided
        if not bbox:
            bbox = self.LIMASSOL_BBOX

        self._do_fetch(bbox, on_results, on_error)

    # ------------------------------------------------------------------ #
    # FETCH                                                              #
    # ------------------------------------------------------------------ #

    def _do_fetch(self, bbox, on_results, on_error):
        try:
            min_lon, min_lat, max_lon, max_lat = bbox

            print(f"[OSMService] Fetching Limassol data...")
            print(f"[OSMService] BBOX: {min_lat},{min_lon},{max_lat},{max_lon}")

            # ✅ Correct Overpass query
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

            print("[OSMService] Sending request to Overpass...")

            # ✅ FIXED REQUEST (this was your issue)
            response = self._session.post(
                self.OVERPASS_URL,
                data={"data": query},  # IMPORTANT
                headers={
                    "User-Agent": "AccessNav/1.0 (student project)"
                },
                timeout=20
            )

            response.raise_for_status()

            print(f"[OSMService] Response OK ({response.status_code})")

            if self._cancel:
                print("[OSMService] Cancelled")
                return

            data = response.json()
            elements = data.get("elements", [])

            print(f"[OSMService] Elements received: {len(elements)}")

            features = self._parse_features(elements)

            print(f"[OSMService] Parsed features: {len(features)}")

            # ------------------------------------------------------------------
            # Fallback sample data (for demo stability)
            # ------------------------------------------------------------------
            if not features:
                print("[OSMService] No real data found — adding sample markers")

                center_lat = (min_lat + max_lat) / 2
                center_lon = (min_lon + max_lon) / 2

                features = [
                    {
                        "lat": center_lat + 0.001,
                        "lon": center_lon + 0.001,
                        "type": "ramp",
                        "name": "Sample Ramp",
                    },
                    {
                        "lat": center_lat - 0.001,
                        "lon": center_lon,
                        "type": "elevator",
                        "name": "Sample Elevator",
                    },
                    {
                        "lat": center_lat,
                        "lon": center_lon - 0.001,
                        "type": "barrier",
                        "name": "Sample Barrier",
                    },
                ]

            # Return to UI thread
            if on_results:
                Clock.schedule_once(lambda dt: on_results(features), 0)

        except Exception as e:
            msg = f"OSM fetch error: {str(e)}"
            print(f"[OSMService] {msg}")

            if on_error:
                Clock.schedule_once(lambda dt: on_error(msg), 0)

    # ------------------------------------------------------------------ #
    # PARSING                                                            #
    # ------------------------------------------------------------------ #

    def _parse_features(self, elements):
        features = []

        for el in elements:
            if el.get("type") not in ("node", "way"):
                continue

            # Coordinates
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

            tags = el.get("tags", {})
            ftype = self._classify(tags)

            if not ftype:
                continue

            features.append({
                "lat": lat,
                "lon": lon,
                "type": ftype,
                "name": tags.get("name", ftype.title())
            })

        return features

    def _classify(self, tags):
        # Ramp
        if tags.get("wheelchair") == "yes" or tags.get("ramp") == "yes":
            return "ramp"

        # Elevator
        if tags.get("highway") == "elevator":
            return "elevator"

        # Barrier
        if tags.get("barrier"):
            return "barrier"

        return None

    # ------------------------------------------------------------------ #
    # CONTROL                                                            #
    # ------------------------------------------------------------------ #

    def cancel(self):
        self._cancel = True