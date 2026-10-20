import io
import threading
import time
import datetime
import math

import flet as ft
from mutagen import File as AudioFile

from core.api_client import MultiBridge
from core.naming import name_from_url, safe_filename
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
    "(for example Downloads).\n\n"
    "Only use audio you have the right to convert."
)


def _length_from_bytes(data):
    try:
        f = AudioFile(io.BytesIO(data))
        return f.info.length if f is not None and f.info is not None else None
    except Exception:
        return None


def main(page: ft.Page):
    page.title = "tetomidi"
    page.bgcolor = "#000000"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    api = MultiBridge(ENDPOINTS, TOKEN)
    api.start_keepalive(minutes=10)
    st = {"name": None, "data": None, "link": None, "jid": None, "t0": None,
          "pct": 0, "midi_name": None, "running": False}

    # ---------- log ----------
    log_list = ft.ListView(spacing=2, height=160, auto_scroll=True)
    log_box = ft.Container(content=log_list, visible=False, bgcolor="#0d0d0d",
                           padding=10, border_radius=10)

    def log(msg):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_list.controls.append(ft.Text(f"[{stamp}] {msg}", size=11, color="#8a8a8a"))
        page.update()

    def toggle_log(e):
        log_box.visible = not log_box.visible
        page.update()

    # ---------- widgets ----------
    file_lbl = ft.Text("No file selected", color="#8a8a8a", size=12)
    status = ft.Text("", color="#8a8a8a", size=12)
    hint = ft.Text("", color="#8a8a8a", size=10)
    bar = ft.ProgressBar(value=0, visible=False, color="#ffffff", bgcolor="#151515")
    link_field = ft.TextField(hint_text="Paste a SoundCloud or other link", border_radius=24,
                              bgcolor="#151515", border_color="#2a2a2a", color="#ffffff")
    go_btn = ft.ElevatedButton("Transcribe", on_click=lambda e: start(), height=52, expand=True)
    cancel_btn = ft.IconButton(icon=ft.icons.CLOSE, on_click=lambda e: cancel(),
                               visible=False, icon_color="#ffffff")
    back_btn = ft.OutlinedButton("Back", on_click=lambda e: reset(), visible=False, expand=True)

    def on_pick(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        if f.path:  # a real file path (desktop preview)
            with open(f.path, "rb") as fh:
                data = fh.read()
            accept(f.name, data)
        else:  # Android: upload the file to Flet first, then read it
            url = page.get_upload_url(f.name, 600)
            picker.upload([ft.FilePickerUploadFile(f.name, upload_url=url)])
            st["pending"] = f.name

    def on_upload(e: ft.FilePickerUploadEvent):
        if e.progress == 1 and st.get("pending"):
            import os
            path = os.path.join("uploads", st.pop("pending"))
            with open(path, "rb") as fh:
                data = fh.read()
            accept(os.path.basename(path), data)

    def accept(name, data):
        length = _length_from_bytes(data)
        if length is not None and length > MAX_SECONDS:
            file_lbl.value = "This file is longer than 40 minutes."
            file_lbl.color = "#ff6b6b"
            st["name"] = st["data"] = None
        else:
            st["name"], st["data"], st["link"] = safe_filename(name), data, None
            link_field.value = ""
            file_lbl.value = st["name"]
            file_lbl.color = "#ffffff"
            log(f"File chosen: {st['name']}")
        page.update()

    picker = ft.FilePicker(on_result=on_pick, on_upload=on_upload)
    page.overlay.append(picker)

    def pick_click(e):
        picker.pick_files(allow_multiple=False, allowed_extensions=AUDIO_EXT)

    # Save: system dialog, the user chooses Downloads
    def on_saved(path):
        if path:
            status.value = f"Saved: {st['midi_name']}"
            log(f"Saved MIDI to {path}")
        else:
            status.value = "Save canc
