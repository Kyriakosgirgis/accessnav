from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFabButton
from kivymd.uix.appbar import (
    MDTopAppBar,
    MDTopAppBarTitle,
    MDTopAppBarTrailingButtonContainer,
    MDActionTopAppBarButton,
)
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp


class MapScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    # ------------------------------------------------------------------ #
    #  Auth guard                                                          #
    # ------------------------------------------------------------------ #
    def on_enter(self, *args):
        app = self._get_app()
        if not app.is_logged_in():
            self.manager.current = "login"
            return
        print(f"[MapScreen] Welcome, {app.current_user['name']}")

    def _on_authenticated(self):
        """Called only when a valid session exists. Put map init logic here."""
        app = MDApp.get_running_app()
        print(f"[MapScreen] Logged in as {app.current_user['name']}")
        # Phase 3: start GPS, load POIs, etc.

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def build_ui(self):
        root = FloatLayout()

        map_placeholder = MDBoxLayout(
            orientation="vertical",
            md_bg_color=(0.88, 0.96, 0.93, 1),
        )
        map_placeholder.add_widget(
            MDLabel(
                text="[b]Map loads here[/b]\nMapView widget — Phase 3",
                markup=True,
                halign="center",
                theme_text_color="Custom",
                text_color=(0.06, 0.43, 0.27, 1),
            )
        )
        root.add_widget(map_placeholder)

        legend = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height="40dp",
            pos_hint={"x": 0, "y": 0.08},
            padding="12dp",
            spacing="16dp",
            md_bg_color=(1, 1, 1, 0.95),
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
                )
            )
            legend.add_widget(
                MDLabel(
                    text=label,
                    font_style="Label",
                    role="small",
                    theme_text_color="Secondary",
                )
            )
        root.add_widget(legend)

        fab = MDFabButton(
            icon="crosshairs-gps",
            pos_hint={"right": 0.95, "y": 0.12},
            on_release=self.on_locate,
        )
        root.add_widget(fab)

        toolbar = MDTopAppBar(
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
        root.add_widget(toolbar)

        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #


    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def on_locate(self, *args):
        print("[MapScreen] Locate me tapped — GPS coming in Phase 3")

    def do_logout(self, *args):
        MDApp.get_running_app().logout()