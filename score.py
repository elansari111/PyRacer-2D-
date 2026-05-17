# ============================================================
#  PyRacer: Ultimate Neon Highway
#  score.py — Logique de score, multiplicateurs, streak
# ============================================================

import json
import os
import settings as S
from maps.map_config import score_key


DEFAULT_CONFIG = {
    "version": 2,
    "hi_scores": {},       # "city_1": 1234
    "legacy_levels": [0, 0, 0],  # compat ancien format
    "unlocked": {"city_1": True, "highway_1": True, "circuit_1": True},
}


class ScoreManager:
    """
    Hiérarchie de score :
      1. Dépassement en Nitro  → +150 pts  (priorité max)
      2. Streak actif          → ×(1 + streak×0.05) sur chaque pt
      3. Dépassement normal    → +50 pts
      4. Collecte de bonus     → +100 pts
      5. Survie au fil du temps → +speed×0.04 pts/frame
    """

    def __init__(self):
        self.score       = 0.0
        self.total_score = 0.0

        self.streak      = 0
        self.max_streak  = 0

        self.overtakes   = 0
        self.bonuses_col = 0

        self.hi_scores: dict = {}
        self.unlocked: dict = {}
        self.hi_scores_legacy = [0, 0, 0]
        self._current_map_key: str | None = None
        self._load()

    def set_map_level(self, map_id: str, level: int):
        """Contexte courant pour sauvegarde hi-score."""
        self._current_map_key = score_key(map_id, level)

    def reset_level(self):
        self.score       = 0.0
        self.streak      = 0
        self.max_streak  = 0
        self.overtakes   = 0
        self.bonuses_col = 0

    def commit_level(self, level: int = None, map_id: str = None, map_level: int = None):
        """Clôture un niveau et sauvegarde le record."""
        self.total_score += self.score
        key = self._current_map_key
        if map_id and map_level:
            key = score_key(map_id, map_level)
        if key:
            prev = self.hi_scores.get(key, 0)
            if int(self.score) > prev:
                self.hi_scores[key] = int(self.score)
            # Débloquer niveau suivant
            parts = key.rsplit("_", 1)
            if len(parts) == 2:
                mid, lv = parts[0], int(parts[1])
                if lv < 3:
                    self.unlocked[f"{mid}_{lv + 1}"] = True
            self._save()
        elif level is not None and 0 <= level < 3:
            if int(self.score) > self.hi_scores_legacy[level]:
                self.hi_scores_legacy[level] = int(self.score)
                self._save()

    def add_time(self, speed: float, dt: float, nitro_active: bool):
        pts = speed * 0.04 * dt
        if nitro_active:
            pts *= S.NITRO_SCORE_MULT
        if self.streak >= S.STREAK_MIN:
            pts *= 1 + self.streak * 0.05
        self.score += pts

    def add_overtake(self, nitro_active: bool) -> int:
        if nitro_active:
            pts = S.SCORE_OVERTAKE_NITRO
        else:
            pts = S.SCORE_OVERTAKE

        self.streak   += 1
        self.max_streak = max(self.max_streak, self.streak)
        self.overtakes += 1

        if self.streak >= S.STREAK_MIN:
            pts += self.streak * 10
            pts = int(pts * (1 + self.streak * 0.05))

        self.score += pts
        return pts

    def add_bonus(self, score_add: int):
        self.score       += score_add
        self.bonuses_col += 1

    def add(self, pts: int, near_miss: bool = False):
        self.score += pts

    def break_streak(self):
        self.streak = 0

    def get_display(self) -> int:
        return int(self.score)

    def get_hi(self, level: int) -> int:
        return self.hi_scores_legacy[level]

    def get_hi_map(self, map_id: str, level: int) -> int:
        return self.hi_scores.get(score_key(map_id, level), 0)

    def is_new_record(self, level: int = None, map_id: str = None, map_level: int = None) -> bool:
        if map_id and map_level:
            return int(self.score) >= self.get_hi_map(map_id, map_level) and self.score > 0
        if level is not None:
            return int(self.score) >= self.hi_scores_legacy[level] and self.score > 0
        return False

    def is_level_unlocked(self, map_id: str, level: int) -> bool:
        return self.unlocked.get(score_key(map_id, level), level == 1)

    def _load(self):
        if not os.path.exists(S.SCORE_FILE):
            self._apply_defaults()
            return
        try:
            with open(S.SCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, TypeError):
            self._apply_defaults()
            self._save()
            return

        version = data.get("version", 1)
        if version >= 2:
            self.hi_scores = dict(data.get("hi_scores", {}))
            self.unlocked = dict(data.get("unlocked", DEFAULT_CONFIG["unlocked"]))
            self.hi_scores_legacy = list(data.get("legacy_levels", [0, 0, 0]))
        else:
            legacy = data.get("hi_scores", [0, 0, 0])
            self.hi_scores_legacy = list(legacy) if isinstance(legacy, list) else [0, 0, 0]
            self._migrate_legacy()

    def _migrate_legacy(self):
        """Migre hi_scores [n0,n1,n2] vers city_1, highway_1, circuit_1."""
        maps = ["city", "highway", "circuit"]
        for i, mid in enumerate(maps):
            if i < len(self.hi_scores_legacy):
                self.hi_scores[score_key(mid, 1)] = self.hi_scores_legacy[i]
        for mid in maps:
            self.unlocked.setdefault(f"{mid}_1", True)

    def _apply_defaults(self):
        cfg = DEFAULT_CONFIG.copy()
        self.hi_scores = dict(cfg["hi_scores"])
        self.unlocked = dict(cfg["unlocked"])
        self.hi_scores_legacy = list(cfg["legacy_levels"])

    def _save(self):
        payload = {
            "version": 2,
            "hi_scores": self.hi_scores,
            "unlocked": self.unlocked,
            "legacy_levels": self.hi_scores_legacy,
        }
        try:
            with open(S.SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except OSError:
            pass
