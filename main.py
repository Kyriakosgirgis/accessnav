from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.lang import Builder
from kivy.core.window import Window

from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.map_screen import MapScreen
from screens.ar_screen import ARScreen
from screens.report_screen import ReportScreen
from services.session_service import SessionService

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
    current_user = None  # Dict: {id, name, email} — set after login

    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"
        self.title = "AccessNav"
        self.session = SessionService()

        root = Builder.load_string(KV)

        sm = root.ids.screen_manager
        sm.transition = NoTransition()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(ARScreen(name="ar"))
        sm.add_widget(ReportScreen(name="report"))

        # Restore session if one exists, otherwise go to login
        saved = self.session.load()
        if saved:
            self.current_user = saved
            sm.current = "map"
            self._show_nav(True, root)
        else:
            sm.current = "login"
            self._show_nav(False, root)

        return root

    def login(self, user) -> None:
        """Call this from LoginScreen and RegisterScreen after auth succeeds."""
        self.current_user = user.to_dict()
        self.session.save(user)
        self._show_nav(True)
        self.root.ids.screen_manager.current = "map"

    def logout(self) -> None:
        """Call this from anywhere to log the user out."""
        self.current_user = None
        self.session.clear()
        self._show_nav(False)
        self.root.ids.screen_manager.current = "login"

    def is_logged_in(self) -> bool:
        return self.current_user is not None

    def switch_screen(self, nav_bar, item, item_name) -> None:
        if self.is_logged_in():
            self.root.ids.screen_manager.current = item_name

    def _show_nav(self, visible: bool, root=None) -> None:
        """Show or hide the bottom nav bar based on login state."""
        nav = (root or self.root).ids.nav_bar
        nav.size_hint_y = None if visible else 0
        nav.opacity = 1 if visible else 0
        nav.disabled = not visible


if __name__ == "__main__":
    AccessNavApp().run()