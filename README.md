# BYBE Studio

**Local-first, non-destructive audio/video QA workstation.** Windows + Chrome + Python 3.11. Intended for Czech800: four audio roles per Czech word (normal word, slow/syllabic word, normal example sentence, slow/syllabic example sentence).

> **Status: BYBE bootstrap v0.2 + V3 isolated pilot.** Current repo includes the V2 launcher/backup bridge and a separate source-linked waveform editor pilot. V3 runs on 127.0.0.1:8766 and creates immutable WAV candidates; it does not overwrite V2. No claim of completed content QA, OCR/ASR, MCP or Drive uploads.

## Windows quick start

1. Download/clone this repository to a local folder.
2. Keep your current QA V2 folder unchanged at:
   `D:\Czech800\Czech800_QA_STUDIO_V2_CHROME_EDITOR\Czech800_QA_STUDIO_V2`
3. Double-click **START_BYBE.bat**. The existing V2 should open at <http://127.0.0.1:8765/>.
4. To check that your manually edited WAV files are actually present:

   ```bat
   py -3.11 scripts\bybe.py status
   ```

5. To make a **single validated backup ZIP** containing *both QA JSON and all actual edited WAVs*:

   ```bat
   py -3.11 scripts\bybe.py backup
   ```

   Output: `local_data/backups/BYBE_CZECH800_QA_*.zip` (not in Git).

If V2 is stored elsewhere, create `local-config.json` next to this README:

```json
{"legacy_workspace": "D:\\Czech800\\Czech800_QA_STUDIO_V2_CHROME_EDITOR\\Czech800_QA_STUDIO_V2"}
```

## V3 waveform editor pilot (separate from V2)

Once your V2 workspace exists and you have registered the matching source videos using the commands below, double-click **START_BYBE_V3_PILOT.bat** or run:

```bat
py -3.11 studio\server.py
```

Open <http://127.0.0.1:8766/>. This pilot reads the old V2 manifest and QA state, displays original WAV, retrieves a short context from the linked MKV via **FFmpeg**, preloads start/end boundaries, lets you drag both edges, saves an immutable WAV candidate under `local_data/revisions/`, and requires six explicit human checks for approval. It does **not** rewrite the old WAV or V2 QA state.

**Requires FFmpeg/ffprobe available on Windows PATH** for source extraction. A missing or cross-part source is shown as an error rather than silently guessing.

## Register original source videos without copying them

```bat
py -3.11 scripts\bybe.py link-source --part 003 --file "D:\Czech800\raw\YOUR_003.mkv"
py -3.11 scripts\bybe.py link-source --part 004 --file "D:\Czech800\raw\YOUR_004.mkv"
py -3.11 scripts\bybe.py link-source --part 005 --file "D:\Czech800\raw\YOUR_005.mkv"
```

Replace YOUR_003.mkv with your *actual* filenames. The tool validates file presence and saves its SHA-256 to `local_data/source_map.json`. It does not modify source media. Do not assume the source chunk can be inferred from the manifest's video_num field.

## Architecture / roadmap

- [Architecture and safeguards](docs/ARCHITECTURE.md)
- [Монгол заавар](docs/WORKFLOW_MN.md)
- [MCP integration plan](docs/MCP_PLAN.md)
- [Open source dependencies and licensing](docs/OPEN_SOURCE.md)
- [Current project map](docs/PROJECT_MAP.md)

**Public repository:** Never commit MKV/MP4/WAV/MP3 recordings, personal QA exports, Drive credentials, API keys, `edits/`, `local_data/`, or source paths. This code works offline; Codex tokens are not required for basic editing or backups. No automatic Google Drive sync or MCP is claimed. The public repo contains no private media.

## Tests

```bat
py -3.11 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE) for code authored in this repository. AudioMass, WaveSurfer.js, FFmpeg, Whisper/Qwen3 and other external tools are **not currently vendored**; each retains its own license and must be reviewed before integration.
