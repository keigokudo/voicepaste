# LocalFlow

LocalFlow is a minimal, fully local push-to-talk dictation tool for Windows 11.
Hold **F8**, speak, and release F8. LocalFlow transcribes with faster-whisper,
conservatively cleans the text with Ollama, copies it to the clipboard, and sends
Ctrl+V to the application that already has focus. It never presses Enter.

## Requirements

- Windows 11
- Python 3.11 or newer (native Windows Python, not WSL Python)
- A working microphone
- Ollama
- Optional: a compatible NVIDIA GPU for faster transcription

## Setup (Windows PowerShell)

Open PowerShell in the LocalFlow repository, then create and activate a virtual
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
ollama pull qwen3:4b
```

The Ollama Windows application normally starts its local server automatically.
If it is not running, start it from the Start menu, or run this in a separate
PowerShell window:

```powershell
ollama serve
```

Start LocalFlow from the activated virtual environment:

```powershell
python main.py
```

Wait for `LocalFlow ready`. Put the cursor in any normal Windows text field,
hold F8 while speaking, then release it. Press Escape while recording to cancel.
The console prints the raw and cleaned text plus timing and paste status.

After console-mode operation is confirmed, start it without a visible console:

```powershell
Start-Process -FilePath ".\.venv\Scripts\pythonw.exe" -ArgumentList "main.py" -WorkingDirectory $PWD
```

To stop a hidden instance, use Task Manager to end its `pythonw.exe` process.

## First startup and models

On its first run, faster-whisper downloads `large-v3-turbo` from Hugging Face,
so startup can take substantially longer and requires an internet connection.
By default Hugging Face stores downloaded models in the user cache at
`%USERPROFILE%\.cache\huggingface\hub`. Once downloaded, transcription and
cleanup run locally and do not require cloud inference.

LocalFlow automatically tries CUDA when CTranslate2 detects a compatible NVIDIA
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
