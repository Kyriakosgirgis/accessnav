from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.lang import Builder
from kivy.core.window import Window

from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.map_screen import MapScreen
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
                icon: 'camera'

            MDNavigationItemLabel:
                text: 'AR'

        MDNavigationItem:
            name: 'report'

            MDNavigationItemIcon:
                icon: 'flag-plus'

            MDNavigationItemLabel:
                text: 'Report'
"""


class AccessNavApp(MDApp):

    current_user = None

    def build(self):

        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"

        self.title = "AccessNav"

        self.session = SessionService()

        root = Builder.load_string(KV)

        sm = root.ids.screen_manager
        sm.transition = NoTransition()

        # -------------------------------------------------- #
        # Screens
        # -------------------------------------------------- #

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MapScreen(name="map"))

        # Lazy-load AR screen
        from kivymd.uix.screen import MDScreen

        class DeferredARScreen(MDScreen):

            loaded = False

            def on_enter(self_inner, *args):

                if self_inner.loaded:
                    return

                self_inner.loaded = True

                try:
                    print("[Main] Loading ARScreen...")

                    from screens.ar_screen import ARScreen

                    ar_screen = ARScreen(name="ar")

                    sm.add_widget(ar_screen)

                    sm.remove_widget(self_inner)

                    Clock.schedule_once(
                        lambda dt: setattr(sm, "current", "ar"),
                        0
                    )

                    print("[Main] ARScreen loaded")

                except Exception as e:
                    print(f"[Main] Failed to load ARScreen: {e}")

        from kivy.clock import Clock

        sm.add_widget(DeferredARScreen(name="ar"))

        sm.add_widget(ReportScreen(name="report"))

        # -------------------------------------------------- #
        # Session restore
        # -------------------------------------------------- #

        saved = self.session.load()

        if saved:

            self.current_user = saved

            sm.current = "map"

            self._show_nav(True, root)

        else:

            sm.current = "login"

            self._show_nav(False, root)

        return root

    # ------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------ #

    def login(self, user):

        self.current_user = user.to_dict()

        self.session.save(user)

        self._show_nav(True)

        self.root.ids.screen_manager.current = "map"

    def logout(self):

        self.current_user = None

        self.session.clear()

        self._show_nav(False)

        self.root.ids.screen_manager.current = "login"

    def is_logged_in(self):

        return self.current_user is not None

    # ------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------ #

    def switch_screen(self, nav_bar, item, item_icon, item_text):

        if not self.is_logged_in():
            return

        try:
            self.root.ids.screen_manager.current = item.name
        except Exception as e:
            print(f"[Main] Navigation error: {e}")

    # ------------------------------------------------------ #
    # Bottom nav visibility
    # ------------------------------------------------------ #

    def _show_nav(self, visible, root=None):

        nav = (root or self.root).ids.nav_bar

        nav.size_hint_y = None if visible else 0

        nav.height = "80dp" if visible else 0

        nav.opacity = 1 if visible else 0

        nav.disabled = not visible


if __name__ == "__main__":
    AccessNavApp().run()