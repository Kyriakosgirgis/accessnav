import json
from kivy.clock import Clock


class ARBridge:
    """
    Bridge between Python and the ARCore/AR.js scene running in WebView.
    Queues JS commands and delivers them once the scene is ready.
    """

    def __init__(self):
        self._browser            = None
        self._ready              = False
        self._queue              = []
        self._on_ready_cb        = None
        self._on_waypoint_cb     = None
        self._on_destination_cb  = None
        self._on_bearing_cb      = None
        self._browser_type       = None  # 'cef' or 'pywebview'

    # ------------------------------------------------------------------ #
    #  Setup                                                               #
    # ------------------------------------------------------------------ #

    def set_browser(self, browser):
        # Accept either a CEF browser or a pywebview Window object. The
        # caller may set browser_type attribute on the object or we try to
        # detect by presence of known methods.
        self._browser = browser
        # Detect type
        if browser is None:
            self._browser_type = None
        elif hasattr(browser, "ExecuteJavascript"):
            self._browser_type = "cef"
        else:
            # Assume pywebview window
            self._browser_type = "pywebview"

    def set_ready(self):
        self._ready = True
        for cmd in self._queue:
            self._exec(cmd)
        self._queue.clear()
        if self._on_ready_cb:
            Clock.schedule_once(lambda dt: self._on_ready_cb(), 0)

    def on_ready(self, cb):
        self._on_ready_cb = cb

    def on_waypoint_reached(self, cb):
        self._on_waypoint_cb = cb

    def on_destination_reached(self, cb):
        self._on_destination_cb = cb

    def on_bearing_update(self, cb):
        self._on_bearing_cb = cb

    def handle_message(self, url):
        """Called by the CEF URL interceptor when JS fires accessnav://..."""
        msg = url.replace("accessnav://", "")

        if msg == "ar_ready":
            Clock.schedule_once(lambda dt: self.set_ready(), 0)

        elif msg.startswith("waypoint_reached:"):
            idx = int(msg.split(":")[1])
            if self._on_waypoint_cb:
                Clock.schedule_once(lambda dt: self._on_waypoint_cb(idx), 0)

        elif msg == "destination_reached":
            if self._on_destination_cb:
                Clock.schedule_once(lambda dt: self._on_destination_cb(), 0)

        elif msg.startswith("bearing:"):
            try:
                bearing = float(msg.split(":")[1])
                if self._on_bearing_cb:
                    Clock.schedule_once(
                        lambda dt: self._on_bearing_cb(bearing), 0
                    )
            except ValueError:
                pass

    # ------------------------------------------------------------------ #
    #  AR commands → JS                                                    #
    # ------------------------------------------------------------------ #

    def set_user_location(self, lat, lon):
        self._run(f"setUserLocation({lat}, {lon});")

    def set_compass_bearing(self, degrees):
        self._run(f"setCompassBearing({degrees});")

    def set_waypoints(self, waypoints):
        """waypoints: list of (lat, lon) tuples"""
        coords = json.dumps([{"lat": p[0], "lon": p[1]} for p in waypoints])
        self._run(f"setWaypoints({coords});")

    def add_poi(self, lat, lon, spot_type, description=""):
        safe = description.replace("'", "\\'")
        self._run(f"addPOI({lat}, {lon}, '{spot_type}', '{safe}');")

    def clear_pois(self):
        self._run("clearPOIs();")

    def show_obstacle_warning(self, message):
        safe = message.replace("'", "\\'")
        self._run(f"showObstacleWarning('{safe}');")

    def update_hud(self, distance_m, eta_minutes):
        self._run(f"updateHUD({distance_m:.1f}, {eta_minutes:.1f});")

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
            if not self._browser:
                return
            if self._browser_type == "cef":
                try:
                    self._browser.ExecuteJavascript(js)
                    return
                except Exception:
                    # fall through to generic handler
                    pass

            # pywebview: try window.evaluate_js or webview.evaluate_js
            try:
                # Some pywebview Window objects expose evaluate_js
                if hasattr(self._browser, "evaluate_js"):
                    self._browser.evaluate_js(js)
                    return
            except Exception:
                pass

            try:
                import webview
                webview.evaluate_js(self._browser, js)
                return
            except Exception:
                pass

        except Exception as e:
            print(f"[ARBridge] JS error: {e}")