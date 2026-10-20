"""Android storage: MIDI is written with the system 'Save as' dialog (Downloads or any folder)."""
import flet as ft


def make_saver(page, on_done):
    """Create a FilePicker used to save MIDI. Call saver.save_file(...) to open the dialog."""
    def handle(e: ft.FilePickerResultEvent):
        on_done(e.path)

    saver = ft.FilePicker(on_result=handle)
    page.overlay.append(saver)
    page.update()
    return saver
