import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Ellipse

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFabButton, MDIconButton, MDButton, MDButtonText
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.divider import MDDivider
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.appbar import (
    MDTopAppBar,
    MDTopAppBarTitle,
    MDTopAppBarLeadingButtonContainer,
    MDTopAppBarTrailingButtonContainer,
    MDActionTopAppBarButton,
)
from kivymd.app import MDApp

from kivy_garden.mapview import MapView, MapMarker

from services.gps_service import GPSService
from services.geocoding_service import GeocodingService
from services.osm_service import OSMService
from services.routing_service import RoutingService

from components.route_layer import RouteLayer

VIEWBOX = (32.95, 34.63, 33.15, 34.72)


# ------------------------------------------------------------------ #
#  POI Marker                                                          #
# ------------------------------------------------------------------ #

class POIMarker(MapMarker):

    def __init__(self, lat, lon, feature_type="ramp", **kwargs):
        super().__init__(lat=lat, lon=lon, **kwargs)
        self.feature_type = feature_type
        self.size     = (dp(18), dp(18))
        self.anchor_x = 0.5
        self.anchor_y = 0.5

        color_map = {
            "ramp":     (0.18, 0.62, 0.38, 1),
            "elevator": (0.27, 0.49, 0.85, 1),
            "barrier":  (0.88, 0.36, 0.20, 1),
        }
        color = color_map.get(feature_type, (0.5, 0.5, 0.5, 1))

        with self.canvas:
            Color(1, 1, 1, 1)
            self.bg  = Ellipse(size=(dp(20), dp(20)), pos=self.pos)
            Color(*color)
            self.dot = Ellipse(size=(dp(14), dp(14)), pos=self.pos)

        self.bind(pos=self._update)

    def _update(self, *args):
        self.bg.pos  = self.pos
        self.dot.pos = (self.pos[0] + dp(3), self.pos[1] + dp(3))


# ------------------------------------------------------------------ #
#  Tappable row                                                        #
# ------------------------------------------------------------------ #

class TappableRow(ButtonBehavior, MDBoxLayout):
    def on_press(self):
        self.md_bg_color = (0.11, 0.62, 0.46, 0.07)

    def on_release(self):
        self.md_bg_color = (1, 1, 1, 1)


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _haversine(lat1, lon1, lat2, lon2):
    import math
    R    = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a    = (math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ------------------------------------------------------------------ #
#  MapScreen                                                           #
# ------------------------------------------------------------------ #

class MapScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gps            = GPSService()
        self.geocoder       = GeocodingService()
        self.osm            = OSMService()
        self.routing        = RoutingService()
        self.route_layer    = RouteLayer()
        self.map_view       = None
        self.user_marker    = None
        self.dest_marker    = None
        self._map_ready     = False
        self._first_fix     = False
        self._search_event  = None
        self._searching     = False
        self._routing       = False
        self.destination    = None
        self.poi_markers    = []
        self.poi_visible    = True
        self.build_ui()

    # ------------------------------------------------------------------ #
    #  Auth guard                                                          #
    # ------------------------------------------------------------------ #

    def on_enter(self, *args):
        app = MDApp.get_running_app()
        if not app.is_logged_in():
            Clock.schedule_once(
                lambda dt: setattr(self.manager, "current", "login"), 0
            )
            return
        self._on_authenticated()

    def on_leave(self, *args):
        self.gps.stop()
        self.osm.cancel()
        self.routing.cancel()
        self._clear_poi_markers()
        try:
            self.route_layer.clear_route()
        except Exception:
            pass
        try:
            self._hide_route_info()
        except Exception:
            pass
        self._first_fix = False

    def _on_authenticated(self):
        app = MDApp.get_running_app()
        print(f"[MapScreen] Welcome, {app.current_user['name']}")
        self._show_status("Getting location...", searching=True)
        self.gps.start(
            on_location=self._on_location_update,
            on_status=self._on_gps_status,
        )

    # ------------------------------------------------------------------ #
    #  Build UI — unchanged from your file                                #
    # ------------------------------------------------------------------ #

    def build_ui(self):
        root = FloatLayout()

        # ── Map ───────────────────────────────────────────────── #
        self.map_view = MapView(
            zoom=16,
            lat=34.7071,
            lon=33.0226,
            double_tap_zoom=True,
            size_hint=(1, 1),
        )
        self.user_marker = MapMarker(lat=34.7071, lon=33.0226)
        self.map_view.add_marker(self.user_marker)

        try:
            self.map_view.add_layer(self.route_layer, mode="window")
            self.route_layer._map_view = self.map_view
            self.route_layer.size      = self.map_view.size
            self.route_layer.pos       = (0, 0)
            try:
                self.map_view.bind(
                    size=lambda *a: setattr(
                        self.route_layer, "size", self.map_view.size
                    )
                )
            except Exception:
                pass
        except Exception:
            try:
                self.map_view.add_widget(self.route_layer)
                self.route_layer._map_view = self.map_view
            except Exception:
                print("[MapScreen] Warning: could not attach RouteLayer")

        self._map_ready = True
        root.add_widget(self.map_view)

        # ── Top app bar ───────────────────────────────────────── #
        root.add_widget(
            MDTopAppBar(
                MDTopAppBarLeadingButtonContainer(
                    MDActionTopAppBarButton(icon="menu")
                ),
                MDTopAppBarTitle(text="AccessNav"),
                MDTopAppBarTrailingButtonContainer(
                    MDActionTopAppBarButton(
                        icon="logout",
                        on_release=self.do_logout,
                    )
                ),
                type="small",
                pos_hint={"top": 1},
                size_hint_y=None,
                height="56dp",
            )
        )

        # ── Search pill ───────────────────────────────────────── #
        search_pill = MDBoxLayout(
            orientation="horizontal",
            size_hint=(0.92, None),
            height=dp(48),
            pos_hint={"center_x": 0.5, "top": 0.87},
            md_bg_color=(1, 1, 1, 1),
            radius=[dp(24)],
            padding=(dp(8), dp(6), dp(8), dp(6)),
            spacing=dp(4),
        )
        search_pill.add_widget(
            MDIconButton(
                icon="magnify",
                theme_icon_color="Custom",
                icon_color=(0.11, 0.62, 0.46, 1),
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                pos_hint={"center_y": 0.5},
            )
        )
        self.search_field = TextInput(
            hint_text="Where to?",
            hint_text_color=(0.75, 0.75, 0.75, 1),
            background_color=(0, 0, 0, 0),
            foreground_color=(0.08, 0.08, 0.08, 1),
            cursor_color=(0.11, 0.62, 0.46, 1),
            multiline=False,
            size_hint=(1, None),
            height=dp(36),
            padding=(dp(0), dp(10)),
            font_size=sp(15),
        )
        self.search_field.bind(text=self._on_search_text)
        search_pill.add_widget(self.search_field)
        self.search_spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            pos_hint={"center_y": 0.5},
            opacity=0,
        )
        search_pill.add_widget(self.search_spinner)
        self.clear_btn = MDIconButton(
            icon="close-circle-outline",
            theme_icon_color="Custom",
            icon_color=(0.65, 0.65, 0.65, 1),
            size_hint=(None, None),
            size=(dp(38), dp(38)),
            pos_hint={"center_y": 0.5},
            opacity=0,
            on_release=self.clear_search,
        )
        search_pill.add_widget(self.clear_btn)
        root.add_widget(search_pill)

        # ── Dropdown results ──────────────────────────────────── #
        self.dropdown_scroll = ScrollView(
            size_hint=(0.92, None),
            height=0,
            pos_hint={"center_x": 0.5, "top": 0.805},
            opacity=0,
            do_scroll_x=False,
        )
        self.dropdown_list = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            adaptive_height=True,
            md_bg_color=(1, 1, 1, 1),
            radius=[0, 0, dp(20), dp(20)],
            padding=(dp(0), dp(6), dp(0), dp(8)),
            spacing=dp(0),
        )
        self.dropdown_scroll.add_widget(self.dropdown_list)
        root.add_widget(self.dropdown_scroll)

        # ── Destination card ──────────────────────────────────── #
        self.dest_card = MDBoxLayout(
            orientation="horizontal",
            size_hint=(0.92, None),
            height=0,
            opacity=0,
            pos_hint={"center_x": 0.5, "top": 0.805},
            md_bg_color=(1, 1, 1, 1),
            radius=[dp(16)],
            padding=(dp(12), dp(8), dp(12), dp(8)),
            spacing=dp(10),
        )
        self.dest_card.add_widget(
            MDIconButton(
                icon="map-marker",
                theme_icon_color="Custom",
                icon_color=(0.11, 0.62, 0.46, 1),
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                pos_hint={"center_y": 0.5},
            )
        )
        dest_text = MDBoxLayout(orientation="vertical", size_hint_x=1)
        self.dest_name_label = MDLabel(
            text="",
            font_style="Label",
            role="large",
            theme_text_color="Primary",
            bold=True,
            size_hint_y=None,
            height=dp(22),
            shorten=True,
            shorten_from="right",
        )
        self.dest_addr_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(16),
            shorten=True,
            shorten_from="right",
        )
        dest_text.add_widget(self.dest_name_label)
        dest_text.add_widget(self.dest_addr_label)
        self.dest_card.add_widget(dest_text)
        self.go_btn = MDButton(
            MDButtonText(text="Go"),
            style="filled",
            size_hint=(None, None),
            size=(dp(52), dp(36)),
            pos_hint={"center_y": 0.5},
            on_release=self.start_navigation,
        )
        self.dest_card.add_widget(self.go_btn)
        root.add_widget(self.dest_card)

        # ── GPS status bar ────────────────────────────────────── #
        self.status_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(30),
            pos_hint={"x": 0, "y": 0.105},
            padding=(dp(12), dp(4)),
            spacing=dp(8),
            md_bg_color=(0.11, 0.62, 0.46, 0.92),
            opacity=0,
        )
        self.status_spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(16), dp(16)),
            pos_hint={"center_y": 0.5},
        )
        self.status_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        self.accuracy_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.8, 1, 0.9, 1),
            halign="right",
        )
        self.status_bar.add_widget(self.status_spinner)
        self.status_bar.add_widget(self.status_label)
        self.status_bar.add_widget(self.accuracy_label)
        root.add_widget(self.status_bar)

        # ── Legend ────────────────────────────────────────────── #
        legend = MDBoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=dp(40),
            width=dp(320),
            pos_hint={"center_x": 0.5, "y": 0.005},
            padding=(dp(14), dp(6)),
            spacing=dp(14),
            md_bg_color=(1, 1, 1, 0.98),
            radius=[dp(10)],
        )
        for color, label in [
            ((0.11, 0.62, 0.46, 1), "Ramp"),
            ((0.22, 0.47, 0.87, 1), "Elevator"),
            ((0.89, 0.35, 0.19, 1), "Barrier"),
        ]:
            dot = MDBoxLayout(
                size_hint=(None, None),
                size=(dp(12), dp(12)),
                md_bg_color=color,
                radius=[dp(6)],
                pos_hint={"center_y": 0.5},
            )
            lbl = MDLabel(
                text=label,
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint=(None, None),
                size=(dp(70), dp(20)),
                halign="left",
                font_size="13sp",
            )
            legend.add_widget(dot)
            legend.add_widget(lbl)
        root.add_widget(legend)

        # ── Locate me FAB ─────────────────────────────────────── #
        root.add_widget(
            MDFabButton(
                icon="crosshairs-gps",
                pos_hint={"right": 0.95, "y": 0.12},
                on_release=self.centre_on_user,
            )
        )

        # ── POI Toggle FAB ────────────────────────────────────── #
        self.poi_toggle = MDFabButton(
            icon="map-marker-multiple",
            pos_hint={"x": 0.05, "y": 0.12},
            on_release=self._toggle_poi_markers,
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            md_bg_color=(0.2, 0.8, 0.2, 1),
        )
        root.add_widget(self.poi_toggle)

        # ── Route info card ───────────────────────────────────── #
        self.route_info_card = MDCard(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(260), dp(72)),
            # Move the route info card lower on the screen to avoid
            # overlapping the top UI elements. 'y' places the card a
            # fraction above the bottom of the screen.
            pos_hint={"right": 0.98, "y": 0.22},
            md_bg_color=(1, 1, 1, 0.98),
            radius=[dp(12)],
            padding=(dp(12), dp(8)),
            spacing=dp(6),
            elevation=6,
            opacity=0,
            height=0,
        )

        top_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(22),
        )
        self.route_title = MDLabel(
            text="Route",
            font_style="Label",
            role="small",
            bold=True,
            size_hint_x=1,
            halign="left",
            theme_text_color="Primary",
        )
        close_btn = MDIconButton(
            icon="close",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5},
            on_release=lambda *_: self.stop_route(),
        )
        ar_btn = MDIconButton(
            icon="camera",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5},
            on_release=lambda *_: self._open_ar(),
        )
        top_row.add_widget(self.route_title)
        top_row.add_widget(ar_btn)
        top_row.add_widget(close_btn)

        info_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
        )
        self.route_distance_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            size_hint_x=0.5,
            halign="left",
            theme_text_color="Secondary",
        )
        self.route_eta_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            size_hint_x=0.3,
            halign="center",
            theme_text_color="Secondary",
        )
        self.route_score_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            size_hint_x=0.2,
            halign="right",
            theme_text_color="Secondary",
        )
        info_row.add_widget(self.route_distance_label)
        info_row.add_widget(self.route_eta_label)
        info_row.add_widget(self.route_score_label)

        self.route_info_card.add_widget(top_row)
        self.route_info_card.add_widget(info_row)
        root.add_widget(self.route_info_card)

        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Search logic                                                        #
    # ------------------------------------------------------------------ #

    def _on_search_text(self, field, text):
        if self._searching:
            return
        self.clear_btn.opacity = 1 if text else 0
        if self._search_event:
            self._search_event.cancel()
        if not text.strip():
            self._close_dropdown()
            self.geocoder.cancel()
            self.search_spinner.opacity = 0
            return
        self._search_event = Clock.schedule_once(
            lambda dt: self._do_search(text), 0.6
        )

    def _do_search(self, query):
        self.search_spinner.opacity = 1
        self.geocoder.search(
            query=query,
            on_results=self._on_results,
            on_error=self._on_search_error,
            viewbox=VIEWBOX,
        )

    def _on_results(self, results):
        self.search_spinner.opacity = 0
        self._close_dropdown()
        if not results:
            self._add_message_row(
                "No places found. Try a different search.", error=False
            )
            self._open_dropdown(1)
            return
        for r in results:
            self._add_result_row(r)
        self._open_dropdown(min(len(results), 4))

    def _on_search_error(self, message):
        self.search_spinner.opacity = 0
        self._close_dropdown()
        self._add_message_row(message, error=True)
        self._open_dropdown(1)

    # ------------------------------------------------------------------ #
    #  Result rows                                                         #
    # ------------------------------------------------------------------ #

    def _add_result_row(self, result):
        row = TappableRow(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(12), dp(6), dp(12), dp(6)),
            spacing=dp(10),
            md_bg_color=(1, 1, 1, 1),
        )
        row.add_widget(
            MDBoxLayout(
                MDIconButton(
                    icon="map-marker-outline",
                    theme_icon_color="Custom",
                    icon_color=(0.11, 0.62, 0.46, 1),
                    size_hint=(None, None),
                    size=(dp(28), dp(28)),
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                ),
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                md_bg_color=(0.11, 0.62, 0.46, 0.12),
                radius=[dp(10)],
                pos_hint={"center_y": 0.5},
            )
        )
        text_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=1,
            padding=(0, dp(2), 0, dp(2)),
        )
        text_col.add_widget(
            MDLabel(
                text=result["name"],
                font_style="Label",
                role="large",
                theme_text_color="Primary",
                bold=True,
                size_hint_y=None,
                height=dp(20),
                shorten=True,
                shorten_from="right",
            )
        )
        text_col.add_widget(
            MDLabel(
                text=result.get("address", "Cyprus"),
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(14),
                shorten=True,
                shorten_from="right",
            )
        )
        row.add_widget(text_col)
        row.add_widget(
            MDIconButton(
                icon="chevron-right",
                theme_icon_color="Custom",
                icon_color=(0.82, 0.82, 0.82, 1),
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={"center_y": 0.5},
            )
        )
        row.bind(on_release=lambda x, r=result: self._pick_result(r))
        self.dropdown_list.add_widget(row)
        self.dropdown_list.add_widget(
            MDDivider(size_hint_y=None, height="0.5dp")
        )

    def _add_message_row(self, text, error=False):
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            padding=(dp(12), dp(6), dp(12), dp(6)),
            spacing=dp(10),
            md_bg_color=(1, 1, 1, 1),
        )
        row.add_widget(
            MDIconButton(
                icon="alert-circle-outline" if error else "information-outline",
                theme_icon_color="Custom",
                icon_color=(
                    (0.89, 0.35, 0.19, 1) if error else (0.65, 0.65, 0.65, 1)
                ),
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={"center_y": 0.5},
            )
        )
        row.add_widget(
            MDLabel(
                text=text,
                font_style="Label",
                role="medium",
                theme_text_color="Custom",
                text_color=(
                    (0.89, 0.35, 0.19, 1) if error else (0.60, 0.60, 0.60, 1)
                ),
            )
        )
        self.dropdown_list.add_widget(row)

    def _pick_result(self, result):
        self._searching  = True
        self.destination = result
        self._close_dropdown()
        self.geocoder.cancel()
        if self._search_event:
            self._search_event.cancel()
        self.search_field.text      = result["name"]
        self.clear_btn.opacity      = 1
        self.search_spinner.opacity = 0
        Clock.schedule_once(
            lambda dt: setattr(self, "_searching", False), 0.1
        )
        self._place_destination_marker(result["lat"], result["lon"])
        self._show_dest_card(result)
        print(
            f"[MapScreen] Destination: {result['name']} "
            f"({result['lat']:.5f}, {result['lon']:.5f})"
        )

    # ------------------------------------------------------------------ #
    #  Dropdown                                                            #
    # ------------------------------------------------------------------ #

    def _open_dropdown(self, num_rows):
        self.dropdown_scroll.height  = min(num_rows * dp(67), dp(268))
        self.dropdown_scroll.opacity = 1

    def _close_dropdown(self):
        self.dropdown_list.clear_widgets()
        self.dropdown_scroll.height  = 0
        self.dropdown_scroll.opacity = 0

    # ------------------------------------------------------------------ #
    #  Destination card                                                    #
    # ------------------------------------------------------------------ #

    def _show_dest_card(self, result):
        self.dest_name_label.text = result["name"]
        self.dest_addr_label.text = result.get("address", "Cyprus")
        self.dest_card.height     = dp(60)
        self.dest_card.opacity    = 1

    def _hide_dest_card(self):
        self.dest_card.height  = 0
        self.dest_card.opacity = 0

    # ------------------------------------------------------------------ #
    #  Map marker                                                          #
    # ------------------------------------------------------------------ #

    def _place_destination_marker(self, lat, lon):
        if self.dest_marker:
            try:
                self.map_view.remove_marker(self.dest_marker)
            except Exception:
                pass
        self.dest_marker = MapMarker(lat=lat, lon=lon)
        self.map_view.add_marker(self.dest_marker)
        self.map_view.center_on(lat, lon)
        try:
            self.route_layer.clear_route()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  POI markers                                                         #
    # ------------------------------------------------------------------ #

    def _fetch_poi_markers(self, lat, lon):
        if hasattr(self, "_last_poi_fetch"):
            last_lat, last_lon = self._last_poi_fetch
            if abs(lat - last_lat) < 0.001 and abs(lon - last_lon) < 0.001:
                return
        self._last_poi_fetch = (lat, lon)
        offset = 0.003
        bbox   = (
            lon - offset, lat - offset,
            lon + offset, lat + offset,
        )
        print(f"[MapScreen] Fetching LOCAL POIs for bbox: {bbox}")
        self.osm.fetch_accessibility_features(
            bbox=bbox,
            on_results=self._on_poi_results,
            on_error=self._on_poi_error,
        )

    def _on_poi_results(self, features):
        self._clear_poi_markers()
        print(f"[MapScreen] Got {len(features)} POI features from OSM")
        for feature in features:
            try:
                marker = POIMarker(
                    lat=feature["lat"],
                    lon=feature["lon"],
                    feature_type=feature["type"],
                )
                marker.feature_name = feature.get(
                    "name", feature["type"].title()
                )
                marker.feature_data = feature
                marker.bind(on_release=self._on_poi_marker_tap)
                self.map_view.add_marker(marker)
                self.poi_markers.append(marker)
            except Exception as e:
                print(f"[MapScreen] Error adding POI marker: {e}")

    def _on_poi_marker_tap(self, marker):
        try:
            feature_name = getattr(marker, "feature_name", "POI")
            feature_type = getattr(marker, "feature_type", "unknown")
            MDSnackbar(
                MDSnackbarText(
                    text=f"{feature_name} ({feature_type.title()})",
                ),
                duration=2,
            ).open()
        except Exception as e:
            print(f"[MapScreen] POI tap error: {e}")

    def _on_poi_error(self, message):
        print(f"[MapScreen] POI fetch error: {message}")

    def _clear_poi_markers(self):
        for marker in self.poi_markers:
            try:
                self.map_view.remove_marker(marker)
            except Exception:
                pass
        self.poi_markers.clear()

    def _toggle_poi_markers(self, *args):
        self.poi_visible = not self.poi_visible
        if self.poi_visible:
            for marker in self.poi_markers:
                try:
                    self.map_view.add_marker(marker)
                except Exception:
                    pass
            self.poi_toggle.md_bg_color = (0.2, 0.8, 0.2, 1)
        else:
            for marker in self.poi_markers:
                try:
                    self.map_view.remove_marker(marker)
                except Exception:
                    pass
            self.poi_toggle.md_bg_color = (0.5, 0.5, 0.5, 1)

    # ------------------------------------------------------------------ #
    #  GPS callbacks                                                       #
    # ------------------------------------------------------------------ #

    def _on_location_update(self, lat, lon, accuracy):
        if not self._map_ready:
            return
        if not self._first_fix:
            self._first_fix = True
            self.map_view.center_on(lat, lon)
            self.map_view.zoom = 16
            self._show_status(
                "Location found", searching=False, accuracy=accuracy
            )
            Clock.schedule_once(lambda dt: self._hide_status_bar(), 3)
            self._fetch_poi_markers(lat, lon)
        self._move_user_marker(lat, lon)
        self.accuracy_label.text = f"±{accuracy:.0f}m"

    def _on_gps_status(self, stype, message):
        if stype == "provider-disabled":
            self._show_status("GPS unavailable", searching=False)

    def _move_user_marker(self, lat, lon):
        if not self.map_view or not self.user_marker:
            return
        try:
            self.map_view.remove_marker(self.user_marker)
            self.user_marker = MapMarker(lat=lat, lon=lon)
            self.map_view.add_marker(self.user_marker)
        except Exception as e:
            print(f"[MapScreen] Marker error: {e}")

    # ------------------------------------------------------------------ #
    #  Status bar                                                          #
    # ------------------------------------------------------------------ #

    def _show_status(self, message, searching=True, accuracy=None):
        self.status_bar.opacity     = 1
        self.status_label.text      = message
        self.status_spinner.opacity = 1 if searching else 0
        self.accuracy_label.text    = f"±{accuracy:.0f}m" if accuracy else ""
        self.status_bar.md_bg_color = (
            (0.11, 0.62, 0.46, 0.92) if searching
            else (0.4, 0.4, 0.4, 0.88)
        )

    def _hide_status_bar(self, dt=None):
        self.status_bar.opacity = 0

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def clear_search(self, *args):
        self._searching = True
        self.search_field.text = ""
        self.clear_btn.opacity = 0
        Clock.schedule_once(
            lambda dt: setattr(self, "_searching", False), 0.1
        )
        self._close_dropdown()
        self._hide_dest_card()
        self.destination = None
        if self.dest_marker:
            try:
                self.map_view.remove_marker(self.dest_marker)
                self.dest_marker = None
            except Exception:
                pass
        try:
            self.route_layer.clear_route()
            self._hide_route_info()
        except Exception:
            pass

    def centre_on_user(self, *args):
        lat, lon = self.gps.get_location()
        if self._map_ready and self.map_view:
            self.map_view.center_on(lat, lon)
            self.map_view.zoom = 16

    def start_navigation(self, *args):
        """Tap Go — calls ORS directly, no graph build needed."""
        if not self.destination or self._routing:
            return

        self._routing = True
        origin = self.gps.get_location()
        dest   = (self.destination["lat"], self.destination["lon"])

        # Disable Go button while routing
        self.go_btn.disabled = True
        for child in self.go_btn.children:
            if hasattr(child, "text"):
                child.text = "..."

        self._show_status("Finding route...", searching=True)

        # Collect barrier POIs and pass them as avoid_polygons to ORS.
        barriers = []
        try:
            for marker in self.poi_markers:
                if getattr(marker, "feature_type", None) == "barrier":
                    barriers.append((marker.lat, marker.lon))
        except Exception:
            barriers = []

        self.routing.find_route(
            origin=origin,
            destination=dest,
            on_route=self._on_route,
            on_error=self._on_route_error,
            avoid_polygons=barriers,
            avoid_radius_m=4,
        )

    def do_logout(self, *args):
        self.gps.stop()
        MDApp.get_running_app().logout()

    # ------------------------------------------------------------------ #
    #  Routing callbacks                                                   #
    # ------------------------------------------------------------------ #

    def _on_route(self, result):
        """Called by RoutingService when ORS returns a route."""
        self._routing        = False
        self.go_btn.disabled = False
        for child in self.go_btn.children:
            if hasattr(child, "text"):
                child.text = "Go"

        try:
            waypoints = result.get("waypoints", [])
            score     = result.get("accessibility_score", 0.85)
            dist      = result.get("distance_m", 0.0)
            eta       = result.get("eta_minutes", 0.0)

            if not waypoints or len(waypoints) < 2:
                self._on_route_error("Route returned no waypoints")
                return

            # Draw route
            try:
                self.route_layer._map_view = self.map_view
                self.route_layer.set_route(waypoints, score=score)
                self.route_layer.invalidate()
            except Exception as e:
                print(f"[MapScreen] Route draw error: {e}")

            # Centre map on route midpoint
            try:
                mid = waypoints[len(waypoints) // 2]
                self.map_view.center_on(mid[0], mid[1])
            except Exception:
                pass

            # Show info card
            self._show_route_info(result)
            self._hide_status_bar()

            # Pass waypoints to AR screen
            try:
                ar = self.manager.get_screen("ar")
                if hasattr(ar, "set_route"):
                    ar.set_route(waypoints)
            except Exception:
                pass

        except Exception as e:
            print(f"[MapScreen] _on_route error: {e}")

    def _on_route_error(self, message):
        """ORS failed — draw a straight-line fallback."""
        self._routing        = False
        self.go_btn.disabled = False
        for child in self.go_btn.children:
            if hasattr(child, "text"):
                child.text = "Go"

        print(f"[MapScreen] Route error: {message}")

        try:
            origin = self.gps.get_location()
            dest   = (
                self.destination["lat"],
                self.destination["lon"],
            ) if self.destination else None

            if dest:
                fallback_dist = _haversine(
                    origin[0], origin[1], dest[0], dest[1]
                )
                fallback = [origin, dest]
                try:
                    self.route_layer._map_view = self.map_view
                    self.route_layer.set_route(fallback, score=0.5)
                    self.route_layer.invalidate()
                except Exception:
                    pass
                self._show_route_info({
                    "waypoints":           fallback,
                    "distance_m":          fallback_dist,
                    "eta_minutes":         fallback_dist / 60.0,
                    "accessibility_score": 0.5,
                })
        except Exception as e:
            print(f"[MapScreen] Fallback routing failed: {e}")

        self._hide_status_bar()

        MDSnackbar(
            MDSnackbarText(text=message),
            duration=4,
        ).open()

    def _show_route_info(self, result):
        try:
            dist  = result.get("distance_m",          0.0)
            eta   = result.get("eta_minutes",          0.0)
            score = result.get("accessibility_score",  0.0)
            self.route_distance_label.text = f"{dist:.0f} m"
            self.route_eta_label.text      = f"{eta:.0f} min"
            self.route_score_label.text    = f"{score:.2f}"
            self.route_info_card.opacity   = 1
            self.route_info_card.height    = dp(72)
        except Exception as e:
            print(f"[MapScreen] _show_route_info error: {e}")

    def _hide_route_info(self):
        try:
            self.route_info_card.opacity       = 0
            self.route_info_card.height        = 0
            self.route_distance_label.text     = ""
            self.route_eta_label.text          = ""
            self.route_score_label.text        = ""
        except Exception:
            pass

    def stop_route(self, *args):
        try:
            self.route_layer.clear_route()
        except Exception:
            pass
        self._hide_route_info()

    def _open_ar(self):
        try:
            ar = self.manager.get_screen("ar")
            waypoints = getattr(self.route_layer, "_waypoints", None)
            if waypoints and hasattr(ar, "set_route"):
                ar.set_route(waypoints)
            self.manager.current = "ar"
        except Exception as e:
            print(f"[MapScreen] _open_ar failed: {e}")