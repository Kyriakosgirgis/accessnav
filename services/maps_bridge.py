import json
from kivy.clock import Clock


class MapsBridge:
    """
    Bridge between Python and the Google Maps JavaScript running
    inside the WebView. Queues JS commands and dispatches them
    when the map is ready.
    """

    def __init__(self):
        self._browser       = None   # CEF browser instance
        self._ready         = False  # True after JS signals map is loaded
        self._queue         = []     # commands queued before map is ready
        self._on_marker_cb  = None   # called when user taps a map marker
        self._on_ready_cb   = None   # called when map finishes loading

    # ------------------------------------------------------------------ #
    #  Setup                                                               #
    # ------------------------------------------------------------------ #

    def set_browser(self, browser):
        self._browser = browser

    def set_ready(self):
        """Called by JS via CEF's string visitor when the map loads."""
        self._ready = True
        if self._on_ready_cb:
            Clock.schedule_once(lambda dt: self._on_ready_cb(), 0)
        # Flush any commands that were queued before the map was ready
        for cmd in self._queue:
            self._exec(cmd)
        self._queue.clear()

    def on_ready(self, callback):
        self._on_ready_cb = callback

    def on_marker_tap(self, callback):
        self._on_marker_cb = callback

    # ------------------------------------------------------------------ #
    #  Map control commands                                                #
    # ------------------------------------------------------------------ #

    def center_on(self, lat, lon, zoom=16):
        self._run(f"mapCenterOn({lat}, {lon}, {zoom});")

    def set_user_marker(self, lat, lon):
        self._run(f"setUserMarker({lat}, {lon});")

    def set_destination_marker(self, lat, lon, title="Destination"):
        safe_title = title.replace("'", "\\'")
        self._run(f"setDestinationMarker({lat}, {lon}, '{safe_title}');")

    def clear_destination_marker(self):
        self._run("clearDestinationMarker();")

    def draw_route(self, waypoints):
        """
        Draw a polyline route on the map.
        waypoints: list of (lat, lon) tuples
        """
        coords = json.dumps([{"lat": p[0], "lng": p[1]} for p in waypoints])
        self._run(f"drawRoute({coords});")

    def clear_route(self):
        self._run("clearRoute();")

    def add_accessibility_marker(self, lat, lon, spot_type, description=""):
        """
        spot_type: 'ramp' | 'elevator' | 'barrier'
        """
        safe_desc = description.replace("'", "\\'")
        self._run(
            f"addAccessibilityMarker({lat}, {lon}, "
            f"'{spot_type}', '{safe_desc}');"
        )

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _run(self, js):
        if self._ready and self._browser:
            self._exec(js)
        else:
            self._queue.append(js)

    def _exec(self, js):
        try:
            self._browser.ExecuteJavascript(js)
        except Exception as e:
            print(f"[MapsBridge] JS error: {e}")