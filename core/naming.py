"""Shared naming rules. Same result on Windows and Android."""
import os
import re
import urllib.parse


def safe_filename(name):
    """Remove characters that are not allowed in file names."""
    base = os.path.basename(name or "")
    base = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", base).strip(" ._")
    return base[:120] or "result"


def name_from_url(url):
    """Last part of the link, e.g. .../artist/track-name -> track-name."""
    p = urllib.parse.urlparse(url)
    parts = [x for x in p.path.split("/") if x]
    base = urllib.parse.unquote(parts[-1]) if parts else p.netloc
    return safe_filename(base) if base else "link"


def midi_name(stem):
    return safe_filename(stem) + ".mid"


def unique_name(name, exists):
    """Return name, or 'name (2).mid', 'name (3).mid'... until exists(name) is False.
    exists is a function that takes a file name and returns True if it is taken."""
    base, ext = os.path.splitext(name)
    candidate, i = name, 2
    while exists(candidate):
        candidate = f"{base} ({i}){ext}"
        i += 1
    return candidate
