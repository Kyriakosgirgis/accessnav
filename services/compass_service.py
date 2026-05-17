from kivy.utils import platform
from kivy.clock import Clock


class CompassService:
    """
    Reads device compass heading via plyer.
    Falls back to 0 degrees on desktop.
    """

    def __init__(self):
        self.heading     = 0.0
        self.is_running  = False
        self._on_heading = None
        self._poll_event = None

    def start(self, on_heading=None):
        self._on_heading = on_heading
        self.is_running  = True

        if platform in ("android", "ios"):
            self._start_device_compass()
        else:
            print("[CompassService] Desktop — compass fixed at 0°")
            self._poll_event = Clock.schedule_interval(
                self._desktop_tick, 0.5
            )

    def stop(self):
        self.is_running = False
        if self._poll_event:
            self._poll_event.cancel()
            self._poll_event = None

    def get_heading(self):
        return self.heading

    def _start_device_compass(self):
        try:
            from plyer import compass
            compass.enable()
            self._poll_event = Clock.schedule_interval(
                self._device_tick, 0.2
            )
        except Exception as e:
            print(f"[CompassService] Failed to start compass: {e}")

    def _device_tick(self, dt):
        try:
            from plyer import compass
            val = compass.field
            if val and len(val) >= 3:
                import math
                self.heading = (math.degrees(
                    math.atan2(val[0], val[1])
                ) + 360) % 360
                if self._on_heading:
                    self._on_heading(self.heading)
        except Exception:
            pass

    def _desktop_tick(self, dt):
        if self._on_heading:
            self._on_heading(self.heading)