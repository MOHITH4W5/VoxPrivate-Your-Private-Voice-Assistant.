"""
src/audio/processing.py
Audio preprocessing utilities — converts raw PCM bytes to numpy float arrays.
"""

import numpy as np


def pcm_to_float(audio_bytes: bytes, dtype=np.int16) -> np.ndarray:
    """
    Convert raw PCM bytes to a normalised float32 numpy array.
    faster-whisper expects float32 audio in [-1, 1].
    """
    audio_array = np.frombuffer(audio_bytes, dtype=dtype)
    return audio_array.astype(np.float32) / np.iinfo(dtype).max


def trim_silence(audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    """Remove leading and trailing silence from an audio array."""
    non_silent = np.where(np.abs(audio) > threshold)[0]
    if len(non_silent) == 0:
        return audio
    return audio[non_silent[0]: non_silent[-1] + 1]


def compute_rms(audio: np.ndarray) -> float:
    """Compute root-mean-square amplitude (useful for waveform visualisation)."""
    return float(np.sqrt(np.mean(audio ** 2)))
