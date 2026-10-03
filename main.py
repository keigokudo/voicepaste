"""VoicePaste: hold a global key, dictate, release, and paste."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from pynput import keyboard

import config
from cleaner import Cleaner
from output import TextOutput
from recorder import Recorder
from transcriber import Transcriber


BASE_DIR = Path(__file__).resolve().parent
CTRL_KEYS = frozenset((keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r))
SHIFT_KEYS = frozenset(
    (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r)
)


def load_vocabulary() -> list[str]:
    path = BASE_DIR / "vocabulary.txt"
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def parse_key(name: str):
    normalized = name.strip().lower()
    if len(normalized) == 1:
        return keyboard.KeyCode.from_char(normalized)
    try:
        return getattr(keyboard.Key, normalized)
    except AttributeError as exc:
        raise ValueError(
            f"Unsupported HOTKEY {name!r}. Use a pynput key name such as 'f8'."
        ) from exc


class VoicePaste:
    def __init__(self) -> None:
        vocabulary = load_vocabulary()
        self.hotkey = parse_key(config.HOTKEY)
        self.recorder = Recorder(
            sample_rate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            device=config.AUDIO_DEVICE,
        )
        # Model loading happens once, before the keyboard listener starts.
        self.transcriber = Transcriber(vocabulary)
        self.cleaner = Cleaner(vocabulary)
        self.output = TextOutput()
        self._state_lock = threading.Lock()
        self._recording = False
        self._processing = False
        self._pressed_modifiers: set[str] = set()

    def on_press(self, key) -> bool | None:
        if key in CTRL_KEYS:
            self._pressed_modifiers.add("ctrl")
        if key in SHIFT_KEYS:
            self._pressed_modifiers.add("shift")

        character = getattr(key, "char", None)
        is_q_key = (
            character is not None and character.lower() == "q"
        ) or getattr(key, "vk", None) == ord("Q")
        if (
            is_q_key
            and {"ctrl", "shift"}.issubset(self._pressed_modifiers)
        ):
            self._cancel_recording()
            return False

        if key == keyboard.Key.esc:
            self._cancel_recording()
            return
        if key != self.hotkey:
            return

        with self._state_lock:
            # This also filters OS key-repeat events.
            if self._recording or self._processing:
                return
            self._recording = True
            try:
                self.recorder.start()
            except Exception as exc:
                self._recording = False
                print(f"Could not start recording: {exc}")
                return
        print("Recording started.")

    def on_release(self, key) -> None:
        if key in CTRL_KEYS:
            self._pressed_modifiers.discard("ctrl")
        if key in SHIFT_KEYS:
            self._pressed_modifiers.discard("shift")

        if key != self.hotkey:
            return
        with self._state_lock:
            if not self._recording:
                return
            self._recording = False
            self._processing = True

        try:
            audio = self.recorder.stop()
        except Exception as exc:
            print(f"Could not stop recording: {exc}")
            with self._state_lock:
                self._processing = False
            return

        duration = len(audio) / config.SAMPLE_RATE
        print(f"Recording stopped ({duration:.1f}s).")
        worker = threading.Thread(
            target=self._process_audio,
            args=(audio,),
            name="voicepaste-processing",
            daemon=True,
        )
        worker.start()

    def _cancel_recording(self) -> None:
        with self._state_lock:
            if not self._recording:
                return
            self._recording = False
        try:
            self.recorder.cancel()
        except Exception as exc:
            print(f"Recording cancellation warning: {exc}")
        print("Recording cancelled.")

    def _process_audio(self, audio) -> None:
        try:
            if audio.size == 0:
                print("No audio captured; nothing to transcribe.")
                return

            whisper_started = time.perf_counter()
            try:
                result = self.transcriber.transcribe(audio)
            except Exception as exc:
                print(f"Whisper transcription failed: {exc}")
                return
            whisper_elapsed = time.perf_counter() - whisper_started
            probability = (
                f" ({result.language_probability:.0%})"
                if result.language_probability is not None
                else ""
            )
            print(f"Detected language: {result.language or 'unknown'}{probability}")
            print(f"Raw transcription: {result.text}")
            print(f"Whisper processing time: {whisper_elapsed:.2f}s")

            if not result.text:
                print("No speech detected; nothing to paste.")
                return

            llm_started = time.perf_counter()
            try:
                final_text = self.cleaner.clean(result.text)
                llm_elapsed = time.perf_counter() - llm_started
                print(f"Cleaned transcription: {final_text}")
                print(f"Local LLM processing time: {llm_elapsed:.2f}s")
            except Exception as exc:
                llm_elapsed = time.perf_counter() - llm_started
                final_text = result.text
                print(f"Local LLM cleanup failed; using raw transcription: {exc}")
                print(f"Local LLM processing time: {llm_elapsed:.2f}s")
                print(f"Cleaned transcription (fallback): {final_text}")

            try:
                pasted = self.output.copy_and_paste(final_text)
                print(f"Auto-paste succeeded: {'yes' if pasted else 'no'}")
            except Exception as exc:
                # This normally means clipboard access itself failed. If copy
                # succeeded and only paste failed, TextOutput handles it above.
                print(f"Clipboard/output failed: {exc}")
                print("Auto-paste succeeded: no")
        finally:
            with self._state_lock:
                self._processing = False

    def run(self) -> None:
        print(
            f"VoicePaste ready. Hold {config.HOTKEY.upper()} to dictate; "
            "Esc cancels; Ctrl+Shift+Q quits."
        )
        listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        )
        try:
            with listener:
                listener.join()
        except KeyboardInterrupt:
            listener.stop()
        finally:
            if self.recorder.is_recording:
                self._cancel_recording()
            print("VoicePaste stopped.")


def main() -> None:
    VoicePaste().run()


if __name__ == "__main__":
    main()
