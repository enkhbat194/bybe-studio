# PROJECT MAP — BYBE Studio

Repository: enkhbat194/bybe-studio (public)
Stage: bootstrap v0.2 + isolated V3 pilot
Design: GitHub source code + Windows-local runtime/workspace + optional MCP and cloud backup.

## Current code
- scripts/bybe.py — verifies V2 QA state and actual edited WAV references, creates complete local QA backups, registers source media by hash, launches V2.
- studio/server.py — isolated localhost 8766 source-linked wave extraction and append-only candidate WAV revisions, 6-point confirmation and combined backup.
- studio/index.html — independent offline waveform editor, draggable boundaries and playback.
- START_BYBE_V3_PILOT.bat — pilot entry point (does not replace V2).
- START_BYBE.bat — double-click Windows entry point.
- .gitignore — prevents locally generated data, media and QA records from going into Git.
- docs/* — architecture, usage and safe integration scope.
- tests/* — backup and missing-WAV validation.
- .github/workflows/ci.yml — stdlib unit-test workflow.

## Existing local assets (NOT committed)
- Czech800_QA_STUDIO_V2: old interactive Chrome waveform editor, 003 + new 30.
- D:\Czech800\raw: source files (actual names must be verified and linked locally).
- 003 136 WAV: edited 8 clips, but final ending phoneme QA disputed.
- 004 108 WAV: not imported into existing UI, human QA outstanding.
- 005 new 30: 118 MP3, two missing sentence clips for klidná.
- 004/005 edge: #122 květina needs manual source-linked reconstruction.

## Next exact milestone (not complete yet)
Run the isolated V3 pilot on real #61 knír, #63 DVD přehrávač, #94 zlatá media. Fix any pilot defects; then migrate JSON revision storage to SQLite and create a source linking GUI. Do not switch production from V2 until user confirms all three round-trip tests.

## Acceptance criteria
1. User selects clip; source video auto-resolves to a verified absolute time interval.
2. Waveform includes preceding and following context, with initial markers loaded.
3. Adjusting start AND end generates a NEW revision; previous WAV survives.
4. User listens to first sound / last sound / whole phrase and confirms language, text and role.
5. Backups include actual generated WAV bytes and QA database; restore and audit pass.
6. All works offline and without Codex.
7. Media and private QA data never appear in the public Git repository.
