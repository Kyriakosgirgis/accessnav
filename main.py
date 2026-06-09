from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.lang import Builder
from kivy.core.window import Window

from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.map_screen import MapScreen
from screens.ar_screen import ARScreen
from screens.report_screen import ReportScreen
from screens.settings_screen import SettingsScreen
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

        MDNavigationItem:
            name: 'settings'
            MDNavigationItemIcon:
                icon: 'cog-outline'
            MDNavigationItemLabel:
                text: 'Settings'
"""


class AccessNavApp(MDApp):
    current_user = None

    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style     = "Light"
        self.title                     = "AccessNav"
        self.session                   = SessionService()

        root = Builder.load_string(KV)

        sm = root.ids.screen_manager
        sm.transition = NoTransition()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(ARScreen(name="ar"))
        sm.add_widget(ReportScreen(name="report"))
        sm.add_widget(SettingsScreen(name="settings"))

        saved = self.session.load()
        if saved:
            self.current_user = saved
            sm.current = "map"
            self._set_nav(root, visible=True)
        else:
            sm.current = "login"
            self._set_nav(root, visible=False)

        return root

    # ------------------------------------------------------------------ #
    #  Session                                                             #
    # ------------------------------------------------------------------ #

    def login(self, user):
        self.current_user = user.to_dict()
        self.session.save(user)
        self._set_nav(self.root, visible=True)
        self.root.ids.screen_manager.current = "map"

    def logout(self):
        self.current_user = None
        self.session.clear()
        self._set_nav(self.root, visible=False)
        self.root.ids.screen_manager.current = "login"

    def is_logged_in(self):
        return self.current_user is not None

    # ------------------------------------------------------------------ #
    #  Navigation                                                          #
    # ------------------------------------------------------------------ #

    def switch_screen(self, *args):
        """Handle navigation bar callbacks with flexible signatures.

        Prefer an argument object with a `name` attribute (the
        navigation item). If only a string is provided (often the
        display label like "Settings"), try to resolve it to a known
        screen name in the ScreenManager in a case-insensitive way.
        """
        if not self.is_logged_in():
            return

        sm = self.root.ids.screen_manager

        # Prefer an object with a `name` attribute.
        item_name = None
        for a in reversed(args):
            if hasattr(a, "name"):
                item_name = getattr(a, "name")
                break

        # Fallback to a string argument (e.g. a label text) if no
        # `name`-bearing object was found.
        if item_name is None:
            for a in reversed(args):
                if isinstance(a, str):
                    item_name = a
                    break

        if not item_name:
            return

        # If the item_name doesn't exactly match any screen, try
        # case-insensitive matching against available screen names.
        available = [s.name for s in sm.screens]
        if item_name in available:
            target = item_name
        else:
            lowered = item_name.strip().lower()
            target = None
            for name in available:
                if name.lower() == lowered or lowered == name.lower():
                    target = name
                    break
                # also handle display labels like 'Settings' -> 'settings'
                if lowered == name.lower():
                    target = name
                    break

        if target:
            sm.current = target

    # ------------------------------------------------------------------ #
    #  Nav bar visibility                                                  #
    # ------------------------------------------------------------------ #

    def _set_nav(self, root, visible):
        nav          = root.ids.nav_bar
        nav.opacity  = 1 if visible else 0
        nav.disabled = not visible
        nav.size_hint_y = None if visible else 0
        nav.height      = "80dp" if visible else "0dp"


if __name__ == "__main__":
    AccessNavApp().run()