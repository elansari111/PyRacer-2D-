"""
renderer.py — Rendu par couches avec dirty rects.

Rôle: Orchestrer background → road → entities → HUD → post-fx.
Paramètres: surfaces pygame, entités du frame.
Dépendances: pygame, settings.
"""

import pygame
from enum import IntEnum
from typing import Callable, List, Optional

import settings as S


class RenderLayer(IntEnum):
    BACKGROUND = 0
    ROAD = 1
    SHADOWS = 2
    ENTITIES = 3
    PARTICLES = 4
    HUD = 5
    POST_FX = 6


class SceneRenderer:
    """
    Moteur de rendu par couches ordonnées.

    Utilise un système de dirty rects pour limiter les blits.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.canvas = pygame.Surface((width, height))
        self._layers: dict[RenderLayer, List[Callable]] = {l: [] for l in RenderLayer}
        self._dirty: List[pygame.Rect] = []
        self.clear_color = S.C_BG

    def register(self, layer: RenderLayer, draw_fn: Callable[[pygame.Surface], None]):
        """Enregistre une fonction de dessin pour une couche."""
        self._layers[layer].append(draw_fn)

    def clear_layer_callbacks(self, layer: RenderLayer):
        self._layers[layer].clear()

    def mark_dirty(self, rect: pygame.Rect):
        self._dirty.append(rect.clamp(self.canvas.get_rect()))

    def begin_frame(self, full_redraw: bool = False):
        """Prépare le frame."""
        if full_redraw or not self._dirty:
            self.canvas.fill(self.clear_color)
            self._full_frame = True
        else:
            for r in self._dirty:
                self.canvas.fill(self.clear_color, r)
            self._full_frame = False

    def render(self, post_process: Optional[Callable[[pygame.Surface], pygame.Surface]] = None) -> pygame.Surface:
        """Exécute toutes les couches et retourne la surface finale."""
        if getattr(self, "_full_frame", True):
            self.canvas.fill(self.clear_color)
        for layer in RenderLayer:
            if layer == RenderLayer.POST_FX:
                continue
            for fn in self._layers[layer]:
                fn(self.canvas)
        out = self.canvas
        if post_process:
            out = post_process(out)
        self._dirty.clear()
        return out

    def blit_to(self, target: pygame.Surface, offset=(0, 0)):
        target.blit(self.canvas, offset)
