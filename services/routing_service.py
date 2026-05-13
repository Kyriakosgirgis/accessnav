import os
import threading

import openrouteservice
from kivy.clock import Clock

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


API_KEY = os.getenv("ORS_API_KEY", "")


class RoutingService:
    """
    Wheelchair-accessible routing using OpenRouteService.

    Uses ORS's built-in wheelchair profile instead of custom
    barrier avoidance logic.

    This provides:
    - better pedestrian geometry
    - smoother routes
    - accessibility-aware routing
    - kerb/incline/surface handling
    - more realistic navigation
    """

    def __init__(self):

        if not API_KEY:
            print(
                "[RoutingService] WARNING — "
                "ORS_API_KEY not found in .env"
            )

        self.client = openrouteservice.Client(
            key=API_KEY
        )

        self._cancel = False

    # ------------------------------------------------------------------ #
    #  Public API                                                        #
    # ------------------------------------------------------------------ #

    def find_route(
        self,
        origin,
        destination,
        on_route=None,
        on_error=None,
        avoid_polygons=None,
        avoid_radius_m=3,
    ):
        """
        origin/destination: (lat, lon)

        avoid_polygons: optional list of (lat, lon) tuples or dicts {"lat":..,"lon":..}
                        which will be converted to small buffer polygons and
                        passed to ORS as a MultiPolygon under the `options`
                        -> "avoid_polygons" key.

        result: { waypoints, distance_m, eta_minutes, instructions, accessibility_score }
        """

        self._cancel = False

        threading.Thread(
            target=self._route_thread,
            args=(
                origin,
                destination,
                on_route,
                on_error,
                avoid_polygons,
                avoid_radius_m,
            ),
            daemon=True,
        ).start()

    def cancel(self):
        self._cancel = True

    # ------------------------------------------------------------------ #
    #  Background Routing                                                #
    # ------------------------------------------------------------------ #

    def _route_thread(
        self,
        origin,
        destination,
        on_route,
        on_error,
        avoid_polygons=None,
        avoid_radius_m=3,
    ):

        try:

            print(
                f"[RoutingService] Requesting wheelchair route {origin} → {destination}"
            )

            # ORS requires [lon, lat]
            coords = [
                [origin[1], origin[0]],
                [destination[1], destination[0]],
            ]

            # Build avoid_polygons option if requested
            options = None
            polys = []
            if avoid_polygons:
                for pt in avoid_polygons:
                    if isinstance(pt, dict):
                        lat = pt.get("lat")
                        lon = pt.get("lon")
                    else:
                        lat, lon = pt
                    if lat is None or lon is None:
                        continue
                    ring = self._buffer_point_ring(lat, lon, avoid_radius_m)
                    ring_lonlat = [[p[1], p[0]] for p in ring]
                    polys.append([ring_lonlat])
                if polys:
                    options = {"avoid_polygons": {"type": "MultiPolygon", "coordinates": polys}}

            if options:
                print(f"[RoutingService] Sending avoid_polygons with {len(polys)} polygon(s)")
                route = self.client.directions(
                    coordinates=coords,
                    profile="wheelchair",
                    format="geojson",
                    instructions=True,
                    instructions_format="text",
                    language="en",
                    geometry_simplify=False,
                    validate=False,
                    options=options,
                )
            else:
                print("[RoutingService] No avoid_polygons — standard routing")
                route = self.client.directions(
                    coordinates=coords,
                    profile="wheelchair",
                    format="geojson",
                    instructions=True,
                    instructions_format="text",
                    language="en",
                    geometry_simplify=False,
                    validate=False,
                )

            if self._cancel:
                return

            # ---------------------------------------------------------- #
            # Parse response                                             #
            # ---------------------------------------------------------- #

            feature = route["features"][0]

            geometry = feature["geometry"]["coordinates"]

            props = feature["properties"]

            summary = props["summary"]

            segments = props.get("segments", [])

            # Flatten geometry
            def flatten(coords):
                for item in coords:
                    if not item:
                        continue
                    if isinstance(item[0], (int, float)):
                        yield item
                    else:
                        for sub in item:
                            if isinstance(sub, list) and len(sub) >= 2:
                                yield sub

            raw_coords = list(flatten(geometry))

            # Convert to (lat, lon)
            waypoints = []
            prev = None
            for coord in raw_coords:
                try:
                    lon, lat = coord[0], coord[1]
                except Exception:
                    continue
                pt = (lat, lon)
                if prev:
                    if abs(prev[0] - pt[0]) < 1e-06 and abs(prev[1] - pt[1]) < 1e-06:
                        continue
                waypoints.append(pt)
                prev = pt

            # Instructions
            instructions = []
            for seg in segments:
                for step in seg.get("steps", []):
                    instructions.append({
                        "instruction": step.get("instruction", ""),
                        "distance": step.get("distance", 0),
                        "duration": step.get("duration", 0),
                        "type": step.get("type", 0),
                    })

            # Accessibility score
            score = 0.85
            if summary["distance"] < 300:
                score += 0.03
            if len(instructions) < 10:
                score += 0.02
            score = min(score, 1.0)

            result = {
                "waypoints": waypoints,
                "distance_m": summary["distance"],
                "eta_minutes": summary["duration"] / 60,
                "instructions": instructions,
                "accessibility_score": round(score, 2),
            }

            print(
                f"[RoutingService] Route found — {len(waypoints)} waypoints, "
                f"{summary['distance']:.0f}m, {summary['duration'] / 60:.1f} min"
            )

            if on_route and not self._cancel:
                Clock.schedule_once(lambda dt: on_route(result), 0)

        except openrouteservice.exceptions.ApiError as e:

            self._deliver_error(
                on_error,
                f"Routing API error: {e}"
            )

        except openrouteservice.exceptions.ValidationError as e:

            self._deliver_error(
                on_error,
                f"Invalid coordinates: {e}"
            )

        except Exception as e:

            msg = str(e)

            if "quota" in msg.lower() or "429" in msg:

                self._deliver_error(
                    on_error,
                    "Daily routing quota exceeded."
                )

            elif "Unable to find" in msg or "2010" in msg:

                self._deliver_error(
                    on_error,
                    "No wheelchair-accessible route found."
                )

            else:

                self._deliver_error(
                    on_error,
                    f"Routing error: {msg}"
                )

    # ------------------------------------------------------------------ #
    #  Error Handling                                                    #
    # ------------------------------------------------------------------ #

    def _deliver_error(
        self,
        on_error,
        message,
    ):

        print(f"[RoutingService] {message}")

        if on_error and not self._cancel:

            Clock.schedule_once(
                lambda dt: on_error(message),
                0,
            )

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _buffer_point_ring(self, lat, lon, radius_m, steps=12):
        """Return a small circular polygon ring approximating a buffer
        around the given (lat, lon). Uses a simple degrees-per-metre
        approximation adequate for small radii (few metres).
        Returns list of (lat, lon) with first == last to close the ring.
        """
        import math

        # degrees per metre at the given latitude
        deg_per_m_lat = 1.0 / 111320.0
        deg_per_m_lon = 1.0 / (111320.0 * math.cos(math.radians(lat)))

        ring = []
        for i in range(steps):
            theta = 2 * math.pi * i / steps
            dlat = math.sin(theta) * radius_m * deg_per_m_lat
            dlon = math.cos(theta) * radius_m * deg_per_m_lon
            ring.append((lat + dlat, lon + dlon))
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])
        return ring