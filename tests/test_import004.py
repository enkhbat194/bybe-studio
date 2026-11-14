import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave
import zipfile

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_part004_test", HERE / "scripts" / "import_part004.py")
imp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(imp)


def audio_bytes():
    file = io.BytesIO()
    with wave.open(file, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\0" * 44100)
    return file.getvalue()


class Part004ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / "part004.zip"
        self.base = self.root / "imports"
        self.active = self.base / "active.json"

    def make_zip(self, omit_last=False):
        wav = audio_bytes()
        with zipfile.ZipFile(self.archive, "w") as z:
            for i in range(95, 122):
                prefix = f"Czech800_Part004/{i:04d}_word/"
                metadata = {
                    "word_no": i,
                    "czech_word": f"word_{i}",
                    "clip_times_part004_local": {
                        role: [float(i), float(i) + 2.5] for role in imp.ROLES
                    }
                }
                z.writestr(prefix + "data.json", json.dumps(metadata))
                for role in imp.ROLES:
                    if omit_last and i == 121 and role == "sentence_slow":
                        continue
                    z.writestr(prefix + role + ".wav", wav)

    def test_import_108_and_idempotence(self):
        self.make_zip()
        with patch.object(imp, "BASE", self.base), patch.object(imp, "ACTIVE", self.active):
            dest = imp.import_004(self.archive)
            data = json.loads((dest / "records.json").read_text())
            self.assertEqual(len(data["records"]), 108)
            self.assertEqual(data["records"][0]["status"], "pending")
            self.assertTrue((dest / "audio" / "0095" / "word_normal.wav").exists())
            self.assertEqual(imp.import_004(self.archive), dest)

    def test_missing_clip_fails_without_activating(self):
        self.make_zip(omit_last=True)
        with patch.object(imp, "BASE", self.base), patch.object(imp, "ACTIVE", self.active):
            with self.assertRaises(imp.bybe.BybeError):
                imp.import_004(self.archive)
            self.assertFalse(self.active.exists())


if __name__ == "__main__":
    unittest.main()
