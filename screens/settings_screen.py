import json
import os

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.scrollview import ScrollView

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.slider import MDSlider, MDSliderHandle
from kivymd.uix.divider import MDDivider
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.appbar import (
    MDTopAppBar,
    MDTopAppBarTitle,
    MDTopAppBarTrailingButtonContainer,
    MDActionTopAppBarButton,
)
from kivymd.app import MDApp

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "settings.json"
)

DEFAULTS = {
    "high_contrast":    False,
    "font_size":        1,      # 0=Small  1=Medium  2=Large
    "voice_navigation": True,
    "haptic_feedback":  True,
}

FONT_LABELS  = ["Small", "Medium", "Large"]

FONT_SIZES = {
    0: 12,   # Small
    1: 15,   # Medium (default)
    2: 18,   # Large
}


# ------------------------------------------------------------------ #
#  Settings persistence                                                #
# ------------------------------------------------------------------ #

def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception:
        return dict(DEFAULTS)


def save_settings(data: dict):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Settings] Could not save: {e}")


# ------------------------------------------------------------------ #
#  Live font resize — walks the entire widget tree                     #
# ------------------------------------------------------------------ #

def apply_font_size_to_tree(root_widget, font_sp: int):
    """
    Recursively walk the widget tree and update font_size on every
    Label and MDLabel so the change is visible immediately.
    """
    from kivy.uix.label import Label as KivyLabel

    for widget in root_widget.walk():
        try:
            if isinstance(widget, KivyLabel):
                widget.font_size = sp(font_sp)
        except Exception:
            pass


# ------------------------------------------------------------------ #
#  SettingsScreen                                                      #
# ------------------------------------------------------------------ #

class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._settings = load_settings()
        self._loading  = False
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
        self._apply_to_ui()

    # ------------------------------------------------------------------ #
    #  Build UI                                                            #
    # ------------------------------------------------------------------ #

    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        # ── Toolbar ───────────────────────────────────────────── #
        root.add_widget(
            MDTopAppBar(
                MDTopAppBarTitle(text="Settings"),
                MDTopAppBarTrailingButtonContainer(
                    MDActionTopAppBarButton(
                        icon="logout",
                        on_release=self._do_logout,
                    )
                ),
                type="small",
                size_hint_y=None,
                height="56dp",
            )
        )

        # ── Scrollable body ───────────────────────────────────── #
        scroll = ScrollView()
        body   = MDBoxLayout(
            orientation="vertical",
            padding=(dp(20), dp(8), dp(20), dp(32)),
            spacing=dp(4),
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── Account section ───────────────────────────────────── #
        body.add_widget(self._section_header("Account"))

        self.account_label = MDLabel(
            text="Not logged in",
            font_style="Label",
            role="large",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(40),
        )
        body.add_widget(self.account_label)
        body.add_widget(MDDivider(size_hint_y=None, height="0.5dp"))

        # ── Accessibility section ─────────────────────────────── #
        body.add_widget(self._section_header("Accessibility"))

        # High contrast toggle
        self.contrast_switch = MDSwitch()
        self.contrast_switch.bind(active=self._on_contrast)
        body.add_widget(
            self._row(
                icon="contrast-circle",
                title="High contrast",
                subtitle="Increases colour contrast for better visibility",
                control=self.contrast_switch,
            )
        )
        body.add_widget(MDDivider(size_hint_y=None, height="0.5dp"))

        # Font size slider
        body.add_widget(
            self._row(
                icon="format-size",
                title="Text size",
                subtitle="Changes the size of text throughout the app",
                control=None,
            )
        )

        # Current size preview label — updates live
        self.font_preview = MDLabel(
            text=f"Preview text — {FONT_LABELS[self._settings['font_size']]}",
            theme_text_color="Primary",
            halign="center",
            size_hint_y=None,
            height=dp(32),
            font_size=sp(FONT_SIZES[self._settings["font_size"]]),
        )
        body.add_widget(self.font_preview)

        slider_col = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(60),
            padding=(dp(8), 0, dp(8), 0),
        )
        self.font_slider = MDSlider(
            MDSliderHandle(),
            min=0,
            max=2,
            step=1,
            value=self._settings["font_size"],
        )
        self.font_slider.bind(value=self._on_font_size)
        slider_col.add_widget(self.font_slider)

        labels_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(18),
            padding=(dp(8), 0, dp(8), 0),
        )
        for lbl in FONT_LABELS:
            labels_row.add_widget(
                MDLabel(
                    text=lbl,
                    font_style="Label",
                    role="small",
                    theme_text_color="Secondary",
                    halign="center",
                )
            )
        slider_col.add_widget(labels_row)
        body.add_widget(slider_col)
        body.add_widget(MDDivider(size_hint_y=None, height="0.5dp"))

        # ── Navigation section ────────────────────────────────── #
        body.add_widget(self._section_header("Navigation"))

        # Voice navigation toggle
        self.voice_switch = MDSwitch()
        self.voice_switch.bind(active=self._on_voice)
        body.add_widget(
            self._row(
                icon="volume-high",
                title="Voice navigation",
                subtitle="Announce turns and distance aloud",
                control=self.voice_switch,
            )
        )
        body.add_widget(MDDivider(size_hint_y=None, height="0.5dp"))

        # Haptic feedback toggle
        self.haptic_switch = MDSwitch()
        self.haptic_switch.bind(active=self._on_haptic)
        body.add_widget(
            self._row(
                icon="vibrate",
                title="Haptic feedback",
                subtitle="Vibrate at waypoints and obstacle warnings",
                control=self.haptic_switch,
            )
        )

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Row helpers                                                         #
    # ------------------------------------------------------------------ #

    def _section_header(self, text):
        return MDLabel(
            text=text.upper(),
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.11, 0.62, 0.46, 1),
            size_hint_y=None,
            height=dp(38),
        )

    def _row(self, icon, title, subtitle, control):
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64) if subtitle else dp(48),
            spacing=dp(12),
            padding=(0, dp(4), 0, dp(4)),
        )
        row.add_widget(
            MDIconButton(
                icon=icon,
                theme_icon_color="Custom",
                icon_color=(0.11, 0.62, 0.46, 1),
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                pos_hint={"center_y": 0.5},
            )
        )
        text_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=1,
            pos_hint={"center_y": 0.5},
        )
        text_col.add_widget(
            MDLabel(
                text=title,
                font_style="Label",
                role="large",
                theme_text_color="Primary",
                bold=True,
                size_hint_y=None,
                height=dp(22),
            )
        )
        if subtitle:
            text_col.add_widget(
                MDLabel(
                    text=subtitle,
                    font_style="Label",
                    role="small",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height=dp(18),
                )
            )
        row.add_widget(text_col)
        if control:
            control.pos_hint = {"center_y": 0.5}
            row.add_widget(control)
        return row

    # ------------------------------------------------------------------ #
    #  Populate UI from saved settings                                     #
    # ------------------------------------------------------------------ #

    def _apply_to_ui(self):
        self._loading = True

        app = MDApp.get_running_app()
        if app.current_user:
            self.account_label.text = (
                f"{app.current_user.get('name', 'User')}  ·  "
                f"{app.current_user.get('email', '')}"
            )

        self.contrast_switch.active = self._settings["high_contrast"]
        self.font_slider.value      = self._settings["font_size"]
        self.voice_switch.active    = self._settings["voice_navigation"]
        self.haptic_switch.active   = self._settings["haptic_feedback"]

        self._loading = False

    # ------------------------------------------------------------------ #
    #  Toggle callbacks                                                    #
    # ------------------------------------------------------------------ #

    def _on_contrast(self, switch, value):
        if self._loading:
            return
        self._settings["high_contrast"] = value
        self._save()
        self._apply_contrast(value)

    def _on_font_size(self, slider, value):
        if self._loading:
            return
        idx      = int(round(value))
        font_sp  = FONT_SIZES[idx]
        self._settings["font_size"] = idx
        self._save()

        # Update the preview label immediately
        self.font_preview.font_size = sp(font_sp)
        self.font_preview.text      = (
            f"Preview text — {FONT_LABELS[idx]}"
        )

        # Walk the ENTIRE app widget tree and resize every label live
        try:
            app = MDApp.get_running_app()
            apply_font_size_to_tree(app.root, font_sp)
        except Exception as e:
            print(f"[Settings] Font resize error: {e}")

        MDSnackbar(
            MDSnackbarText(text=f"Text size: {FONT_LABELS[idx]}"),
            duration=1.2,
        ).open()

    def _on_voice(self, switch, value):
        if self._loading:
            return
        self._settings["voice_navigation"] = value
        self._save()
        MDSnackbar(
            MDSnackbarText(
                text=f"Voice navigation {'on' if value else 'off'}"
            ),
            duration=1.5,
        ).open()

    def _on_haptic(self, switch, value):
        if self._loading:
            return
        self._settings["haptic_feedback"] = value
        self._save()
        if value:
            self._vibrate()

    # ------------------------------------------------------------------ #
    #  Apply to running app                                                #
    # ------------------------------------------------------------------ #

    def _apply_contrast(self, enabled):
        app = MDApp.get_running_app()
        if enabled:
            app.theme_cls.theme_style     = "Dark"
            app.theme_cls.primary_palette = "Teal"
        else:
            app.theme_cls.theme_style     = "Light"
            app.theme_cls.primary_palette = "Green"

        MDSnackbar(
            MDSnackbarText(
                text=f"High contrast {'enabled' if enabled else 'disabled'}"
            ),
            duration=1.5,
        ).open()

    def _vibrate(self):
        try:
            from plyer import vibrator
            vibrator.vibrate(0.1)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _save(self):
        save_settings(self._settings)

    def _do_logout(self, *args):
        MDApp.get_running_app().logout()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get(key: str):
        """
        Read any setting from anywhere in the app:
            SettingsScreen.get("voice_navigation")  →  True
            SettingsScreen.get("haptic_feedback")   →  True
            SettingsScreen.get("font_size")         →  1
        """
        return load_settings().get(key, DEFAULTS.get(key))