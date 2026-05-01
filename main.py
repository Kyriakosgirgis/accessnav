from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.lang import Builder
from kivy.core.window import Window

from screens.map_screen import MapScreen
from screens.ar_screen import ARScreen
from screens.report_screen import ReportScreen

Window.size = (390, 844)

KV = """
MDBoxLayout:
    orientation: 'vertical'
    md_bg_color: app.theme_cls.backgroundColor

    ScreenManager:
        id: screen_manager

    MDNavigationBar:
        id: nav_bar
        on_switch_tabs: app.switch_screen(*args)

        MDNavigationItem:
            name: 'map'
            MDNavigationItemIcon:
                icon: 'map-marker-radius'
            MDNavigationItemLabel:
                text: 'Map'

        MDNavigationItem:
            name: 'ar'
            MDNavigationItemIcon:
                icon: 'navigation'
            MDNavigationItemLabel:
                text: 'Navigate'

        MDNavigationItem:
            name: 'report'
            MDNavigationItemIcon:
                icon: 'flag-plus'
            MDNavigationItemLabel:
                text: 'Report'
"""


class AccessNavApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"
        self.title = "AccessNav"

        root = Builder.load_string(KV)

        sm = root.ids.screen_manager
        sm.transition = NoTransition()
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(ARScreen(name="ar"))
        sm.add_widget(ReportScreen(name="report"))

        return root

    def switch_screen(self, nav_bar, item, item_name):
        self.root.ids.screen_manager.current = item_name


if __name__ == "__main__":
    AccessNavApp().run()