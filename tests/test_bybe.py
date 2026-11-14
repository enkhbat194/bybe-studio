import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bybe.py"
spec = importlib.util.spec_from_file_location("bybe_test", SCRIPT)
bybe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bybe)


def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(b"\0\0" * 44100)
    return buffer.getvalue()


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "legacy"
        self.root.mkdir()
        (self.root / "server.py").write_text("# mocked server", encoding="utf-8")
        (self.root / "qa_records.json").write_text('{"records":[]}', encoding="utf-8")

    def write_state(self, item):
        (self.root / "qa_state_server.json").write_text(
            json.dumps({"schema": 2, "records": {"P3-061-word_slow": item}}),
            encoding="utf-8"
        )

    def test_missing_edited_wav_is_fatal(self):
        self.write_state({"choice": "edited", "edited": "edits/P3-061-word_slow.wav", "status": "approved"})
        with self.assertRaises(bybe.BybeError):
            bybe.collect_backup(self.root)

    def test_real_edited_wav_is_included(self):
        self.write_state({"choice": "edited", "edited": "edits/P3-061-word_slow.wav", "status": "approved"})
        (self.root / "edits").mkdir()
        (self.root / "edits" / "P3-061-word_slow.wav").write_bytes(wav_bytes())
        state, refs, files = bybe.collect_backup(self.root)
        self.assertEqual(len(refs), 1)
        self.assertTrue(any(p.name == "P3-061-word_slow.wav" for p in files))
        self.assertEqual(state["records"]["P3-061-word_slow"]["status"], "approved")

    def test_missing_reference_for_edited_choice_is_fatal(self):
        self.write_state({"choice": "edited", "status": "approved"})
        with self.assertRaises(bybe.BybeError):
            bybe.collect_backup(self.root)

    def test_path_escape_is_rejected(self):
        self.write_state({"choice": "edited", "edited": "edits/../something.wav"})
        with self.assertRaises(bybe.BybeError):
            bybe.collect_backup(self.root)


if __name__ == "__main__":
    unittest.main()
