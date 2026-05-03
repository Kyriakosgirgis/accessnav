from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFabButton, MDButton, MDButtonText, MDIconButton
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

from services.gps_service import GPSService
from services.geocoding_service import GeocodingService


# Limassol bounding box — adjust for your campus
VIEWBOX = (32.95, 34.63, 33.15, 34.72)  # (min_lon, min_lat, max_lon, max_lat)


class TappableRow(ButtonBehavior, MDBoxLayout):
    """A tappable MDBoxLayout row used in the search dropdown."""
    pass


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
        self._dropdown_open = False
        self._picking       = False   # suppresses search when we set field text
        self.destination    = None
        self.build_ui()

    # ------------------------------------------------------------------ #
    #  Auth guard & lifecycle                                              #
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
        self.geocoder.cancel()
        self._close_dropdown()
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
        self._build_map(root)

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

        # ── Search pill (Google Maps style) ───────────────────── #
        # Single white pill: [🔍] [bare TextInput] [spinner] [✕]
        # No visible inner borders — the pill IS the search bar.
        search_card = MDBoxLayout(
            orientation="vertical",
            size_hint=(0.9, None),
            adaptive_height=True,
            pos_hint={"center_x": 0.5, "top": 0.89},
            md_bg_color=(1, 1, 1, 1),
            radius=[dp(28)],
            padding=(dp(4), dp(6), dp(8), dp(6)),
        )

        search_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(0),
        )

        # Magnify icon — left anchor, purely decorative
        search_row.add_widget(
            MDIconButton(
                icon="magnify",
                theme_icon_color="Custom",
                icon_color=(0.45, 0.45, 0.45, 1),
                size_hint=(None, None),
                size=(dp(40), dp(44)),
                pos_hint={"center_y": 0.5},
            )
        )

        # Bare TextInput — transparent so the pill bg shows through
        self.search_field = TextInput(
            hint_text="Where to?",
            hint_text_color=(0.55, 0.55, 0.55, 1),
            foreground_color=(0.1, 0.1, 0.1, 1),
            cursor_color=(0.11, 0.62, 0.46, 1),
            background_color=(0, 0, 0, 0),
            background_normal="",
            background_active="",
            border=(0, 0, 0, 0),
            multiline=False,
            size_hint=(1, None),
            height=dp(44),
            padding=(dp(4), dp(12), dp(4), dp(12)),
            font_size=sp(16),
        )
        self.search_field.bind(text=self._on_search_text)
        search_row.add_widget(self.search_field)

        # Spinner — visible only while geocoding
        self.search_spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            pos_hint={"center_y": 0.5},
            opacity=0,
        )
        search_row.add_widget(self.search_spinner)

        # Clear button — hidden until the user types something
        self.clear_btn = MDIconButton(
            icon="close-circle",
            theme_icon_color="Custom",
            icon_color=(0.65, 0.65, 0.65, 1),
            size_hint=(None, None),
            size=(dp(36), dp(44)),
            pos_hint={"center_y": 0.5},
            opacity=0,
            on_release=self.clear_search,
        )
        search_row.add_widget(self.clear_btn)

        search_card.add_widget(search_row)

        # Destination strip — slides in when a result is picked
        self.dest_strip = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=0,
            opacity=0,
            padding=(dp(12), dp(4), dp(8), dp(8)),
            spacing=dp(8),
        )
        dest_text = MDBoxLayout(orientation="vertical")
        self.dest_name_label = MDLabel(
            text="",
            font_style="Label",
            role="medium",
            theme_text_color="Primary",
        )
        self.dest_addr_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            theme_text_color="Secondary",
        )
        dest_text.add_widget(self.dest_name_label)
        dest_text.add_widget(self.dest_addr_label)

        navigate_btn = MDButton(
            MDButtonText(text="Go"),
            style="filled",
            size_hint=(None, None),
            size=(dp(56), dp(40)),
            pos_hint={"center_y": 0.5},
            on_release=self.start_navigation,
        )
        self.dest_strip.add_widget(dest_text)
        self.dest_strip.add_widget(navigate_btn)
        search_card.add_widget(self.dest_strip)

        root.add_widget(search_card)
        self.search_card = search_card

        # ── Dropdown ──────────────────────────────────────────── #
        # Single MDBoxLayout — acts as both the styled container and the row list.
        # ScrollView can't clip with radius (corners stay rectangular).
        # Rows are capped at 4 so scrolling isn't needed.
        self.dropdown_scroll = MDBoxLayout(
            orientation="vertical",
            size_hint=(0.9, None),
            height=0,
            pos_hint={"center_x": 0.5, "top": 0.822},
            md_bg_color=(1, 1, 1, 1),
            radius=[0, 0, dp(24), dp(24)],
            opacity=0,
        )
        self.dropdown_list = self.dropdown_scroll   # same widget — no nesting
        root.add_widget(self.dropdown_scroll)

        # ── GPS status bar ────────────────────────────────────── #
        self.status_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height="30dp",
            pos_hint={"x": 0, "y": 0.08},
            padding=("12dp", "4dp"),
            spacing="8dp",
            md_bg_color=(0.11, 0.62, 0.46, 0.92),
            opacity=0,
        )
        self.status_spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=("16dp", "16dp"),
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
            adaptive_width=True,
            height="36dp",
            pos_hint={"center_x": 0.5, "y": 0.005},
            padding=("12dp", "4dp"),
            spacing="12dp",
            md_bg_color=(1, 1, 1, 0.92),
            radius=[10],
        )
        for color, label in [
            ((0.11, 0.62, 0.46, 1), "Ramp"),
            ((0.22, 0.47, 0.87, 1), "Elevator"),
            ((0.89, 0.35, 0.19, 1), "Barrier"),
        ]:
            legend.add_widget(
                MDBoxLayout(
                    size_hint=(None, None),
                    size=("10dp", "10dp"),
                    md_bg_color=color,
                    radius=[5],
                    pos_hint={"center_y": 0.5},
                )
            )
            legend.add_widget(
                MDLabel(
                    text=label,
                    font_style="Label",
                    role="small",
                    theme_text_color="Secondary",
                    size_hint_x=None,
                    width="60dp",
                )
            )
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

    def _build_map(self, root):
        try:
            from kivy_garden.mapview import MapView, MapMarker
            self.map_view = MapView(
                zoom=16,
                lat=GPSService.DEFAULT_LAT,
                lon=GPSService.DEFAULT_LON,
                double_tap_zoom=True,
            )
            self.user_marker = MapMarker(
                lat=GPSService.DEFAULT_LAT,
                lon=GPSService.DEFAULT_LON,
            )
            self.map_view.add_marker(self.user_marker)
            self._map_ready = True
            root.add_widget(self.map_view)
        except ImportError:
            root.add_widget(
                MDBoxLayout(md_bg_color=(0.95, 0.95, 0.95, 1))
            )
            root.add_widget(
                MDLabel(
                    text="[b]MapView not installed[/b]",
                    markup=True,
                    halign="center",
                    theme_text_color="Secondary",
                )
            )

    # ------------------------------------------------------------------ #
    #  Search logic                                                        #
    # ------------------------------------------------------------------ #

    def _on_search_text(self, field, text):
        self.clear_btn.opacity = 1 if text else 0

        if self._picking:
            return

        if self._search_event:
            self._search_event.cancel()

        text = text.strip()
        if not text:
            self._close_dropdown()
            self.geocoder.cancel()
            self._hide_search_spinner()
            return

        # Debounce — wait 600ms after typing stops
        self._search_event = Clock.schedule_once(
            lambda dt: self._do_search(text), 0.6
        )

    def _do_search(self, query):
        self._show_search_spinner()
        self.geocoder.search(
            query=query,
            on_results=self._on_results,
            on_error=self._on_search_error,
            viewbox=VIEWBOX,
        )

    def _on_results(self, results):
        self._hide_search_spinner()
        self._close_dropdown()

        if not results:
            self._show_no_results()
            return

        for result in results:
            self._add_dropdown_row(result)

        self._open_dropdown(min(len(results), 4))

    def _on_search_error(self, message):
        self._hide_search_spinner()
        self._close_dropdown()
        self._show_error_row(message)
        self._open_dropdown(1)

    def _add_dropdown_row(self, result):
        # TappableRow uses ButtonBehavior — it grabs the touch before dispatching
        # to children, so MDIconButton inside is purely decorative (never sees touches).
        tappable = TappableRow(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(4), 0, dp(16), 0),
            spacing=dp(4),
        )

        # Pin icon — safe to use without disabled; TappableRow catches all touches first
        tappable.add_widget(
            MDIconButton(
                icon="map-marker-outline",
                theme_icon_color="Custom",
                icon_color=(0.45, 0.45, 0.45, 1),
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                pos_hint={"center_y": 0.5},
            )
        )

        # Text column — explicit height + center_y keeps labels vertically centred
        text_col = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(38),
            pos_hint={"center_y": 0.5},
            spacing=dp(2),
        )
        text_col.add_widget(
            MDLabel(
                text=result["name"],
                font_style="Label",
                role="large",
                theme_text_color="Primary",
                size_hint_y=None,
                height=dp(22),
                shorten=True,
                shorten_from="right",
            )
        )
        text_col.add_widget(
            MDLabel(
                text=result["address"],
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(16),
                shorten=True,
                shorten_from="right",
            )
        )
        tappable.add_widget(text_col)
        tappable.bind(on_release=lambda x, r=result: self._pick_result(r))

        self.dropdown_list.add_widget(tappable)
        self.dropdown_list.add_widget(
            MDDivider(
                size_hint_y=None,
                height=dp(1),
                color=(0.9, 0.9, 0.9, 1),
            )
        )

    def _show_no_results(self):
        row = MDBoxLayout(
            size_hint_y=None,
            height=dp(52),
            padding=(dp(20), dp(10), dp(16), dp(10)),
        )
        row.add_widget(
            MDLabel(
                text="No places found.",
                font_style="Label",
                role="medium",
                theme_text_color="Secondary",
            )
        )
        self.dropdown_list.add_widget(row)
        self._open_dropdown(1)

    def _show_error_row(self, message):
        row = MDBoxLayout(
            size_hint_y=None,
            height=dp(52),
            padding=(dp(20), dp(10), dp(16), dp(10)),
        )
        row.add_widget(
            MDLabel(
                text=message,
                font_style="Label",
                role="medium",
                theme_text_color="Custom",
                text_color=(0.89, 0.35, 0.19, 1),
            )
        )
        self.dropdown_list.add_widget(row)

    def _pick_result(self, result):
        self._picking = True
        self.destination = result
        self.search_field.text = result["name"]   # would re-trigger search without flag
        self._picking = False
        if self._search_event:
            self._search_event.cancel()
        self._close_dropdown()
        self._place_destination_marker(result["lat"], result["lon"])
        self._show_destination_strip(result)
        print(
            f"[MapScreen] Destination: {result['name']} "
            f"({result['lat']:.5f}, {result['lon']:.5f})"
        )

    # ------------------------------------------------------------------ #
    #  Dropdown helpers                                                    #
    # ------------------------------------------------------------------ #

    def _open_dropdown(self, num_rows):
        self.dropdown_scroll.height  = num_rows * dp(57)
        self.dropdown_scroll.opacity = 1
        self._dropdown_open = True

    def _close_dropdown(self):
        self.dropdown_scroll.clear_widgets()
        self.dropdown_scroll.height  = 0
        self.dropdown_scroll.opacity = 0
        self._dropdown_open = False

    # ------------------------------------------------------------------ #
    #  Destination marker & strip                                          #
    # ------------------------------------------------------------------ #

    def _place_destination_marker(self, lat, lon):
        if not self._map_ready:
            return
        try:
            from kivy_garden.mapview import MapMarker
            if self.dest_marker:
                self.map_view.remove_marker(self.dest_marker)
            self.dest_marker = MapMarker(lat=lat, lon=lon)
            self.map_view.add_marker(self.dest_marker)
            self.map_view.center_on(lat, lon)
        except Exception as e:
            print(f"[MapScreen] Destination marker error: {e}")

    def _show_destination_strip(self, result):
        self.dest_name_label.text = result["name"]
        self.dest_addr_label.text = result["address"]
        self.dest_strip.height    = 52
        self.dest_strip.opacity   = 1

    def _hide_destination_strip(self):
        self.dest_strip.height  = 0
        self.dest_strip.opacity = 0

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
            from kivy_garden.mapview import MapMarker
            self.map_view.remove_marker(self.user_marker)
            self.user_marker = MapMarker(lat=lat, lon=lon)
            self.map_view.add_marker(self.user_marker)
        except Exception as e:
            print(f"[MapScreen] Marker error: {e}")

    # ------------------------------------------------------------------ #
    #  Status bar helpers                                                  #
    # ------------------------------------------------------------------ #

    def _show_status(self, message, searching=True, accuracy=None):
        self.status_bar.opacity     = 1
        self.status_label.text      = message
        self.status_spinner.opacity = 1 if searching else 0
        self.accuracy_label.text    = f"±{accuracy:.0f}m" if accuracy else ""
        self.status_bar.md_bg_color = (
            (0.11, 0.62, 0.46, 0.92) if searching else (0.6, 0.6, 0.6, 0.9)
        )

    def _hide_status_bar(self, dt=None):
        self.status_bar.opacity = 0

    def _show_search_spinner(self):
        self.search_spinner.opacity = 1

    def _hide_search_spinner(self):
        self.search_spinner.opacity = 0

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def clear_search(self, *args):
        self.search_field.text = ""
        self._close_dropdown()
        self._hide_destination_strip()
        self.destination = None
        if self.dest_marker and self.map_view:
            try:
                self.map_view.remove_marker(self.dest_marker)
                self.dest_marker = None
            except Exception:
                pass

    def centre_on_user(self, *args):
        if self._map_ready and self.map_view:
            lat, lon = self.gps.get_location()
            self.map_view.center_on(lat, lon)
            self.map_view.zoom = 16

    def start_navigation(self, *args):
        if not self.destination:
            return
        print(
            f"[MapScreen] Navigating to: {self.destination['name']} "
            f"({self.destination['lat']:.5f}, {self.destination['lon']:.5f})"
        )
        # Phase 4: pass destination to routing_service, then switch to AR
        self.manager.current = "ar"

    def do_logout(self, *args):
        self.gps.stop()
        MDApp.get_running_app().logout()