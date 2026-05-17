import os
import json

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout

from kivymd.uix.screen import MDScreen

# -------------------------------------------------- #
# Android-safe imports
# -------------------------------------------------- #

try:
    from android.runnable import run_on_ui_thread

    ANDROID = True

except ImportError:

    ANDROID = False

    def run_on_ui_thread(func):
        return func


# -------------------------------------------------- #
# Android-only imports
# -------------------------------------------------- #

if ANDROID:

    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    WebView = autoclass("android.webkit.WebView")
    WebViewClient = autoclass("android.webkit.WebViewClient")
    WebChromeClient = autoclass("android.webkit.WebChromeClient")
    ViewGroup = autoclass("android.view.ViewGroup")
    LinearLayout = autoclass("android.widget.LinearLayout")


# -------------------------------------------------- #
# AR Screen
# -------------------------------------------------- #

class ARScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.route_points = []

        self.layout = FloatLayout()

        self.add_widget(self.layout)

        self.webview = None

        # Desktop placeholder before route loads
        if not ANDROID:

            self.desktop_label = Label(
                text="Waiting for route...",
                font_size="22sp",
                color=(1, 1, 1, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )

            self.layout.add_widget(self.desktop_label)

    # -------------------------------------------------- #
    # Lifecycle
    # -------------------------------------------------- #

    def on_enter(self, *args):

        if ANDROID:

            Clock.schedule_once(
                lambda dt: self.open_webview(),
                0.2
            )

    def on_leave(self, *args):

        if ANDROID:

            Clock.schedule_once(
                lambda dt: self.close_webview(),
                0
            )

    # -------------------------------------------------- #
    # Route handling
    # -------------------------------------------------- #

    def set_route(self, waypoints):

        self.route_points = waypoints or []

        print(f"[ARScreen] Received route: {len(self.route_points)} points")

        # Desktop simulation
        if not ANDROID:

            self._draw_desktop_simulation()

            return

        # Android JS injection
        try:

            if self.webview:

                js_data = json.dumps(self.route_points)

                js = f"window.setRoute({js_data});"

                self.webview.evaluateJavascript(js, None)

                print("[ARScreen] Route injected into WebView")

        except Exception as e:
            print(f"[ARScreen] JS injection error: {e}")

    # -------------------------------------------------- #
    # Desktop visualization
    # -------------------------------------------------- #

    def _draw_desktop_simulation(self):

        self.layout.clear_widgets()

        width = self.width if self.width > 0 else 390
        height = self.height if self.height > 0 else 844

        # -------------------------------------------------- #
        # Background
        # -------------------------------------------------- #

        bg = Widget()

        with bg.canvas:

            Color(0.02, 0.02, 0.03, 1)

            Rectangle(
                pos=(0, 0),
                size=(width, height)
            )

        self.layout.add_widget(bg)

        # -------------------------------------------------- #
        # Horizon line
        # -------------------------------------------------- #

        horizon = Widget()

        with horizon.canvas:

            Color(0.3, 0.3, 0.3, 1)

            Line(
                points=[
                    0,
                    height * 0.53,
                    width,
                    height * 0.53
                ],
                width=1
            )

        self.layout.add_widget(horizon)

        # -------------------------------------------------- #
        # Perspective road
        # -------------------------------------------------- #

        road = Widget()

        with road.canvas:

            Color(0.18, 0.18, 0.18, 1)

            Line(
                points=[
                    width * 0.34, 0,
                    width * 0.48, height * 0.53
                ],
                width=7
            )

            Line(
                points=[
                    width * 0.66, 0,
                    width * 0.52, height * 0.53
                ],
                width=7
            )

        self.layout.add_widget(road)

        # -------------------------------------------------- #
        # Route points
        # -------------------------------------------------- #

        total = min(len(self.route_points), 10)

        route_positions = []

        for i in range(total):

            progress = i / max(total - 1, 1)

            y = 140 + progress * (height * 0.44)

            road_width = 55 * (1 - progress)

            x_center = width / 2

            # Keep nodes aligned INSIDE road
            if i % 2 == 0:
                x = x_center - road_width * 0.3
            else:
                x = x_center + road_width * 0.3

            route_positions.append((x, y))

        # -------------------------------------------------- #
        # Connectors
        # -------------------------------------------------- #

        for i in range(1, len(route_positions)):

            px, py = route_positions[i - 1]
            x, y = route_positions[i]

            connector = Widget()

            with connector.canvas:

                Color(0.1, 1, 0.3, 0.9)

                Line(
                    points=[
                        px + 10,
                        py + 10,
                        x + 10,
                        y + 10
                    ],
                    width=2
                )

            self.layout.add_widget(connector)

        # -------------------------------------------------- #
        # Route markers
        # -------------------------------------------------- #

        for i, (x, y) in enumerate(route_positions):

            progress = i / max(total - 1, 1)

            size = 24 * (1 - progress * 0.35)

            marker = Widget()

            with marker.canvas:

                # Glow
                Color(0.1, 1, 0.3, 0.18)

                Ellipse(
                    pos=(x - size * 0.7, y - size * 0.7),
                    size=(size * 2.2, size * 2.2)
                )

                # Dot
                Color(0.15, 0.95, 0.3, 1)

                Ellipse(
                    pos=(x, y),
                    size=(size, size)
                )

            self.layout.add_widget(marker)

        # -------------------------------------------------- #
        # Destination beacon
        # -------------------------------------------------- #

        beacon = Widget()

        bx = width / 2 - 22
        by = height * 0.64

        with beacon.canvas:

            Color(1, 0.2, 0.2, 0.2)

            Ellipse(
                pos=(bx - 14, by - 14),
                size=(76, 76)
            )

            Color(1, 0.2, 0.2, 1)

            Ellipse(
                pos=(bx, by),
                size=(44, 44)
            )

        self.layout.add_widget(beacon)

        # -------------------------------------------------- #
        # Title
        # -------------------------------------------------- #

        title = Label(
            text="AR Navigation Preview",
            font_size="22sp",
            color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )

        self.layout.add_widget(title)

        # -------------------------------------------------- #
        # HUD
        # -------------------------------------------------- #

        hud = Label(
            text=f"{len(self.route_points)} route points loaded",
            font_size="16sp",
            color=(1, 1, 1, 0.85),
            pos_hint={"center_x": 0.5, "top": 0.88},
        )

        self.layout.add_widget(hud)

        # -------------------------------------------------- #
        # Direction
        # -------------------------------------------------- #

        direction = Label(
            text="↑ Continue Forward",
            font_size="30sp",
            color=(0.1, 1, 0.3, 1),
            pos_hint={"center_x": 0.5, "y": 0.08},
        )

        self.layout.add_widget(direction)

    # -------------------------------------------------- #
    # Android WebView
    # -------------------------------------------------- #

    @run_on_ui_thread
    def open_webview(self):

        if not ANDROID:
            return

        try:

            if self.webview:
                return

            activity = PythonActivity.mActivity

            self.webview = WebView(activity)

            settings = self.webview.getSettings()

            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setMediaPlaybackRequiresUserGesture(False)
            settings.setAllowFileAccess(True)
            settings.setAllowContentAccess(True)

            self.webview.setWebViewClient(WebViewClient())
            self.webview.setWebChromeClient(WebChromeClient())

            html_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "assets",
                    "ar.html"
                )
            )

            url = "file://" + html_path

            print(f"[ARScreen] Loading {url}")

            self.webview.loadUrl(url)

            layout = LinearLayout(activity)

            layout.setOrientation(LinearLayout.VERTICAL)

            layout.addView(
                self.webview,
                ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                ),
            )

            activity.setContentView(layout)

            print("[ARScreen] WebView opened")

            Clock.schedule_once(
                lambda dt: self._inject_route_if_ready(),
                3
            )

        except Exception as e:
            print(f"[ARScreen] open_webview error: {e}")

    # -------------------------------------------------- #
    # Inject route into JS
    # -------------------------------------------------- #

    def _inject_route_if_ready(self):

        if not ANDROID:
            return

        if not self.webview:
            return

        if not self.route_points:
            return

        try:

            js_data = json.dumps(self.route_points)

            js = f"window.setRoute({js_data});"

            self.webview.evaluateJavascript(js, None)

            print("[ARScreen] Initial route injected")

        except Exception as e:
            print(f"[ARScreen] inject error: {e}")

    # -------------------------------------------------- #
    # Cleanup
    # -------------------------------------------------- #

    @run_on_ui_thread
    def close_webview(self):

        if not ANDROID:
            return

        try:

            if not self.webview:
                return

            self.webview.destroy()

            self.webview = None

            print("[ARScreen] WebView destroyed")

        except Exception as e:
            print(f"[ARScreen] close_webview error: {e}")