import json
import os
import threading
import time

from text_utils import normalize_text


class VoiceEngine:
    def __init__(
        self,
        model_path,
        message_queue,
        stop_event=None,
        wake_words=None,
        command_timeout_seconds=5,
        mic_retry_seconds=5,
        max_mic_retries=5,
    ):
        self.model_path = model_path
        self.message_queue = message_queue
        self.stop_event = stop_event or threading.Event()
        self.wake_words = [normalize_text(word) for word in (wake_words or ["catvis"])]
        self.command_timeout_seconds = command_timeout_seconds
        self.mic_retry_seconds = mic_retry_seconds
        self.max_mic_retries = max_mic_retries
        self.thread = None
        self._stream = None
        self._audio = None
        self._muted = threading.Event()

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self._close_audio()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

    def set_muted(self, muted):
        if muted:
            self._muted.set()
            self._send_status("muted")
        else:
            self._muted.clear()
            self._send_status("ready")

    def is_muted(self):
        return self._muted.is_set()

    def _listen(self):
        self._send_status("loading")

        if not os.path.isdir(self.model_path):
            self._send_error("model_not_found", self.model_path)
            return

        try:
            from vosk import KaldiRecognizer, Model
            import pyaudio
        except ImportError as exc:
            self._send_error("dependency_missing", str(exc))
            return

        try:
            model = Model(self.model_path)
            recognizer = KaldiRecognizer(model, 16000)
        except Exception as exc:
            self._send_error("model_load_failed", str(exc))
            return

        retry_count = 0
        while not self.stop_event.is_set():
            try:
                self._open_audio_stream(pyaudio)
                self._send_status("ready")
                self._recognition_loop(recognizer)
                break
            except Exception as exc:
                self._close_audio()

                if self.stop_event.is_set():
                    break

                retry_count += 1
                self._send_error("mic_unavailable", str(exc), retry_count)
                if retry_count >= self.max_mic_retries:
                    self._send_error("mic_error_permanent", str(exc), retry_count)
                    break

                self.stop_event.wait(self.mic_retry_seconds)

        self._close_audio()

    def _open_audio_stream(self, pyaudio_module):
        self._audio = pyaudio_module.PyAudio()
        self._stream = self._audio.open(
            format=pyaudio_module.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192,
        )
        self._stream.start_stream()

    def _recognition_loop(self, recognizer):
        listening_until = None

        while not self.stop_event.is_set():
            if listening_until and time.monotonic() > listening_until:
                listening_until = None
                self._send_status("ready")

            data = self._stream.read(4096, exception_on_overflow=False)
            if not recognizer.AcceptWaveform(data):
                continue

            result = json.loads(recognizer.Result())
            text = normalize_text(result.get("text", ""))
            if not text or self._muted.is_set():
                continue

            self._send_transcript(text)
            wake_word, command_text = self._extract_wake_command(text)
            if wake_word:
                self._send_status("listening")
                listening_until = time.monotonic() + self.command_timeout_seconds
                if command_text:
                    self._send_command(command_text)
                    listening_until = None
                    self._send_status("ready")
                continue

            if listening_until:
                self._send_command(text)
                listening_until = None
                self._send_status("ready")

    def _extract_wake_command(self, text):
        text_words = text.split()
        for wake_word in self.wake_words:
            wake_words = wake_word.split()
            wake_length = len(wake_words)

            for start_index in range(0, len(text_words) - wake_length + 1):
                end_index = start_index + wake_length
                if text_words[start_index:end_index] == wake_words:
                    command_text = " ".join(text_words[end_index:]).strip()
                    return wake_word, command_text

        return None, ""

    def _send_status(self, status):
        self.message_queue.put({"type": "status", "data": status})

    def _send_command(self, command):
        self.message_queue.put({"type": "command", "data": command})

    def _send_transcript(self, text):
        self.message_queue.put({"type": "transcript", "data": text})

    def _send_error(self, code, detail=None, retry_count=None):
        message = {"type": "error", "data": code}
        if detail:
            message["detail"] = detail
        if retry_count is not None:
            message["retry_count"] = retry_count
        self.message_queue.put(message)

    def _close_audio(self):
        stream = self._stream
        audio = self._audio
        self._stream = None
        self._audio = None

        if stream is not None:
            try:
                if stream.is_active():
                    stream.stop_stream()
            except Exception:
                pass

            try:
                stream.close()
            except Exception:
                pass

        if audio is not None:
            try:
                audio.terminate()
            except Exception:
                pass
