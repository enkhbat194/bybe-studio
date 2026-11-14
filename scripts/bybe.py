#!/usr/bin/env python3
"""BYBE Studio local bridge to the existing Czech800 QA V2, stdlib only.

Does not replace V2, edit sources or upload media. Backups contain all
active user edits and QA state; missing referenced edits are fatal.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "local_data"
DEFAULT_V2 = Path(
    r"D:\Czech800\Czech800_QA_STUDIO_V2_CHROME_EDITOR\Czech800_QA_STUDIO_V2"
)
CONFIG = ROOT / "local-config.json"
SOURCE_MAP = DATA / "source_map.json"


class BybeError(Exception):
    pass


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    fd, temp = tempfile.mkstemp(prefix=".bybe-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def workspace(user_path=None):
    if user_path:
        root = Path(user_path)
    elif os.getenv("BYBE_LEGACY_QA"):
        root = Path(os.environ["BYBE_LEGACY_QA"])
    elif CONFIG.is_file():
        root = Path(read_json(CONFIG).get("legacy_workspace", str(DEFAULT_V2)))
    else:
        root = DEFAULT_V2
    root = root.expanduser().resolve()
    if not (root / "qa_records.json").is_file():
        raise BybeError(
            f"QA V2 workspace олдсонгүй: {root}\n"
            "Use --workspace PATH or local-config.json; existing data will NOT be replaced."
        )
    if not (root / "server.py").is_file():
        raise BybeError(f"QA V2 server.py олдсонгүй: {root}")
    return root


def recorded_edits(state):
    if not isinstance(state, dict) or not isinstance(state.get("records"), dict):
        raise BybeError("qa_state_server.json: records object is missing")
    refs = {}
    for clip_id, item in state["records"].items():
        if not isinstance(item, dict):
            continue
        edited = item.get("edited")
        if item.get("choice") == "edited" and not edited:
            raise BybeError(f"{clip_id} edited гэсэн боловч edited зам байхгүй")
        if not edited:
            continue
        expected = f"edits/{clip_id}.wav"
        if edited.replace("\\", "/") != expected:
            raise BybeError(f"Invalid edited path for {clip_id}: {edited}")
        refs[clip_id] = expected
    return refs


def collect_backup(workspace_path):
    state_file = workspace_path / "qa_state_server.json"
    if not state_file.is_file():
        raise BybeError("qa_state_server.json байхгүй: одоогийн QA-г server save хийгээд үз")
    state = read_json(state_file)
    refs = recorded_edits(state)
    files = [workspace_path / "qa_records.json", state_file]
    missing = []
    for clip_id, rel in refs.items():
        file = workspace_path / rel
        if not file.is_file() or file.stat().st_size < 44:
            missing.append((clip_id, rel))
    if missing:
        raise BybeError("Зассан WAV үнэхээр алга: " + "; ".join(f"{id}={path}" for id, path in missing))
    edits_dir = workspace_path / "edits"
    if edits_dir.exists():
        for file in sorted(edits_dir.rglob("*.wav")):
            if file.is_symlink() or not file.resolve().is_relative_to(workspace_path):
                raise BybeError(f"Unsafe WAV path: {file}")
            if file not in files:
                files.append(file)
    return state, refs, files


def cmd_status(args):
    root = workspace(args.workspace)
    state_file = root / "qa_state_server.json"
    print(f"Workspace: {root}")
    if not state_file.is_file():
        print("No current qa_state_server.json (site may still be saving)")
        return
    state = read_json(state_file)
    counts = {}
    for value in state.get("records", {}).values():
        if isinstance(value, dict):
            key = value.get("status", "unspecified")
            counts[key] = counts.get(key, 0) + 1
    print("QA counts:", json.dumps(counts, ensure_ascii=False))
    try:
        _, refs, _ = collect_backup(root)
        print(f"Verified actual edited WAV references: {len(refs)}")
        print("Backup readiness: YES")
    except BybeError as error:
        print(f"Backup readiness: NO — {error}")
        raise


def cmd_backup(args):
    root = workspace(args.workspace)
    state, refs, files = collect_backup(root)
    dest = DATA / "backups"
    dest.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target = dest / f"BYBE_CZECH800_QA_{stamp}.zip"
    temp = dest / f".{target.name}.part"
    manifest = {
        "schema": 1,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "purpose": "Legacy V2 user QA + actual edited WAVs; no original source media",
        "referenced_edited_wav_count": len(refs),
        "qa_record_count": len(state["records"]),
        "files": [],
    }
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=4) as zipout:
            for file in files:
                arc = file.relative_to(root).as_posix()
                zipout.write(file, arcname=arc)
                manifest["files"].append(
                    {"path": arc, "size": file.stat().st_size, "sha256": sha256(file)}
                )
            zipout.writestr(
                "BACKUP_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2)
            )
        with zipfile.ZipFile(temp) as check:
            bad = check.testzip()
            if bad:
                raise BybeError(f"ZIP CRC error: {bad}")
            for file in manifest["files"]:
                if check.getinfo(file["path"]).file_size != file["size"]:
                    raise BybeError(f"Backup mismatch: {file['path']}")
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()
    print(f"BACKUP SUCCESS: {target}")
    print(f"QA records: {manifest['qa_record_count']} | referenced edited WAVs: {len(refs)}")
    print("The original V2 workspace was not changed.")


def cmd_run(args):
    root = workspace(args.workspace)
    print(f"Starting existing QA V2: {root}", flush=True)
    raise SystemExit(subprocess.call([sys.executable, str(root / "server.py")], cwd=root))


def cmd_link_source(args):
    part = str(args.part).zfill(3)
    if not part.isdigit() or len(part) != 3:
        raise BybeError("part must be numeric, e.g. 003")
    file = Path(args.file).expanduser().resolve()
    allowed = {".mkv", ".mp4", ".wav", ".mp3", ".m4a"}
    if not file.is_file() or file.suffix.lower() not in allowed:
        raise BybeError(f"Эх файл олдсонгүй эсвэл формат буруу: {file}")
    mapping = read_json(SOURCE_MAP) if SOURCE_MAP.is_file() else {"schema": 1, "sources": {}}
    st = file.stat()
    mapping["sources"][part] = {
        "path": str(file), "bytes": st.st_size, "mtime_ns": st.st_mtime_ns,
        "sha256": sha256(file),
        "linked_utc": dt.datetime.now(dt.timezone.utc).isoformat()
    }
    atomic_json(SOURCE_MAP, mapping)
    print(f"Linked part {part}: {file.name}, SHA256 {mapping['sources'][part]['sha256']}")
    print(f"Local source registry: {SOURCE_MAP}; source not copied or changed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="BYBE Studio local, non-destructive QA bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "status", "backup"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--workspace", default=None, help="Existing QA V2 folder")
    link = sub.add_parser("link-source")
    link.add_argument("--part", required=True, help="e.g. 003")
    link.add_argument("--file", required=True, help="Existing MKV/MP4/audio file path")
    args = parser.parse_args(argv)
    try:
        {"run": cmd_run, "status": cmd_status, "backup": cmd_backup,
         "link-source": cmd_link_source}[args.command](args)
        return 0
    except (BybeError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
