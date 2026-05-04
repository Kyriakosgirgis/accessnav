import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFabButton, MDIconButton, MDButton, MDButtonText
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.divider import MDDivider
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

VIEWBOX = (32.95, 34.63, 33.15, 34.72)


# ------------------------------------------------------------------ #
#  Tappable row                                                        #
# ------------------------------------------------------------------ #

class TappableRow(ButtonBehavior, MDBoxLayout):
    def on_press(self):
        self.md_bg_color = (0.11, 0.62, 0.46, 0.07)

    def on_release(self):
        self.md_bg_color = (1, 1, 1, 1)


# ------------------------------------------------------------------ #
#  MapScreen                                                           #
# ------------------------------------------------------------------ #

class MapScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gps            = GPSService()
        self.geocoder       = GeocodingService()
        self.map_view       = None
        self.user_marker    = None
        self.dest_marker    = None
        self._map_ready     = False
        self._first_fix     = False
        self._search_event  = None
        self._searching     = False   # lock — prevents dropdown reopening
        self.destination    = None
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
    #  Build UI                                                            #
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
        # Fully pill-shaped search bar (radius = half height)
        search_pill = MDBoxLayout(
            orientation="horizontal",
            size_hint=(0.92, None),
            height=dp(48),
            pos_hint={"center_x": 0.5, "top": 0.87},
            md_bg_color=(1, 1, 1, 1),
            radius=[dp(24)],          # full pill
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

        # ── Destination strip ─────────────────────────────────── #
        # Appears below the search pill after picking a result
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

        # Pin icon
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

        # Name + address
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

        # Go button
        self.dest_card.add_widget(
            MDButton(
                MDButtonText(text="Go"),
                style="filled",
                size_hint=(None, None),
                size=(dp(52), dp(36)),
                pos_hint={"center_y": 0.5},
                on_release=self.start_navigation,
            )
        )
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

        # ── Legend — centred pill ─────────────────────────────── #
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

        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Search logic                                                        #
    # ------------------------------------------------------------------ #

    def _on_search_text(self, field, text):
        # If we just picked a result, ignore the text change it caused
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

        # Pin icon
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

        # Text
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

        # Chevron
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
        # Set lock BEFORE changing text so _on_search_text ignores the change
        self._searching = True
        self.destination = result

        self._close_dropdown()
        self.geocoder.cancel()
        if self._search_event:
            self._search_event.cancel()

        # Update search field text — lock prevents re-triggering search
        self.search_field.text = result["name"]
        self.clear_btn.opacity = 1
        self.search_spinner.opacity = 0

        # Release lock after one frame
        Clock.schedule_once(lambda dt: setattr(self, "_searching", False), 0.1)

        self._place_destination_marker(result["lat"], result["lon"])
        self._show_dest_card(result)

        print(
            f"[MapScreen] Destination: {result['name']} "
            f"({result['lat']:.5f}, {result['lon']:.5f})"
        )

    # ------------------------------------------------------------------ #
    #  Dropdown open / close                                               #
    # ------------------------------------------------------------------ #

    def _open_dropdown(self, num_rows):
        row_h = dp(67)
        self.dropdown_scroll.height  = min(num_rows * row_h, dp(268))
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
            (0.11, 0.62, 0.46, 0.92) if searching else (0.4, 0.4, 0.4, 0.88)
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
        Clock.schedule_once(lambda dt: setattr(self, "_searching", False), 0.1)
        self._close_dropdown()
        self._hide_dest_card()
        self.destination = None
        if self.dest_marker:
            try:
                self.map_view.remove_marker(self.dest_marker)
                self.dest_marker = None
            except Exception:
                pass

    def centre_on_user(self, *args):
        lat, lon = self.gps.get_location()
        if self._map_ready and self.map_view:
            self.map_view.center_on(lat, lon)
            self.map_view.zoom = 16

    def start_navigation(self, *args):
        if not self.destination:
            return
        print(
            f"[MapScreen] Navigating to {self.destination['name']} "
            f"({self.destination['lat']:.5f}, {self.destination['lon']:.5f})"
        )
        ar = self.manager.get_screen("ar")
        lat, lon = self.gps.get_location()
        ar.set_route([
            (lat, lon),
            (self.destination["lat"], self.destination["lon"]),
        ])
        self.manager.current = "ar"

    def do_logout(self, *args):
        self.gps.stop()
        MDApp.get_running_app().logout()