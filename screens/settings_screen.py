from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.clock import Clock
from kivymd.app import MDApp


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def on_enter(self, *args):
        app = MDApp.get_running_app()
        if not app.is_logged_in():
            Clock.schedule_once(
                lambda dt: setattr(self.manager, "current", "login"), 0
            )

    def build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="24dp")
        root.add_widget(
            MDLabel(
                text="Settings — Phase 7",
                halign="center",
                theme_text_color="Secondary",
            )
        )
        self.add_widget(root)