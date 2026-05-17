"""
road_renderer.py — Route pseudo-3D style OutRun.

Rôle: Projection perspective par segments.
Paramètres: segments, scroll, courbe.
Dépendances: pygame, numpy (optionnel).
"""

import math
import pygame
from dataclasses import dataclass
from typing import List, Tuple

import settings as S


@dataclass
class RoadSegment:
    """Segment de route en perspective."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    curve: float = 0.0
    width: float = 200.0
    color_light: Tuple[int, int, int] = (40, 40, 60)
    color_dark: Tuple[int, int, int] = (25, 25, 40)


class RoadRenderer:
    """
    Rendu route pseudo-3D avec bandes alternées.

    Dépendances: liste de RoadSegment générée par la carte.
    """

    def __init__(self, screen_w: int, screen_h: int, segment_count: int = 300):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.segment_count = segment_count
        self.segments: List[RoadSegment] = []
        self.camera_z = 0.0
        self._build_segments()

    def _build_segments(self):
        self.segments = []
        for i in range(self.segment_count):
            curve = math.sin(i * 0.08) * 0.4
            self.segments.append(RoadSegment(
                z=i * 20.0,
                curve=curve,
                width=S.ROAD_WIDTH * (1.0 - abs(curve) * 0.1),
                color_light=(35 + (i % 2) * 8, 35, 55),
                color_dark=(22, 22, 38),
            ))

    def project(self, seg: RoadSegment, cam_z: float) -> Tuple[float, float, float, float]:
        """Projette un segment en coordonnées écran."""
        dz = seg.z - cam_z
        if dz <= 0:
            dz = 0.1
        scale = 300.0 / dz
        x = self.screen_w / 2 + seg.curve * 80 * scale
        y = self.screen_h * 0.45 + scale * 2
        w = seg.width * scale * 0.01
        return x, y, w, scale

    def draw(self, surface: pygame.Surface, scroll: float, level: int = 0):
        """Dessine la route et les décors bord."""
        self.camera_z = scroll * 5
        road_col = S.C_ROAD[min(level, len(S.C_ROAD) - 1)]
        surface.fill(S.C_BG)
        rx = S.ROAD_X
        rw = S.ROAD_WIDTH
        pygame.draw.rect(surface, road_col, (rx, 0, rw, self.screen_h))
        # Bandes
        lane_w = rw // max(1, S.LANE_COUNT[min(level, 2)])
        offset = int(scroll * 40) % 60
        for lane in range(1, S.LANE_COUNT[min(level, 2)]):
            lx = rx + lane_w * lane
            y = -offset
            while y < self.screen_h:
                pygame.draw.rect(surface, (255, 255, 255, 22), (lx - 1, y, 2, 30))
                y += 60
        # Segments perspective (simplifié — bandes horizontales)
        for i in range(0, min(40, len(self.segments)), 2):
            seg = self.segments[(int(self.camera_z // 20) + i) % len(self.segments)]
            _, sy, sw, _ = self.project(seg, self.camera_z)
            if 0 <= sy < self.screen_h:
                col = seg.color_light if i % 2 == 0 else seg.color_dark
                pygame.draw.rect(surface, col,
                                 (int(self.screen_w / 2 - sw / 2), int(sy), int(sw), 4))

    def draw_rearview(self, surface: pygame.Surface, entities: list, player_y: float):
        """Mini rétroviseur en haut à droite."""
        w, h = 100, 60
        x, y = self.screen_w - w - 12, 12
        mirror = pygame.Surface((w, h), pygame.SRCALPHA)
        mirror.fill((10, 10, 25, 200))
        pygame.draw.rect(mirror, (0, 229, 255, 80), (0, 0, w, h), 1)
        for ent in entities[:8]:
            if hasattr(ent, "y") and ent.y < player_y:
                ey = int((ent.y / max(1, player_y)) * h)
                pygame.draw.circle(mirror, getattr(ent, "color", (255, 100, 50)), (w // 2, h - ey), 3)
        surface.blit(mirror, (x, y))
