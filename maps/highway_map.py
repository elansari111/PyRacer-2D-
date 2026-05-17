"""
highway_map.py — Logique carte Autoroute.

Rôle: 4 voies, camions, police, tunnels, vent.
Paramètres: level 1-3.
Dépendances: map_config, settings.
"""

import random
import pygame
from dataclasses import dataclass
from typing import List

import settings as S
from maps.map_config import MapConfig, get_map_definition


@dataclass
class TunnelZone:
    """Zone tunnel — visibilité réduite."""
    y_start: float
    y_end: float
    active: bool = False


class HighwayMap:
    """
    Autoroute 4 voies, camions, radar police, tunnels.

    Niveau 1: Route dégagée.
    Niveau 2: Police + vent modéré.
    Nivel 3: Chaos — tempête, tunnel.
    """

    POLICE_SPEED_LIMIT = 180  # km/h
    WIND_THRESHOLD = 180

    def __init__(self, level: int, road_x: int, road_w: int):
        self.level = max(1, min(3, level))
        self.defn = get_map_definition(MapConfig.HIGHWAY, self.level)
        self.road_x = road_x
        self.road_w = road_w
        self.lane_count = 4
        self.police_active = False
        self.police_timer = 0.0
        self.wind_strength = self.defn.extra.get("wind", 0.0)
        self.in_tunnel = False
        self.tunnel_boost_timer = 0.0
        self.tunnels: List[TunnelZone] = []
        if self.defn.extra.get("tunnel"):
            self.tunnels.append(TunnelZone(y_start=400, y_end=900))

    def update(self, dt: float, speed: float, player_speed_kmh: float) -> dict:
        """Met à jour autoroute. Retourne effets gameplay."""
        result = {
            "lateral_drift": 0.0,
            "visibility": 1.0,
            "tunnel_boost": False,
            "police_chase": False,
            "score_penalty": 0,
        }

        # Police / speed trap
        police_count = self.defn.extra.get("police", 0)
        if police_count > 0 and player_speed_kmh > self.POLICE_SPEED_LIMIT:
            self.police_timer += dt
            if self.police_timer > 30:
                self.police_active = True
                result["police_chase"] = True
                result["score_penalty"] = -50
        else:
            self.police_timer = max(0, self.police_timer - dt * 2)
            if self.police_timer <= 0:
                self.police_active = False

        # Vent latéral
        if player_speed_kmh > self.WIND_THRESHOLD and self.wind_strength > 0:
            result["lateral_drift"] = self.wind_strength * random.uniform(-1, 1) * dt * 8

        # Tunnel
        self.in_tunnel = False
        for t in self.tunnels:
            if t.y_start < 500 < t.y_end:
                self.in_tunnel = True
                result["visibility"] = 0.35
        if self.tunnel_boost_timer > 0:
            self.tunnel_boost_timer -= dt
            result["tunnel_boost"] = True

        if self.defn.extra.get("storm"):
            result["visibility"] *= 0.6

        return result

    def on_tunnel_exit(self):
        """Boost à la sortie du tunnel."""
        self.tunnel_boost_timer = 60.0
        self.in_tunnel = False

    def draw_decor(self, surface: pygame.Surface, scroll: float):
        """Ponts, glissières, panneaux."""
        rx, rw = self.road_x, self.road_w
        for y in range(0, S.SCREEN_H, 200):
            sy = int((y + scroll) % S.SCREEN_H)
            pygame.draw.rect(surface, (200, 200, 210), (rx - 8, sy, 6, 40))
            pygame.draw.rect(surface, (200, 200, 210), (rx + rw + 2, sy, 6, 40))
        if self.level >= 2:
            sign = pygame.font.SysFont("consolas", 12).render("180", True, (255, 255, 255))
            surface.blit(sign, (rx + rw // 2 - 10, 40))
