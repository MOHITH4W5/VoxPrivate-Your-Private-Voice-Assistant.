"""
src/models/speech_recognition.py
Offline Speech-to-Text using faster-whisper (local, no cloud).
"""

import numpy as np
from src.audio.processing import pcm_to_float, trim_silence


class SpeechRecognizer:
    """
    Wraps faster-whisper for offline speech recognition.
    The model is lazy-loaded on the first transcribe() call.
    """

    def __init__(self, config):
        self.model_size: str = config.get("model", "speech_recognition", default="tiny")
        self.language: str = config.get("model", "language", default="en")
        self.use_gpu: bool = config.get("model", "gpu_acceleration", default=False)
        self._model = None

    def _load_model(self):
        """Lazy-load the Whisper model (downloads on first run ~150MB for tiny)."""
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            device = "cuda" if self.use_gpu else "cpu"
            compute_type = "float16" if self.use_gpu else "int8"
            print(f"[STT] Loading faster-whisper '{self.model_size}' model on {device}...")
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
            )
            print("[STT] Model loaded successfully.")
        except ImportError:
            raise RuntimeError(
                "faster-whisper is not installed. Run: pip install faster-whisper"
            )

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe raw PCM audio bytes to text.
        Returns an empty string if no speech is detected.
        """
        self._load_model()
        audio_float = pcm_to_float(audio_bytes)
        audio_float = trim_silence(audio_float)

        if len(audio_float) < 1000:
            return ""  # Too short to be meaningful speech

        segments, info = self._model.transcribe(
            audio_float,
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text

    def is_loaded(self) -> bool:
        return self._model is not None
