"""Transcribe, cancel and save actions."""
import asyncio
import os
import time

from core.naming import midi_name, name_from_url
from mobile.consts import DISCORD_URL, GREEN, GREY, RED


def make_run(c):
    def set_busy(busy):
        c.st["running"] = busy
        c.bar.visible = busy
        c.bar.value = None if busy else 0
        c.go_btn.disabled = busy
        c.cancel_btn.visible = busy
        c.page.update()

    async def save_click(e=None):
        if not c.st["midi"]:
            return
        try:
            path = await c.save_midi(c.st["midi_name"], c.st["midi"])
        except Exception as ex:
            c.log(f"Save error: {ex}")
            c.set_status("Could not save the MIDI.", RED)
            c.page.update()
            return
        if path:
            c.set_status("Saved.", GREEN)
            c.log(f"Saved: {path}")
        c.page.update()

    async def go_click(e=None):
        st = c.st
        if st["running"]:
            return
        link = (c.link_field.value or "").strip()
        if not st["data"] and not link:
            c.set_status("Choose a file or paste a link first.", RED)
            c.page.update()
            return
        use_file = bool(st["data"]) and not link
        stem = os.path.splitext(st["name"])[0] if use_file else name_from_url(link)
        job_id = f"job{int(time.time() * 1000)}"
        st["jid"] = job_id
        st["midi"] = None
        c.save_btn.visible = False
        c.set_status("Transcribing... this can take a few minutes.", GREY)
        c.log("Started: " + (st["name"] if use_file else link))
        set_busy(True)
        try:
            if use_file:
                midi = await asyncio.to_thread(
                    c.api.transcribe_file, job_id, st["name"], st["data"], c.log)
            else:
                midi = await asyncio.to_thread(c.api.transcribe_link, job_id, link, c.log)
        except Exception as ex:
            set_busy(False)
            c.set_status(f"Failed: {ex}", RED)
            c.log(f"Failed: {ex}")
            c.page.update()
            return
        set_busy(False)
        st["midi"] = midi
        st["midi_name"] = midi_name(stem)
        c.save_btn.visible = True
        c.set_status("Transcriber done!", GREEN)
        c.log(f"MIDI ready: {st['midi_name']} ({len(midi)} bytes)")
        c.page.update()
        await save_click()

    async def cancel_click(e=None):
        if c.st["jid"] and c.st["running"]:
            c.log("Cancelling...")
            await asyncio.to_thread(c.api.cancel, c.st["jid"])

    async def discord_click(e=None):
        try:
            await c.page.launch_url(DISCORD_URL)
        except Exception as ex:
            c.log(f"Could not open link: {ex}")

    return go_click, cancel_click, save_click, discord_click
