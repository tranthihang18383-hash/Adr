"""Constants and small helpers for the mobile app."""
import io

from mutagen import File as AudioFile

ENDPOINTS = [
    {"server": "https://3000-6ad4c9405f7614a332e7f5ba--b-bd3f144-73761e7d75078ee6.imported.base44-preview.app",
     "file_path": "/transcribe", "link_path": "/transcribe-url", "cancel_path": "/cancel/{job_id}"},
    {"server": "https://8080-6ad4c9405f7614a332e7f5ba--b-bd3f144-73761e7d75078ee6.imported.base44-preview.app",
     "file_path": "/transcribe", "link_path": "/transcribe-url", "cancel_path": "/cancel/{job_id}"},
]
TOKEN = ""
MAX_SECONDS = 40 * 60
DISCORD_URL = "https://discord.gg/peaqm6uqgB"
AUDIO_EXT = ["mp3", "mp4", "m4a", "wav", "flac", "ogg", "aac", "mkv", "webm"]
GUIDE = (
    "How to use tetomidi\n\n"
    "1. Tap the box and choose an audio or video file.\n\n"
    "2. Or paste a SoundCloud link.\n\n"
    "3. Tap Transcribe.\n\n"
    "4. When it says Transcriber done!, choose where to save the MIDI "
    "(for example Downloads). If the save window does not open, tap Save MIDI.\n\n"
    "Only use audio you have the right to convert."
)

GREY = "#8a8a8a"
WHITE = "#ffffff"
RED = "#ff6b6b"
GREEN = "#6bff95"


def length_from_bytes(data):
    try:
        f = AudioFile(io.BytesIO(data))
        return f.info.length if f is not None and f.info is not None else None
    except Exception:
        return None
