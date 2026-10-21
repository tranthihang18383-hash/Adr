"""Helpers for BridgeClient (multipart, response parsing)."""
import base64
import json
import uuid

from core.http_base import ApiError


class BridgeHelpers:
    # ---------- helpers ----------
    @staticmethod
    def _multipart(field, filename, data):
        boundary = "----tetomidi" + uuid.uuid4().hex
        safe = filename.replace('"', "_")
        head = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field}"; filename="{safe}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
        return f"multipart/form-data; boundary={boundary}", head + data + tail

    def _midi_from_response(self, ctype, body):
        """Accept raw MIDI bytes, or JSON with midi_base64 / midi_url."""
        if body[:4] == b"MThd":
            return body
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception:
            raise ApiError("The server did not return a MIDI file.")
        if not isinstance(obj, dict):
            raise ApiError("The server did not return a MIDI file.")
        if obj.get("error"):
            raise ApiError(str(obj["error"]))
        if obj.get("midi_base64"):
            return base64.b64decode(obj["midi_base64"])
        url = obj.get("midi_url")
        if url:
            if url.startswith("/"):
                url = self.base + url
            _, _, data = self._request("GET", url, headers=self._auth())
            return data
        raise ApiError("The server response has no MIDI.")

    def _register(self, job_id):
        with self.lock:
            self.jobs[job_id] = True

    def _forget(self, job_id):
        with self.lock:
            self.jobs.pop(job_id, None)
