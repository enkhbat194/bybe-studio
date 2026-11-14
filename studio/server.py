#!/usr/bin/env python3
"""BYBE Studio V3 pilot — local source-linked audio trimming.

Works alongside existing V2. Originals and V2 edits are NEVER overwritten.
Standard library only; FFmpeg CLI is required to extract source context.
"""
from __future__ import annotations

import datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit, parse_qs
import uuid
import wave
import webbrowser
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bybe

DATA = bybe.DATA
REV_DIR = DATA / "revisions"
INDEX = DATA / "revision_index.json"
PORT = int(os.getenv("BYBE_STUDIO_PORT", "8766"))
LOCK = threading.RLock()
VALID_ID = re.compile(r"^[a-zA-Z0-9_-]+$")
CHECKS = ("start_heard", "end_heard", "whole_heard",
          "language_correct", "text_correct", "role_correct")


def records():
    folder = bybe.workspace()
    payload = bybe.read_json(folder / "qa_records.json")
    result = {r["id"]: r for r in payload.get("records", []) if VALID_ID.fullmatch(r["id"])}
    active_file = DATA / "imports" / "active.json"
    if active_file.is_file():
        pointer = bybe.read_json(active_file).get("004")
        if isinstance(pointer, str) and re.fullmatch(r"part004_[a-f0-9]{12}", pointer):
            imported = DATA / "imports" / pointer / "records.json"
            if imported.is_file():
                for row in bybe.read_json(imported).get("records", []):
                    if VALID_ID.fullmatch(row.get("id", "")) and row["id"] not in result:
                        result[row["id"]] = row
    return result


def legacy_state():
    folder = bybe.workspace()
    p = folder / "qa_state_server.json"
    return bybe.read_json(p).get("records", {}) if p.is_file() else {}


def registry():
    return bybe.read_json(bybe.SOURCE_MAP).get("sources", {}) if bybe.SOURCE_MAP.exists() else {}


def times(r):
    """Original absolute recording timestamps (not file-relative)."""
    val = str(r.get("timing", "")).strip()
    if val.startswith("["):
        try:
            intervals = json.loads(val)
            if len(intervals) != 1:
                raise ValueError("Cross-part source span needs special handling")
            part, start, end = intervals[0][:3]
            return str(int(part)).zfill(3), float(start), float(end)
        except (ValueError, IndexError, TypeError, json.JSONDecodeError):
            raise ValueError("Unsupported or cross-part timing; manual source mapping required")
    if r.get("set") == "new30":
        match = re.match(r"(\d+):(\d+(?:\.\d+)?)\s*[–-]\s*(\d+):(\d+(?:\.\d+)?)", val)
        if match:
            start = int(match[1]) * 60 + float(match[2])
            end = int(match[3]) * 60 + float(match[4])
            return "005", start, end
    raise ValueError("Source timing not mapped")


def source_for(r):
    part, begin, end = times(r)
    info = registry().get(part)
    if not info:
        raise ValueError("Source part " + part + " is not linked: use scripts/bybe.py link-source")
    path = Path(info["path"]).resolve()
    if (not path.is_file() or path.suffix.lower() not in
            {".mkv", ".mp4", ".wav", ".m4a", ".mp3"}):
        raise ValueError("Linked source file missing or unsupported")
    st = path.stat()
    if st.st_size != info["bytes"] or st.st_mtime_ns != info["mtime_ns"]:
        raise ValueError("Linked source changed; relink and recheck")
    if begin < 0 or end <= begin:
        raise ValueError("Invalid source interval")
    return path, part, begin, end


def ffmpeg_clip(path, begin, end):
    exe = shutil.which("ffmpeg")
    if not exe:
        raise ValueError("FFmpeg not found in PATH; install/configure FFmpeg separately")
    if begin < 0 or end <= begin or end - begin > 35:
        raise ValueError("Clip must be 0.001–35 seconds")
    DATA.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".wav", prefix=".bybe-", dir=DATA)
    os.close(fd)
    try:
        cmd = [exe, "-hide_banner", "-nostdin", "-loglevel", "error",
               "-i", str(path), "-ss", f"{begin:.6f}", "-t", f"{end-begin:.6f}",
               "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "48000",
               "-c:a", "pcm_s16le", "-y", str(tmp)]
        job = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if job.returncode:
            raise ValueError("FFmpeg failed: " + job.stderr[-500:])
        with wave.open(tmp, "rb") as w:
            if w.getnframes() < 100:
                raise ValueError("Empty audio extraction")
            seconds = w.getnframes() / w.getframerate()
            if abs(seconds - (end - begin)) > 0.15:
                raise ValueError("Unexpected extracted audio duration")
        return Path(tmp).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)


def get_index():
    if not INDEX.exists():
        return {"schema": 1, "clips": {}}
    return bybe.read_json(INDEX)


def save_index(obj):
    bybe.atomic_json(INDEX, obj)


def make_backup():
    with LOCK:
        root = bybe.workspace()
        state, refs, files = bybe.collect_backup(root)
        paths = [(file, "legacy/" + file.relative_to(root).as_posix()) for file in files]
        if INDEX.exists():
            paths.append((INDEX, "v3/revision_index.json"))
        if REV_DIR.exists():
            paths += [(p, "v3/revisions/" + p.relative_to(REV_DIR).as_posix())
                      for p in REV_DIR.rglob("*.wav") if p.is_file()]
        directory = DATA / "backups"
        directory.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dest = directory / ("BYBE_FULL_BACKUP_" + stamp + ".zip")
        temp = directory / ("." + dest.name + ".part")
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=4) as archive:
                sums = []
                for path, name in paths:
                    archive.write(path, name)
                    sums.append({"path": name, "size": path.stat().st_size,
                                 "sha256": bybe.sha256(path)})
                archive.writestr("BACKUP_MANIFEST.json", json.dumps(
                    {"created": stamp, "files": sums, "v2_edits": len(refs)}, indent=2))
            with zipfile.ZipFile(temp) as z:
                if z.testzip():
                    raise ValueError("Backup CRC validation failed")
            os.replace(temp, dest)
        finally:
            temp.unlink(missing_ok=True)
        return dest


class Handler(BaseHTTPRequestHandler):
    server_version = "BYBEStudioV3Pilot/0.1"

    def send(self, data, mime, status=200, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def out(self, obj, status=200):
        self.send(json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                  "application/json; charset=utf-8", status)

    def permitted(self, write=False):
        host = self.headers.get("Host", "").split(":")[0]
        if host not in ("localhost", "127.0.0.1"):
            return False
        if write:
            origin = self.headers.get("Origin", "")
            if origin not in ("", f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
                return False
            if self.headers.get("X-BYBE-Local") != "1":
                return False
        return True

    def do_GET(self):
        if not self.permitted():
            return self.out({"error": "Only localhost is supported"}, 403)
        url = urlsplit(self.path)
        q = parse_qs(url.query)
        path = url.path
        try:
            if path in ("/", "/index.html"):
                return self.send((HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            if path == "/api/status":
                return self.out({"status": "ok", "records": len(records()),
                                 "ffmpeg": bool(shutil.which("ffmpeg")), "linked_sources": list(registry())})
            if path == "/api/records":
                legacy = legacy_state()
                revised = get_index()["clips"]
                result = []
                for id, row in records().items():
                    try:
                        part, start, end = times(row)
                        ready = part in registry()
                    except ValueError:
                        part, start, end, ready = None, None, None, False
                    result.append({"id": id, "word": row.get("word"), "role": row.get("role"),
                                   "expected": row.get("reference") or row.get("word"),
                                   "part": part, "start": start, "end": end,
                                   "source_linked": ready,
                                   "legacy_status": legacy.get(id, {}).get("status", row.get("status")),
                                   "legacy_edited": bool(legacy.get(id, {}).get("edited")),
                                   "revision": revised.get(id, {}).get("active"),
                                   "v3_status": revised.get(id, {}).get("status", "UNREVIEWED")})
                return self.out({"records": result})
            if path == "/api/legacy-audio":
                id = q.get("id", [""])[0]
                row = records().get(id)
                if not row:
                    return self.out({"error": "Unknown clip ID"}, 404)
                root = DATA if row.get("storage") == "bybe" else bybe.workspace()
                state = legacy_state().get(id, {})
                relative = (state.get("edited") if state.get("choice") == "edited"
                            else row.get("src"))
                if not relative:
                    return self.out({"error": "Audio missing"}, 404)
                loc = (root / relative).resolve()
                if not loc.is_relative_to(root) or loc.suffix.lower() not in (".wav", ".mp3", ".m4a"):
                    raise ValueError("Invalid source path")
                if not loc.is_file():
                    return self.out({"error": "Selected WAV does not exist"}, 404)
                content_type = {".wav": "audio/wav", ".mp3": "audio/mpeg",
                                ".m4a": "audio/mp4"}[loc.suffix.lower()]
                return self.send(loc.read_bytes(), content_type)
            if path == "/api/context":
                id = q.get("id", [""])[0]
                row = records().get(id)
                if not row:
                    return self.out({"error": "Unknown clip ID"}, 404)
                source, part, start, end = source_for(row)
                pad = min(5.0, max(0.5, float(q.get("pad", ["3"])[0])))
                a, b = max(0.0, start - pad), end + pad
                return self.send(ffmpeg_clip(source, a, b), "audio/wav",
                                 extra={"X-BYBE-Base": str(a),
                                        "X-BYBE-Start": str(start), "X-BYBE-End": str(end)})
            if path == "/api/revision":
                id = q.get("id", [""])[0]
                rev = q.get("rev", [""])[0]
                revisions = get_index()["clips"].get(id, {}).get("revisions", [])
                info = next((x for x in revisions if x["rev"] == rev), None)
                if not info:
                    return self.out({"error": "Revision not found"}, 404)
                file = (REV_DIR / id / (rev + ".wav")).resolve()
                if not file.is_relative_to(REV_DIR.resolve()) or not file.is_file():
                    return self.out({"error": "Revision WAV missing"}, 404)
                return self.send(file.read_bytes(), "audio/wav")
            if path == "/api/backup":
                file = make_backup()
                return self.send(file.read_bytes(), "application/zip",
                                 extra={"Content-Disposition": "attachment; filename=BYBE_FULL_BACKUP.zip"})
            return self.out({"error": "Not found"}, 404)
        except Exception as e:
            return self.out({"error": str(e)}, 422)

    def do_POST(self):
        if not self.permitted(write=True):
            return self.out({"error": "Local write security check failed"}, 403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Object expected")
            path = urlsplit(self.path).path
            id = str(data.get("id", ""))
            row = records().get(id)
            if not row:
                raise ValueError("Unknown clip ID")
            with LOCK:
                idx = get_index()
                info = idx["clips"].setdefault(id, {"active": None, "status": "UNREVIEWED", "revisions": []})
                if path == "/api/candidate":
                    src, part, begin, end = source_for(row)
                    start = float(data["start"])
                    stop = float(data["end"])
                    if not (max(0.0, begin - 5) <= start < stop <= end + 5):
                        raise ValueError("Selection must remain within original ±5s source context")
                    content = ffmpeg_clip(src, start, stop)
                    rev = uuid.uuid4().hex
                    out = REV_DIR / id / (rev + ".wav")
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with open(out, "xb") as file:
                        file.write(content)
                        file.flush()
                        os.fsync(file.fileno())
                    info["revisions"].append({"rev": rev, "part": part, "start": start,
                                             "end": stop, "sha256": bybe.sha256(out),
                                             "created": dt.datetime.now(dt.timezone.utc).isoformat(),
                                             "status": "NEEDS_REVIEW"})
                    info["active"] = rev
                    info["status"] = "NEEDS_REVIEW"
                    save_index(idx)
                    return self.out({"ok": True, "rev": rev, "status": "NEEDS_REVIEW"})
                if path == "/api/verify":
                    rev = str(data.get("rev", ""))
                    checks = data.get("checks", {})
                    if rev != info["active"]:
                        raise ValueError("Only active revision can be verified")
                    if not isinstance(checks, dict) or not all(checks.get(k) is True for k in CHECKS):
                        raise ValueError("Listen to beginning, ending, full clip and verify language, text, role")
                    target = next((r for r in info["revisions"] if r["rev"] == rev), None)
                    if not target or not (REV_DIR / id / (rev + ".wav")).is_file():
                        raise ValueError("Selected revision WAV missing")
                    target["status"] = "MANUALLY_VERIFIED"
                    target["checks"] = checks
                    info["status"] = "MANUALLY_VERIFIED"
                    save_index(idx)
                    return self.out({"ok": True, "status": info["status"]})
            return self.out({"error": "Unknown write endpoint"}, 404)
        except Exception as e:
            return self.out({"error": str(e)}, 422)

    def log_message(self, format, *args):
        if " 200 " not in (format % args):
            super().log_message(format, *args)


def main():
    bybe.workspace()
    DATA.mkdir(parents=True, exist_ok=True)
    with ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as server:
        print(f"BYBE Studio V3 pilot: http://127.0.0.1:{PORT}/", flush=True)
        print("Existing V2 and source recordings are read-only.")
        threading.Timer(.7, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/")).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
