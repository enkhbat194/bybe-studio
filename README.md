# BYBE Studio

**Local-first, non-destructive audio/video QA workstation.** Windows + Chrome + Python 3.11. Intended for Czech800: four audio roles per Czech word (normal word, slow/syllabic word, normal example sentence, slow/syllabic example sentence).

> **Status: bootstrap v0.1.** This repository currently contains a working **launcher, backup/diagnostics and source registry bridge for existing Czech800 QA Studio V2**. It does NOT yet include the V2 web editor's code, media files, integrated Source Manager UI, OCR/ASR, or a working MCP server. These are the next implementation phases. No claims of finished automated audio QA.

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

## Register original source videos without copying them

```bat
py -3.11 scripts\bybe.py link-source --part 003 --file "D:\Czech800\raw\YOUR_003.mkv"
py -3.11 scripts\bybe.py link-source --part 004 --file "D:\Czech800\raw\YOUR_004.mkv"
py -3.11 scripts\bybe.py link-source --part 005 --file "D:\Czech800\raw\YOUR_005.mkv"
```

Replace YOUR_003.mkv with your *actual* filenames. The tool validates file presence and saves its SHA-256 to `local_data/source_map.json`. It does not modify source media.

## Architecture / roadmap

- [Architecture and safeguards](docs/ARCHITECTURE.md)
- [Монгол заавар](docs/WORKFLOW_MN.md)
- [MCP integration plan](docs/MCP_PLAN.md)
- [Open source dependencies and licensing](docs/OPEN_SOURCE.md)
- [Current project map](docs/PROJECT_MAP.md)

**Public repository:** Never commit MKV/MP4/WAV/MP3 recordings, personal QA exports, Drive credentials, API keys, `edits/`, `local_data/`, or source paths. This code works offline; Codex tokens are not required for basic editing or backups. No automatic Google Drive sync is claimed.

## Tests

```bat
py -3.11 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE) for code authored in this repository. AudioMass, WaveSurfer.js, FFmpeg, Whisper/Qwen3 and other external tools are **not currently vendored**; each retains its own license and must be reviewed before integration.
