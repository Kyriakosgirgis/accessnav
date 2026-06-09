"""
Enhanced route information card component with accessibility scoring,
warnings, and detailed route metrics.
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.progressindicator import MDLinearProgressIndicator


def _score_to_color(score):
    """Convert accessibility score (0–1) to RGB tuple."""
    if score >= 0.75:
        return (0.11, 0.72, 0.46, 1)      # green
    elif score >= 0.45:
        return (0.95, 0.65, 0.10, 1)      # amber
    else:
        return (0.89, 0.25, 0.15, 1)      # red


def _score_to_label(score):
    """Convert score to human-readable label."""
    if score >= 0.75:
        return "Good"
    elif score >= 0.45:
        return "Moderate"
    else:
        return "Challenging"


class RouteInfoCard(MDCard):
    """
    Enhanced route information display with:
    - Distance and ETA
    - Accessibility score with color bar
    - Difficulty level
    - Barrier count (if available)
    - Expandable for details
    """

    def __init__(self, on_close=None, on_expand=None, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(300), dp(140)),
            md_bg_color=(1, 1, 1, 0.98),
            radius=[dp(12)],
            padding=(dp(14), dp(10)),
            spacing=dp(8),
            elevation=6,
            opacity=0,
            height=0,
            **kwargs
        )
        self.on_close_callback = on_close
        self.on_expand_callback = on_expand
        self._expanded = False
        self._route_data = {}
        
        self._build_ui()

    def _build_ui(self):
        """Build the card UI structure."""
        
        # ── Header row (title + buttons) ──
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(4),
        )
        
        self.route_title = MDLabel(
            text="Fastest Accessible Route",
            font_style="Label",
            role="small",
            bold=True,
            size_hint_x=1,
            halign="left",
            theme_text_color="Primary",
        )
        header.add_widget(self.route_title)
        
        # AR button
        ar_btn = MDIconButton(
            icon="camera",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5},
            icon_size="20sp",
        )
        ar_btn.bind(on_release=self._on_ar_tap)
        header.add_widget(ar_btn)
        
        # Close button
        close_btn = MDIconButton(
            icon="close",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5},
            icon_size="20sp",
        )
        close_btn.bind(on_release=self._on_close_tap)
        header.add_widget(close_btn)
        
        self.add_widget(header)
        
        # ── Primary metrics row (distance | ETA | difficulty) ──
        metrics_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            spacing=dp(8),
        )
        
        # Distance
        dist_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.35,
            spacing=dp(2),
        )
        dist_col.add_widget(
            MDLabel(
                text="Distance",
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(12),
            )
        )
        self.distance_label = MDLabel(
            text="0.0 km",
            font_style="Label",
            role="large",
            theme_text_color="Primary",
            bold=True,
            size_hint_y=None,
            height=dp(20),
        )
        dist_col.add_widget(self.distance_label)
        metrics_row.add_widget(dist_col)
        
        # ETA
        eta_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.35,
            spacing=dp(2),
        )
        eta_col.add_widget(
            MDLabel(
                text="ETA",
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(12),
            )
        )
        self.eta_label = MDLabel(
            text="0 min",
            font_style="Label",
            role="large",
            theme_text_color="Primary",
            bold=True,
            size_hint_y=None,
            height=dp(20),
        )
        eta_col.add_widget(self.eta_label)
        metrics_row.add_widget(eta_col)
        
        # Difficulty
        diff_col = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.30,
            spacing=dp(2),
        )
        diff_col.add_widget(
            MDLabel(
                text="Difficulty",
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(12),
            )
        )
        self.difficulty_label = MDLabel(
            text="Good",
            font_style="Label",
            role="large",
            theme_text_color="Custom",
            text_color=(0.11, 0.72, 0.46, 1),
            bold=True,
            size_hint_y=None,
            height=dp(20),
        )
        diff_col.add_widget(self.difficulty_label)
        metrics_row.add_widget(diff_col)
        
        self.add_widget(metrics_row)
        
        # ── Accessibility score bar ──
        score_section = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(4),
        )
        
        score_label_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(16),
        )
        score_label_row.add_widget(
            MDLabel(
                text="Accessibility Score",
                font_style="Label",
                role="small",
                theme_text_color="Secondary",
                size_hint_x=1,
            )
        )
        self.score_percent_label = MDLabel(
            text="85%",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.11, 0.72, 0.46, 1),
            bold=True,
            size_hint_x=None,
            width=dp(40),
            halign="right",
        )
        score_label_row.add_widget(self.score_percent_label)
        score_section.add_widget(score_label_row)
        
        # Progress bar with dynamic color
        self.score_bar = MDLinearProgressIndicator(
            value=85,
            size_hint_y=None,
            height=dp(8),
            radius=[dp(4)],
            md_bg_color=(0.92, 0.92, 0.92, 1),
        )
        score_section.add_widget(self.score_bar)
        
        self.add_widget(score_section)
        
        # ── Warnings/Info row (optional) ──
        self.warnings_label = MDLabel(
            text="",
            font_style="Label",
            role="small",
            theme_text_color="Custom",
            text_color=(0.89, 0.25, 0.15, 1),
            size_hint_y=None,
            height=dp(16),
            shorten=True,
            shorten_from="right",
            opacity=0,
        )
        self.add_widget(self.warnings_label)

    def set_route_info(self, distance_m, eta_minutes, score, barrier_count=0):
        """
        Update the card with route information.
        
        Args:
            distance_m: distance in meters
            eta_minutes: estimated time in minutes
            score: accessibility score 0.0–1.0
            barrier_count: number of barriers detected (optional)
        """
        self._route_data = {
            "distance_m": distance_m,
            "eta_minutes": eta_minutes,
            "score": score,
            "barrier_count": barrier_count,
        }
        
        # Format distance
        if distance_m >= 1000:
            dist_text = f"{distance_m / 1000:.1f} km"
        else:
            dist_text = f"{distance_m:.0f} m"
        self.distance_label.text = dist_text
        
        # Format ETA
        if eta_minutes < 1:
            eta_text = f"{int(eta_minutes * 60)} sec"
        elif eta_minutes < 60:
            eta_text = f"{int(eta_minutes)} min"
        else:
            hours = int(eta_minutes // 60)
            mins = int(eta_minutes % 60)
            eta_text = f"{hours}h {mins}m"
        self.eta_label.text = eta_text
        
        # Update accessibility score
        score_percent = int(score * 100)
        self.score_percent_label.text = f"{score_percent}%"
        self.score_bar.value = score_percent
        
        # Update difficulty label and color
        difficulty = _score_to_label(score)
        color = _score_to_color(score)
        self.difficulty_label.text = difficulty
        self.difficulty_label.text_color = color
        
        # Update progress bar color
        self.score_bar.md_bg_color = color
        
        # Show warnings if applicable
        self._update_warnings(barrier_count)

    def _update_warnings(self, barrier_count):
        """Update warnings section based on barriers."""
        if barrier_count > 0:
            self.warnings_label.text = f"⚠ {barrier_count} barrier(s) detected"
            self.warnings_label.opacity = 1
        else:
            self.warnings_label.opacity = 0

    def show(self):
        """Display the card with animation."""
        self.opacity = 1
        self.height = dp(140)

    def hide(self):
        """Hide the card."""
        self.opacity = 0
        self.height = 0

    def _on_close_tap(self, *args):
        """Handle close button tap."""
        self.hide()
        if self.on_close_callback:
            self.on_close_callback()

    def _on_ar_tap(self, *args):
        """Handle AR button tap."""
        if self.on_expand_callback:
            self.on_expand_callback()
