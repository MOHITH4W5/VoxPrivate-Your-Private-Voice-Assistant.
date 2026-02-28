"""
src/audio/capture.py
Real-time microphone audio capture with Voice Activity Detection.
"""

import pyaudio
import numpy as np
import threading
import queue
import time


class AudioCapture:
    """
    Captures microphone audio in real-time.
    Uses energy-based VAD to detect speech and produce audio segments.
    """

    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    def __init__(self, config):
        self.sample_rate: int = config.get("audio", "sample_rate", default=16000)
        self.chunk_size: int = config.get("audio", "chunk_size", default=1024)
        self.silence_threshold: int = config.get("audio", "silence_threshold", default=500)
        self.silence_duration: float = config.get("audio", "silence_duration", default=1.5)

        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._running = False
        self._thread = None
        self._audio_queue: queue.Queue = queue.Queue()

        # Amplitude callback for GUI waveform
        self.amplitude_callback = None

    def _is_speech(self, data: bytes) -> bool:
        """Simple energy-based voice activity detection."""
        audio_array = np.frombuffer(data, dtype=np.int16)
        energy = np.abs(audio_array).mean()
        if self.amplitude_callback:
            self.amplitude_callback(int(energy))
        return energy > self.silence_threshold

    def _capture_loop(self):
        """Background thread: captures audio segments separated by silence."""
        stream = self._pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        buffer = []
        silent_chunks = 0
        speaking = False
        chunks_per_second = self.sample_rate / self.chunk_size
        silence_chunks_needed = int(self.silence_duration * chunks_per_second)

        try:
            while self._running:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                is_speech = self._is_speech(data)

                if is_speech:
                    buffer.append(data)
                    silent_chunks = 0
                    speaking = True
                elif speaking:
                    buffer.append(data)
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed:
                        # End of utterance — send to queue
                        audio_bytes = b"".join(buffer)
                        self._audio_queue.put(audio_bytes)
                        buffer = []
                        silent_chunks = 0
                        speaking = False
        finally:
            stream.stop_stream()
            stream.close()

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
        Returns raw PCM bytes or None if nothing available.
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

    def __del__(self):
        self.stop()
        if self._pa:
            self._pa.terminate()
