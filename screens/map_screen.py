from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFabButton, MDIconButton
from kivymd.uix.progressindicator import MDCircularProgressIndicator
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


class TappableRow(ButtonBehavior, MDBoxLayout):
    pass


class MapScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.gps = GPSService()
        self.geocoder = GeocodingService()

        self.map_view = None
        self.user_marker = None
        self.dest_marker = None

        self._map_ready = False
        self._first_fix = False
        self._search_event = None

        self.build_ui()

    # ---------------- UI ---------------- #
    def build_ui(self):
        root = FloatLayout()

        # ---------- MAP (BACKGROUND) ----------
        self.map_view = MapView(
            zoom=16,
            lat=34.7071,
            lon=33.0226,
            size_hint=(1, 1),
        )

        self.user_marker = MapMarker(
            lat=34.7071,
            lon=33.0226,
        )

        self.map_view.add_widget(self.user_marker)
        self._map_ready = True

        root.add_widget(self.map_view)

        # ---------- TOP BAR ----------
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
            )
        )

        # ---------- SEARCH BAR ----------
        search_box = MDBoxLayout(
            orientation="horizontal",
            size_hint=(0.9, None),
            height=dp(50),
            pos_hint={"center_x": 0.5, "top": 0.88},
            md_bg_color=(1, 1, 1, 1),
            radius=[dp(25)],
            padding=(dp(10), 0),
            spacing=dp(5),
        )

        search_box.add_widget(
            MDIconButton(icon="magnify")
        )

        self.search_field = TextInput(
            hint_text="Where to?",
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0, 0, 1),
            multiline=False,
            size_hint=(1, 1),
            padding=(dp(5), dp(12)),
            font_size=sp(16),
        )
        self.search_field.bind(text=self._on_search_text)

        search_box.add_widget(self.search_field)

        self.search_spinner = MDCircularProgressIndicator(
            size=(dp(20), dp(20)),
            opacity=0,
        )
        search_box.add_widget(self.search_spinner)

        self.clear_btn = MDIconButton(
            icon="close-circle",
            opacity=0,
            on_release=self.clear_search,
        )
        search_box.add_widget(self.clear_btn)

        root.add_widget(search_box)

        # ---------- DROPDOWN ----------
        self.dropdown = MDBoxLayout(
            orientation="vertical",
            size_hint=(0.9, None),
            height=0,
            pos_hint={"center_x": 0.5, "top": 0.82},
            md_bg_color=(1, 1, 1, 1),
            radius=[0, 0, dp(20), dp(20)],
            opacity=0,
        )
        root.add_widget(self.dropdown)

        # ---------- LEGEND ----------
        legend = MDBoxLayout(
            orientation="horizontal",
            size_hint=(0.9, None),
            height=dp(40),
            pos_hint={"center_x": 0.5, "y": 0.07},
            md_bg_color=(1, 1, 1, 0.95),
            radius=[dp(10)],
            padding=dp(10),
            spacing=dp(15),
        )

        for color, label in [
            ((0.11, 0.62, 0.46, 1), "Ramp"),
            ((0.22, 0.47, 0.87, 1), "Elevator"),
            ((0.89, 0.35, 0.19, 1), "Barrier"),
        ]:
            dot = MDBoxLayout(
                size_hint=(None, None),
                size=(dp(10), dp(10)),
                md_bg_color=color,
                radius=[dp(5)],
            )
            legend.add_widget(dot)
            legend.add_widget(MDLabel(text=label, size_hint_x=None, width=dp(70)))

        root.add_widget(legend)

        # ---------- FAB ----------
        root.add_widget(
            MDFabButton(
                icon="crosshairs-gps",
                pos_hint={"right": 0.95, "y": 0.18},
                on_release=self.centre_on_user,
            )
        )

        self.add_widget(root)

    # ---------------- SEARCH ---------------- #
    def _on_search_text(self, field, text):
        self.clear_btn.opacity = 1 if text else 0

        if self._search_event:
            self._search_event.cancel()

        if not text.strip():
            self._close_dropdown()
            return

        self._search_event = Clock.schedule_once(
            lambda dt: self._do_search(text), 0.5
        )

    def _do_search(self, query):
        self.search_spinner.opacity = 1
        self.geocoder.search(
            query=query,
            on_results=self._on_results,
            on_error=lambda e: print(e),
        )

    def _on_results(self, results):
        self.search_spinner.opacity = 0
        self._close_dropdown()

        for r in results:
            row = TappableRow(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=r["name"]))
            row.bind(on_release=lambda x, res=r: self._pick_result(res))
            self.dropdown.add_widget(row)

        self.dropdown.height = len(results) * dp(50)
        self.dropdown.opacity = 1

    def _close_dropdown(self):
        self.dropdown.clear_widgets()
        self.dropdown.height = 0
        self.dropdown.opacity = 0

    def _pick_result(self, result):
        self._place_destination_marker(result["lat"], result["lon"])

    # ---------------- MAP ---------------- #
    def _place_destination_marker(self, lat, lon):
        if self.dest_marker:
            self.map_view.remove_widget(self.dest_marker)

        self.dest_marker = MapMarker(lat=lat, lon=lon)
        self.map_view.add_widget(self.dest_marker)
        self.map_view.center_on(lat, lon)

    # ---------------- GPS ---------------- #
    def centre_on_user(self, *args):
        lat, lon = self.gps.get_location()
        self.map_view.center_on(lat, lon)

    # ---------------- ACTIONS ---------------- #
    def clear_search(self, *args):
        self.search_field.text = ""
        self._close_dropdown()

    def do_logout(self, *args):
        self.gps.stop()
        MDApp.get_running_app().logout()