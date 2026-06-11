from kivy.metrics import dp

from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton


def _score_to_color(score):
    if score >= 0.75:
        return (0.11, 0.72, 0.46, 1)
    elif score >= 0.45:
        return (0.95, 0.65, 0.10, 1)
    return (0.89, 0.25, 0.15, 1)


def _score_to_label(score):
    if score >= 0.75:
        return "Excellent"
    elif score >= 0.45:
        return "Moderate"
    return "Challenging"


class RouteInfoCard(MDCard):

    def __init__(self, on_close=None, on_expand=None, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(360), dp(170)),
            padding=dp(16),
            spacing=dp(12),
            radius=[dp(24)],
            opacity=0,
            **kwargs
        )

        self.on_close_callback = on_close
        self.on_expand_callback = on_expand

        self._build_ui()

    def _build_ui(self):

        # Header
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
        )

        title = MDLabel(
            text="Accessible Route",
            bold=True,
            font_size="20sp",
        )

        close_btn = MDIconButton(
            icon="close"
        )
        close_btn.bind(on_release=self._on_close_tap)

        header.add_widget(title)
        header.add_widget(close_btn)

        self.add_widget(header)

        # Main content row
        content_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(12),
        )

        # Left side
        left_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.5,
        )

        self.eta_label = MDLabel(
            text="0 min",
            bold=True,
            font_size="30sp",
            size_hint_y=None,
            height=dp(36),
        )

        self.distance_label = MDLabel(
            text="0 m",
            theme_text_color="Secondary",
            font_size="16sp",
            size_hint_y=None,
            height=dp(24),
        )

        left_col.add_widget(self.eta_label)
        left_col.add_widget(self.distance_label)

        # Right side
        right_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.5,
        )

        right_col.add_widget(
            MDLabel(
                text="Accessibility",
                halign="center",
                size_hint_y=None,
                height=dp(24),
            )
        )

        self.rating_label = MDLabel(
            text="Excellent",
            bold=True,
            halign="center",
            font_size="20sp",
            size_hint_y=None,
            height=dp(30),
        )

        right_col.add_widget(self.rating_label)

        content_row.add_widget(left_col)
        content_row.add_widget(right_col)

        self.add_widget(content_row)

        # Spacer
        self.add_widget(
            MDBoxLayout(
                size_hint_y=1
            )
        )

        # AR Button
        self.ar_button = MDButton(
            MDButtonText(
                text="Start AR Navigation"
            ),
            style="filled",
            size_hint=(1, None),
            height=dp(52),
        )

        self.ar_button.bind(
            on_release=self._on_ar_tap
        )

        self.add_widget(self.ar_button)

    # ----------------------------------------------------
    # Public API
    # ----------------------------------------------------

    def set_route_info(
        self,
        distance_m,
        eta_minutes,
        score,
        barrier_count=0,
    ):

        # Distance
        if distance_m >= 1000:
            self.distance_label.text = (
                f"{distance_m / 1000:.1f} km"
            )
        else:
            self.distance_label.text = (
                f"{distance_m:.0f} m"
            )

        # ETA
        if eta_minutes < 60:
            self.eta_label.text = (
                f"{int(round(eta_minutes))} min"
            )
        else:
            hours = int(eta_minutes // 60)
            mins = int(eta_minutes % 60)

            self.eta_label.text = (
                f"{hours}h {mins}m"
            )

        # Accessibility
        rating = _score_to_label(score)

        self.rating_label.text = rating
        self.rating_label.text_color = (
            _score_to_color(score)
        )

    # ----------------------------------------------------
    # Visibility
    # ----------------------------------------------------

    def show(self):
        self.opacity = 1
        self.height = dp(170)

    def hide(self):
        self.opacity = 0
        self.height = 0

    # ----------------------------------------------------
    # Events
    # ----------------------------------------------------

    def _on_close_tap(self, *args):

        self.hide()

        if self.on_close_callback:
            self.on_close_callback()

    def _on_ar_tap(self, *args):

        if self.on_expand_callback:
            self.on_expand_callback()