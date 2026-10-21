"""Android storage: MIDI is written with the system 'Save as' dialog (Downloads or any folder)."""
import flet as ft


def make_saver(page):
    """Register a FilePicker service and return an async save(file_name, data) function.

    save() opens the system 'Save as' dialog and writes `data` (bytes).
    It returns the saved path (or None when the user cancels).
    On Android the bytes MUST be passed to save_file (src_bytes), Flet writes them for us.
    """
    saver = ft.FilePicker()
    page.services.append(saver)

    async def save(file_name, data):
        return await saver.save_file(
            dialog_title="Save MIDI",
            file_name=file_name,
            src_bytes=data,
        )

    return save
