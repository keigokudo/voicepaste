"""Windows clipboard and paste output."""

from __future__ import annotations

import time

import pyperclip
from pynput.keyboard import Controller, Key

import config


class TextOutput:
    def __init__(self) -> None:
        self.keyboard = Controller()

    def copy_and_paste(self, text: str) -> bool:
        """Copy text, then try Ctrl+V. Clipboard remains intact on paste failure."""
        pyperclip.copy(text)
        time.sleep(config.PASTE_DELAY_SECONDS)
        try:
            with self.keyboard.pressed(Key.ctrl):
                self.keyboard.press("v")
                self.keyboard.release("v")
            return True
        except Exception as exc:
            print(f"Auto-paste failed (text is still in clipboard): {exc}")
            return False

