import datetime
from types import SimpleNamespace

import flet as ft

from core.api_client import MultiBridge
from mobile.consts import ENDPOINTS, GREY, GUIDE, TOKEN, WHITE
from mobile.pick import make_pick
from mobile.run import make_run
from mobile.storage import make_saver


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

    picker = ft.FilePicker()
    page.services.append(picker)
    save_midi = make_saver(page)

    log_list = ft.ListView(spacing=2, height=160, auto_scroll=True)
    log_box = ft.Container(content=log_list, visible=False, bgcolor="#0d0d0d",
                           padding=10, border_radius=10)
    guide_box = ft.Container(content=ft.Text(GUIDE, size=13, color="#cfcfcf"),
                             visible=False, bgcolor="#0d0d0d", padding=14,
                             border_radius=12)

    def log(msg):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_list.controls.append(ft.Text(f"[{stamp}] {msg}", size=11, color=GREY))
        page.update()

    def toggle_log(e=None):
        log_box.visible = not log_box.visible
        page.update()

    def toggle_guide(e=None):
        guide_box.visible = not guide_box.visible
        page.update()

    file_lbl = ft.Text("No file selected", color=GREY, size=12,
                       text_align=ft.TextAlign.CENTER)
    status = ft.Text("", color=GREY, size=12, text_align=ft.TextAlign.CENTER)
    bar = ft.ProgressBar(value=0, visible=False, color=WHITE, bgcolor="#151515")
    link_field = ft.TextField(hint_text="Paste a SoundCloud or other link",
                              border_radius=24, bgcolor="#151515",
                              border_color="#2a2a2a", color=WHITE)
    go_btn = ft.Button(content="Transcribe", width=220)
    cancel_btn = ft.TextButton(content="Cancel", visible=False)
    save_btn = ft.Button(content="Save MIDI", visible=False, width=220)

    def set_status(text, color=GREY):
        status.value = text
        status.color = color

    c = SimpleNamespace(
        page=page, st=st, api=api, picker=picker, save_midi=save_midi, log=log,
        set_status=set_status, file_lbl=file_lbl, link_field=link_field, bar=bar,
        go_btn=go_btn, cancel_btn=cancel_btn, save_btn=save_btn)

    pick_click = make_pick(c)
    go_click, cancel_click, save_click, discord_click = make_run(c)
    go_btn.on_click = go_click
    cancel_btn.on_click = cancel_click
    save_btn.on_click = save_click

    pick_box = ft.Container(
        content=ft.Column(
            [ft.Text("Tap to choose audio or video", color=WHITE, size=14), file_lbl],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
        alignment=ft.Alignment(0, 0), height=130, border_radius=16,
        bgcolor="#0d0d0d", on_click=pick_click)

    def row(*items):
        return ft.Row(list(items), alignment=ft.MainAxisAlignment.CENTER)

    page.add(ft.Column(
        [
            ft.Image(src="icon.png", width=110, height=110, border_radius=24),
            ft.Text("tetomidi", size=26, weight=ft.FontWeight.BOLD, color=WHITE),
            pick_box, link_field, row(go_btn), row(cancel_btn), bar, status,
            row(save_btn),
            row(ft.TextButton(content="Guide", on_click=toggle_guide),
                ft.TextButton(content="Log", on_click=toggle_log),
                ft.TextButton(content="Discord", on_click=discord_click)),
            guide_box, log_box,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14))
