import base64
import json
import threading
import time
import urllib.error
import urllib.request
import uuid

from core.bridge_helpers import BridgeHelpers
from core.http_base import ApiError, SSL_CTX


class BridgeClient(BridgeHelpers):
    """
    Talks to an existing transcription endpoint that accepts a file or a link
    and returns the MIDI. Keeps the same interface as ApiClient so the UI
    does not need to change:
        POST {base}{file_path}   multipart/form-data, field "file"
        POST {base}{link_path}   JSON {"url": "..."}
    The response may be the MIDI bytes directly, or JSON containing
    "midi_url" (fetched next), or "midi_base64".
    """

    def __init__(self, base, file_path="/transcribe", link_path="/transcribe-url",
                 token="", timeout=7200, cancel_path="/cancel/{job_id}"):
        self.base = base.rstrip("/")
        self.file_path = file_path
        self.link_path = link_path
        self.cancel_path = cancel_path
        self.token = token
        self.timeout = timeout
        self.jobs = {}
        self.lock = threading.Lock()

    def health(self):
        return {"ok": True}

    def _headers(self, content_type):
        h = {"Content-Type": content_type}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ---------- low level ----------
    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _request(self, method, url, body=None, headers=None, timeout=None):
        req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout, context=SSL_CTX) as r:
                return r.headers.get("Content-Type", ""), r.headers.get("Content-Disposition", ""), r.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            raise ApiError(f"HTTP {e.code}: {detail}")

    # ---------- public ----------
    def ping(self):
        try:
            self._request("GET", self.base + "/", headers=self._auth(), timeout=15)
        except Exception:
            pass

    def transcribe_file(self, job_id, name, data):
        ctype, body = self._multipart("file", name, data)
        self._register(job_id)
        try:
            _, _, out = self._request("POST", self.base + self.file_path,
                                      body=body, headers=self._headers(ctype))
        finally:
            self._forget(job_id)
        return self._midi_from_response("", out)

    def transcribe_link(self, job_id, url):
        self._register(job_id)
        try:
            _, _, out = self._request(
                "POST", self.base + self.link_path,
                body=json.dumps({"url": url}).encode("utf-8"),
                headers=self._headers("application/json"))
        finally:
            self._forget(job_id)
        return self._midi_from_response("", out)

    def cancel(self, job_id):
        try:
            path = self.cancel_path.format(job_id=job_id)
            self._request("POST", self.base + path, body=b"",
                          headers=self._headers("application/json"), timeout=15)
        except Exception:
            pass
