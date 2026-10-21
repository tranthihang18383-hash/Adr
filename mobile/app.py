import asyncio
import datetime
import io
import math
import os
import time

import flet as ft
from mutagen import File as AudioFile

from core.api_client import MultiBridge
from core.naming import midi_name, name_from_url, safe_filename
from mobile.storage import make_saver

# Same endpoints as the Windows app: 3000 first, 8080 as backup
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


def _length_from_bytes(data):
    try:
        f = AudioFile(io.BytesIO(data))
        return f.info.length if f is not None and f.info is not None else None
    except Exception:
        return None


def _fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def main(page: ft.Page):
    page.title = "tetomidi"
    page.bgcolor = "#000000"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    api = MultiBridge(ENDPOINTS, TOKEN)
    api.start_keepalive(minutes=10)
    st = {"name": None, "data": None, "link": None, "jid": None, "length": None,
          "midi": None, "midi_name": None, "running": False}

    # Services (Flet 1.0: FilePicker is a service, added to page.services)
    picker = ft.FilePicker()
    page.services.append(picker)
    save_midi = make_saver(page)

    # ---------- log ----------
    log_list = ft.ListView(spacing=2, height=160, auto_scroll=True)
    log_box = ft.Container(content=log_list, visible=False, bgcolor="#0d0d0d",
                           padding=10, border_radius=10)

    def log(msg):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_list.controls.append(ft.Text(f"[{stamp}] {msg}", size=11, color=GREY))
        page.update()

    def toggle_log(e=None):
        log_box.visible = not log_box.visible
        page.update()

    guide_box = ft.Container(content=ft.Text(GUIDE, size=13, color="#cfcfcf"), visible=False,
                             bgcolor="#0d0d0d", padding=14, border_radius=12)

    def toggle_guide(e=None):
        guide_box.visible = not guide_box.visible
        page.update()

    # ---------- widgets ----------
    file_lbl = ft.Text("No file selected", color=GREY, size=12, text_align=ft.TextAlign.CENTER)
    status = ft.Text("", color=GREY, size=12, text_align=ft.TextAlign.CENTER)
    hint = ft.Text("", color=GREY, size=10, text_align=ft.TextAlign.CENTER)
    bar = ft.ProgressBar(value=0, visible=False, color=WHITE, bgcolor="#151515")
    link_field = ft.TextField(hint_text="Paste a SoundCloud or other link", border_radius=24,
                              bgcolor="#151515", border_color="#2a2a2a", color=WHITE)

    def set_status(text, color=GREY):
        status.value = text
        status.color = color

    # ---------- file picking ----------
    def accept(name, data):
        length = _length_from_bytes(data)
        if length is not None and length > MAX_SECONDS:
            file_lbl.value = "This file is longer than 40 minutes."
            file_lbl.color = RED
            st["name"] = st["data"] = st["length"] = None
        else:
            st["name"], st["data"], st["link"] = safe_filename(name), data, None
            st["length"] = length
            link_field.value = ""
            file_lbl.value = st["name"]
            file_lbl.color = WHITE
            set_status("")
            log(f"File chosen: {st['name']}")
        page.update()

    async def pick_click(e=None):
        if st["running"]:
            return
        try:
            files = await picker.pick_files(
                allow_multiple=False,
                with_data=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=AUDIO_EXT,
            )
        except Exception as ex:
            log(f"File picker error: {ex}")
            set_status("Could not open the file picker.", RED)
            page.update()
            return
        if not files:
            return
        f = files[0]
        data = f.bytes
        if not data and f.path:  # des
