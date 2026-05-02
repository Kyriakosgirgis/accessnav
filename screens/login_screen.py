from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.divider import MDDivider
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = FloatLayout()

        # Green header band
        header = MDBoxLayout(
            orientation="vertical",
            md_bg_color=(0.11, 0.62, 0.46, 1),
            size_hint=(1, 0.32),
            pos_hint={"top": 0.93},
            padding=("24dp", "24dp", "24dp", "16dp"),
        )
        header.add_widget(
            MDLabel(
                text="AccessNav",
                font_style="Display",
                role="small",
                halign="left",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )
        header.add_widget(
            MDLabel(
                text="Accessible navigation for everyone",
                font_style="Body",
                role="medium",
                halign="left",
                theme_text_color="Custom",
                text_color=(0.8, 1, 0.92, 1),
            )
        )
        root.add_widget(header)

        # Scrollable form
        scroll = ScrollView(
            size_hint=(1, 0.61),
            pos_hint={"x": 0, "y": 0},
        )
        form_wrap = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            adaptive_height=True,
            padding=("24dp", "32dp", "24dp", "24dp"),
            spacing="16dp",
        )

        form_wrap.add_widget(
            MDLabel(
                text="Sign in",
                font_style="Headline",
                role="small",
                theme_text_color="Primary",
                size_hint_y=None,
                height="40dp",
            )
        )

        self.email_field = MDTextField(
            hint_text="Email address",
            mode="outlined",
            size_hint_y=None,
            height="56dp",
            input_type="mail",
        )
        form_wrap.add_widget(self.email_field)

        self.password_field = MDTextField(
            hint_text="Password",
            mode="outlined",
            password=True,
            size_hint_y=None,
            height="56dp",
        )
        form_wrap.add_widget(self.password_field)

        self.error_label = MDLabel(
            text="",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.89, 0.35, 0.19, 1),
            size_hint_y=None,
            height="24dp",
        )
        form_wrap.add_widget(self.error_label)

        login_btn = MDButton(
            MDButtonText(text="Sign in"),
            style="filled",
            size_hint=(1, None),
            height="52dp",
            on_release=self.do_login,
        )
        form_wrap.add_widget(login_btn)

        form_wrap.add_widget(MDDivider(size_hint_y=None, height="1dp"))

        register_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="40dp",
            spacing="4dp",
        )
        register_row.add_widget(
            MDLabel(
                text="Don't have an account?",
                font_style="Body",
                role="medium",
                theme_text_color="Secondary",
                halign="right",
            )
        )
        register_row.add_widget(
            MDButton(
                MDButtonText(text="Register"),
                style="text",
                on_release=self.go_to_register,
            )
        )
        form_wrap.add_widget(register_row)

        scroll.add_widget(form_wrap)
        root.add_widget(scroll)
        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def do_login(self, *args):
        email    = self.email_field.text.strip()
        password = self.password_field.text.strip()

        error = self._validate(email, password)
        if error:
            self.show_error(error)
            return

        self.clear_error()

        from services.auth_service import AuthService
        auth = AuthService()
        user = auth.login(email, password)

        if user:
            self._get_app().login(user)
        else:
            self.show_error("Incorrect email or password.")

    def go_to_register(self, *args):
        self.clear_error()
        self.manager.current = "register"

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def _validate(self, email, password):
        if not email:
            return "Email is required."
        if "@" not in email or "." not in email:
            return "Enter a valid email address."
        if not password:
            return "Password is required."
        if len(password) < 6:
            return "Password must be at least 6 characters."
        return None

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def show_error(self, message):
        self.error_label.text = message

    def clear_error(self):
        self.error_label.text = ""

    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()