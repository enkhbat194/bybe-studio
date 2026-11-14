#!/usr/bin/env python3
"""Import Czech800 PART004 WAV bundle into BYBE local-only storage.

Does not overwrite existing V2 or source files. Extracts exactly 27*4 WAV files
and data.json timing as unverified source anchors. Safe with untrusted ZIP paths.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import wave
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bybe

ROLES = ("word_normal", "word_slow", "sentence_normal", "sentence_slow")
BASE = bybe.DATA / "imports"
ACTIVE = BASE / "active.json"


def import_004(archive_path: Path):
    archive_path = archive_path.expanduser().resolve()
    if not archive_path.is_file():
        raise bybe.BybeError("004 ZIP файл олдсонгүй: " + str(archive_path))
    digest = bybe.sha256(archive_path)[:12]
    folder_name = "part004_" + digest
    target = BASE / folder_name
    BASE.mkdir(parents=True, exist_ok=True)
    rows = []
    if target.exists():
        existing = target / "records.json"
        if not existing.is_file():
            raise bybe.BybeError("Өмнө импортолсон хэсэг эвдэрсэн; overwrite хийхгүй")
        rows = bybe.read_json(existing)["records"]
    else:
        staging = Path(tempfile.mkdtemp(prefix=".bybe-import-", dir=BASE))
        try:
            with zipfile.ZipFile(archive_path, "r") as src:
                names = src.namelist()
                defs = [n for n in names if n.endswith("/data.json")]
                if len(defs) != 27:
                    raise bybe.BybeError("004 ZIP-д 27 data.json байх ёстой, олдсон: " + str(len(defs)))
                found = set()
                for name in defs:
                    metadata = json.loads(src.read(name))
                    word_no = int(metadata["word_no"])
                    if not 95 <= word_no <= 121 or word_no in found:
                        raise bybe.BybeError("Unexpected/duplicate word number: " + str(word_no))
                    found.add(word_no)
                    word = str(metadata["czech_word"]).strip()
                    timing = metadata.get("clip_times_part004_local")
                    if not isinstance(timing, dict):
                        raise bybe.BybeError("Missing source boundaries for " + str(word_no))
                    for role in ROLES:
                        clip_name = name.removesuffix("data.json") + role + ".wav"
                        if clip_name not in names:
                            raise bybe.BybeError("Missing WAV: " + clip_name)
                        start, end = map(float, timing[role])
                        if not (0 <= start < end < 4000):
                            raise bybe.BybeError("Invalid boundary: " + clip_name)
                        raw = src.read(clip_name)
                        with wave.open(io.BytesIO(raw), "rb") as audio:
                            if (audio.getnchannels() not in (1,2) or audio.getsampwidth()!=2
                                    or audio.getnframes() < 100):
                                raise bybe.BybeError("Invalid PCM16 WAV: " + clip_name)
                        item_id = "P4-" + str(word_no).zfill(3) + "-" + role
                        relative = "imports/" + folder_name + "/audio/" + str(word_no).zfill(4) + "/" + role + ".wav"
                        outfile = staging / "audio" / str(word_no).zfill(4) / (role + ".wav")
                        outfile.parent.mkdir(parents=True, exist_ok=True)
                        outfile.write_bytes(raw)
                        rows.append({
                            "id": item_id, "set": "004", "wordNo": word_no,
                            "word": word, "role": role, "src": relative,
                            "storage": "bybe", "status": "pending",
                            "reference": word if role.startswith("word") else str(metadata.get("czech_sentence") or "").strip(),
                            "english_reference": str((metadata.get("english_word") if role.startswith("word") else metadata.get("english_sentence")) or "").strip(),
                            "source_screen_sec": metadata.get("reference_screen_sec"),
                            "textVerified": False, "qa": "REVIEW_REQUIRED",
                            "timing": json.dumps([[4, start, end]]),
                            "source_evidence": str(metadata.get("analysis_method") or "part004 data.json; not independently verified"),
                            "sha256": hashlib.sha256(raw).hexdigest()
                        })
                if found != set(range(95, 122)) or len(rows) != 108:
                    raise bybe.BybeError("004 word coverage/count mismatch")
            bybe.atomic_json(staging / "records.json", {"schema": 1, "part": "004", "records": rows})
            os.replace(staging, target)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    # Switch pointer only after files and metadata are present; previous import survives.
    active = bybe.read_json(ACTIVE) if ACTIVE.exists() else {"schema": 1}
    active["004"] = folder_name
    bybe.atomic_json(ACTIVE, active)
    print(f"Imported PART004: {len(rows)} WAV records in {target}")
    print("All 108 are REVIEW_REQUIRED. 004 media has NOT been added to public GitHub.")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safely add 004/95–121 WAV to local BYBE Studio")
    parser.add_argument("--zip", required=True, help="Path to 004 WAV ZIP")
    args = parser.parse_args()
    try:
        import_004(Path(args.zip))
    except (bybe.BybeError, ValueError, OSError, json.JSONDecodeError,
            KeyError, zipfile.BadZipFile, wave.Error) as error:
        print("IMPORT FAILED: " + str(error), file=sys.stderr)
        raise SystemExit(2)
