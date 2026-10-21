"""File picking."""
import flet as ft

from core.naming import safe_filename
from mobile.consts import AUDIO_EXT, MAX_SECONDS, RED, WHITE, length_from_bytes


def make_pick(c):
    """c is the shared context (page, st, widgets, log, set_status, picker)."""

    def accept(name, data):
        length = length_from_bytes(data)
        if length is not None and length > MAX_SECONDS:
            c.file_lbl.value = "This file is longer than 40 minutes."
            c.file_lbl.color = RED
            c.st["name"] = c.st["data"] = c.st["length"] = None
        else:
            c.st["name"], c.st["data"], c.st["link"] = safe_filename(name), data, None
            c.st["length"] = length
            c.link_field.value = ""
            c.file_lbl.value = c.st["name"]
            c.file_lbl.color = WHITE
            c.set_status("")
            c.log(f"File chosen: {c.st['name']}")
        c.page.update()

    async def pick_click(e=None):
        if c.st["running"]:
            return
        try:
            files = await c.picker.pick_files(
                allow_multiple=False,
                with_data=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=AUDIO_EXT,
            )
        except Exception as ex:
            c.log(f"File picker error: {ex}")
            c.set_status("Could not open the file picker.", RED)
            c.page.update()
            return
        if not files:
            return
        f = files[0]
        data = f.bytes
        if not data and f.path:
            try:
                with open(f.path, "rb") as fh:
                    data = fh.read()
            except Exception as ex:
                c.log(f"Could not read file: {ex}")
        if not data:
            c.set_status("Could not read that file.", RED)
            c.page.update()
            return
        accept(f.name or "audio", data)

    return pick_click
