# BYBE Studio — architecture and design contract

## Connected in bootstrap v0

- GitHub: source code, documentation and automated checks. The repository is PUBLIC: no private QA state, video files or audio are committed.
- Windows local workspace: an existing Czech800 QA Studio V2 can be discovered at D:\Czech800\Czech800_QA_STUDIO_V2_CHROME_EDITOR\Czech800_QA_STUDIO_V2, by BYBE_LEGACY_QA environment variable, or local-config.json.
- START_BYBE.bat launches the existing V2 localhost site without replacing it.
- scripts/bybe.py implements workspace diagnostics, consistent backup and source-media registration.
- Source media registry is stored ONLY locally, never in the public repository.

## Non-negotiable rules

1. Never modify original MKV/MP4/WAV/MP3 media.
2. Every clip needs stable clip_id, source_id, absolute timestamps, language, speaker, role, Czech reference text, revision and QA status.
3. Video transitions, OCR/SRT anchors, audio speech boundaries and ASR timestamps are different evidence.
4. VAD silence detection cannot distinguish Czech from English; syllable pauses do not mean word boundaries.
5. Technical QA, content QA and human first/last/full speech QA are separate.
6. Changing one audio boundary invalidates the whole-clip approval; recheck beginning AND ending.
7. APP_READY is forbidden without verified selected WAV, expected language, correct text/role and whole-clip QA.
8. Audio revisions are append-only and backups must include real WAV bytes, not merely JSON file references.
9. Keep public GitHub free of user private paths/data, binary source materials and API secrets.
10. All core editing, export and backup functions must work without Codex tokens or internet.

## Planned stages (NOT implemented yet)

- V3 pilot: local JSON revision index, FFmpeg context extraction, waveform with prefilled draggable absolute boundaries, nondestructive WAV output (implemented). Next: replace pilot JSON revision index with transactional SQLite, improve file restore and source manager UI.
- V4: OCR + Czech/English ASR via independent Whisper and Qwen3 signals, role classifier, contextual speech-end QA and user review queue.
- V5: optional local MCP adapter for Codex and other agents with read-only default; authorized candidate creation and gated QA approval.
- Optional: Drive for desktop sync folder backup; API upload only with explicit connection and user authorization.

## Verified chunk inventory

- Part 003: #61–94 = 34 words, 136 WAV, 8 manually edited; final phonetic endings QA is still disputed.
- Part 004: #95–121 = 27 words, 108 WAV; needs human QA.
- #122 květina: crosses 004/005 boundary; needs special review.
- Part 005: #123–152 = 30 words, 118/120 MP3; klidná has 2 missing sentence files.

A manifest's video_num is not automatically equal to the MKV chunk number. Never infer source mappings from that column alone.
