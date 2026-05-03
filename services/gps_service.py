from kivy.clock import Clock
from kivy.utils import platform


class GPSService:

    # Limassol
    DEFAULT_LAT = 34.6786
    DEFAULT_LON  = 33.0413

    # Ignore GPS readings worse than this many metres
    MAX_ACCURACY_METRES = 50

    # How often to request GPS updates (milliseconds)
    MIN_TIME_MS = 1000

    # Minimum distance before a new update fires (metres)
    MIN_DISTANCE_M = 1

    def __init__(self):
        self.lat           = self.DEFAULT_LAT
        self.lon           = self.DEFAULT_LON
        self.accuracy      = 0.0
        self.is_running    = False
        self._on_location  = None
        self._on_status    = None
        self._gps          = None
        self._sim_event    = None   # desktop simulation clock event
        self._sim_step     = 0      # simulation step counter

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def start(self, on_location=None, on_status=None):
        """
        Start GPS updates.

        Callbacks:
            on_location(lat, lon, accuracy) — called on every valid fix
            on_status(status_type, message) — called on GPS state changes
        """
        if self.is_running:
            return

        self._on_location = on_location
        self._on_status   = on_status

        if platform in ("android", "ios"):
            self._start_device_gps()
        else:
            self._start_desktop_simulation()

    def stop(self):
        """Stop all GPS updates and clean up."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop real GPS
        if self._gps and platform in ("android", "ios"):
            try:
                self._gps.stop()
                print("[GPSService] GPS stopped")
            except Exception as e:
                print(f"[GPSService] Error stopping GPS: {e}")

        # Stop desktop simulation
        if self._sim_event:
            self._sim_event.cancel()
            self._sim_event = None
            print("[GPSService] Simulation stopped")

    def get_location(self):
        """Return the latest (lat, lon) tuple."""
        return self.lat, self.lon

    def get_accuracy(self):
        """Return the latest accuracy reading in metres."""
        return self.accuracy

    # ------------------------------------------------------------------ #
    #  Device GPS (Android / iOS)                                          #
    # ------------------------------------------------------------------ #

    def _start_device_gps(self):
        try:
            from plyer import gps
            self._gps = gps
            gps.configure(
                on_location=self._handle_device_location,
                on_status=self._handle_status,
            )
            gps.start(
                minTime=self.MIN_TIME_MS,
                minDistance=self.MIN_DISTANCE_M,
            )
            self.is_running = True
            print("[GPSService] Device GPS started")
            self._fire_status("provider-enabled", "GPS started")

        except Exception as e:
            print(f"[GPSService] Failed to start device GPS: {e}")
            self._fire_status("provider-disabled", str(e))
            # Fall back to desktop simulation
            self._start_desktop_simulation()

    def _handle_device_location(self, **kwargs):
        """
        Called by plyer on every GPS update.
        plyer passes: lat, lon, altitude, speed, bearing, accuracy, time
        """
        lat      = kwargs.get("lat",      self.lat)
        lon      = kwargs.get("lon",      self.lon)
        accuracy = kwargs.get("accuracy", self.MAX_ACCURACY_METRES + 1)

        # Filter out low-accuracy readings
        if accuracy > self.MAX_ACCURACY_METRES:
            print(
                f"[GPSService] Skipping low-accuracy reading: "
                f"{accuracy:.1f}m (max allowed: {self.MAX_ACCURACY_METRES}m)"
            )
            return

        self._update(lat, lon, accuracy)

    def _handle_status(self, stype, status):
        print(f"[GPSService] Status: {stype} — {status}")
        self._fire_status(stype, status)

    # ------------------------------------------------------------------ #
    #  Desktop simulation                                                  #
    # ------------------------------------------------------------------ #

    def _start_desktop_simulation(self):
        """
        Simulates a user walking a small route around the default location.
        Fires updates every 2 seconds so you can see the marker move.
        """
        self.is_running = True
        self._sim_step  = 0
        print("[GPSService] Desktop simulation started")
        self._fire_status("provider-enabled", "Simulating GPS (desktop mode)")

        # Fire initial position immediately
        Clock.schedule_once(lambda dt: self._sim_tick(dt), 1)

        # Then fire updates every 2 seconds
        self._sim_event = Clock.schedule_interval(self._sim_tick, 2)

    def _sim_tick(self, dt):
        """
        Each tick moves the simulated user slightly north-east,
        creating a short walking path around the default location.
        """
        # Small offsets in degrees (~5-10 metres per step)
        offsets = [
            (0.00000,  0.00000),   # starting position
            (0.00003,  0.00005),
            (0.00007,  0.00009),
            (0.00012,  0.00012),
            (0.00016,  0.00014),
            (0.00018,  0.00010),
            (0.00015,  0.00006),
            (0.00010,  0.00002),
            (0.00005, -0.00002),
            (0.00000,  0.00000),   # return to start
        ]

        idx = self._sim_step % len(offsets)
        d_lat, d_lon = offsets[idx]

        sim_lat = self.DEFAULT_LAT + d_lat
        sim_lon = self.DEFAULT_LON + d_lon
        sim_accuracy = 5.0   # simulate a good 5-metre accuracy

        self._sim_step += 1
        self._update(sim_lat, sim_lon, sim_accuracy)

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _update(self, lat, lon, accuracy=0.0):
        self.lat      = lat
        self.lon      = lon
        self.accuracy = accuracy

        print(
            f"[GPSService] Location: {lat:.6f}, {lon:.6f} "
            f"(±{accuracy:.1f}m)"
        )

        if self._on_location:
            # Always call on the main Kivy thread
            Clock.schedule_once(
                lambda dt: self._on_location(lat, lon, accuracy), 0
            )

    def _fire_status(self, stype, msg):
        if self._on_status:
            Clock.schedule_once(
                lambda dt: self._on_status(stype, msg), 0
            )