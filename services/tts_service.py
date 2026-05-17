from kivy.utils import platform


class TTSService:
    """
    Text-to-speech announcements for navigation.
    Uses plyer.tts on Android/iOS, prints to console on desktop.
    """

    def speak(self, text: str):
        if platform in ("android", "ios"):
            try:
                from plyer import tts
                tts.speak(text)
            except Exception as e:
                print(f"[TTSService] TTS error: {e}")
        else:
            print(f"[TTSService] (desktop) {text}")

    def announce_turn(self, direction: str, distance_m: float):
        msg = f"In {int(distance_m)} metres, {direction}"
        self.speak(msg)

    def announce_arrival(self):
        self.speak("You have arrived at your destination")

    def announce_obstacle(self, description: str):
        self.speak(f"Warning — {description} ahead")