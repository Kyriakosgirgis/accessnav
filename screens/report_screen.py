import os
import requests
import threading

from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.appbar import MDTopAppBar, MDTopAppBarTitle
from kivymd.uix.divider import MDDivider
from kivymd.app import MDApp

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


class ReportScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.barrier_checks = {}
        self._submitting    = False
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
        self._refresh_location_label()

    # ------------------------------------------------------------------ #
    #  Build UI                                                            #
    # ------------------------------------------------------------------ #

    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        # ── Toolbar ───────────────────────────────────────────── #
        root.add_widget(
            MDTopAppBar(
                MDTopAppBarTitle(text="Report a Barrier"),
                type="small",
                size_hint_y=None,
                height="56dp",
            )
        )

        # ── Scrollable form ───────────────────────────────────── #
        scroll = ScrollView()
        form   = MDBoxLayout(
            orientation="vertical",
            padding=(dp(20), dp(16), dp(20), dp(24)),
            spacing=dp(14),
            size_hint_y=None,
            adaptive_height=True,
        )

        # Location info row
        loc_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            spacing=dp(8),
        )
        loc_row.add_widget(
            MDIconButton(
                icon="crosshairs-gps",
                theme_icon_color="Custom",
                icon_color=(0.11, 0.62, 0.46, 1),
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={"center_y": 0.5},
            )
        )
        self.location_label = MDLabel(
            text="Fetching location...",
            font_style="Label",
            role="medium",
            theme_text_color="Secondary",
        )
        loc_row.add_widget(self.location_label)
        form.add_widget(loc_row)

        form.add_widget(MDDivider(size_hint_y=None, height="0.5dp"))

        # Barrier type heading
        form.add_widget(
            MDLabel(
                text="What did you find?",
                font_style="Title",
                role="small",
                theme_text_color="Primary",
                size_hint_y=None,
                height=dp(32),
            )
        )

        # Barrier type checkboxes
        barrier_types = [
            ("broken_elevator", "Broken elevator",        "elevator"),
            ("missing_ramp",    "Missing ramp",           "wheelchair-accessibility"),
            ("blocked_path",    "Blocked accessible path","road-variant"),
            ("steep_slope",     "Steep slope",            "image-filter-hdr"),
            ("other",           "Other barrier",          "alert-circle-outline"),
        ]

        for key, label, icon in barrier_types:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                spacing=dp(12),
            )
            cb = MDCheckbox(
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={"center_y": 0.5},
            )
            self.barrier_checks[key] = cb

            row.add_widget(cb)
            row.add_widget(
                MDIconButton(
                    icon=icon,
                    theme_icon_color="Custom",
                    icon_color=(0.11, 0.62, 0.46, 1),
                    size_hint=(None, None),
                    size=(dp(28), dp(28)),
                    pos_hint={"center_y": 0.5},
                )
            )
            row.add_widget(
                MDLabel(
                    text=label,
                    font_style="Label",
                    role="large",
                    theme_text_color="Primary",
                    pos_hint={"center_y": 0.5},
                )
            )
            form.add_widget(row)

        form.add_widget(MDDivider(size_hint_y=None, height="0.5dp"))

        # Description field
        form.add_widget(
            MDLabel(
                text="Add details",
                font_style="Title",
                role="small",
                theme_text_color="Primary",
                size_hint_y=None,
                height=dp(32),
            )
        )

        self.description_field = MDTextField(
            hint_text="Describe the barrier so others can avoid it...",
            mode="outlined",
            multiline=True,
            size_hint_y=None,
            height=dp(120),
        )
        form.add_widget(self.description_field)

        # Error label
        self.error_label = MDLabel(
            text="",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.89, 0.25, 0.15, 1),
            size_hint_y=None,
            height=dp(24),
        )
        form.add_widget(self.error_label)

        # Submit row
        submit_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(12),
        )

        self.submit_spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5},
            opacity=0,
        )
        submit_row.add_widget(self.submit_spinner)

        self.submit_btn = MDButton(
            MDButtonText(text="Submit report"),
            style="filled",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.submit_report,
        )
        submit_row.add_widget(self.submit_btn)
        form.add_widget(submit_row)

        scroll.add_widget(form)
        root.add_widget(scroll)
        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Location label                                                      #
    # ------------------------------------------------------------------ #

    def _refresh_location_label(self):
        try:
            app = MDApp.get_running_app()
            map_screen = app.root.ids.screen_manager.get_screen("map")
            lat, lon   = map_screen.gps.get_location()
            self.location_label.text = f"{lat:.5f}, {lon:.5f}"
        except Exception:
            self.location_label.text = "Location unavailable"

    # ------------------------------------------------------------------ #
    #  Submit                                                              #
    # ------------------------------------------------------------------ #

    def submit_report(self, *args):
        if self._submitting:
            return

        # Validate barrier type selected
        selected = [k for k, cb in self.barrier_checks.items() if cb.active]
        if not selected:
            self._show_error("Please select at least one barrier type.")
            return

        description = self.description_field.text.strip()
        if not description:
            self._show_error("Please add a description.")
            return

        # Get GPS coords from map screen
        try:
            app        = MDApp.get_running_app()
            map_screen = app.root.ids.screen_manager.get_screen("map")
            lat, lon   = map_screen.gps.get_location()
        except Exception:
            self._show_error("Could not get your location. Try again.")
            return

        # Get logged-in user ID
        user_id = app.current_user.get("id")
        if not user_id:
            self._show_error("You must be logged in to submit a report.")
            return

        self._set_loading(True)
        self._clear_error()

        payload = {
            "lat":          lat,
            "lon":          lon,
            "barrier_type": selected[0],   # primary selection
            "description":  description,
            "user_id":      user_id,
        }

        threading.Thread(
            target=self._post_report,
            args=(payload,),
            daemon=True,
        ).start()

    def _post_report(self, payload):
        try:
            response = requests.post(
                f"{API_BASE}/report",
                json=payload,
                timeout=10,
            )

            if response.status_code == 201:
                Clock.schedule_once(lambda dt: self._on_success(), 0)
            elif response.status_code == 404:
                Clock.schedule_once(
                    lambda dt: self._on_error("User not found. Please log in again."), 0
                )
            elif response.status_code == 422:
                Clock.schedule_once(
                    lambda dt: self._on_error("Invalid data. Check your input."), 0
                )
            else:
                Clock.schedule_once(
                    lambda dt: self._on_error(
                        f"Server error ({response.status_code}). Try again."
                    ), 0
                )

        except requests.exceptions.ConnectionError:
            Clock.schedule_once(
                lambda dt: self._on_error(
                    "Cannot reach server. Check your internet connection."
                ), 0
            )
        except requests.exceptions.Timeout:
            Clock.schedule_once(
                lambda dt: self._on_error("Request timed out. Try again."), 0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._on_error(f"Unexpected error: {e}"), 0
            )

    def _on_success(self):
        self._set_loading(False)
        self._reset_form()

        MDSnackbar(
            MDSnackbarText(
                text="Report submitted — thank you!"
            ),
            duration=3,
        ).open()

        # Switch back to map after a short delay
        Clock.schedule_once(
            lambda dt: setattr(self.manager, "current", "map"), 2
        )

    def _on_error(self, message):
        self._set_loading(False)
        self._show_error(message)

    # ------------------------------------------------------------------ #
    #  UI helpers                                                          #
    # ------------------------------------------------------------------ #

    def _set_loading(self, loading):
        self._submitting           = loading
        self.submit_spinner.opacity = 1 if loading else 0
        self.submit_btn.disabled   = loading
        for child in self.submit_btn.children:
            if hasattr(child, "text"):
                child.text = "Submitting..." if loading else "Submit report"

    def _show_error(self, message):
        self.error_label.text = message

    def _clear_error(self):
        self.error_label.text = ""

    def _reset_form(self):
        for cb in self.barrier_checks.values():
            cb.active = False
        self.description_field.text = ""
        self._clear_error()