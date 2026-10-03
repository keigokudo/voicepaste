"""VoicePaste configuration.

Edit these constants to change models, devices, or the push-to-talk key.
"""

# Global push-to-talk key. Named pynput keys (for example "f8" or "scroll_lock")
# and single characters are supported.
HOTKEY = "f8"

# Audio is captured as mono float32 at Whisper's native sample rate.
SAMPLE_RATE = 16_000
CHANNELS = 1
AUDIO_DEVICE = None  # None uses the Windows default input device.

# faster-whisper settings. "auto" tries CUDA first, then CPU INT8.
WHISPER_MODEL = "small"
WHISPER_DEVICE = "auto"  # "auto", "cuda", or "cpu"
WHISPER_CUDA_COMPUTE_TYPE = "float16"
WHISPER_CPU_COMPUTE_TYPE = "int8"
WHISPER_BEAM_SIZE = 1
WHISPER_VAD_FILTER = True

# Ollama settings.
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen3:1.7b"
OLLAMA_TIMEOUT_SECONDS = 20

# A short pause helps Windows make clipboard content available before Ctrl+V.
PASTE_DELAY_SECONDS = 0.08
