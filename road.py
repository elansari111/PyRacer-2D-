# ============================================================
#  PyRacer: Ultimate Neon Highway
#  road.py — Défilement de route, voies, décor
# ============================================================

import pygame
import random
import settings as S


class Road:
    """Gère le rendu et le défilement de la route par niveau."""

    STRIPE_SPACING = 80     # espacement entre tirets de voie
    STRIPE_LEN     = 40
    STRIPE_W       = 2

    def __init__(self, level: int, is_circuit: bool = False):
        self.level      = level
        self.lane_count = S.LANE_COUNT[level]
        self.road_x     = S.ROAD_X
        self.road_w     = S.ROAD_WIDTH
        self.lane_w     = self.road_w // self.lane_count

        self.scroll_offset = 0.0
        self.bg_scroll     = 0.0   # décor plus lent (parallaxe)

        # Bâtiments / décor latéral
        self._buildings = self._gen_buildings()
        self._prepare_building_surfaces()

        # Obstacles fixes (Circuit et niveau 2)
        self.obstacles = []
        if level == 2 or is_circuit:
            self._gen_obstacles()

        # Caches
        self._road_surf = pygame.Surface((self.road_w, S.SCREEN_H), pygame.SRCALPHA)
        self._glow_surf = self._gen_neon_glow()
        self._lane_surf = pygame.Surface((self.road_w, S.SCREEN_H), pygame.SRCALPHA)
        self._spd_surf  = pygame.Surface((self.road_w, S.SCREEN_H), pygame.SRCALPHA)

    # ----------------------------------------------------------
    def _gen_buildings(self) -> list:
        """Génère des bâtiments aléatoires pour les deux côtés."""
        buildings = []
        for side in ("left", "right"):
            for i in range(8):
                bw = random.randint(40, self.road_x - 20)
                bh = random.randint(60, 220)
                bx = (random.randint(4, self.road_x - bw - 8)
                      if side == "left"
                      else self.road_x + self.road_w + random.randint(8, 40))
                by = random.randint(-bh, S.SCREEN_H)
                buildings.append({"x": bx, "y": by, "w": bw, "h": bh,
                                  "side": side,
                                  "window_rows": random.randint(3, 10),
                                  "window_cols": random.randint(2, 5)})
        return buildings

    def _prepare_building_surfaces(self):
        """Prepare cached window surfaces for buildings"""
        for b in self._buildings:
            win_surf = pygame.Surface((b["w"], b["h"]), pygame.SRCALPHA)
            ww = max(4, b["w"] // (b["window_cols"] + 1))
            wh = max(4, b["h"] // (b["window_rows"] + 1))
            for row in range(b["window_rows"]):
                for col in range(b["window_cols"]):
                    if random.random() < 0.55:
                        wx = 6 + col * (ww + 4)
                        wy = 6 + row * (wh + 5)
                        pygame.draw.rect(win_surf, (255, 255, 200, 18), (wx, wy, ww, wh))
            b["win_surf"] = win_surf

    def _gen_neon_glow(self) -> pygame.Surface:
        edge_col = S.C_EDGE_GLOW[self.level]
        glow_l = pygame.Surface((self.road_x, S.SCREEN_H), pygame.SRCALPHA)
        for i in range(self.road_x, 0, -1):
            a = max(0, 18 - i // 3)
            pygame.draw.line(glow_l, (*edge_col, a),
                             (self.road_x - i, 0), (self.road_x - i, S.SCREEN_H))
        return glow_l

    def _gen_obstacles(self):
        """Génère des cônes / barrières pour le Circuit."""
        for i in range(6):
            lane = random.randrange(self.lane_count)
            self.obstacles.append({
                "x": self.road_x + self.lane_w * lane + self.lane_w // 2 - 10,
                "y": random.randint(-1000, -200),
                "w": 20, "h": 20,
                "color": S.C_YELLOW,
            })

    def reset_obstacle(self, obs):
        """Réinitialise la position d'un obstacle en haut de l'écran."""
        if obs in self.obstacles:
            lane = random.randrange(self.lane_count)
            obs["x"] = self.road_x + self.lane_w * lane + self.lane_w // 2 - 10
            obs["y"] = random.randint(-800, -200)

    # ----------------------------------------------------------
    def update(self, speed: float, dt: float):
        """Avance le scroll selon la vitesse du joueur."""
        self.scroll_offset = (self.scroll_offset + speed * dt) % self.STRIPE_SPACING
        self.bg_scroll     = (self.bg_scroll     + speed * dt * 0.35) % S.SCREEN_H

        # Bâtiments : défilement parallaxe
        for b in self._buildings:
            b["y"] += speed * dt * 0.30
            if b["y"] > S.SCREEN_H + b["h"]:
                b["y"] = -b["h"] - random.randint(0, 200)
                b["h"]  = random.randint(60, 220)

        # Obstacles Circuit
        for obs in self.obstacles:
            obs["y"] += speed * dt
            if obs["y"] > S.SCREEN_H + 40:
                lane = random.randrange(self.lane_count)
                obs["x"] = self.road_x + self.lane_w * lane + self.lane_w // 2 - 10
                obs["y"] = random.randint(-600, -100)

    # ----------------------------------------------------------
    def draw(self, surface: pygame.Surface, speed: float):
        """Dessine l'arrière-plan, la route et les obstacles."""
        bg_col  = S.C_ROAD[self.level]
        bld_col = S.C_BUILDING[self.level]
        edge_col = S.C_EDGE_GLOW[self.level]
        raw_lane = S.C_LANE[self.level]          # (r,g,b,a)
        lane_col = raw_lane[:3]
        lane_alpha = raw_lane[3] if len(raw_lane) > 3 else 24

        # --- Fond général ---
        surface.fill(S.C_BG)

        # --- Bâtiments latéraux ---
        for b in self._buildings:
            pygame.draw.rect(surface, bld_col, (b["x"], b["y"], b["w"], b["h"]))
            surface.blit(b["win_surf"], (b["x"], b["y"]))

        # --- Lueur néon sur les côtés ---
        surface.blit(self._glow_surf, (0, 0))

        # --- Chaussée ---
        pygame.draw.rect(surface, bg_col,
                         (self.road_x, 0, self.road_w, S.SCREEN_H))

        # --- Lignes de voie (tirets) ---
        self._lane_surf.fill((0, 0, 0, 0))
        for lane_i in range(1, self.lane_count):
            lx = self.lane_w * lane_i
            y  = -self.scroll_offset
            while y < S.SCREEN_H:
                pygame.draw.rect(self._lane_surf, (*lane_col, lane_alpha),
                                 (lx - 1, int(y), self.STRIPE_W, self.STRIPE_LEN))
                y += self.STRIPE_SPACING
        surface.blit(self._lane_surf, (self.road_x, 0))

        # --- Bordures lumineuses ---
        pygame.draw.line(surface, (*edge_col, 160),
                         (self.road_x, 0), (self.road_x, S.SCREEN_H), 2)
        pygame.draw.line(surface, (*edge_col, 160),
                         (self.road_x + self.road_w, 0),
                         (self.road_x + self.road_w, S.SCREEN_H), 2)

        # --- Lignes de vitesse (haute vitesse) ---
        if speed > 6:
            alpha = min(35, int((speed - 6) * 5))
            self._spd_surf.fill((0, 0, 0, 0))
            for _ in range(6):
                sx = random.randint(0, self.road_w)
                pygame.draw.line(self._spd_surf, (255, 255, 255, alpha),
                                 (sx, 0), (sx, S.SCREEN_H))
            surface.blit(self._spd_surf, (self.road_x, 0))

        # --- Obstacles Circuit ---
        for obs in self.obstacles:
            pygame.draw.rect(surface, obs["color"],
                             (obs["x"], obs["y"], obs["w"], obs["h"]),
                             border_radius=3)
            pygame.draw.rect(surface, (255, 255, 255),
                             (obs["x"] + 4, obs["y"] + 4, obs["w"] - 8, 4))

    # ----------------------------------------------------------
    def get_obstacle_rects(self) -> list:
        return [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                for o in self.obstacles]
