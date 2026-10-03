"""Local speech recognition using faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass

import ctranslate2
import numpy as np
from faster_whisper import WhisperModel

import config


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str | None
    language_probability: float | None


def _automatic_device() -> tuple[str, str]:
    try:
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", config.WHISPER_CUDA_COMPUTE_TYPE
    except Exception:
        pass
    return "cpu", config.WHISPER_CPU_COMPUTE_TYPE


class Transcriber:
    def __init__(self, vocabulary: list[str]) -> None:
        self.initial_prompt = ", ".join(vocabulary)

        if config.WHISPER_DEVICE == "auto":
            device, compute_type = _automatic_device()
        else:
            device = config.WHISPER_DEVICE
            compute_type = (
                config.WHISPER_CUDA_COMPUTE_TYPE
                if device == "cuda"
                else config.WHISPER_CPU_COMPUTE_TYPE
            )

        print(
            f"Loading Whisper model {config.WHISPER_MODEL!r} "
            f"on {device} ({compute_type})..."
        )
        try:
            self.model = WhisperModel(
                config.WHISPER_MODEL,
                device=device,
                compute_type=compute_type,
            )
        except Exception:
            # Auto detection can succeed even when the installed CUDA runtime is
            # incompatible. A CPU retry keeps the first-run experience reliable.
            if config.WHISPER_DEVICE != "auto" or device == "cpu":
                raise
            print("CUDA model initialization failed; retrying on CPU (int8).")
            self.model = WhisperModel(
                config.WHISPER_MODEL,
                device="cpu",
                compute_type=config.WHISPER_CPU_COMPUTE_TYPE,
            )
        print("Whisper model ready.")

    def transcribe(self, audio: np.ndarray) -> Transcription:
        segments, info = self.model.transcribe(
            audio,
            task="transcribe",
            beam_size=config.WHISPER_BEAM_SIZE,
            vad_filter=config.WHISPER_VAD_FILTER,
            initial_prompt=self.initial_prompt,
            language=None,
            condition_on_previous_text=False,
        )
        text = "".join(segment.text for segment in segments).strip()
        return Transcription(
            text=text,
            language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
        )
