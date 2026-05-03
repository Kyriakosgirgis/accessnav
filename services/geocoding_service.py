import requests
import threading
from typing import List, Dict, Optional


class GeocodingService:
    """
    Geocodes addresses using the free OpenStreetMap Nominatim API.
    No API key required.

    Nominatim usage policy:
    - Maximum 1 request per second
    - Must include a User-Agent header
    - Do not store results for long periods
    https://operations.osmfoundation.org/policies/nominatim/
    """

    BASE_URL    = "https://nominatim.openstreetmap.org/search"
    USER_AGENT  = "AccessNav/1.0 (accessible navigation app)"
    TIMEOUT     = 8    # seconds before giving up
    MAX_RESULTS = 5    # max results shown in the dropdown

    # Bias results toward Cyprus
    COUNTRY_CODES = "cy"

    def __init__(self):
        self._last_query  = ""
        self._cancel_flag = False

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def search(
        self,
        query: str,
        on_results,
        on_error=None,
        viewbox: Optional[tuple] = None,
    ):
        """
        Search for a place asynchronously.
        Results are delivered via on_results(list[dict]) on the main thread.

        Args:
            query      — the user's search text
            on_results — callback(results: list[dict])
                         each dict has: name, address, lat, lon
            on_error   — callback(error_message: str)
            viewbox    — optional (min_lon, min_lat, max_lon, max_lat)
                         to bias results toward a bounding box
        """
        query = query.strip()
        if not query or query == self._last_query:
            return

        self._last_query  = query
        self._cancel_flag = False

        thread = threading.Thread(
            target=self._fetch,
            args=(query, on_results, on_error, viewbox),
            daemon=True,
        )
        thread.start()

    def cancel(self):
        """Cancel any in-flight search."""
        self._cancel_flag = True
        self._last_query  = ""

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _fetch(self, query, on_results, on_error, viewbox):
        params = {
            "q":              query,
            "format":         "json",
            "addressdetails": 1,
            "limit":          self.MAX_RESULTS,
            "countrycodes":   self.COUNTRY_CODES,
            "dedupe":         1,
        }

        # Add viewbox bias if provided
        if viewbox:
            min_lon, min_lat, max_lon, max_lat = viewbox
            params["viewbox"]  = f"{min_lon},{max_lat},{max_lon},{min_lat}"
            params["bounded"]  = 0   # 0 = prefer viewbox but show global too

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers={"User-Agent": self.USER_AGENT},
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()

            if self._cancel_flag:
                return

            raw      = response.json()
            results  = [self._parse(r) for r in raw]
            results  = [r for r in results if r]  # filter None

            # Deliver results on the Kivy main thread
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: on_results(results), 0)

        except requests.exceptions.ConnectionError:
            self._deliver_error(
                on_error, "No internet connection. Check your network."
            )
        except requests.exceptions.Timeout:
            self._deliver_error(on_error, "Search timed out. Try again.")
        except requests.exceptions.HTTPError as e:
            self._deliver_error(on_error, f"Search error: {e}")
        except Exception as e:
            self._deliver_error(on_error, f"Unexpected error: {e}")

    def _parse(self, raw: dict) -> Optional[Dict]:
        """Convert a raw Nominatim result into a clean dict."""
        try:
            lat  = float(raw["lat"])
            lon  = float(raw["lon"])
            name = self._build_name(raw)
            addr = self._build_address(raw.get("address", {}))
            return {
                "name":    name,
                "address": addr,
                "lat":     lat,
                "lon":     lon,
            }
        except (KeyError, ValueError):
            return None

    def _build_name(self, raw: dict) -> str:
        """Build a readable place name from the result."""
        addr = raw.get("address", {})

        # Try common name fields in priority order
        for key in ("name", "amenity", "shop", "building", "road"):
            if key in addr and addr[key]:
                return addr[key]

        # Fall back to display_name truncated
        display = raw.get("display_name", "Unknown place")
        return display.split(",")[0].strip()

    def _build_address(self, addr: dict) -> str:
        """Build a short readable address string."""
        parts = []
        for key in ("road", "suburb", "city", "town", "village", "state"):
            val = addr.get(key)
            if val and val not in parts:
                parts.append(val)
            if len(parts) == 3:
                break
        return ", ".join(parts) if parts else "Cyprus"

    def _deliver_error(self, on_error, message):
        if self._cancel_flag:
            return
        print(f"[GeocodingService] {message}")
        if on_error:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: on_error(message), 0)