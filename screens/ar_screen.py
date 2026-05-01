from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFabButton
from kivy.uix.floatlayout import FloatLayout


class ARScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = FloatLayout()

        # Camera placeholder background
        cam_bg = MDBoxLayout(md_bg_color=(0.08, 0.08, 0.10, 1))
        root.add_widget(cam_bg)

        # Camera label
        root.add_widget(
            MDLabel(
                text="[b]Camera feed[/b]\nLive AR overlay — Phase 3",
                markup=True,
                halign="center",
                theme_text_color="Custom",
                text_color=(0.6, 0.6, 0.6, 1),
            )
        )

        # AR arrow placeholder
        arrow_hint = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=("120dp", "120dp"),
            pos_hint={"center_x": 0.5, "center_y": 0.55},
            md_bg_color=(0.11, 0.62, 0.46, 0.15),
            radius=[60],
        )
        arrow_hint.add_widget(
            MDLabel(
                text="AR",
                font_style="Display",
                role="small",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.11, 0.62, 0.46, 1),
            )
        )
        root.add_widget(arrow_hint)

        # HUD distance card
        hud = MDBoxLayout(
            orientation="vertical",
            size_hint=(0.6, None),
            height="64dp",
            pos_hint={"center_x": 0.5, "y": 0.14},
            md_bg_color=(0, 0, 0, 0.6),
            radius=[12],
            padding="8dp",
        )
        hud.add_widget(
            MDLabel(
                text="Distance to destination",
                font_style="Label",
                role="small",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.8, 0.8, 0.8, 1),
            )
        )
        hud.add_widget(
            MDLabel(
                text="-- m  |  -- min",
                font_style="Title",
                role="small",
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )
        root.add_widget(hud)

        # Stop navigation FAB
        stop_btn = MDFabButton(
            icon="close",
            style="small",
            pos_hint={"center_x": 0.5, "y": 0.04},
            on_release=self.stop_navigation,
        )
        root.add_widget(stop_btn)

        self.add_widget(root)

    def stop_navigation(self, *args):
        self.manager.current = "map"
        print("[ARScreen] Navigation stopped")