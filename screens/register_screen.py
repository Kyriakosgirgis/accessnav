from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldHintText,
    MDTextFieldHelperText,
    MDTextFieldLeadingIcon,
    MDTextFieldTrailingIcon,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.divider import MDDivider
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout


class RegisterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password_visible = False
        self.confirm_visible = False
        self.build_ui()

    def build_ui(self):
        root = FloatLayout()

        # ── Green header ──────────────────────────────────────── #
        header = MDBoxLayout(
            orientation="vertical",
            md_bg_color=(0.11, 0.62, 0.46, 1),
            size_hint=(1, 0.26),
            pos_hint={"top": 1},
            padding=("24dp", "48dp", "24dp", "16dp"),
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

        # ── Scrollable form ───────────────────────────────────── #
        scroll = ScrollView(
            size_hint=(1, 0.77),
            pos_hint={"x": 0, "y": 0},
        )
        form = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            adaptive_height=True,
            padding=("24dp", "20dp", "24dp", "32dp"),
            spacing="18dp",
        )
        form.add_widget(
            MDLabel(
                text="Your details",
                font_style="Headline",
                role="small",
                theme_text_color="Primary",
                size_hint_y=None,
                height="40dp",
            )
        )

        # ── Full Name ────────────────────────────────────────── #

        self.name_field = MDTextField(
            MDTextFieldLeadingIcon(icon="account-outline"),
            MDTextFieldHintText(text="Full name"),
            MDTextFieldHelperText(
                text="Enter your first and last name",
                mode="on_focus",
            ),
            mode="outlined",
            size_hint_y=None,
            height="64dp",
        )
        form.add_widget(self.name_field)

        # ── Email ────────────────────────────────────────────── #

        self.email_field = MDTextField(
            MDTextFieldLeadingIcon(icon="email-outline"),
            MDTextFieldHintText(text="Email address"),
            MDTextFieldHelperText(
                text="e.g. name@example.com",
                mode="on_focus",
            ),
            mode="outlined",
            size_hint_y=None,
            height="64dp",
            input_type="mail",
        )
        form.add_widget(self.email_field)

        # ── Password ───────────────────────────────────────── #

        password_container = FloatLayout(
            size_hint_y=None,
            height="64dp",
        )

        self.password_field = MDTextField(
            MDTextFieldLeadingIcon(icon="lock-outline"),
            MDTextFieldHintText(text="Password"),
            MDTextFieldHelperText(
                text="At least 6 characters",
                mode="on_focus",
            ),
            mode="outlined",
            password=True,
            multiline=False,
            size_hint=(1, None),
            height="64dp",
            pos_hint={"x": 0, "center_y": 0.5},
        )

        self.password_eye = MDIconButton(
            icon="eye-off",
            pos_hint={"right": 0.995, "center_y": 0.5},
            on_release=self.toggle_password,
        )

        password_container.add_widget(self.password_field)
        password_container.add_widget(self.password_eye)

        form.add_widget(password_container)

        # ── Confirm Password ───────────────────────────────── #

        confirm_container = FloatLayout(
            size_hint_y=None,
            height="64dp",
        )

        self.confirm_field = MDTextField(
            MDTextFieldLeadingIcon(icon="lock-check-outline"),
            MDTextFieldHintText(text="Confirm password"),
            MDTextFieldHelperText(
                text="Re-enter your password",
                mode="on_focus",
            ),
            mode="outlined",
            password=True,
            multiline=False,
            size_hint=(1, None),
            height="64dp",
            pos_hint={"x": 0, "center_y": 0.5},
        )

        self.confirm_eye = MDIconButton(
            icon="eye-off",
            pos_hint={"right": 0.995, "center_y": 0.5},
            on_release=self.toggle_confirm,
        )

        confirm_container.add_widget(self.confirm_field)
        confirm_container.add_widget(self.confirm_eye)

        form.add_widget(confirm_container)

        # Error label
        self.error_label = MDLabel(
            text="",
            font_style="Label",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.89, 0.35, 0.19, 1),
            size_hint_y=None,
            height="24dp",
        )
        form.add_widget(self.error_label)

        # Register button
        form.add_widget(
            MDButton(
                MDButtonText(text="Create account"),
                style="filled",
                size_hint=(1, None),
                height="52dp",
                on_release=self.do_register,
            )
        )

        form.add_widget(MDDivider(size_hint_y=None, height="1dp"))

        # Back to login row
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
        form.add_widget(login_row)

        scroll.add_widget(form)
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
        auth    = AuthService()
        success, message = auth.register(name, email, password)

        if success:
            user = auth.login(email, password)
            self._get_app().login(user)
        else:
            self.show_error(message)

    def go_to_login(self, *args):
        self.clear_error()
        self.manager.current = "login"

    def toggle_password(self, *args):
        self.password_visible = not self.password_visible

        self.password_field.password = not self.password_visible

        self.password_eye.icon = (
            "eye"
            if self.password_visible
            else "eye-off"
        )

    def toggle_confirm(self, *args):
        self.confirm_visible = not self.confirm_visible

        self.confirm_field.password = not self.confirm_visible

        self.confirm_eye.icon = (
            "eye"
            if self.confirm_visible
            else "eye-off"
        )

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def _validate(self, name, email, password, confirm):
        if not name:
            return "Full name is required."
        if len(name) < 2:
            return "Enter your full name."
        if not email:
            return "Email address is required."
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