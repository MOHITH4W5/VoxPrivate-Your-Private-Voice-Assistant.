"""
src/audio/capture.py
Real-time microphone audio capture using sounddevice (no C++ Build Tools needed).
Uses energy-based Voice Activity Detection to produce clean audio segments.
"""

import sounddevice as sd
import numpy as np
import threading
import queue


class AudioCapture:
    """
    Captures microphone audio in real-time using sounddevice.
    Uses energy-based VAD to detect speech and produce audio segments.
    """

    def __init__(self, config):
        self.sample_rate: int = config.get("audio", "sample_rate", default=16000)
        self.chunk_size: int = config.get("audio", "chunk_size", default=1024)
        self.silence_threshold: int = config.get("audio", "silence_threshold", default=500)
        self.silence_duration: float = config.get("audio", "silence_duration", default=1.5)

        self._running = False
        self._thread = None
        self._audio_queue: queue.Queue = queue.Queue()

        # Amplitude callback for GUI waveform visualisation
        self.amplitude_callback = None

    def _is_speech(self, data: np.ndarray) -> bool:
        """Simple energy-based voice activity detection."""
        # data is float32 in [-1, 1]; convert to int16-equivalent energy
        energy = int(np.abs(data).mean() * 32768)
        if self.amplitude_callback:
            self.amplitude_callback(energy)
        return energy > self.silence_threshold

    def _capture_loop(self):
        """Background thread: accumulates audio and emits complete utterances."""
        buffer = []
        silent_chunks = 0
        speaking = False
        chunks_per_second = self.sample_rate / self.chunk_size
        silence_chunks_needed = int(self.silence_duration * chunks_per_second)

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_size,
        ) as stream:
            while self._running:
                data, _ = stream.read(self.chunk_size)
                data_flat = data[:, 0]  # mono
                is_speech = self._is_speech(data_flat)

                if is_speech:
                    buffer.append(data_flat.copy())
                    silent_chunks = 0
                    speaking = True
                elif speaking:
                    buffer.append(data_flat.copy())
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed:
                        # End of utterance — concatenate and enqueue as float32
                        audio_array = np.concatenate(buffer)
                        self._audio_queue.put(audio_array)
                        buffer = []
                        silent_chunks = 0
                        speaking = False

    def start(self):
        """Start the capture thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the capture thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def get_audio(self, timeout: float = 0.1):
        """
        Get next audio segment from queue.
        Returns a float32 numpy array or None if nothing available.
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        """Flush any pending audio."""
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
