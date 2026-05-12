from kivy_garden.mapview import MapLayer
from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import dp


# Colour thresholds based on accessibility score
# score >= 0.75 → green  (good)
# score >= 0.45 → amber  (moderate)
# score <  0.45 → red    (poor)

def _score_to_color(score):
    if score >= 0.75:
        return (0.11, 0.72, 0.46, 1)   # teal green
    elif score >= 0.45:
        return (0.95, 0.65, 0.10, 1)   # amber
    else:
        return (0.89, 0.25, 0.15, 1)   # red


class RouteLayer(MapLayer):
    """
    A MapLayer that draws a route polyline on top of the MapView.

    Usage:
        layer = RouteLayer()
        map_view.add_layer(layer)

        # Set a route (list of (lat, lon) tuples + accessibility score)
        layer.set_route(waypoints, score=0.82)

        # Clear it
        layer.clear_route()
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._waypoints = []
        self._score     = 1.0
        self._map_view  = None

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def set_route(self, waypoints, score=1.0):
        """
        waypoints : list of (lat, lon) tuples
        score     : accessibility score 0.0–1.0
        """
        self._waypoints = waypoints
        self._score     = score
        self.invalidate()   # triggers a redraw

    def clear_route(self):
        self._waypoints = []
        self.invalidate()

    # ------------------------------------------------------------------ #
    #  MapLayer overrides                                                  #
    # ------------------------------------------------------------------ #

    def reposition(self):
        """Called by MapView whenever the map pans or zooms."""
        self.invalidate()

    def invalidate(self):
        self.canvas.clear()
        if len(self._waypoints) < 2 or self._map_view is None:
            return
        self._draw()

    # ------------------------------------------------------------------ #
    #  Drawing                                                             #
    # ------------------------------------------------------------------ #

    def _draw(self):
        mv    = self._map_view
        color = _score_to_color(self._score)

        # Convert all waypoints to screen pixels
        points = []
        for lat, lon in self._waypoints:
            x, y = mv.get_window_xy_from(lat, lon, mv.zoom)
            points.extend([x, y])

        with self.canvas:
            # ── Shadow line (dark, slightly wider) ────────────── #
            Color(0, 0, 0, 0.18)
            Line(
                points=points,
                width=dp(6),
                cap="round",
                joint="round",
            )

            # ── Main coloured route line ───────────────────────── #
            Color(*color)
            Line(
                points=points,
                width=dp(4),
                cap="round",
                joint="round",
            )

            # ── Origin dot ────────────────────────────────────── #
            ox, oy = points[0], points[1]
            self._draw_dot(ox, oy, (1, 1, 1, 1), dp(14))   # white fill
            self._draw_dot(ox, oy, color,         dp(10))   # coloured centre

            # ── Destination dot ───────────────────────────────── #
            dx, dy = points[-2], points[-1]
            self._draw_dot(dx, dy, (1, 1, 1, 1), dp(16))
            self._draw_dot(dx, dy, color,         dp(10))

            # ── Intermediate waypoint ticks ───────────────────── #
            # Small white dots every 5th waypoint so the route
            # looks segmented and easier to follow
            Color(1, 1, 1, 0.85)
            for i in range(0, len(points) - 2, 10):   # every 5 waypoints
                wx, wy = points[i], points[i + 1]
                r = dp(3)
                Ellipse(pos=(wx - r, wy - r), size=(r * 2, r * 2))

    def _draw_dot(self, x, y, color, size):
        Color(*color)
        r = size / 2
        Ellipse(pos=(x - r, y - r), size=(size, size))