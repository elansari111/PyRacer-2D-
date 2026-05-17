"""
map_select_screen.py — Écran sélection carte et niveau.

Rôle: 3 cartes cliquables, niveaux verrouillés, hi-scores.
Paramètres: ScoreManager, progression débloquée.
Dépendances: pygame, maps.map_config, settings.
"""

import pygame
import settings as S
from maps.map_config import MapConfig, score_key


class MapSelectScreen:
    """
    Interface de sélection map + niveau.

    Dépendances: ScoreManager pour afficher les records.
    """

    MAPS = [
        (MapConfig.CITY, "VILLE", S.C_CYAN, "Feux • Piétons • 120 km/h"),
        (MapConfig.HIGHWAY, "AUTOROUTE", S.C_MAGENTA, "4 voies • Camions • Police"),
        (MapConfig.CIRCUIT, "CIRCUIT", S.C_YELLOW, "Tours • DRS • Classement"),
    ]

    def __init__(self):
        self.selected_map = 0
        self.selected_level = 0
        self.font_title = pygame.font.SysFont("orbitron,consolas", 36, bold=True)
        self.font_med = pygame.font.SysFont("orbitron,consolas", 18, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 13)
        self._card_rects: list = []
        self._level_rects: list = []

    def handle_event(self, event: pygame.event.Event, unlocked: dict) -> str | None:
        """
        Gère clic / clavier.

        Returns:
            "start" si partie lancée, None sinon.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected_map = (self.selected_map - 1) % 3
            elif event.key == pygame.K_RIGHT:
                self.selected_map = (self.selected_map + 1) % 3
            elif event.key == pygame.K_UP:
                self.selected_level = max(0, self.selected_level - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_level = min(2, self.selected_level + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                mid = self.MAPS[self.selected_map][0].value
                if unlocked.get(f"{mid}_{self.selected_level + 1}", self.selected_level == 0):
                    return "start"
            elif event.key == pygame.K_ESCAPE:
                return "menu"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(pos):
                    self.selected_map = i
            for i, rect in enumerate(self._level_rects):
                if rect.collidepoint(pos):
                    mid = self.MAPS[self.selected_map][0].value
                    if unlocked.get(f"{mid}_{i + 1}", i == 0):
                        self.selected_level = i
                        return "start"
        return None

    def get_selection(self) -> tuple:
        """Retourne (map_id str, level 1-3)."""
        cfg, _, _, _ = self.MAPS[self.selected_map]
        return cfg.value, self.selected_level + 1

    def draw(self, surface: pygame.Surface, hi_scores: dict, unlocked: dict):
        """Dessine l'écran de sélection."""
        W, H = surface.get_size()
        surface.fill(S.C_BG)
        title = self.font_title.render("CHOISIR UNE CARTE", True, S.C_WHITE)
        surface.blit(title, title.get_rect(centerx=W // 2, centery=50))

        self._card_rects = []
        card_w, card_h = 220, 140
        gap = 24
        total_w = 3 * card_w + 2 * gap
        sx = W // 2 - total_w // 2

        for i, (cfg, label, col, desc) in enumerate(self.MAPS):
            bx = sx + i * (card_w + gap)
            by = 100
            rect = pygame.Rect(bx, by, card_w, card_h)
            self._card_rects.append(rect)
            active = i == self.selected_map
            pygame.draw.rect(surface, (*col, 55 if active else 22), rect, border_radius=8)
            pygame.draw.rect(surface, (*col, 255 if active else 120), rect, 2, border_radius=8)
            t = self.font_med.render(label, True, S.C_WHITE)
            surface.blit(t, t.get_rect(centerx=rect.centerx, centery=by + 32))
            d = self.font_small.render(desc, True, (200, 210, 230))
            surface.blit(d, d.get_rect(centerx=rect.centerx, centery=by + 68))
            mid = cfg.value
            best = max(
                hi_scores.get(score_key(mid, lv), 0) for lv in range(1, 4)
            )
            hi = self.font_small.render(f"Meilleur: {best:,}", True, (140, 140, 160))
            surface.blit(hi, hi.get_rect(centerx=rect.centerx, centery=by + 105))

        # Niveaux
        self._level_rects = []
        mid = self.MAPS[self.selected_map][0].value
        _, _, col, _ = self.MAPS[self.selected_map]
        ly = 280
        for lv in range(3):
            bx = W // 2 - 200 + lv * 140
            rect = pygame.Rect(bx, ly, 120, 50)
            self._level_rects.append(rect)
            key = f"{mid}_{lv + 1}"
            is_unlocked = unlocked.get(key, lv == 0)
            is_sel = lv == self.selected_level
            if not is_unlocked:
                pygame.draw.rect(surface, (40, 40, 50), rect, border_radius=6)
                pygame.draw.rect(surface, (80, 80, 95), rect, 1, border_radius=6)
                lock = self.font_small.render("VERROUILLE", True, (110, 110, 125))
                surface.blit(lock, lock.get_rect(center=rect.center))
            else:
                pygame.draw.rect(surface, (*col, 50 if is_sel else 20), rect, border_radius=6)
                pygame.draw.rect(surface, (*col, 200 if is_sel else 100), rect, 2, border_radius=6)
                t = self.font_med.render(f"Niv. {lv + 1}", True, S.C_WHITE)
                surface.blit(t, t.get_rect(center=rect.center))
                sc = hi_scores.get(score_key(mid, lv + 1), 0)
                st = self.font_small.render(f"HI {sc:,}", True, (130, 130, 150))
                surface.blit(st, st.get_rect(centerx=rect.centerx, centery=ly + 58))

        hint = self.font_small.render(
            "←→ Carte   ↑↓ Niveau   ENTER Lancer   ESC Menu", True, (100, 100, 120))
        surface.blit(hint, hint.get_rect(centerx=W // 2, centery=H - 30))
