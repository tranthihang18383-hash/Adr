"""Small result table shown after a transcription: notes, tempo, length."""
import flet as ft

from core.midi_info import format_length, format_tempo, read_midi_info
from mobile.consts import GREY, WHITE


def make_stats():
    """Return (box, show, hide). show(midi_bytes) fills and reveals the table."""
    values = {k: ft.Text("-", size=18, weight=ft.FontWeight.BOLD, color=WHITE,
                         text_align=ft.TextAlign.CENTER)
              for k in ("notes", "tempo", "length")}

    def cell(key, caption):
        return ft.Column(
            [values[key], ft.Text(caption, size=9, color=GREY,
                                  text_align=ft.TextAlign.CENTER)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    box = ft.Container(
        content=ft.Row(
            [cell("notes", "NOTES"), cell("tempo", "TEMPO BPM"),
             cell("length", "LENGTH MM:SS")],
            alignment=ft.MainAxisAlignment.SPACE_AROUND),
        visible=False, bgcolor="#0d0d0d", border_radius=14,
        padding=12)

    def show(midi):
        """Returns a one-line summary for the log, or None if unreadable."""
        info = read_midi_info(midi)
        values["notes"].value = f"{info['notes']:,}"
        values["tempo"].value = format_tempo(info)
        values["length"].value = format_length(info["seconds"])
        box.visible = True
        return (f"{info['notes']} notes, {format_tempo(info)} BPM, "
                f"{format_length(info['seconds'])}")

    def hide():
        box.visible = False

    return box, show, hide
