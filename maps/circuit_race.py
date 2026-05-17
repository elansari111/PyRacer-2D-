"""
circuit_race.py — Course circuit vs IA.

Progression commune : tous les pilotes avancent sur la même piste virtuelle.
Un tour ≈ 50–70 s à vitesse de croisière.
"""

import random
import pygame
import settings as S

# ~50–70 s par tour à vitesse moyenne (speed ≈ 6, 60 FPS)
LAP_LENGTH = 18000.0
PROGRESS_SCALE = 0.48
GAP_TO_PIXELS = 0.09

RIVAL_NAMES = [
    "Vega", "Blaze", "Nova", "Rex", "Kira",
    "Zephyr", "Axel", "Luna", "Bolt", "Storm",
]
RIVAL_COLORS = [
    (255, 80, 80), (255, 140, 0), (200, 80, 255),
    (80, 200, 255), (255, 220, 80), (100, 255, 150),
    (255, 100, 180), (180, 255, 100),
]


def _laps_from_pos(track_pos: float) -> int:
    return int(max(0.0, track_pos) // LAP_LENGTH)


def _lap_pct(track_pos: float) -> float:
    return (max(0.0, track_pos) % LAP_LENGTH) / LAP_LENGTH


class RivalRacer:
    """Pilote IA — avance sur la piste au même rythme que le joueur × pace."""

    def __init__(self, name: str, road_x: int, road_w: int, lane_count: int,
                 skill: float, color: tuple, start_offset: float):
        self.name = name
        self.road_x = road_x
        self.road_w = road_w
        self.lane_count = lane_count
        self.lane_w = max(1, road_w // lane_count)
        self.skill = skill
        self.color = color
        # Position sur la piste (même référentiel que le joueur)
        self.track_pos = start_offset
        self.pace = 0.96 + skill * 0.07 + random.uniform(-0.02, 0.02)
        self.pace = max(0.90, min(1.10, self.pace))
        self.w, self.h = 30, 50
        self.type = 1
        self.passed = False
        self.lane = random.randrange(lane_count)
        self.target_lane = self.lane
        self.x = float(self._lane_x(self.lane))
        self.y = 0.0
        self.speed = 0.0
        self._lane_timer = random.randint(60, 140)
        self._nitro_timer = 0.0
        self._finished = False
        self.finish_time = 0.0

    @property
    def laps_done(self) -> int:
        return _laps_from_pos(self.track_pos)

    def _lane_x(self, lane: int) -> float:
        lane = max(0, min(self.lane_count - 1, lane))
        return self.road_x + self.lane_w * lane + self.lane_w // 2 - self.w // 2

    def update(self, dt: float, player_speed: float, player_track_pos: float,
               player_lane: int, player_x: float, player_y: float):
        if self._finished or player_speed < 0.15:
            return

        nitro = 1.0
        if self._nitro_timer > 0:
            self._nitro_timer -= dt
            nitro = 1.18
        elif random.random() < 0.0008 * self.skill:
            self._nitro_timer = 55.0

        self.track_pos += player_speed * dt * PROGRESS_SCALE * self.pace * nitro

        # Changement de voie (moins fréquent, plus stable)
        self._lane_timer -= dt
        if self._lane_timer <= 0:
            self._lane_timer = random.randint(120, 280)
            if random.random() < 0.22:
                self.target_lane = random.randrange(self.lane_count)
        if self.target_lane != self.lane:
            d = 1 if self.target_lane > self.lane else -1
            self.lane = max(0, min(self.lane_count - 1, self.lane + d))

        self.target_x = self._lane_x(self.lane)
        self.x += (self.target_x - self.x) * 0.06 * dt
        self.x = max(self.road_x, min(self.road_x + self.road_w - self.w, self.x))

        gap = self.track_pos - player_track_pos
        self.y = player_y - gap * GAP_TO_PIXELS
        self.speed = player_speed * self.pace

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) + 3, int(self.y) + 3, self.w - 6, self.h - 6)

    def is_visible(self) -> bool:
        return -100 < self.y < S.SCREEN_H + 100 and not self._finished

    def draw(self, surface: pygame.Surface):
        if not self.is_visible():
            return
        ex, ey = int(self.x), int(self.y)
        pygame.draw.rect(surface, self.color, (ex + 2, ey, self.w - 4, self.h), border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255, 80), (ex + 4, ey + 8, self.w - 8, 10))
        pygame.draw.rect(surface, (255, 40, 40), (ex + 4, ey + self.h - 8, 8, 4))
        pygame.draw.rect(surface, (255, 40, 40), (ex + self.w - 12, ey + self.h - 8, 8, 4))
        if self._nitro_timer > 0:
            pygame.draw.rect(surface, S.C_YELLOW, (ex, ey - 4, self.w, 3))


class CircuitRace:
    """Gestionnaire de course — piste unique, classement par distance parcourue."""

    def __init__(self, level: int, road_x: int, road_w: int, lane_count: int, total_laps: int):
        self.level = level
        self.road_x = road_x
        self.road_w = road_w
        self.lane_count = lane_count
        self.total_laps = total_laps
        self.rivals: list[RivalRacer] = []
        self.player_track_pos = 0.0
        self.race_time = 0.0
        self._finished = False
        self.player_finish_pos = 0
        self.player_finish_time = 0.0
        self._countdown = 120.0
        self._prev_player_laps = 0

    @property
    def player_laps(self) -> int:
        return _laps_from_pos(self.player_track_pos)

    @property
    def player_gap(self) -> float:
        return self.player_track_pos % LAP_LENGTH

    def start(self, rival_count: int, difficulty: float = 1.0):
        self.rivals.clear()
        self.player_track_pos = 0.0
        self._prev_player_laps = 0
        count = min(rival_count, len(RIVAL_NAMES))
        names = random.sample(RIVAL_NAMES, count)
        base_skill = 0.88 + self.level * 0.04 + difficulty * 0.06

        # Grille : tous les rivaux démarrent sur la même ligne que le joueur (offset = 0)
        offsets = [0] * count

        for i, name in enumerate(names):
            skill = base_skill + random.uniform(-0.05, 0.05) - i * 0.015
            skill = max(0.82, min(1.08, skill))
            color = RIVAL_COLORS[i % len(RIVAL_COLORS)]
            self.rivals.append(RivalRacer(
                name, self.road_x, self.road_w, self.lane_count,
                skill, color, offsets[i]))

    def update(self, dt: float, player_speed: float, player_lane: int,
               player_x: float, player_y: float, player_w: int) -> dict:
        result = {
            "grip_mod": 1.0,
            "drs_boost": 1.0,
            "lap": 1,
            "total_laps": self.total_laps,
            "lap_progress": 0.0,
            "race_time": self.race_time,
            "race_finished": False,
            "ranking": [],
            "player_position": 1,
            "countdown": self._countdown,
            "lap_complete": False,
            "drs_active": False,
        }

        if self._countdown > 0:
            self._countdown -= dt
            result["countdown"] = self._countdown
            for r in self.rivals:
                gap = r.track_pos - self.player_track_pos
                r.y = player_y - gap * GAP_TO_PIXELS
                r.x = r._lane_x(r.lane)
            result["ranking"] = self._build_ranking()
            result["lap_progress"] = 0.0
            return result

        self.race_time += dt

        lap_pct = _lap_pct(self.player_track_pos)
        drs_active = 0.38 < lap_pct < 0.62
        drs_mult = 1.15 if drs_active else 1.0

        if player_speed >= 0.2:
            self.player_track_pos += player_speed * dt * PROGRESS_SCALE * drs_mult

        cur_laps = self.player_laps
        lap_done = cur_laps > self._prev_player_laps
        self._prev_player_laps = cur_laps

        finish_line = self.total_laps * LAP_LENGTH
        if self.player_track_pos >= finish_line and not self._finished:
            self._finished = True
            self.player_finish_time = self.race_time
            self._compute_final_positions()

        for r in self.rivals:
            r.update(dt, player_speed, self.player_track_pos,
                     player_lane, player_x, player_y)
            if not r._finished and r.track_pos >= finish_line:
                r._finished = True
                r.finish_time = self.race_time

        ranking = self._build_ranking()
        result["ranking"] = ranking
        result["lap"] = min(cur_laps + 1, self.total_laps)
        result["lap_progress"] = lap_pct
        result["race_finished"] = self._finished
        result["lap_complete"] = lap_done
        result["drs_active"] = drs_active
        result["drs_boost"] = drs_mult
        result["player_position"] = self._player_rank(ranking)
        return result

    def _build_ranking(self) -> list:
        entries = [("Joueur", self.player_track_pos, True)]
        for r in self.rivals:
            entries.append((r.name, r.track_pos, False))
        entries.sort(key=lambda e: -e[1])
        out = []
        for pos, (name, tpos, is_player) in enumerate(entries, 1):
            lap_display = min(_laps_from_pos(tpos) + 1, self.total_laps)
            out.append((name, pos, lap_display, is_player))
        return out

    def _player_rank(self, ranking: list) -> int:
        for _name, pos, _lap, is_player in ranking:
            if is_player:
                return pos
        return 1

    def _compute_final_positions(self):
        self.player_finish_pos = self._player_rank(self._build_ranking())

    def get_visible_rivals(self) -> list:
        return [r for r in self.rivals if r.is_visible()]

    def get_ranking_display(self) -> list:
        return [(n, p, l) for n, p, l, _ in self._build_ranking()]

    def draw_hud_ranking(self, surface: pygame.Surface, ranking: list):
        font = pygame.font.SysFont("consolas", 12, bold=True)
        title = pygame.font.SysFont("consolas", 14, bold=True).render(
            "CLASSEMENT", True, S.C_YELLOW)
        h = 24 + len(ranking) * 22
        pygame.draw.rect(surface, (10, 10, 25, 200), (8, 88, 155, h))
        pygame.draw.rect(surface, (*S.C_YELLOW, 100), (8, 88, 155, h), 1)
        surface.blit(title, (16, 94))
        for i, (name, pos, lap, is_player) in enumerate(ranking[:8]):
            col = S.C_CYAN if is_player else (180, 180, 200)
            if pos == 1:
                col = S.C_YELLOW
            txt = font.render(f"{pos}. {name[:8]:8}  T{lap}", True, col)
            surface.blit(txt, (14, 118 + i * 20))

    def draw_start_lights(self, surface: pygame.Surface):
        cx = S.SCREEN_W // 2
        for i, lit in enumerate([self._countdown < 80, self._countdown < 40, self._countdown <= 0]):
            c = (255, 50, 50) if lit and self._countdown > 0 else (
                (50, 255, 80) if self._countdown <= 0 else (60, 60, 70))
            pygame.draw.circle(surface, c, (cx - 60 + i * 60, 120), 18)
