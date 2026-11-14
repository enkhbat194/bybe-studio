# Open-source foundations — selection notes

Existing independent OSS projects:

- AudioMass: https://github.com/pkalogiros/AudioMass — MIT licensed browser audio editor. Good reference for editing UI, but its editor is **not** part of this repository yet. Preserve notices if importing it.
- WaveSurfer.js: https://github.com/katspaugh/wavesurfer.js — BSD-3-Clause; useful for waveform regions and zoom. It does not by itself encode, write or version WAV files.
- Label Studio: https://github.com/HumanSignal/label-studio — Apache-2.0; broader labeling/QA platform, too heavyweight to require for a local-first desktop pilot.
- FFmpeg: https://ffmpeg.org/ — optional external binary used for media decoding and sample-accurate extractions. Comply with the license of the binary distribution actually used.
- Whisper/Qwen3-ASR: model licenses and Czech-language timing capabilities vary. Model output must not be confused with proof of clip integrity.

Decision: BYBE Studio begins with existing locally running V2 (no rewrite and no media copied to public Git), then adds source-linked non-destructive editor and optional automation. Before importing AudioMass wholesale, run a compatible proof-of-concept and retain required license attribution.

**Nothing in this list is already installed or integrated merely because a link appears here.**
