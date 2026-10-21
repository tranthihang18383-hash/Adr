import threading
import time

from core.bridge_client import BridgeClient
from core.http_base import ApiError


class MultiBridge:
    """Tries several endpoints in order (e.g. port 3000, then 8080 as backup)."""

    def __init__(self, endpoints, token=""):
        self.clients = [
            BridgeClient(e["server"], e.get("file_path", "/transcribe"),
                         e.get("link_path", "/transcribe-url"), token,
                         cancel_path=e.get("cancel_path", "/cancel/{job_id}"))
            for e in endpoints
        ]
        self._cancelled = set()
        self._ka_started = False

    def start_keepalive(self, minutes=10):
        if self._ka_started:
            return
        self._ka_started = True

        def loop():
            while True:
                for c in self.clients:
                    c.ping()
                time.sleep(max(1, minutes) * 60)

        threading.Thread(target=loop, daemon=True).start()

    def _run(self, job_id, fn, log=None):
        last = None
        for i, c in enumerate(self.clients):
            if job_id in self._cancelled:
                raise ApiError("Cancelled.")
            try:
                if log:
                    log(f"Trying server {i + 1}...")
                return fn(c)
            except ApiError as e:
                last = e
                if job_id in self._cancelled:
                    raise ApiError("Cancelled.")
                if log:
                    log(f"Server {i + 1} failed: {e}")
            except Exception as e:  # timeouts, resets, ...
                last = ApiError(f"Connection problem: {e}")
                if log:
                    log(f"Server {i + 1} failed: {e}")
        raise last or ApiError("No server available.")

    def transcribe_file(self, job_id, name, data, log=None):
        return self._run(job_id, lambda c: c.transcribe_file(job_id, name, data), log)

    def transcribe_link(self, job_id, url, log=None):
        return self._run(job_id, lambda c: c.transcribe_link(job_id, url), log)

    def cancel(self, job_id):
        self._cancelled.add(job_id)
        for c in self.clients:
            c.cancel(job_id)
