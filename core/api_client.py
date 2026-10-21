"""
HTTP client the tetomidi app uses to talk to the transcription server.
Has no GUI code, so it can be tested on its own.
"""
import base64
import json
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ApiError(Exception):
    pass


def _ssl_context():
    """Use certifi's CA bundle so HTTPS works inside the packaged .exe."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL = _ssl_context()


class ApiClient:
    def __init__(self, server, token, timeout=30):
        self.base = server.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _open(self, method, path, body=None, headers=None, timeout=None):
        h = {"Authorization": f"Bearer {self.token}"}
        h.update(headers or {})
        req = urllib.request.Request(self.base + path, data=body, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout, context=_SSL) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode("utf-8")).get("error", str(e))
            except Exception:
                msg = str(e)
            raise ApiError(f"HTTP {e.code}: {msg}")
        except urllib.error.URLError as e:
            raise ApiError(f"Cannot reach server: {e.reason}")
        except OSError as e:
            raise ApiError(f"Connection problem: {e}")

    def health(self):
        return json.loads(self._open("GET", "/api/health").decode("utf-8"))

    def submit_file(self, path):
        with open(path, "rb") as f:
            data = f.read()
        headers = {
            "Content-Type": "application/octet-stream",
            "X-Filename": urllib.parse.quote(os.path.basename(path)),
        }
        body = self._open("POST", "/api/jobs", body=data, headers=headers, timeout=600)
        return json.loads(body.decode("utf-8"))["id"]

    def submit_link(self, url):
        body = json.dumps({"url": url}).encode("utf-8")
        out = self._open("POST", "/api/links", body=body,
                         headers={"Content-Type": "application/json"})
        return json.loads(out.decode("utf-8"))["id"]

    def status(self, job_id):
        return json.loads(self._open("GET", f"/api/jobs/{job_id}").decode("utf-8"))

    def download_midi(self, job_id, dst_path):
        data = self._open("GET", f"/api/jobs/{job_id}/midi", timeout=300)
        with open(dst_path, "wb") as f:
            f.write(data)
        return dst_path

    def cancel(self, job_id):
        return json.loads(self._open("DELETE", f"/api/jobs/{job_id}").decode("utf-8"))


def _name_from_url(url):
    """Use the last part of the link as the name, e.g. .../artist/track-name -> track-name."""
    p = urllib.parse.urlparse(url)
    parts = [x for x in p.path.split("/") if x]
    base = urllib.parse.unquote(parts[-1]) if parts else p.netloc
    base = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", base).strip(" ._")
    return (base or "link")[:100]


class BridgeClient:
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
            with urllib.request.urlopen(req, timeout=timeout or self.timeout, context=_SSL) as r:
                return r.headers.get("Content-Type", ""), r.headers.get("Content-Disposition", ""), r.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            raise ApiError(f"HTTP {e.code}: {detail}")
    
