# ============================================================
#  PyRacer: Ultimate Neon Highway
#  game_states.py — Machine à états du jeu
# ============================================================

from enum import Enum, auto
import pygame
import math
import settings as S


class State(Enum):
    MENU       = auto()
    PLAYING    = auto()
    PAUSE      = auto()
    TRANSITION = auto()   # entre deux niveaux
    GAMEOVER   = auto()
    WIN        = auto()
    SETTINGS   = auto()   # menu des paramètres
    ACHIEVEMENTS = auto() # écran des succès
    CUSTOMIZE  = auto()   # personnalisation voiture


# ============================================================
#  Renderer d'écrans (Menu, Pause, Transition, GameOver, Win)
# ============================================================

class ScreenRenderer:
    """Dessine tous les écrans hors-jeu (menus, transitions, etc.)."""

    def __init__(self):
        self.font_giant  = pygame.font.SysFont("orbitron,consolas,monospace", 72, bold=True)
        self.font_big    = pygame.font.SysFont("orbitron,consolas,monospace", 42, bold=True)
        self.font_title  = pygame.font.SysFont("orbitron,consolas,monospace", 28, bold=True)
        self.font_med    = pygame.font.SysFont("orbitron,consolas,monospace", 18, bold=True)
        self.font_small  = pygame.font.SysFont("orbitron,consolas,monospace", 13)
        self.font_body   = pygame.font.SysFont("rajdhani,segoeui,sans",       16)
        self.font_tiny   = pygame.font.SysFont("orbitron,consolas,monospace", 10)

        self._road_scroll = 0.0   # animation route en menu
        self._menu_items = ["JOUER", "PARAMETRES", "SUCCES", "QUITTER"]
        self._menu_selected = 0
        self._settings_items = ["Audio", "Musique", "SFX", "Difficulte", "Couleur", "Retour"]
        self._settings_selected = 0
        
        # Pour l'écran de transition
        self._transition_selected = 0  # 0 = Continuer, 1 = Menu
        self._is_last_level = False
        
        # NOUVEAU: Micro-interactions UI
        self._prev_menu_selected = -1  # Pour détecter changement de sélection
        self._selection_change_time = 0  # Timer pour animation
        self._hover_pulse = 0.0  # Animation de pulse

    # ----------------------------------------------------------
    def draw_menu(self, surface: pygame.Surface,
                  selected_level: int, hi_scores: list, dt: float):
        W, H = surface.get_size()
        surface.fill(S.C_BG)

        # Animation route stylisée
        self._road_scroll = (self._road_scroll + 4 * dt) % 80
        road_x    = (W - S.ROAD_WIDTH) // 2
        pygame.draw.rect(surface, S.C_ROAD[0], (road_x, 0, S.ROAD_WIDTH, H))
        lw = S.ROAD_WIDTH // 3
        for l in range(1, 3):
            lx = road_x + lw * l
            y  = -self._road_scroll
            while y < H:
                pygame.draw.rect(surface, (255, 255, 255, 18),
                                 (lx - 1, int(y), 2, 36))
                y += 80

        # Lueurs latérales
        for side_x, col in [(road_x, S.C_CYAN), (road_x + S.ROAD_WIDTH, S.C_CYAN)]:
            pygame.draw.line(surface, (*col, 120), (side_x, 0), (side_x, H), 2)

        # ---- Titre ----
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.002))
        cy    = int(pulse * 4)

        t1 = self.font_giant.render("PYRACER", True, S.C_CYAN)
        t2 = self.font_big.render("ULTIMATE NEON HIGHWAY", True, S.C_MAGENTA)
        surface.blit(t1, t1.get_rect(centerx=W // 2, centery=130 + cy))
        surface.blit(t2, t2.get_rect(centerx=W // 2, centery=195 + cy))

        tag = self.font_small.render("LA VITESSE  •  LE RÉFLEXE  •  LE SCORE",
                                     True, (200, 200, 200))
        surface.blit(tag, tag.get_rect(centerx=W // 2, centery=230))

        # ---- Sélection niveau ----
        level_labels = ["VILLE", "AUTOROUTE", "CIRCUIT"]
        total_w = 3 * 140 + 2 * 16
        sx0     = W // 2 - total_w // 2
        for i, lbl in enumerate(level_labels):
            bx  = sx0 + i * 156
            by  = 280
            bw, bh = 140, 44
            col = S.LEVEL_COLORS[i]
            active = (i == selected_level)
            bg_a   = 60 if active else 15
            pygame.draw.rect(surface, (*col, bg_a), (bx, by, bw, bh), border_radius=4)
            pygame.draw.rect(surface, (*col, 200 if active else 80),
                             (bx, by, bw, bh), 2, border_radius=4)
            txt = self.font_small.render(lbl, True, col)
            surface.blit(txt, txt.get_rect(centerx=bx + bw // 2,
                                           centery=by + bh // 2))
            hi = self.font_small.render(f"HI {hi_scores[i]:,}", True,
                                        (180, 180, 180))
            surface.blit(hi, hi.get_rect(centerx=bx + bw // 2,
                                         centery=by + bh + 12))

        # ---- Menu items ----
        menu_y = 360
        for i, item in enumerate(self._menu_items):
            color = S.C_CYAN if i == self._menu_selected else (150, 150, 170)
            y_pos = menu_y + i * 42
            self._draw_button(surface, W // 2, y_pos, item, color, selected=(i == self._menu_selected))

        # ---- Contrôles ----
        controls = [
            "← →  Déplacer       ↑  Accélérer       ↓  Freiner",
            "ESPACE  Nitro           B  Bouclier           P  Pause",
        ]
        for i, line in enumerate(controls):
            ctxt = self.font_small.render(line, True, (120, 120, 140))
            surface.blit(ctxt, ctxt.get_rect(centerx=W // 2, centery=580 + i * 20))
            
    def menu_next(self):
        """Sélectionne l'item suivant du menu."""
        self._prev_menu_selected = self._menu_selected
        self._menu_selected = (self._menu_selected + 1) % len(self._menu_items)
        self._selection_change_time = pygame.time.get_ticks()
        return self._selection_changed()  # Retourne True si changement
        
    def menu_prev(self):
        """Sélectionne l'item précédent du menu."""
        self._prev_menu_selected = self._menu_selected
        self._menu_selected = (self._menu_selected - 1) % len(self._menu_items)
        self._selection_change_time = pygame.time.get_ticks()
        return self._selection_changed()
    
    # NOUVEAU: Détection de changement pour feedback sonore
    def _selection_changed(self) -> bool:
        """Retourne True si la sélection a changé (pour son)."""
        return self._prev_menu_selected != self._menu_selected
        
    def menu_get_selected(self) -> str:
        """Retourne l'item sélectionné."""
        return self._menu_items[self._menu_selected]

    # ----------------------------------------------------------
    def draw_pause(self, surface: pygame.Surface):
        W, H = surface.get_size()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 5, 15, 180))
        surface.blit(overlay, (0, 0))

        t = self.font_big.render("PAUSE", True, S.C_CYAN)
        surface.blit(t, t.get_rect(centerx=W // 2, centery=H // 2 - 60))
        self._draw_button(surface, W // 2, H // 2 + 20,  "▶  REPRENDRE", S.C_CYAN)
        self._draw_button(surface, W // 2, H // 2 + 80, "⏎  MENU",      S.C_MAGENTA)

    # ----------------------------------------------------------
    def draw_transition(self, surface: pygame.Surface,
                        level: int, stats: dict, last_level: bool):
        """Dessine l'écran de transition entre niveaux avec choix."""
        W, H = surface.get_size()
        surface.fill(S.C_BG)
        col = S.LEVEL_COLORS[level]
        
        # Mémorise si c'est le dernier niveau
        self._is_last_level = last_level

        t1 = self.font_big.render(f"NIVEAU {level + 1} TERMINÉ", True, col)
        t2 = self.font_med.render(S.LEVEL_NAMES[level], True, (200, 200, 200))
        surface.blit(t1, t1.get_rect(centerx=W // 2, centery=130))
        surface.blit(t2, t2.get_rect(centerx=W // 2, centery=178))

        # Stats grid 2×2
        items = [
            ("SCORE",        f"{stats['score']:,}"),
            ("DÉPASSEMENTS", str(stats["overtakes"])),
            ("BONUS",        str(stats["bonuses"])),
            ("STREAK MAX",   str(stats["max_streak"])),
        ]
        gx, gy = W // 2 - 175, 220
        for i, (label, val) in enumerate(items):
            bx = gx + (i % 2) * 190
            by = gy + (i // 2) * 90
            pygame.draw.rect(surface, (255, 255, 255, 12), (bx, by, 175, 76),
                             border_radius=4)
            pygame.draw.rect(surface, (255, 255, 255, 30), (bx, by, 175, 76),
                             1, border_radius=4)
            lbl = self.font_small.render(label, True, (160, 160, 180))
            val_txt = self.font_med.render(val, True, col)
            surface.blit(lbl, lbl.get_rect(centerx=bx + 87, centery=by + 22))
            surface.blit(val_txt, val_txt.get_rect(centerx=bx + 87, centery=by + 52))

        # ---- Boutons de choix ----
        if last_level:
            # Dernier niveau: seulement Victoire et Menu
            self._draw_button(surface, W // 2, 400, "🏆  VICTOIRE !", 
                            S.C_YELLOW if self._transition_selected == 0 else (150, 150, 150))
            self._draw_button(surface, W // 2, 460, "⏎  MENU", 
                            S.C_MAGENTA if self._transition_selected == 1 else (150, 150, 150))
        else:
            # Niveau normal: Niveau Suivant et Menu
            colors_next = S.C_CYAN if self._transition_selected == 0 else (150, 150, 150)
            colors_menu = S.C_MAGENTA if self._transition_selected == 1 else (150, 150, 150)
            
            self._draw_button(surface, W // 2, 400, "▶  NIVEAU SUIVANT", colors_next)
            self._draw_button(surface, W // 2, 460, "⏎  RETOUR MENU", colors_menu)
            
        # Instructions
        hint = self.font_small.render("↑↓: Choisir  ENTER: Confirmer", True, (100, 100, 120))
        surface.blit(hint, hint.get_rect(centerx=W // 2, centery=H - 30))
        
    def transition_next(self):
        """Change la sélection dans l'écran de transition."""
        self._transition_selected = (self._transition_selected + 1) % 2
            
    def transition_prev(self):
        """Change la sélection dans l'écran de transition."""
        self._transition_selected = (self._transition_selected - 1) % 2
            
    def transition_get_selected(self) -> int:
        """Retourne l'option sélectionnée (0 = Continuer/Victoire, 1 = Menu)."""
        return self._transition_selected
        
    def transition_reset(self):
        """Réinitialise la sélection de transition."""
        self._transition_selected = 0

    # ----------------------------------------------------------
    def draw_gameover(self, surface: pygame.Surface,
                      score: int, hi_score: int, new_record: bool):
        W, H = surface.get_size()
        surface.fill(S.C_BG)

        t = self.font_big.render("GAME OVER", True, S.C_MAGENTA)
        surface.blit(t, t.get_rect(centerx=W // 2, centery=180))

        sc = self.font_giant.render(f"{score:,}", True, S.C_YELLOW)
        surface.blit(sc, sc.get_rect(centerx=W // 2, centery=270))

        sub = ("🏆  NOUVEAU RECORD !" if new_record
               else f"Record : {hi_score:,}")
        st = self.font_med.render(sub, True,
                                  S.C_YELLOW if new_record else (160, 160, 180))
        surface.blit(st, st.get_rect(centerx=W // 2, centery=330))

        self._draw_button(surface, W // 2, 400, "▶  REJOUER",  S.C_CYAN)
        self._draw_button(surface, W // 2, 460, "⏎  MENU",    S.C_MAGENTA)

    # ----------------------------------------------------------
    def draw_win(self, surface: pygame.Surface, total_score: int, hi_scores: list):
        W, H = surface.get_size()
        surface.fill(S.C_BG)

        t = self.font_big.render("VICTOIRE !", True, S.C_YELLOW)
        surface.blit(t, t.get_rect(centerx=W // 2, centery=160))
        sub = self.font_med.render("Vous avez conquis les 3 niveaux.", True, (200, 200, 200))
        surface.blit(sub, sub.get_rect(centerx=W // 2, centery=212))

        sc = self.font_giant.render(f"{total_score:,}", True, S.C_YELLOW)
        surface.blit(sc, sc.get_rect(centerx=W // 2, centery=300))

        hi = self.font_small.render(f"Meilleur score toutes niveaux : {max(hi_scores):,}",
                                    True, (180, 180, 180))
        surface.blit(hi, hi.get_rect(centerx=W // 2, centery=360))

        self._draw_button(surface, W // 2, 430, "⏎  MENU", S.C_YELLOW)
        
    def draw_settings(self, surface: pygame.Surface, config_data: dict):
        """Dessine l'écran des paramètres."""
        W, H = surface.get_size()
        surface.fill(S.C_BG)
        
        # Titre
        t = self.font_big.render("PARAMETRES", True, S.C_CYAN)
        surface.blit(t, t.get_rect(centerx=W // 2, centery=80))
        
        # Options
        items = [
            ("Audio", "ON" if config_data.get("audio_enabled") else "OFF"),
            ("Musique", f"{int(config_data.get('music_volume', 0.5) * 100)}%"),
            ("SFX", f"{int(config_data.get('sfx_volume', 0.8) * 100)}%"),
            ("Difficulte", config_data.get("difficulty", "normal").upper()),
            ("Couleur", config_data.get("car_color", "cyan").upper()),
            ("Retour", ""),
        ]
        
        y_start = 150
        for i, (label, value) in enumerate(items):
            y_pos = y_start + i * 50
            is_selected = i == self._settings_selected
            
            # Fond avec style néon
            if is_selected:
                # Lueur externe
                for j, alpha in enumerate([40, 25, 15]):
                    offset = (j + 1) * 2
                    pygame.draw.rect(surface, (*S.C_CYAN[:3], alpha), 
                                   (W//2 - 202 - offset, y_pos - 22 - offset, 
                                    404 + offset*2, 49 + offset*2), 
                                   1, border_radius=6 + offset)
                # Fond
                pygame.draw.rect(surface, (*S.C_CYAN, 25), (W//2 - 200, y_pos - 20, 400, 45), border_radius=6)
                # Bordure brillante
                pygame.draw.rect(surface, (*S.C_CYAN, 200), (W//2 - 200, y_pos - 20, 400, 45), 2, border_radius=6)
            else:
                # Style minimal non-sélectionné
                pygame.draw.rect(surface, (255, 255, 255, 12), (W//2 - 200, y_pos - 20, 400, 45), border_radius=6)
                pygame.draw.rect(surface, (255, 255, 255, 60), (W//2 - 200, y_pos - 20, 400, 45), 1, border_radius=6)
            
            # Label
            color = S.C_CYAN if is_selected else (180, 180, 180)
            lbl = self.font_med.render(label, True, color)
            surface.blit(lbl, (W//2 - 180, y_pos - 10))
            
            # Valeur
            if value:
                val_color = S.C_YELLOW if is_selected else (150, 150, 150)
                val = self.font_med.render(value, True, val_color)
                surface.blit(val, (W//2 + 180 - val.get_width(), y_pos - 10))
                
        # Instructions
        hint = self.font_small.render("↑↓: Changer  ←→: Modifier  ENTER: Confirmer", True, (100, 100, 120))
        surface.blit(hint, hint.get_rect(centerx=W // 2, centery=H - 40))
        
    def settings_next(self):
        self._settings_selected = (self._settings_selected + 1) % len(self._settings_items)
        
    def settings_prev(self):
        self._settings_selected = (self._settings_selected - 1) % len(self._settings_items)
        
    def settings_get_selected(self) -> int:
        return self._settings_selected
        
    def draw_achievements(self, surface: pygame.Surface, achievements_mgr):
        """Dessine l'écran des succès."""
        W, H = surface.get_size()
        surface.fill(S.C_BG)
        
        # Titre
        t = self.font_big.render("SUCCES", True, S.C_YELLOW)
        surface.blit(t, t.get_rect(centerx=W // 2, centery=60))
        
        # Progression globale
        pct = achievements_mgr.get_completion_percentage()
        prog = self.font_med.render(f"Progression: {pct:.1f}%", True, S.C_CYAN)
        surface.blit(prog, prog.get_rect(centerx=W // 2, centery=100))
        
        # Barre de progression
        bar_w = 300
        bar_x = W//2 - bar_w//2
        pygame.draw.rect(surface, (50, 50, 70), (bar_x, 125, bar_w, 10), border_radius=5)
        pygame.draw.rect(surface, S.C_CYAN, (bar_x, 125, int(bar_w * pct / 100), 10), border_radius=5)
        
        # Liste des succès
        by_tier = achievements_mgr.get_achievements_by_tier()
        y_pos = 160
        colors_tier = {
            "bronze": (205, 127, 50),
            "silver": (192, 192, 192),
            "gold": (255, 215, 0),
            "platinum": (229, 228, 226),
        }
        
        for tier in ["platinum", "gold", "silver", "bronze"]:
            for ach in by_tier.get(tier, []):
                if y_pos > H - 60:
                    break
                    
                color = colors_tier.get(tier.value if hasattr(tier, 'value') else tier, (200, 200, 200))
                if not ach.unlocked:
                    color = (80, 80, 80)  # Grisé si non débloqué
                    
                # Icône
                icon = self.font_med.render(ach.icon, True, color if ach.unlocked else (80, 80, 80))
                surface.blit(icon, (50, y_pos))
                
                # Nom
                name = self.font_small.render(ach.name, True, color if ach.unlocked else (100, 100, 100))
                surface.blit(name, (90, y_pos))
                
                # Description
                desc = self.font_tiny.render(ach.description, True, (120, 120, 120))
                surface.blit(desc, (90, y_pos + 18))
                
                y_pos += 45
                
        # Bouton retour
        self._draw_button(surface, W // 2, H - 40, "⏎  RETOUR", S.C_MAGENTA)

    # ----------------------------------------------------------
    def _draw_button(self, surface: pygame.Surface,
                     cx: int, cy: int, text: str, color: tuple,
                     selected: bool = False, hover_scale: float = 1.0):
        # NOUVEAU: Animation de pulse sur sélection
        pulse = 1.0
        if selected:
            pulse = 1.0 + math.sin(pygame.time.get_ticks() * 0.008) * 0.03
            hover_scale *= pulse
        
        # NOUVEAU: Scale appliqué
        scale = hover_scale if selected else 1.0
        
        txt = self.font_med.render(text, True, (255, 255, 255) if selected else color)
        tw, th = txt.get_size()
        bw = int((tw + 40) * scale)
        bh = int((th + 16) * scale)
        bx, by = cx - bw // 2, cy - bh // 2

        if selected:
            # Style sélectionné: néon glow avec animation
            pulse_alpha = int(40 + math.sin(pygame.time.get_ticks() * 0.01) * 15)
            pygame.draw.rect(surface, (*color, pulse_alpha), (bx, by, bw, bh),
                           border_radius=4)
            
            # Lueur externe pulsante
            glow_layers = 4
            for i in range(glow_layers):
                offset = (i + 1) * 2
                alpha = int(40 * (1 - i/glow_layers) * pulse)
                pygame.draw.rect(surface, (*color, alpha), 
                               (bx - offset, by - offset, bw + offset*2, bh + offset*2),
                               2, border_radius=4 + offset)
            
            # Bordure brillante
            pygame.draw.rect(surface, (*color, 220), (bx, by, bw, bh),
                           2, border_radius=4)
            
            # NOUVEAU: Ligne brillante animée
            line_width = int(2 + math.sin(pygame.time.get_ticks() * 0.015) * 1)
            pygame.draw.line(surface, S.C_WHITE, 
                           (bx + 4, by + 2), (bx + bw - 4, by + 2), line_width)
            
            # NOUVEAU: Point indicateur sur le côté
            indicator_x = bx - 15
            pygame.draw.circle(surface, color, (int(indicator_x), cy), 4)
            pygame.draw.circle(surface, (*color, 100), (int(indicator_x), cy), 8, 1)
        else:
            # Style non-sélectionné: minimal avec hover subtil
            bg_alpha = int(15 + math.sin(pygame.time.get_ticks() * 0.005 + cy * 0.01) * 5)
            pygame.draw.rect(surface, (255, 255, 255, bg_alpha), (bx, by, bw, bh),
                           border_radius=4)
            pygame.draw.rect(surface, (*color, 60), (bx, by, bw, bh),
                           1, border_radius=4)
        
        # Texte centré
        txt_rect = txt.get_rect(centerx=cx, centery=cy)
        surface.blit(txt, txt_rect)

        return pygame.Rect(bx, by, bw, bh)
