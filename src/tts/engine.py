"""
src/tts/engine.py
Offline Text-to-Speech engine using pyttsx3 (no cloud dependencies).
"""

import threading
import pyttsx3


class TTSEngine:
    """Wraps pyttsx3 for offline speech synthesis."""

    def __init__(self, config):
        self.rate: int = config.get("tts", "rate", default=175)
        self.volume: float = config.get("tts", "volume", default=1.0)
        self.voice_id: int = config.get("tts", "voice_id", default=0)

        self._engine = None
        self._lock = threading.Lock()
        self._init_engine()

    def _init_engine(self):
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
            voices = self._engine.getProperty("voices")
            if voices and self.voice_id < len(voices):
                self._engine.setProperty("voice", voices[self.voice_id].id)
        except Exception as e:
            print(f"[TTS] Warning: Could not initialize pyttsx3 engine: {e}")
            self._engine = None

    def speak(self, text: str):
        """Speak the given text synchronously (blocks until done)."""
        if not text:
            return
        if self._engine is None:
            print(f"[TTS] (no engine): {text}")
            return
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"[TTS] Error speaking: {e}")

    def speak_async(self, text: str):
        """Speak in a background thread so the app stays responsive."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def set_rate(self, rate: int):
        self.rate = rate
        if self._engine:
            self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self._engine:
            self._engine.setProperty("volume", self.volume)
