# VoicePaste

VoicePaste is a minimal, fully local push-to-talk dictation tool for Windows 11.
Hold **F8**, speak, and release F8. VoicePaste transcribes with faster-whisper,
conservatively cleans the text with Ollama, copies it to the clipboard, and sends
Ctrl+V to the application that already has focus. It never presses Enter.

## Requirements

- Windows 11
- Python 3.11 or newer (native Windows Python, not WSL Python)
- A working microphone
- Ollama
- Optional: a compatible NVIDIA GPU for faster transcription

## Install and verify Python

VoicePaste must use native 64-bit Windows Python, not Python inside WSL. If
`py -3.11 --version` already reports Python 3.11, skip the installation commands
below. On a fresh Windows 11 installation, install the official Python Install
Manager with WinGet:

```powershell
winget install 9NQ7512CXL7T -e --accept-package-agreements --accept-source-agreements
```

Close and reopen PowerShell so the Python launcher is available, install the
3.11 runtime, then verify its version and executable location:

```powershell
py install 3.11
py -3.11 --version
py -3.11 -c "import sys; print(sys.executable)"
```

The first command should report `Python 3.11.x`; any native Windows Python 3.11
or newer is supported. The executable path should be a normal Windows path, not
a WSL path.

## Setup (Windows PowerShell)

Open PowerShell in the VoicePaste repository, then create and activate a virtual
environment:

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install Ollama if it is not already installed:

```powershell
winget install --id Ollama.Ollama -e
```

Close and reopen PowerShell if `ollama` is not found after installation. Verify
that Ollama is available and download the cleanup model:

```powershell
ollama --version
ollama pull qwen3:1.7b
```

The Ollama Windows application normally starts its local server automatically.
If it is not running, start it from the Start menu, or run this in a separate
PowerShell window:

```powershell
ollama serve
```

Start VoicePaste from the activated virtual environment:

```powershell
python main.py
```

Wait for `VoicePaste ready`. Put the cursor in any normal Windows text field,
hold F8 while speaking, then release it. Press Escape while recording to cancel.
The console prints the raw and cleaned text plus timing and paste status.

## Notepad smoke test

Keep VoicePaste running in its PowerShell window, then perform this simple
end-to-end check:

1. Open Notepad and click in the empty document so the text cursor is visible.
2. Hold F8 and say a short sentence, for example: "VoicePasteのテストです。"
3. Release F8 and wait for processing to finish.
4. Confirm that cleaned text appears in Notepad without Enter being pressed.
5. Press Enter yourself, then press Ctrl+V. The same text should paste again,
   confirming that it remains in the clipboard.

The PowerShell window should show recording start/stop messages, detected
language, raw and cleaned transcriptions, processing times, and
`Auto-paste succeeded: yes`. If Ollama is unavailable, VoicePaste should still
paste the raw Whisper transcription.

After console-mode operation is confirmed, start it without a visible console:

```powershell
Start-Process -FilePath ".\.venv\Scripts\pythonw.exe" -ArgumentList "main.py" -WorkingDirectory $PWD
```

To stop a hidden instance, use Task Manager to end its `pythonw.exe` process.

## First startup and models

The initial downloads are substantial. The faster-whisper `large-v3-turbo`
model is approximately 1.6 GB, and the Ollama `qwen3:1.7b` model is approximately
1.4 GB. Python packages, Ollama itself, model metadata, and download caches need
additional space. Allow at least 8 GB of free disk space before setup; the exact
usage varies by package and model versions.

On its first run, faster-whisper downloads `large-v3-turbo` from Hugging Face,
so startup can take substantially longer and requires an internet connection.
The console remains at the model-loading message during this download. By
default Hugging Face stores the model in the user cache at
`%USERPROFILE%\.cache\huggingface\hub`. Ollama stores its model separately in
its own local model directory. Once both models are downloaded, transcription
and cleanup run locally and do not require cloud inference.

VoicePaste automatically tries CUDA when CTranslate2 detects a compatible NVIDIA
GPU; otherwise it uses CPU INT8. If automatic CUDA initialization fails, it
retries on CPU. Model, device, hotkey, audio device, Ollama URL, and timing
settings are intentionally kept in `config.py`. Custom terminology is loaded
from `vocabulary.txt` at startup and supplied to both Whisper and Ollama.

## Reliability behavior

- The Whisper model is loaded once at startup and reused.
- Audio is held in memory and is never logged or saved permanently.
- If Ollama is unavailable or cleanup fails, the raw Whisper result is used.
- Text is copied before Ctrl+V is sent. If auto-paste fails, the text remains in
  the clipboard for a manual paste.
- While one recording is being processed, additional F8 presses are ignored.

If the microphone is wrong, set `AUDIO_DEVICE` in `config.py`. To inspect Windows
input device names and indices from the activated environment, run:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```
