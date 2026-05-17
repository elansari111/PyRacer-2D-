"""
circuit_map.py — Carte Circuit (course vs IA).

Rôle: Délègue à CircuitRace pour la course.
Paramètres: level 1-3.
Dépendances: circuit_race, map_config, settings.
"""

import pygame
import settings as S
from maps.map_config import MapConfig, get_map_definition
from maps.circuit_race import CircuitRace, LAP_LENGTH


class CircuitMap:
    """
    Circuit — course contre rivaux IA.

    Niveau 1: 3 tours, 2 rivaux
    Niveau 2: 5 tours, 5 rivaux, usure pneus
    Niveau 3: 7 tours, 8 rivaux
    """

    def __init__(self, level: int, road_x: int, road_w: int, lane_count: int = 3):
        self.level = max(1, min(3, level))
        self.defn = get_map_definition(MapConfig.CIRCUIT, self.level)
        self.road_x = road_x
        self.road_w = road_w
        self.lane_count = lane_count
        self.total_laps = self.defn.extra.get("laps", 3)
        rival_counts = {1: 2, 2: 5, 3: 8}
        self.race = CircuitRace(
            self.level, road_x, road_w, lane_count, self.total_laps)
        self.race.start(rival_counts.get(self.level, 3))
        self.tires_wear = self.defn.extra.get("tire_wear", False)
        self._grip = 1.0

    def update(self, dt: float, speed: float, player_y: float,
               player_lane: int = 1, player_x: float = 0,
               player_w: int = 36) -> dict:
        if self.tires_wear:
            self._grip = max(0.45, self._grip - 0.0006 * speed * dt)

        result = self.race.update(
            dt, speed, player_lane, player_x, player_y, player_w)
        result["grip_mod"] = self._grip
        return result

    @property
    def _race_finished(self) -> bool:
        return self.race._finished

    @property
    def current_lap(self) -> int:
        return min(self.race.player_laps + 1, self.total_laps)

    @property
    def lap_progress(self) -> float:
        from maps.circuit_race import LAP_LENGTH
        return (self.race.player_track_pos % LAP_LENGTH) / LAP_LENGTH

    def get_rivals(self):
        return self.race.get_visible_rivals()

    def get_ranking_display(self):
        return self.race.get_ranking_display()

    def draw_decor(self, surface: pygame.Surface, scroll: float):
        W = surface.get_width()
        pygame.draw.rect(surface, (35, 38, 50), (0, S.SCREEN_H - 48, W, 48))
        for i in range(10):
            x = 20 + i * (W // 10)
            pygame.draw.rect(surface, (55, 70, 95), (x, 70, 55, 35))
            pygame.draw.rect(surface, S.C_YELLOW, (x + 4, 75, 47, 6))
        pygame.draw.rect(surface, (80, 90, 110),
                         (self.road_x - 6, 0, 6, S.SCREEN_H))
        pygame.draw.rect(surface, (80, 90, 110),
                         (self.road_x + self.road_w, 0, 6, S.SCREEN_H))
        line_y = int((scroll * 0.5) % 80)
        for y in range(-80, S.SCREEN_H, 80):
            pygame.draw.line(surface, (255, 255, 255, 40),
                             (self.road_x, y + line_y),
                             (self.road_x + self.road_w, y + line_y), 2)

    def draw_race_ui(self, surface: pygame.Surface, race_state: dict):
        if race_state.get("countdown", 0) > 0:
            self.race.draw_start_lights(surface)
            font = pygame.font.SysFont("orbitron,consolas", 48, bold=True)
            n = max(1, int(race_state["countdown"] / 30) + 1)
            if race_state["countdown"] <= 15:
                t = font.render("GO!", True, (80, 255, 120))
            else:
                t = font.render(str(n), True, S.C_YELLOW)
            surface.blit(t, t.get_rect(center=(S.SCREEN_W // 2, 200)))
        self.race.draw_hud_ranking(surface, race_state.get("ranking", []))
