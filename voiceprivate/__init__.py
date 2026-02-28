"""
voiceprivate/__init__.py
Public API for VoxPrivate — exposes the VoiceAssistant class as described in README.

Usage:
    from voiceprivate import VoiceAssistant
    assistant = VoiceAssistant()
    assistant.listen()
"""

import threading
import time
import sys
import os

# Add project root to path so relative imports work when used as a package
_ROOT = os.path.dirname(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.utils.config import Config
from src.audio.capture import AudioCapture
from src.models.speech_recognition import SpeechRecognizer
from src.models.intent_classifier import classify_intent
from src.commands.executor import CommandExecutor
from src.tts.engine import TTSEngine


class VoiceAssistant:
    """
    High-level VoxPrivate voice assistant.

    Can be used standalone (no GUI) or driven by the GUI app.
    """

    def __init__(self, config_path: str = None, gui=None):
        self.config = Config.from_file(config_path)
        self.gui = gui  # optional GUI reference

        self._stt = SpeechRecognizer(self.config)
        self._tts = TTSEngine(self.config)
        self._capture = AudioCapture(self.config)
        self._executor = CommandExecutor(self.config, self._tts)

        self._listening = False
        self._should_exit = False
        self._thread = None

        # Wire amplitude callback for waveform
        if self.gui:
            self._capture.amplitude_callback = self.gui.set_amplitude
            self._executor.action_callback = self._on_response

    # ── Public API ────────────────────────────────────────────────────────────

    def listen(self):
        """Start listening in a blocking loop (use for CLI / headless mode)."""
        print("[VoxPrivate] Starting in headless mode. Press Ctrl+C to exit.")
        self._tts.speak("VoxPrivate is ready. How can I help you?")
        self.start_listening()
        try:
            while not self._should_exit:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def start_listening(self):
        """Begin continuous listening in a background thread."""
        if self._listening:
            return
        self._listening = True
        self._capture.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        if self.gui:
            self.gui.set_listening(True)
            self.gui.set_status("listening")
            self.gui.log("Listening started.")

    def stop_listening(self):
        """Pause listening."""
        self._listening = False
        if self.gui:
            self.gui.set_listening(False)
            self.gui.set_status("idle")

    def toggle_listening(self):
        """Toggle listening state (called by GUI mic button)."""
        if self._listening:
            self.stop_listening()
        else:
            self.start_listening()

    def stop(self):
        """Fully shut down the assistant."""
        self._should_exit = True
        self._listening = False
        self._capture.stop()

    # ── Internal Loop ─────────────────────────────────────────────────────────

    def _loop(self):
        while not self._should_exit:
            if not self._listening:
                time.sleep(0.1)
                continue

            audio_data = self._capture.get_audio(timeout=0.2)
            if audio_data is None:
                continue

            # Update GUI
            if self.gui:
                self.gui.set_status("thinking")

            # STT transcription
            try:
                text = self._stt.transcribe(audio_data)
            except Exception as e:
                print(f"[STT Error] {e}")
                text = ""

            if not text:
                if self.gui:
                    self.gui.set_status("listening")
                continue

            print(f"[Heard] {text}")
            if self.gui:
                self.gui.set_transcription(text)
                self.gui.log(f"You: {text}")

            # Intent classification
            intent, metadata = classify_intent(text)
            print(f"[Intent] {intent} | metadata={metadata}")

            # Exit condition
            if intent == "stop":
                response = self._executor.execute(intent, metadata)
                self._speak(response)
                self.stop()
                break

            # Execute command & respond
            response = self._executor.execute(intent, metadata)
            self._speak(response)

            if self.gui:
                self.gui.set_status("listening")

    def _speak(self, text: str):
        print(f"[VoxPrivate] {text}")
        if self.gui:
            self.gui.set_status("speaking")
            self.gui.log(f"Assistant: {text}")
        self._tts.speak(text)

    def _on_response(self, text: str):
        if self.gui:
            self.gui.set_response(text)
