"""
city_map.py — Logique carte Ville.

Rôle: Contraintes urbaines (feux, piétons, ralentisseurs).
Paramètres: level 1-3, road geometry.
Dépendances: map_config, settings.
"""

import random
import pygame
from dataclasses import dataclass, field
from typing import List, Tuple

import settings as S
from maps.map_config import MapConfig, get_map_definition


@dataclass
class TrafficLight:
    """Feu rouge sur la route."""
    x: float
    y: float
    state: str = "red"  # red, green
    timer: float = 0.0


@dataclass
class Pedestrian:
    """Piéton traversant."""
    x: float
    y: float
    vx: float = 0.0


@dataclass
class SpeedBump:
    """Ralentisseur — force ~40 km/h."""
    x: float
    y: float
    w: int = 60
    h: int = 12


class CityMap:
    """
    Carte ville avec feux, piétons et route étroite.

    Niveau 1: Banlieue calme — 3 ennemis, pas de feux.
    Niveau 2: Centre-ville — feux, ralentisseurs.
    Niveau 3: Rush hour — trafic dense, brouillard.
    """

    SPEED_LIMIT_KMH = 120
    BUMP_SPEED_KMH = 40

    def __init__(self, level: int, road_x: int, road_w: int):
        self.level = max(1, min(3, level))
        self.defn = get_map_definition(MapConfig.CITY, self.level)
        self.road_x = road_x
        self.road_w = int(road_w * self.defn.road_width_mod)
        self.traffic_lights: List[TrafficLight] = []
        self.pedestrians: List[Pedestrian] = []
        self.speed_bumps: List[SpeedBump] = []
        self._scroll = 0.0
        self._hit_cooldown: dict = {}
        self._init_elements()

    def _init_elements(self):
        ex = self.defn.extra
        n_lights = ex.get("traffic_lights", 0)
        lane_w = self.road_w // 3
        for i in range(n_lights):
            self.traffic_lights.append(TrafficLight(
                x=self.road_x + lane_w * (i % 3) + lane_w // 2,
                y=-random.randint(200, 800),
            ))
        if ex.get("pedestrians"):
            for _ in range(4):
                self.pedestrians.append(Pedestrian(
                    x=self.road_x + random.randint(20, self.road_w - 20),
                    y=-random.randint(300, 1200),
                    vx=random.choice([-1.5, 1.5]),
                ))
        if self.level >= 2:
            for _ in range(3 + self.level):
                self.speed_bumps.append(SpeedBump(
                    x=self.road_x + random.randint(40, self.road_w - 100),
                    y=-random.randint(400, 1500),
                ))

    def update(self, dt: float, speed: float) -> dict:
        """
        Met à jour la carte. Retourne effets sur le joueur.

        Returns:
            dict: speed_cap, score_penalty, collision_rects
        """
        result = {
            "speed_cap_kmh": self.SPEED_LIMIT_KMH,
            "score_penalty": 0,
            "dynamic_rects": [],
            "force_slow": False,
            "fog": self.defn.extra.get("fog", False),
        }
        self._scroll += speed * dt

        for tl in self.traffic_lights:
            tl.y += speed * dt
            tl.timer += dt
            if tl.timer > 90:
                tl.timer = 0
                tl.state = "green" if tl.state == "red" else "red"
            if tl.y > S.SCREEN_H + 50:
                tl.y = -random.randint(200, 600)
            if tl.state == "red":
                rect = pygame.Rect(int(tl.x) - 25, int(tl.y) - 8, 50, 16)
                result["dynamic_rects"].append(("traffic_light", rect, -200))

        for ped in self.pedestrians:
            ped.y += speed * dt
            ped.x += ped.vx * dt
            if ped.y > S.SCREEN_H + 30:
                ped.y = -random.randint(200, 900)
            result["dynamic_rects"].append((
                "pedestrian",
                pygame.Rect(int(ped.x) - 8, int(ped.y) - 12, 16, 24),
                0,
            ))

        for bump in self.speed_bumps:
            bump.y += speed * dt
            if bump.y > S.SCREEN_H + 30:
                bump.y = -random.randint(300, 1000)
            result["dynamic_rects"].append((
                "speed_bump",
                pygame.Rect(int(bump.x), int(bump.y), bump.w, bump.h),
                0,
            ))

        return result

    def check_collisions(self, player_rect: pygame.Rect, result: dict, dt: float) -> dict:
        """Applique pénalités de collision ville (une fois par cooldown)."""
        for key in list(self._hit_cooldown):
            self._hit_cooldown[key] -= dt
            if self._hit_cooldown[key] <= 0:
                del self._hit_cooldown[key]

        for kind, rect, penalty in result.get("dynamic_rects", []):
            if not player_rect.colliderect(rect):
                continue
            ck = (kind, int(rect.centerx // 20), int(rect.centery // 20))
            if self._hit_cooldown.get(ck, 0) > 0:
                continue
            self._hit_cooldown[ck] = 45.0

            if kind == "traffic_light":
                result["score_penalty"] = result.get("score_penalty", 0) - abs(penalty)
            elif kind == "speed_bump":
                result["force_slow"] = True
            elif kind == "pedestrian":
                result["hit_pedestrian"] = True
        return result

    def draw_hazards(self, surface: pygame.Surface):
        """Dessine feux, piétons et ralentisseurs."""
        for tl in self.traffic_lights:
            if -40 < tl.y < S.SCREEN_H + 40:
                col = (255, 50, 50) if tl.state == "red" else (50, 220, 80)
                pygame.draw.rect(surface, (40, 40, 40),
                                 (int(tl.x) - 8, int(tl.y) - 20, 16, 36), border_radius=3)
                pygame.draw.circle(surface, col, (int(tl.x), int(tl.y) - 8), 5)
                pygame.draw.circle(surface, (80, 80, 80), (int(tl.x), int(tl.y) + 8), 5)
        for ped in self.pedestrians:
            if -20 < ped.y < S.SCREEN_H + 20:
                pygame.draw.circle(surface, (255, 200, 150),
                                   (int(ped.x), int(ped.y)), 6)
                pygame.draw.rect(surface, (100, 150, 255),
                                 (int(ped.x) - 4, int(ped.y) + 4, 8, 12))
        for bump in self.speed_bumps:
            if -20 < bump.y < S.SCREEN_H + 20:
                pygame.draw.rect(surface, (200, 200, 80),
                                 (int(bump.x), int(bump.y), bump.w, bump.h))

    def draw_decor(self, surface: pygame.Surface, scroll: float):
        """Décors: immeubles, lampadaires."""
        W = surface.get_width()
        for side, ox in [(0, self.road_x - 80), (1, self.road_x + self.road_w + 10)]:
            for i in range(6):
                bh = 60 + (i * 37) % 80
                by = int((scroll * 0.3 + i * 120) % (S.SCREEN_H + bh)) - bh
                col = S.C_BUILDING[0] if side == 0 else S.C_BUILDING[1]
                pygame.draw.rect(surface, col, (ox, by, 70, bh))
                # Lampadaire
                lx = ox + 35
                pygame.draw.line(surface, (80, 80, 90), (lx, by + bh), (lx, by + bh + 25), 2)
                pygame.draw.circle(surface, (255, 230, 150), (lx, by + bh - 2), 4)
