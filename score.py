# ============================================================
#  PyRacer: Ultimate Neon Highway
#  score.py — Logique de score, multiplicateurs, streak
# ============================================================

import json
import os
import settings as S


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
        self.total_score = 0.0   # cumulé sur tous les niveaux joués

        self.streak      = 0
        self.max_streak  = 0

        self.overtakes   = 0
        self.bonuses_col = 0

        # High scores (un par niveau, chargés depuis JSON)
        self.hi_scores   = [0, 0, 0]
        self._load()

    # ----------------------------------------------------------
    def reset_level(self):
        """Réinitialise le score courant en début de niveau."""
        self.score       = 0.0
        self.streak      = 0
        self.max_streak  = 0
        self.overtakes   = 0
        self.bonuses_col = 0

    def commit_level(self, level: int):
        """
        Clôture un niveau : sauvegarde le hi-score si battu
        et cumule dans total_score.
        """
        self.total_score += self.score
        if int(self.score) > self.hi_scores[level]:
            self.hi_scores[level] = int(self.score)
            self._save()

    # ----------------------------------------------------------
    def add_time(self, speed: float, dt: float, nitro_active: bool):
        """Ajoute les points de survie chaque frame."""
        pts = speed * 0.04 * dt
        if nitro_active:
            pts *= S.NITRO_SCORE_MULT
        if self.streak >= S.STREAK_MIN:
            pts *= 1 + self.streak * 0.05
        self.score += pts

    def add_overtake(self, nitro_active: bool) -> int:
        """Enregistre un dépassement et retourne les points gagnés."""
        if nitro_active:
            pts = S.SCORE_OVERTAKE_NITRO
        else:
            pts = S.SCORE_OVERTAKE

        self.streak   += 1
        self.max_streak = max(self.max_streak, self.streak)
        self.overtakes += 1

        # Bonus de streak
        if self.streak >= S.STREAK_MIN:
            pts += self.streak * 10

        # Multiplicateur streak
        if self.streak >= S.STREAK_MIN:
            pts = int(pts * (1 + self.streak * 0.05))

        self.score += pts
        return pts

    def add_bonus(self, score_add: int):
        """Ajoute les points de collecte de bonus."""
        self.score       += score_add
        self.bonuses_col += 1
    
    def add(self, pts: int, near_miss: bool = False):
        """Ajoute des points directement (pour near-miss et autres bonus)."""
        self.score += pts

    def break_streak(self):
        """Réinitialise le streak (collision)."""
        self.streak = 0

    # ----------------------------------------------------------
    def get_display(self) -> int:
        return int(self.score)

    def get_hi(self, level: int) -> int:
        return self.hi_scores[level]

    def is_new_record(self, level: int) -> bool:
        return int(self.score) >= self.hi_scores[level] and self.score > 0

    # ----------------------------------------------------------
    def _load(self):
        if os.path.exists(S.SCORE_FILE):
            try:
                with open(S.SCORE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.hi_scores = data.get("hi_scores", [0, 0, 0])
            except (json.JSONDecodeError, KeyError):
                self.hi_scores = [0, 0, 0]

    def _save(self):
        try:
            with open(S.SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump({"hi_scores": self.hi_scores}, f, indent=2)
        except OSError:
            pass   # Pas bloquant si l'écriture échoue
