import unittest

from cleaner import apply_cleanup_safeguard


class CleanupSafeguardTests(unittest.TestCase):
    def test_rejects_destructively_shortened_japanese_transcript(self) -> None:
        raw = "日本語入力のテストをしています。聞き取ることができますか?"
        candidate = "日本語入力"

        self.assertEqual(apply_cleanup_safeguard(raw, candidate), raw)

    def test_accepts_filler_removal(self) -> None:
        raw = "えーと、今日はReactのテストをしています。"
        candidate = "今日はReactのテストをしています。"

        self.assertEqual(apply_cleanup_safeguard(raw, candidate), candidate)

    def test_accepts_unchanged_transcript(self) -> None:
        raw = "今日はReactのテストをしています。"

        self.assertEqual(apply_cleanup_safeguard(raw, raw), raw)

    def test_empty_raw_transcript_is_safe(self) -> None:
        self.assertEqual(apply_cleanup_safeguard("", "unexpected text"), "")


if __name__ == "__main__":
    unittest.main()
