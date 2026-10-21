"""The big dashed "upload your audio" box on the main screen."""
import flet as ft

from mobile.consts import GREY, WHITE

BOX_BG = "#0d0d0d"
DASH = "#3a3a3a"
RADIUS = 24


def _content(file_lbl):
    icon = getattr(ft.Icons, "AUDIOTRACK_OUTLINED", ft.Icons.MUSIC_NOTE)
    return ft.Column(
        [
            ft.Icon(icon, size=56, color=WHITE),
            ft.Text("Tap to upload your audio file", size=17,
                    weight=ft.FontWeight.BOLD, color=WHITE,
                    text_align=ft.TextAlign.CENTER),
            ft.Text("or paste a link below", size=15, color=GREY,
                    text_align=ft.TextAlign.CENTER),
            ft.Text("MP3, WAV, FLAC, M4A and more — max 40 minutes",
                    size=12, color=GREY, text_align=ft.TextAlign.CENTER),
            file_lbl,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )


def make_upload_box(file_lbl, on_click, height=240):
    """Return a tappable box with a dashed rounded border.

    The dashed border is drawn on a canvas that resizes with the box. If the
    canvas is not available for any reason, a plain solid border is used so
    the app still works.
    """
    try:
        import flet.canvas as cv

        rect = cv.Rect(
            1, 1, 10, 10, border_radius=RADIUS,
            paint=ft.Paint(color=DASH, stroke_width=2,
                           style=ft.PaintingStyle.STROKE,
                           stroke_dash_pattern=[8, 7]))

        def on_resize(e):
            rect.width = max(e.width - 2, 0)
            rect.height = max(e.height - 2, 0)
            canvas.update()

        canvas = cv.Canvas([rect], on_resize=on_resize,
                           left=0, top=0, right=0, bottom=0)
        inner = ft.Container(content=_content(file_lbl), padding=16,
                             alignment=ft.Alignment(0, 0),
                             left=0, top=0, right=0, bottom=0)
        return ft.Container(
            content=ft.Stack([canvas, inner]), height=height, width=None,
            bgcolor=BOX_BG, border_radius=RADIUS, on_click=on_click)
    except Exception:
        return ft.Container(
            content=_content(file_lbl), height=height, padding=16,
            alignment=ft.Alignment(0, 0), bgcolor=BOX_BG,
            border_radius=RADIUS, border=ft.Border.all(2, DASH),
            on_click=on_click)
