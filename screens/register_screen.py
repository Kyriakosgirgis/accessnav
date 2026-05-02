from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.divider import MDDivider
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout


class RegisterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = FloatLayout()

        # Green header band
        header = MDBoxLayout(
            orientation="vertical",
            md_bg_color=(0.11, 0.62, 0.46, 1),
            size_hint=(1, 0.28),
            pos_hint={"top": 0.93},
            padding=("24dp", "24dp", "24dp", "16dp"),
        )
        header.add_widget(
            MDLabel(
                text="Create account",
                font_style="Display",
                role="small",
                halign="left",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )
        header.add_widget(
            MDLabel(
                text="Join the AccessNav community",
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
            size_hint=(1, 0.65),
            pos_hint={"x": 0, "y": 0},
        )
        form_wrap = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            adaptive_height=True,
            padding=("24dp", "24dp", "24dp", "24dp"),
            spacing="14dp",
        )

        form_wrap.add_widget(
            MDLabel(
                text="Your details",
                font_style="Headline",
                role="small",
                theme_text_color="Primary",
                size_hint_y=None,
                height="40dp",
            )
        )

        self.name_field = MDTextField(
            hint_text="Full name",
            mode="outlined",
            size_hint_y=None,
            height="56dp",
        )
        form_wrap.add_widget(self.name_field)

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

        self.confirm_field = MDTextField(
            hint_text="Confirm password",
            mode="outlined",
            password=True,
            size_hint_y=None,
            height="56dp",
        )
        form_wrap.add_widget(self.confirm_field)

        self.strength_label = MDLabel(
            text="Password must be at least 6 characters.",
            font_style="Label",
            role="small",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="20dp",
        )
        form_wrap.add_widget(self.strength_label)

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

        register_btn = MDButton(
            MDButtonText(text="Create account"),
            style="filled",
            size_hint=(1, None),
            height="52dp",
            on_release=self.do_register,
        )
        form_wrap.add_widget(register_btn)

        form_wrap.add_widget(MDDivider(size_hint_y=None, height="1dp"))

        login_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="40dp",
            spacing="4dp",
        )
        login_row.add_widget(
            MDLabel(
                text="Already have an account?",
                font_style="Body",
                role="medium",
                theme_text_color="Secondary",
                halign="right",
            )
        )
        login_row.add_widget(
            MDButton(
                MDButtonText(text="Sign in"),
                style="text",
                on_release=self.go_to_login,
            )
        )
        form_wrap.add_widget(login_row)

        scroll.add_widget(form_wrap)
        root.add_widget(scroll)
        self.add_widget(root)

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def do_register(self, *args):
        name     = self.name_field.text.strip()
        email    = self.email_field.text.strip()
        password = self.password_field.text.strip()
        confirm  = self.confirm_field.text.strip()

        error = self._validate(name, email, password, confirm)
        if error:
            self.show_error(error)
            return

        self.clear_error()

        from services.auth_service import AuthService
        auth = AuthService()
        success, message = auth.register(name, email, password)

        if success:
            user = auth.login(email, password)
            self._get_app().login(user)
        else:
            self.show_error(message)

    def go_to_login(self, *args):
        self.clear_error()
        self.manager.current = "login"

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def _validate(self, name, email, password, confirm):
        if not name:
            return "Full name is required."
        if len(name) < 2:
            return "Enter your full name."
        if not email:
            return "Email is required."
        if "@" not in email or "." not in email:
            return "Enter a valid email address."
        if not password:
            return "Password is required."
        if len(password) < 6:
            return "Password must be at least 6 characters."
        if password != confirm:
            return "Passwords do not match."
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