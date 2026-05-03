from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.appbar import MDTopAppBar, MDTopAppBarTitle
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivymd.app import MDApp


class ReportScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.barrier_checks = {}
        self.build_ui()

    # ------------------------------------------------------------------ #
    #  Auth guard                                                          #
    # ------------------------------------------------------------------ #
    def on_enter(self, *args):
        app = MDApp.get_running_app()
        if not app.is_logged_in():
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self.manager, "current", "login"), 0)
            return
        self._on_authenticated()

    def _on_authenticated(self):
        print("[ReportScreen] Auth OK — ready to accept reports")

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        root.add_widget(
            MDTopAppBar(
                MDTopAppBarTitle(text="Report a Barrier"),
                type="small",
                size_hint_y=None,
                height="56dp",
            )
        )

        scroll = ScrollView()
        form = MDBoxLayout(
            orientation="vertical",
            padding="24dp",
            spacing="16dp",
            size_hint_y=None,
            adaptive_height=True,
        )

        form.add_widget(
            MDLabel(
                text="Your current location will be attached automatically.",
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="28dp",
            )
        )

        form.add_widget(
            MDLabel(
                text="Barrier type",
                font_style="Label",
                role="large",
                theme_text_color="Primary",
                size_hint_y=None,
                height="32dp",
            )
        )

        for key, label in [
            ("broken_elevator", "Broken elevator"),
            ("missing_ramp",    "Missing ramp"),
            ("blocked_path",    "Blocked accessible path"),
            ("steep_slope",     "Steep slope"),
            ("other",           "Other"),
        ]:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="44dp",
                spacing="12dp",
            )
            cb = MDCheckbox(
                size_hint=(None, None),
                size=("32dp", "32dp"),
                pos_hint={"center_y": 0.5},
            )
            self.barrier_checks[key] = cb
            row.add_widget(cb)
            row.add_widget(MDLabel(text=label, theme_text_color="Primary"))
            form.add_widget(row)

        self.description_field = MDTextField(
            hint_text="Describe the barrier...",
            mode="outlined",
            multiline=True,
            size_hint_y=None,
            height="120dp",
        )
        form.add_widget(self.description_field)

        form.add_widget(
            MDButton(
                MDButtonText(text="Submit Report"),
                style="filled",
                size_hint=(1, None),
                height="48dp",
                on_release=self.submit_report,
            )
        )

        scroll.add_widget(form)
        root.add_widget(scroll)
        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def submit_report(self, *args):
        app = MDApp.get_running_app()
        selected = [k for k, cb in self.barrier_checks.items() if cb.active]
        desc = self.description_field.text.strip()

        if not selected:
            print("[ReportScreen] No barrier type selected")
            return

        print(
            f"[ReportScreen] Submitting — "
            f"user={app.current_user['id']}, "
            f"types={selected}, "
            f"desc='{desc}'"
        )
        # Phase 6: POST to FastAPI backend