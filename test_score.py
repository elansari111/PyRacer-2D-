"""Tests unitaires — score.ScoreManager."""

import json
import os
import tempfile
import unittest

import settings as S
from score import ScoreManager, DEFAULT_CONFIG


class TestScoreManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self.tmp.close()
        self._orig_file = S.SCORE_FILE
        S.SCORE_FILE = self.tmp.name

    def tearDown(self):
        S.SCORE_FILE = self._orig_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_default_config_version(self):
        self.assertEqual(DEFAULT_CONFIG["version"], 2)

    def test_add_overtake_increases_score(self):
        mgr = ScoreManager()
        mgr.reset_level()
        pts = mgr.add_overtake(False)
        self.assertGreater(pts, 0)
        self.assertGreater(mgr.score, 0)

    def test_save_load_v2(self):
        mgr = ScoreManager()
        mgr.hi_scores["city_1"] = 999
        mgr._save()
        mgr2 = ScoreManager()
        self.assertEqual(mgr2.hi_scores.get("city_1"), 999)

    def test_corrupt_json_fallback(self):
        with open(self.tmp.name, "w", encoding="utf-8") as f:
            f.write("{invalid")
        mgr = ScoreManager()
        self.assertIn("city_1", mgr.unlocked)


if __name__ == "__main__":
    unittest.main()
