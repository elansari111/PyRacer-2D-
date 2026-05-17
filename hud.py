# ============================================================
#  PyRacer: Ultimate Neon Highway
#  hud.py — Affichage HUD en jeu
# ============================================================

import pygame
import math
import settings as S


class HUD:
    """
    HUD complet : score, vies, jauges nitro/bouclier,
    vitesse, niveau, streak, objectif, flash de collision.
    """

    def __init__(self):
        self._flash_timer   = 0
        self._popup_list: list[dict] = []

        # Polices
        self.font_title  = pygame.font.SysFont("orbitron,consolas,monospace", 22, bold=True)
        self.font_big    = pygame.font.SysFont("orbitron,consolas,monospace", 28, bold=True)
        self.font_med    = pygame.font.SysFont("orbitron,consolas,monospace", 14, bold=True)
        self.font_small  = pygame.font.SysFont("orbitron,consolas,monospace", 11)
        self.font_tiny   = pygame.font.SysFont("orbitron,consolas,monospace", 9)
        self.font_emoji  = pygame.font.SysFont("segoeuiemoji,dejavusans", 16)
        
        # Minimap
        self._minimap_surface = pygame.Surface((S.MINIMAP_W, S.MINIMAP_H), pygame.SRCALPHA)
        
        # Achievement notification
        self._achievement_notification = None
        self._achievement_timer = 0

    # ----------------------------------------------------------
    def trigger_flash(self):
        """Déclenche le flash rouge de collision."""
        self._flash_timer = 18

    def add_popup(self, x: int, y: int, text: str, color: tuple):
        """Ajoute un score flottant à l'écran."""
        self._popup_list.append({"x": x, "y": float(y),
                                 "text": text, "color": color,
                                 "life": 70, "max_life": 70})

    # ----------------------------------------------------------
    def update(self, dt: float):
        if self._flash_timer > 0:
            self._flash_timer -= dt
        for p in self._popup_list:
            p["y"]   -= 0.8 * dt
            p["life"] -= dt
        self._popup_list = [p for p in self._popup_list if p["life"] > 0]

    # ----------------------------------------------------------
    def draw(self, surface: pygame.Surface,
             score: int, lives: int, speed: float,
             nitro_charge: float, nitro_active: bool,
             shield_charge: float, shield_active: bool,
             streak: int, level: int,
             objective_pct: float, objective_label: str,
             active_effects: list = None,
             enemies: list = None,
             player_y: float = None,
             map_id: str = None,
             map_level: int = 1):
        """Dessine tous les éléments du HUD."""

        W, H = surface.get_size()

        # ---- Header gradient ----
        hdr = pygame.Surface((W, 72), pygame.SRCALPHA)
        for i in range(72):
            a = max(0, 180 - i * 2)
            pygame.draw.line(hdr, (5, 5, 15, a), (0, i), (W, i))
        surface.blit(hdr, (0, 0))

        # ---- Score ----
        sc_txt = self.font_big.render(f"{score:,}", True, S.C_CYAN)
        surface.blit(sc_txt, (16, 10))
        lbl = self.font_small.render("SCORE", True, (255, 255, 255, 80))
        surface.blit(lbl, (16, 8))

        # ---- Vies ----
        for i in range(lives):
            heart = self.font_emoji.render("♥", True, S.C_MAGENTA)
            surface.blit(heart, (W - 26 - i * 24, 10))

        # ---- Vitesse (compteur analogique, bas-droite) ----
        self._draw_speedometer(surface, W - 58, H - 118, speed)
        spd_txt = self.font_small.render(f"{int(speed * 30)} km/h", True, S.C_YELLOW)
        surface.blit(spd_txt, spd_txt.get_rect(right=W - 14, top=H - 78))

        # ---- Carte / niveau (haut-droite, sous les vies) ----
        map_names = {"city": "VILLE", "highway": "AUTOROUTE", "circuit": "CIRCUIT"}
        if map_id and map_id in map_names:
            lvl_label = f"{map_names[map_id]} — NIV.{map_level}"
            lvl_col = {"city": S.C_CYAN, "highway": S.C_MAGENTA, "circuit": S.C_YELLOW}.get(
                map_id, S.C_WHITE)
        else:
            lvl_idx = min(level, len(S.LEVEL_NAMES) - 1)
            lvl_label = f"NIV.{level + 1} — {S.LEVEL_NAMES[lvl_idx]}"
            lvl_col = S.LEVEL_COLORS[lvl_idx]
        lvl_txt = self.font_small.render(lvl_label, True, lvl_col)
        surface.blit(lvl_txt, (W - lvl_txt.get_width() - 12, 36))

        # ---- Jauges (centre) ----
        cx = W // 2
        self._draw_gauge(surface, cx - 70, 14, 140, 10,
                         nitro_charge / S.NITRO_MAX,
                         S.C_YELLOW, "NITRO",
                         active=nitro_active)
        self._draw_gauge(surface, cx - 70, 36, 140, 10,
                         shield_charge / S.SHIELD_MAX,
                         S.C_CYAN, "BOUCLIER",
                         active=shield_active)

        # ---- Streak ----
        if streak >= S.STREAK_MIN:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            a     = int(180 + 75 * pulse)
            st_txt = self.font_med.render(f"🔥 STREAK ×{streak}", True,
                                          (*S.C_YELLOW[:3],))
            surface.blit(st_txt, (st_txt.get_rect(centerx=cx).x, 54))

        # ---- Barre objectif ----
        bw = S.ROAD_WIDTH - 4
        bx = S.ROAD_X + 2
        by = S.SCREEN_H - 14
        pygame.draw.rect(surface, (255, 255, 255, 20), (bx, by, bw, 8), border_radius=4)
        fill_col = S.LEVEL_COLORS[min(level, len(S.LEVEL_COLORS) - 1)]
        pygame.draw.rect(surface, fill_col,
                         (bx, by, int(bw * min(1.0, objective_pct)), 8),
                         border_radius=4)
        obj_txt = self.font_small.render(objective_label, True, (255, 255, 255, 160))
        surface.blit(obj_txt, (obj_txt.get_rect(centerx=W // 2).x, by - 16))
        
        # ---- Active Effects ----
        if active_effects:
            self._draw_active_effects(surface, active_effects)
            
        # ---- Minimap ----
        if enemies and player_y is not None:
            self._draw_minimap(surface, enemies, player_y, level)
            
        # NOUVEAU: Danger Warning Indicator
        if enemies and player_y is not None:
            self._draw_danger_warning(surface, enemies, player_y, W, H)
            
        # ---- Achievement Notification ----
        if self._achievement_timer > 0:
            self._draw_achievement_notification(surface)

        # ---- Popups score ----
        for p in self._popup_list:
            alpha = max(0, int(255 * p["life"] / p["max_life"]))
            col   = (*p["color"][:3], alpha) if len(p["color"]) < 4 else p["color"]
            txt   = self.font_med.render(p["text"], True, p["color"])
            txt.set_alpha(alpha)
            surface.blit(txt, (int(p["x"]) - txt.get_width() // 2, int(p["y"])))

        # ---- Flash collision ----
        if self._flash_timer > 0:
            a = min(180, int(self._flash_timer * 10))
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            border = 14
            pygame.draw.rect(flash, (*S.C_MAGENTA, a),
                             (0, 0, W, H), border)
            surface.blit(flash, (0, 0))

    def _draw_speedometer(self, surface, cx, cy, speed: float, max_kmh: float = 220):
        """Compteur analogique (arc + aiguille)."""
        radius = 32
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        pygame.draw.arc(surface, (60, 60, 80), rect, math.pi * 0.75, math.pi * 2.25, 3)
        ratio = min(1.0, (speed * 30) / max_kmh)
        angle = math.pi * 0.75 + ratio * math.pi * 1.5
        nx = cx + math.cos(angle) * (radius - 8)
        ny = cy + math.sin(angle) * (radius - 8)
        pygame.draw.line(surface, S.C_YELLOW, (cx, cy), (int(nx), int(ny)), 3)
        pygame.draw.circle(surface, S.C_CYAN, (cx, cy), 4)

    # ----------------------------------------------------------
    def _draw_gauge(self, surface, x, y, w, h, pct, color, label,
                    active=False):
        # Lueur de fond si actif
        if active:
            glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            for r in range(10, 0, -1):
                a = int(30 * (1 - r/10))
                pygame.draw.rect(glow, (*color[:3], a), 
                               (10 - r, 10 - r, w + 2*r, h + 2*r), border_radius=4+r)
            surface.blit(glow, (x - 10, y - 10), special_flags=pygame.BLEND_ADD)
        
        # Fond avec dégradé
        pygame.draw.rect(surface, (30, 30, 45, 180), (x, y, w, h), border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255, 30), (x, y, w, h), border_radius=4, width=1)
        
        # Remplissage avec lueur
        fill_w = max(0, int(w * min(1.0, pct)))
        if fill_w > 0:
            # Lueur interne
            if fill_w > 4:
                glow_surf = pygame.Surface((fill_w + 8, h + 8), pygame.SRCALPHA)
                for r in range(4, 0, -1):
                    a = int(60 * (1 - r/4) * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)))
                    pygame.draw.rect(glow_surf, (*color[:3], a), 
                                   (r, r, fill_w + 8 - 2*r, h + 8 - 2*r), border_radius=4)
                surface.blit(glow_surf, (x - 4, y - 4), special_flags=pygame.BLEND_ADD)
            
            # Remplissage principal
            pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=4)
            # Ligne brillante au sommet
            pygame.draw.line(surface, (*S.C_WHITE[:3], 150), 
                           (x + 2, y + 1), (x + fill_w - 2, y + 1), 2)
            
        # Contour actif pulsant
        if active:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
            border_a = int(150 + 105 * pulse)
            pygame.draw.rect(surface, (*S.C_WHITE[:3], border_a),
                             (x - 2, y - 2, w + 4, h + 4), 2, border_radius=6)
        
        # Label avec ombre
        lbl = self.font_small.render(label, True, (100, 100, 110))
        surface.blit(lbl, (x + 1, y - 11))
        lbl = self.font_small.render(label, True,
                                     color if not active else S.C_WHITE)
        surface.blit(lbl, (x, y - 12))
        
    def _draw_active_effects(self, surface, effects):
        """Dessine les effets de bonus actifs."""
        x = S.ROAD_X - 100
        y = S.SCREEN_H - 80
        
        for effect_name, remaining_pct in effects:
            color = S.BONUS_COLORS_EXTENDED.get(effect_name, (200, 200, 200))
            icon = S.BONUS_ICONS_EXTENDED.get(effect_name, "?")
            
            # Fond
            pygame.draw.rect(surface, (*color, 40), (x, y, 90, 20), border_radius=3)
            # Barre de durée
            pygame.draw.rect(surface, (*color, 120), 
                           (x, y + 16, int(90 * remaining_pct), 4), border_radius=2)
            # Icône + nom
            txt = self.font_tiny.render(f"{icon} {effect_name.upper()}", True, color)
            surface.blit(txt, (x + 4, y + 2))
            
            y -= 24  # Prochain effet au-dessus
            
    def _draw_minimap(self, surface, enemies, player_y, level):
        """Dessine la minimap avec la position des ennemis."""
        # Fond
        self._minimap_surface.fill((5, 5, 15, 180))
        pygame.draw.rect(self._minimap_surface, (255, 255, 255, 30), 
                        (0, 0, S.MINIMAP_W, S.MINIMAP_H), border_radius=4)
        
        # Route sur la minimap
        road_x_mini = 10
        road_w_mini = S.MINIMAP_W - 20
        lane_w = road_w_mini // S.LANE_COUNT[level]
        
        pygame.draw.rect(self._minimap_surface, (50, 50, 70), 
                        (road_x_mini, 0, road_w_mini, S.MINIMAP_H))
        
        # Lignes de voie
        for i in range(1, S.LANE_COUNT[level]):
            lx = road_x_mini + i * lane_w
            pygame.draw.line(self._minimap_surface, (255, 255, 255, 30),
                           (lx, 0), (lx, S.MINIMAP_H), 1)
        
        # Joueur (position fixe en bas, les ennemis bougent)
        player_x = road_x_mini + road_w_mini // 2 - 3
        player_y_mini = S.MINIMAP_H - 15
        pygame.draw.rect(self._minimap_surface, S.C_CYAN, 
                        (player_x, player_y_mini, 6, 10), border_radius=2)
        
        # Ennemis
        view_distance = S.SCREEN_H * 1.5  # Distance visible sur la minimap
        
        for enemy in enemies:
            # Position relative au joueur
            dy = enemy.y - player_y
            if -view_distance < dy < view_distance and 0 < enemy.x < S.SCREEN_W:
                # Map vers coordonnées minimap
                ex = road_x_mini + ((enemy.x - S.ROAD_X) / S.ROAD_WIDTH) * road_w_mini
                ey = player_y_mini - (dy / view_distance) * S.MINIMAP_H
                
                if 0 < ey < S.MINIMAP_H:
                    color = S.ENEMY_COLORS[enemy.type]
                    size = 4 if enemy.type == 2 else 3  # Camion plus gros
                    pygame.draw.rect(self._minimap_surface, (*color, 200),
                                   (int(ex) - size//2, int(ey) - size//2, size, size))
        
        # Bordure
        pygame.draw.rect(self._minimap_surface, S.LEVEL_COLORS[level], 
                        (0, 0, S.MINIMAP_W, S.MINIMAP_H), 2, border_radius=4)
        
        # Blit sur la surface principale
        surface.blit(self._minimap_surface, (S.MINIMAP_X, S.MINIMAP_Y))
        
    def show_achievement(self, achievement):
        """Affiche une notification de succès."""
        self._achievement_notification = achievement
        self._achievement_timer = 180  # 3 secondes à 60 FPS
        
    def _draw_achievement_notification(self, surface):
        """Dessine la notification de succès."""
        if not self._achievement_notification:
            return
            
        W = surface.get_width()
        ach = self._achievement_notification
        
        # Animation fade in/out
        if self._achievement_timer > 150:
            alpha = int(255 * (180 - self._achievement_timer) / 30)
        elif self._achievement_timer < 30:
            alpha = int(255 * self._achievement_timer / 30)
        else:
            alpha = 255
            
        y = 120
        box_w = 350
        box_h = 70
        box_x = W // 2 - box_w // 2
        
        # Fond
        overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        
        # Couleur selon le tier
        tier_colors = {
            "bronze": (205, 127, 50),
            "silver": (192, 192, 192),
            "gold": (255, 215, 0),
            "platinum": (229, 228, 226),
        }
        color = tier_colors.get(ach.tier.value if hasattr(ach.tier, 'value') else str(ach.tier), S.C_YELLOW)
        
        pygame.draw.rect(overlay, (*color, min(60, alpha)), (0, 0, box_w, box_h), border_radius=8)
        pygame.draw.rect(overlay, (*color, min(180, alpha)), (0, 0, box_w, box_h), 2, border_radius=8)
        
        overlay.set_alpha(alpha)
        surface.blit(overlay, (box_x, y))
        
        # Textes
        title = self.font_med.render("SUCCÈS DÉBLOQUÉ!", True, color)
        title.set_alpha(alpha)
        surface.blit(title, (box_x + 15, y + 10))
        
        name = self.font_small.render(f"{ach.icon} {ach.name}", True, (255, 255, 255))
        name.set_alpha(alpha)
        surface.blit(name, (box_x + 15, y + 38))
        
        self._achievement_timer -= 1
    
    # NOUVEAU: Système d'indication de danger
    def _draw_danger_warning(self, surface, enemies, player_y, W, H):
        """Affiche un avertissement visuel quand un ennemi est proche et dangereux."""
        DANGER_DISTANCE = 150  # Pixels
        
        danger_enemies = []
        for enemy in enemies:
            dy = enemy.y - player_y
            # Ennemi devant et proche
            if 0 < dy < DANGER_DISTANCE and not enemy.passed:
                danger_enemies.append((enemy, dy))
        
        if not danger_enemies:
            return
        
        # Trouver l'ennemi le plus dangereux (le plus proche)
        danger_enemies.sort(key=lambda x: x[1])
        closest_enemy, distance = danger_enemies[0]
        
        # Intensité basée sur la distance (plus proche = plus intense)
        danger_ratio = 1.0 - (distance / DANGER_DISTANCE)
        
        # Type d'avertissement selon l'ennemi
        if closest_enemy.type == 2:  # Camion = danger élevé
            warning_color = S.C_RED
            warning_text = "⚠️ CAMION!"
        elif closest_enemy.type == 1:  # Rapide
            warning_color = S.C_YELLOW
            warning_text = "⚡ RAPIDE!"
        elif closest_enemy.type == 3:  # Imprévisible
            warning_color = S.C_MAGENTA
            warning_text = "❓ IMPRÉVISIBLE!"
        else:
            warning_color = (255, 107, 53)  # Orange standard
            warning_text = "⚠️ ATTENTION"
        
        # Pulse de l'avertissement
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.02)
        alpha = int(150 + 105 * pulse * danger_ratio)
        
        # Barres d'avertissement sur les côtés
        bar_height = int(60 * danger_ratio)
        bar_width = 8
        
        # Gauche
        pygame.draw.rect(surface, (*warning_color, alpha), 
                        (0, H // 2 - bar_height // 2, bar_width, bar_height), 
                        border_radius=2)
        # Droite
        pygame.draw.rect(surface, (*warning_color, alpha), 
                        (W - bar_width, H // 2 - bar_height // 2, bar_width, bar_height), 
                        border_radius=2)
        
        # Texte d'avertissement si danger élevé
        if danger_ratio > 0.6:
            txt = self.font_med.render(warning_text, True, warning_color)
            txt.set_alpha(int(255 * pulse))
            x = W // 2 - txt.get_width() // 2
            y = H // 2 + 80
            surface.blit(txt, (x, y))
