"""
src/models/speech_recognition.py
Offline Speech-to-Text using faster-whisper (local, no cloud).
Accepts float32 numpy arrays from AudioCapture (sounddevice-based).
"""

import numpy as np


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

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe a float32 numpy audio array to text.
        Returns an empty string if no speech is detected.
        """
        self._load_model()

        # Ensure float32 in [-1, 1]
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Trim leading/trailing silence
        non_silent = np.where(np.abs(audio) > 0.01)[0]
        if len(non_silent) == 0:
            return ""
        audio = audio[non_silent[0]: non_silent[-1] + 1]

        if len(audio) < 1000:
            return ""  # Too short to be meaningful speech

        segments, _info = self._model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text

    def is_loaded(self) -> bool:
        return self._model is not None
