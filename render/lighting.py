"""
lighting.py — Cycle jour/nuit et éclairage dynamique.

Rôle: Overlay teinté, phares, lampadaires, tunnels.
Paramètres: time_of_day 0.0-1.0.
Dépendances: pygame.
"""

import math
import pygame
from typing import List, Tuple

import settings as S


class DayNightCycle:
    """
    Cycle jour/nuit (0.0 = midi, 1.0 = minuit).

    Produit une couleur d'overlay SRCALPHA.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.time = 0.25  # départ: fin d'après-midi

    def advance(self, dt: float, speed: float = 0):
        self.time = (self.time + dt * 0.0003 * (1 + speed * 0.02)) % 1.0

    def get_overlay_color(self) -> Tuple[int, int, int, int]:
        """Couleur teinte selon l'heure."""
        t = self.time
        if t < 0.25:  # jour
            return (255, 250, 240, 8)
        if t < 0.5:   # crépuscule
            return (255, 120, 60, 45)
        if t < 0.75:  # nuit
            return (10, 15, 40, 50)
        return (255, 200, 100, 30)  # aube

    def draw_overlay(self, surface: pygame.Surface):
        col = self.get_overlay_color()
        if col[3] <= 0:
            return
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill(col)
        surface.blit(ov, (0, 0))


class LightingSystem:
    """
    Phares voiture, lampadaires ville, obscurité tunnel.

    Dépendances: DayNightCycle.
    """

    def __init__(self, width: int, height: int):
        self.cycle = DayNightCycle(width, height)
        self.tunnel_darkness = 0.0
        self.street_lights: List[Tuple[int, int]] = []

    def set_tunnel(self, darkness: float):
        self.tunnel_darkness = max(0.0, min(1.0, darkness))

    def draw_headlights(self, surface: pygame.Surface, car_x: int, car_y: int, car_w: int):
        """Petits faisceaux devant la voiture (nuit / tunnel uniquement)."""
        for ox in (8, car_w - 8):
            beam = pygame.Surface((24, 36), pygame.SRCALPHA)
            pygame.draw.polygon(beam, (255, 255, 200, 28), [
                (12, 0), (0, 34), (24, 34)])
            surface.blit(beam, (car_x + ox - 12, car_y - 28), special_flags=pygame.BLEND_ADD)

    def draw_street_lamp(self, surface: pygame.Surface, x: int, y: int):
        """Cône triangulaire jaune (ville)."""
        cone = pygame.Surface((60, 80), pygame.SRCALPHA)
        pygame.draw.polygon(cone, (255, 230, 120, 35), [(30, 0), (0, 75), (60, 75)])
        surface.blit(cone, (x - 30, y))

    def apply(self, surface: pygame.Surface, car_pos=None, enable_headlights: bool = False):
        col = self.cycle.get_overlay_color()
        if col[3] > 20:
            self.cycle.draw_overlay(surface)
        if self.tunnel_darkness > 0.08:
            dark = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            alpha = int(90 * self.tunnel_darkness)
            dark.fill((0, 0, 10, alpha))
            surface.blit(dark, (0, 0))
        if enable_headlights and car_pos and self.tunnel_darkness > 0.15:
            self.draw_headlights(surface, *car_pos)
