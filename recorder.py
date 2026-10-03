"""In-memory microphone recording."""

from __future__ import annotations

import threading

import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int, channels: int = 1, device=None) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start a new recording. Repeated calls while active are ignored."""
        with self._lock:
            if self._stream is not None:
                return
            self._chunks = []
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                device=self.device,
                callback=self._audio_callback,
            )
            try:
                stream.start()
            except Exception:
                stream.close()
                raise
            self._stream = stream

    def stop(self) -> np.ndarray:
        """Stop recording and return a one-dimensional float32 waveform."""
        with self._lock:
            stream = self._stream
            self._stream = None

        if stream is None:
            return np.empty(0, dtype=np.float32)

        try:
            stream.stop()
        finally:
            stream.close()

        with self._lock:
            chunks = self._chunks
            self._chunks = []

        if not chunks:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(chunks, axis=0).reshape(-1).astype(np.float32, copy=False)

    def cancel(self) -> None:
        """Stop and discard the current recording."""
        self.stop()

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._stream is not None

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        del frames, time_info
        if status:
            print(f"Audio warning: {status}")
        # PortAudio reuses its input buffer, so every callback must copy it.
        self._chunks.append(indata.copy())

