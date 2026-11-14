import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bybe_pilot_test", HERE / "studio" / "server.py")
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


class SourceBoundaryTests(unittest.TestCase):
    def test_exact_single_part_interval(self):
        part, start, end = pilot.times({"timing": "[[3, 58.56, 59.55]]", "set": "003"})
        self.assertEqual(part, "003")
        self.assertAlmostEqual(start, 58.56)
        self.assertAlmostEqual(end, 59.55)

    def test_new30_is_explicit_part005(self):
        part, start, end = pilot.times(
            {"set": "new30", "timing": "16:20.43 – 16:21.53 (эх manifest)"}
        )
        self.assertEqual((part, round(start, 2), round(end, 2)),
                         ("005", 980.43, 981.53))

    def test_cross_part_must_not_guess(self):
        with self.assertRaises(ValueError):
            pilot.times({"timing": "[[4, 1033.0, 1036.0], [5, 0.0, 1.0]]"})

    def test_unlinked_source_must_fail(self):
        with patch.object(pilot, "registry", return_value={}):
            with self.assertRaises(ValueError):
                pilot.source_for({"timing": "[[3, 58.56, 59.55]]"})

    def test_six_independent_acceptance_checks(self):
        self.assertEqual(len(pilot.CHECKS), 6)
        self.assertIn("end_heard", pilot.CHECKS)
        self.assertIn("language_correct", pilot.CHECKS)


if __name__ == "__main__":
    unittest.main()
