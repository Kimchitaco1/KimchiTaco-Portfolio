import queue
import threading


class SpeechEngine:
    def __init__(
        self,
        enabled=True,
        rate=155,
        volume=0.85,
        preferred_voices=None,
        require_preferred_voice=True,
        logger=None,
    ):
        self.enabled = enabled
        self.rate = rate
        self.volume = volume
        self.preferred_voices = preferred_voices or [
            "sabina",
            "helena",
            "spanish",
            "español",
            "espanol",
            "es-mx",
            "es-es",
        ]
        self.require_preferred_voice = require_preferred_voice
        self.logger = logger
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if not self.enabled:
            return
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def say(self, text):
        if self.enabled and text:
            self._queue.put(str(text))

    def stop(self):
        self._stop_event.set()
        self._queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self):
        try:
            import pyttsx3
        except ImportError:
            self.enabled = False
            if self.logger:
                self.logger.warning("pyttsx3 is not installed; speech disabled")
            return

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            has_preferred_voice = self._select_voice(engine)
            if self.require_preferred_voice and not has_preferred_voice:
                self.enabled = False
                if self.logger:
                    self.logger.warning(
                        "No preferred Spanish speech voice found; speech disabled"
                    )
                return
        except Exception as exc:
            self.enabled = False
            if self.logger:
                self.logger.exception("Speech engine failed to start: %s", exc)
            return False

        while not self._stop_event.is_set():
            text = self._queue.get()
            if text is None:
                break

            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as exc:
                if self.logger:
                    self.logger.exception("Speech failed: %s", exc)

        try:
            engine.stop()
        except Exception:
            pass

    def _select_voice(self, engine):
        try:
            voices = engine.getProperty("voices")
        except Exception:
            return

        if self.logger:
            for voice in voices:
                self.logger.info(
                    "Available speech voice: name=%s id=%s languages=%s",
                    getattr(voice, "name", ""),
                    getattr(voice, "id", ""),
                    getattr(voice, "languages", ""),
                )

        for preferred in self.preferred_voices:
            preferred_lower = str(preferred).lower()
            for voice in voices:
                voice_blob = " ".join(
                    str(value).lower()
                    for value in (
                        getattr(voice, "id", ""),
                        getattr(voice, "name", ""),
                        getattr(voice, "languages", ""),
                    )
                )
                if preferred_lower in voice_blob:
                    engine.setProperty("voice", voice.id)
                    if self.logger:
                        self.logger.info("Selected speech voice: %s", voice.name)
                    return True

        if self.logger and voices:
            self.logger.info("Using default speech voice: %s", voices[0].name)
        return False
