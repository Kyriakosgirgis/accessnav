import os
import math
import json

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.graphics import (
    Color, Ellipse, Line, Rectangle,
    RoundedRectangle, Triangle,
)
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout

from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp

# ------------------------------------------------------------------ #
#  Android-safe imports                                                #
# ------------------------------------------------------------------ #

try:
    from android.runnable import run_on_ui_thread
    ANDROID = True
except ImportError:
    ANDROID = False
    def run_on_ui_thread(func):
        return func

if ANDROID:
    from jnius import autoclass
    PythonActivity  = autoclass("org.kivy.android.PythonActivity")
    Intent          = autoclass("android.content.Intent")
    Uri             = autoclass("android.net.Uri")
    AndroidWebView  = autoclass("android.webkit.WebView")
    WebViewClient   = autoclass("android.webkit.WebViewClient")
    WebChromeClient = autoclass("android.webkit.WebChromeClient")
    ViewGroup       = autoclass("android.view.ViewGroup")
    LinearLayout    = autoclass("android.widget.LinearLayout")


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _haversine(lat1, lon1, lat2, lon2):
    R    = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a    = (math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2)
            * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _total_distance(waypoints):
    if not waypoints or len(waypoints) < 2:
        return 0.0
    return sum(
        _haversine(
            waypoints[i][0], waypoints[i][1],
            waypoints[i + 1][0], waypoints[i + 1][1],
        )
        for i in range(len(waypoints) - 1)
    )


def _fmt_distance(m):
    return f"{m / 1000:.1f} km" if m >= 1000 else f"{int(m)} m"


# ------------------------------------------------------------------ #
#  Paths                                                               #
# ------------------------------------------------------------------ #

ASSETS   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FAKE_CAM = os.path.join(ASSETS, "fake_camera.jpg")
AR_HTML  = os.path.join(ASSETS, "ar", "ar.html")


# ------------------------------------------------------------------ #
#  ARScreen                                                            #
# ------------------------------------------------------------------ #

class ARScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.route_points = []
        self.layout       = FloatLayout()
        self._webview     = None
        self._pulse_anim  = None
        self.add_widget(self.layout)

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def on_enter(self, *args):
        app = MDApp.get_running_app()
        if not app.is_logged_in():
            Clock.schedule_once(
                lambda dt: setattr(self.manager, "current", "login"), 0
            )
            return
        if ANDROID:
            Clock.schedule_once(lambda dt: self._open_webview(), 0.2)
        else:
            Clock.schedule_once(
                lambda dt: self._draw_desktop_simulation(), 0.1
            )

    def on_leave(self, *args):
        if self._pulse_anim:
            self._pulse_anim.stop(self._arrow_widget
                                  if hasattr(self, "_arrow_widget")
                                  else Widget())
        if ANDROID:
            Clock.schedule_once(lambda dt: self._close_webview(), 0)

    # ------------------------------------------------------------------ #
    #  Route handling                                                      #
    # ------------------------------------------------------------------ #

    def set_route(self, waypoints):
        self.route_points = waypoints or []
        print(f"[ARScreen] Route received: {len(self.route_points)} points")
        if not ANDROID:
            Clock.schedule_once(
                lambda dt: self._draw_desktop_simulation(), 0.1
            )
        elif self._webview:
            self._inject_route()

    # ------------------------------------------------------------------ #
    #  Desktop simulation                                                  #
    # ------------------------------------------------------------------ #

    def _draw_desktop_simulation(self):
        self.layout.clear_widgets()

        w = Window.width
        h = Window.height

        # ── 1. Camera background ──────────────────────────────── #
        if os.path.exists(FAKE_CAM):
            self.layout.add_widget(
                Image(
                    source=FAKE_CAM,
                    allow_stretch=True,
                    keep_ratio=False,
                    size_hint=(1, 1),
                    pos_hint={"x": 0, "y": 0},
                )
            )
        else:
            bg = Widget()
            with bg.canvas:
                Color(0.07, 0.09, 0.11, 1)
                Rectangle(pos=(0, 0), size=(w, h))
            self.layout.add_widget(bg)

        # ── 2. Dark vignette over camera ──────────────────────── #
        vignette = Widget()
        with vignette.canvas:
            Color(0, 0, 0, 0.22)
            Rectangle(pos=(0, 0), size=(w, h))
        self.layout.add_widget(vignette)

        # ── 3. Perspective pavement lines ─────────────────────── #
        #   Two converging lines vanishing at horizon (~44% height)
        #   give the illusion of a road receding into the distance.
        horizon_y = h * 0.44
        pavement  = Widget()
        with pavement.canvas:
            # Outer edge guides — faint white
            Color(1, 1, 1, 0.08)
            Line(
                points=[w * 0.08, 0, w * 0.43, horizon_y],
                width=1.2,
            )
            Line(
                points=[w * 0.92, 0, w * 0.57, horizon_y],
                width=1.2,
            )
            # Inner lane markings — dashed teal
            Color(0.11, 0.78, 0.50, 0.30)
            Line(
                points=[w * 0.38, 0, w * 0.475, horizon_y],
                width=1.5,
                dash_offset=8,
                dash_length=14,
            )
            Line(
                points=[w * 0.62, 0, w * 0.525, horizon_y],
                width=1.5,
                dash_offset=8,
                dash_length=14,
            )
        self.layout.add_widget(pavement)

        # ── 4. Ground-plane AR arrow ──────────────────────────── #
        #   Drawn in perspective so it looks painted on the ground.
        #   The arrow widens toward the bottom (near) and narrows
        #   toward the top (far), matching the pavement perspective.
        cx = w * 0.5

        # Arrow geometry — perspective-correct coordinates
        # Near base (bottom of screen) is wide, tip is high and narrow
        tip_x,   tip_y   = cx,          h * 0.36   # vanishing point region
        head_lx, head_ly = cx - w*0.13, h * 0.22   # arrowhead left
        head_rx, head_ry = cx + w*0.13, h * 0.22   # arrowhead right
        stem_lx, stem_ly = cx - w*0.055, h * 0.18  # stem inner-left
        stem_rx, stem_ry = cx + w*0.055, h * 0.18  # stem inner-right
        base_lx, base_ly = cx - w*0.055, h * 0.005 # stem base-left
        base_rx, base_ry = cx + w*0.055, h * 0.005 # stem base-right

        arrow_points = [
            tip_x,   tip_y,
            head_lx, head_ly,
            stem_lx, stem_ly,
            base_lx, base_ly,
            base_rx, base_ry,
            stem_rx, stem_ry,
            head_rx, head_ry,
            tip_x,   tip_y,
        ]

        self._arrow_widget = Widget()
        with self._arrow_widget.canvas:
            # Soft glow
            Color(0.11, 0.95, 0.50, 0.14)
            Line(points=arrow_points, width=22, joint="round", cap="round")

            # Mid glow
            Color(0.11, 0.95, 0.50, 0.28)
            Line(points=arrow_points, width=12, joint="round", cap="round")

            # Solid fill
            Color(0.11, 0.95, 0.50, 0.95)
            Line(points=arrow_points, width=4,  joint="round", cap="round")

        self.layout.add_widget(self._arrow_widget)

        # Breathing pulse animation
        self._pulse_anim = (
            Animation(opacity=0.50, duration=0.85)
            + Animation(opacity=1.00, duration=0.85)
        )
        self._pulse_anim.repeat = True
        self._pulse_anim.start(self._arrow_widget)

        # ── 5. Destination beacon at horizon ──────────────────── #
        #   Small, sits right at the vanishing-point area so it
        #   looks like it's far down the road.
        beacon_cx = cx
        beacon_cy = horizon_y + h * 0.04

        beacon = Widget()
        with beacon.canvas:
            # Outer pulse ring
            Color(1, 0.22, 0.22, 0.18)
            Ellipse(
                pos=(beacon_cx - 28, beacon_cy - 28),
                size=(56, 56),
            )
            # Mid ring
            Color(1, 0.22, 0.22, 0.45)
            Ellipse(
                pos=(beacon_cx - 16, beacon_cy - 16),
                size=(32, 32),
            )
            # Core dot
            Color(1, 0.28, 0.28, 1)
            Ellipse(
                pos=(beacon_cx - 8, beacon_cy - 8),
                size=(16, 16),
            )
        self.layout.add_widget(beacon)

        # Beacon pulse
        beacon_anim = (
            Animation(opacity=0.55, duration=0.7)
            + Animation(opacity=1.00, duration=0.7)
        )
        beacon_anim.repeat = True
        beacon_anim.start(beacon)

        # ── 6. Direction chip — top centre ────────────────────── #
        self.layout.add_widget(
            Label(
                text="↑   Continue forward",
                font_size="17sp",
                bold=True,
                color=(1, 1, 1, 1),
                pos_hint={"center_x": 0.5, "top": 0.97},
                size_hint=(None, None),
                size=("220dp", "36dp"),
            )
        )

        direction_bg = Widget()
        with direction_bg.canvas:
            Color(0, 0, 0, 0.50)
            RoundedRectangle(
                pos=(cx - 110, h * 0.935),
                size=(220, 38),
                radius=[19],
            )
        self.layout.add_widget(direction_bg)

        # ── 7. HUD card — bottom centre ───────────────────────── #
        dist_m  = _total_distance(self.route_points)
        eta_min = max(int(dist_m / 60), 0) if dist_m > 0 else 0

        dist_str = _fmt_distance(dist_m) if dist_m > 0 else "--"
        eta_str  = f"{eta_min} min"        if dist_m > 0 else "--"

        hud_w, hud_h = 240, 70
        hud_x = cx - hud_w / 2
        hud_y = 28

        hud_bg = Widget()
        with hud_bg.canvas:
            Color(0, 0, 0, 0.58)
            RoundedRectangle(
                pos=(hud_x, hud_y),
                size=(hud_w, hud_h),
                radius=[18],
            )
            # Thin border
            Color(1, 1, 1, 0.08)
            Line(
                rounded_rectangle=(hud_x, hud_y, hud_w, hud_h, 18),
                width=1,
            )
            # Divider
            Color(1, 1, 1, 0.12)
            Line(
                points=[cx, hud_y + 10, cx, hud_y + hud_h - 10],
                width=1,
            )
        self.layout.add_widget(hud_bg)

        # Distance value
        self.layout.add_widget(
            Label(
                text=dist_str,
                font_size="22sp",
                bold=True,
                color=(1, 1, 1, 1),
                pos_hint={"center_x": 0.29, "y": 0.065},
                size_hint=(None, None),
                size=("100dp", "30dp"),
            )
        )
        # Distance label
        self.layout.add_widget(
            Label(
                text="DISTANCE",
                font_size="9sp",
                color=(1, 1, 1, 0.45),
                pos_hint={"center_x": 0.29, "y": 0.044},
                size_hint=(None, None),
                size=("100dp", "16dp"),
            )
        )
        # ETA value
        self.layout.add_widget(
            Label(
                text=eta_str,
                font_size="22sp",
                bold=True,
                color=(1, 1, 1, 1),
                pos_hint={"center_x": 0.72, "y": 0.065},
                size_hint=(None, None),
                size=("100dp", "30dp"),
            )
        )
        # ETA label
        self.layout.add_widget(
            Label(
                text="ETA",
                font_size="9sp",
                color=(1, 1, 1, 0.45),
                pos_hint={"center_x": 0.72, "y": 0.044},
                size_hint=(None, None),
                size=("100dp", "16dp"),
            )
        )

        # ── 8. Stop FAB ───────────────────────────────────────── #
        from kivymd.uix.button import MDFabButton
        self.layout.add_widget(
            MDFabButton(
                icon="close",
                style="small",
                pos_hint={"center_x": 0.5, "y": 0.155},
                md_bg_color=(0.89, 0.25, 0.15, 1),
                on_release=self._stop_navigation,
            )
        )

    # ------------------------------------------------------------------ #
    #  Android WebView                                                     #
    # ------------------------------------------------------------------ #

    @run_on_ui_thread
    def _open_webview(self):
        if not ANDROID or self._webview:
            return
        try:
            activity = PythonActivity.mActivity
            self._webview = AndroidWebView(activity)
            s = self._webview.getSettings()
            s.setJavaScriptEnabled(True)
            s.setDomStorageEnabled(True)
            s.setMediaPlaybackRequiresUserGesture(False)
            s.setAllowFileAccess(True)
            s.setAllowContentAccess(True)
            s.setAllowFileAccessFromFileURLs(True)
            s.setAllowUniversalAccessFromFileURLs(True)
            self._webview.setWebViewClient(WebViewClient())
            self._webview.setWebChromeClient(WebChromeClient())
            self._webview.loadUrl("file://" + AR_HTML)
            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.addView(
                self._webview,
                ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                ),
            )
            activity.setContentView(layout)
            print("[ARScreen] WebView opened")
            Clock.schedule_once(lambda dt: self._inject_route(), 3)
        except Exception as e:
            print(f"[ARScreen] _open_webview error: {e}")

    def _inject_route(self):
        if not ANDROID or not self._webview or not self.route_points:
            return
        try:
            js = f"window.setRoute({json.dumps([[p[0], p[1]] for p in self.route_points])});"
            self._webview.evaluateJavascript(js, None)
            print(f"[ARScreen] Route injected — {len(self.route_points)} pts")
        except Exception as e:
            print(f"[ARScreen] _inject_route error: {e}")

    @run_on_ui_thread
    def _close_webview(self):
        if not ANDROID or not self._webview:
            return
        try:
            self._webview.destroy()
            self._webview = None
        except Exception as e:
            print(f"[ARScreen] _close_webview error: {e}")

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def _stop_navigation(self, *args):
        self.manager.current = "map"