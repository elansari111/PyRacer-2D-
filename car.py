# ============================================================
#  PyRacer: Ultimate Neon Highway
#  car.py — Classe Player
# ============================================================

import pygame
import settings as S
from config import config


class Player:
    """Voiture du joueur : contrôles, physique, bonus, collisions."""
    _cache = {}

    def __init__(self, road_x: int, road_w: int, lane_count: int, car_color: str = None):
        self.road_x    = road_x
        self.road_w    = road_w
        self.lane_count = lane_count
        self.lane_w    = road_w // lane_count

        self.w = S.PLAYER_W
        self.h = S.PLAYER_H
        
        # Couleur de la voiture (personnalisable)
        self.car_color = car_color or config.get("car_color", "cyan")

        # Position initiale : voie centrale
        mid_lane = lane_count // 2
        self.x = road_x + self.lane_w * mid_lane + self.lane_w // 2 - self.w // 2
        self.y = S.SCREEN_H * 0.75

        # Vitesse de défilement (partagée avec road.py)
        self.speed     = 0.0
        self.target_speed = 0.0

        # État bonus
        self.nitro_charge  = S.NITRO_MAX
        self.nitro_active  = False
        self.nitro_timer   = 0
        self.shield_charge = 0
        self.shield_active = False
        self.shield_timer  = 0

        # Invincibilité après collision
        self.invincible   = False
        self.inv_timer    = 0
        self.blink        = True   # pour l'animation de clignotement

        # Statistiques
        self.lives        = S.MAX_LIVES

        # Animation
        self.anim_tilt    = 0.0   # inclinaison visuelle lors des virages
        self.trail_alpha  = 0
        
        # Ghost mode (traverser les ennemis)
        self.ghost_mode   = False
        self.ghost_timer  = 0
        
        # Statistiques de session
        self.distance_traveled = 0.0
        self.nitro_activations = 0
        self.max_speed_reached = 0.0

    # ----------------------------------------------------------
    def reset(self, road_x: int, road_w: int, lane_count: int, base_speed: float):
        """Réinitialise le joueur pour un nouveau niveau."""
        self.road_x     = road_x
        self.road_w     = road_w
        self.lane_count = lane_count
        self.lane_w     = road_w // lane_count

        mid_lane = lane_count // 2
        self.x   = road_x + self.lane_w * mid_lane + self.lane_w // 2 - self.w // 2
        self.y   = S.SCREEN_H * 0.75

        self.speed        = base_speed
        self.target_speed = base_speed
        self.nitro_charge = S.NITRO_MAX
        self.nitro_active = False
        self.nitro_timer  = 0
        self.shield_charge = 0
        self.shield_active = False
        self.shield_timer  = 0
        self.invincible    = False
        self.inv_timer     = 0
        self.anim_tilt     = 0.0
        self.ghost_mode    = False
        self.ghost_timer   = 0

    # ----------------------------------------------------------
    def handle_input(self, keys: pygame.key.ScancodeWrapper, dt: float,
                     base_speed: float, max_speed: float):
        """Calcule la vitesse cible et déplace le joueur latéralement."""
        moving_left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        accel        = keys[pygame.K_UP]    or keys[pygame.K_w]
        brake        = keys[pygame.K_DOWN]  or keys[pygame.K_s]

        # --- Vitesse longitudinale ---
        self.target_speed = base_speed
        if accel:
            self.target_speed = min(max_speed, self.target_speed * 1.15)
        if brake:
            self.target_speed = max(1.5, self.target_speed * 0.70)
        if self.nitro_active:
            self.target_speed = min(max_speed, self.target_speed * S.NITRO_MULT)

        self.speed += (self.target_speed - self.speed) * S.ACCEL_RATE * dt
        self.speed  = max(0.5, min(max_speed, self.speed))

        # Inclinaison visuelle
        if moving_left:
            self.anim_tilt = max(-6.0, self.anim_tilt - 1.5 * dt)
        elif moving_right:
            self.anim_tilt = min(6.0,  self.anim_tilt + 1.5 * dt)
        else:
            self.anim_tilt *= (1 - 0.15 * dt)

        # --- Déplacement latéral ---
        lateral = S.PLAYER_SPEED * (1 + self.speed * 0.05) * dt
        if moving_left:
            self.x = max(self.road_x + 4, self.x - lateral)
        if moving_right:
            self.x = min(self.road_x + self.road_w - self.w - 4, self.x + lateral)

    # ----------------------------------------------------------
    def activate_nitro(self):
        """Tente d'activer le nitro."""
        if self.nitro_charge >= S.NITRO_COST and not self.nitro_active:
            self.nitro_active  = True
            self.nitro_timer   = S.NITRO_DURATION
            self.nitro_charge -= S.NITRO_COST
            return True
        return False

    def activate_shield(self):
        """Tente d'activer le bouclier."""
        if self.shield_charge >= S.SHIELD_COST and not self.shield_active:
            self.shield_active = True
            self.shield_timer  = S.SHIELD_DURATION
            self.shield_charge -= S.SHIELD_COST
            return True
        return False

    # ----------------------------------------------------------
    def update(self, dt: float):
        """Met à jour les timers bonus / invincibilité."""
        # Met à jour la distance parcourue
        self.distance_traveled += self.speed * dt * S.PIXELS_TO_METERS
        
        # Met à jour la vitesse max
        current_speed_kmh = self.speed * 30
        if current_speed_kmh > self.max_speed_reached:
            self.max_speed_reached = current_speed_kmh
        
        # Nitro
        if self.nitro_active:
            self.nitro_timer -= dt
            if self.nitro_timer <= 0:
                self.nitro_active = False
        else:
            self.nitro_charge = min(S.NITRO_MAX,
                                    self.nitro_charge + S.NITRO_REGEN * dt)

        # Bouclier
        if self.shield_active:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shield_active = False

        # Invincibilité
        if self.invincible:
            self.inv_timer -= dt
            self.blink = int(self.inv_timer) % 8 > 3
            if self.inv_timer <= 0:
                self.invincible = False
                self.blink = True
                
        # Ghost mode
        if self.ghost_mode:
            self.ghost_timer -= dt
            if self.ghost_timer <= 0:
                self.ghost_mode = False

        # Recharge bouclier passive (via overtake → géré dans main)
        self.shield_charge = max(0, min(S.SHIELD_MAX, self.shield_charge))

    # ----------------------------------------------------------
    def take_hit(self) -> bool:
        """Subit une collision. Retourne True si le jeu doit se terminer."""
        if self.invincible or self.shield_active or self.ghost_mode:
            return False
        self.lives    -= 1
        self.invincible = True
        self.inv_timer  = S.INV_DURATION
        return self.lives <= 0
        
    def activate_ghost(self, duration: int):
        """Active le mode fantôme (traverser les ennemis)."""
        self.ghost_mode = True
        self.ghost_timer = duration

    # ----------------------------------------------------------
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x + 4, self.y + 4, self.w - 8, self.h - 8)
    
    # ----------------------------------------------------------
    def get_lane(self, road_x: int, lane_w: int) -> int:
        """Calcule la voie actuelle du joueur (0-based)."""
        relative_x = (self.x + self.w // 2) - road_x
        lane = int(relative_x / lane_w)
        return max(0, lane)

    # ----------------------------------------------------------
    def draw(self, surface: pygame.Surface):
        """Dessine la voiture du joueur."""
        if not self.blink:
            return   # clignotement invincibilité

        px, py = int(self.x), int(self.y)
        w, h   = self.w, self.h

        # ---- Car Body Cache ----
        # Determine the visual state of the car
        color_tuple = S.CAR_COLORS.get(self.car_color, S.C_CYAN)
        state_key = ("car", w, h, self.shield_active, self.car_color, self.ghost_mode)
        if state_key not in Player._cache:
            car_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            
            # Corps - utilise la couleur personnalisée
            if self.shield_active:
                body_col = S.C_CYAN
            else:
                # Mélange la couleur avec du blanc pour un effet néon
                base = color_tuple
                body_col = (min(255, base[0] + 40), min(255, base[1] + 40), min(255, base[2] + 40))
            
            # Mode ghost: transparence réduite
            alpha = 180 if self.ghost_mode else 255
            if self.ghost_mode:
                car_surf.set_alpha(alpha)
                
            pygame.draw.rect(car_surf, body_col, (4, 0, w - 8, h), border_radius=6)
            
            # Capot
            pygame.draw.rect(car_surf, (176, 204, 224), (6, 4, w - 12, 14))
            
            # Pare-brise
            pygame.draw.rect(car_surf, (77, 200, 255, 140), (6, 18, w - 12, 16))
            
            # Panneaux latéraux
            pygame.draw.rect(car_surf, (34, 102, 170), (4, 36, 8, 16))
            pygame.draw.rect(car_surf, (34, 102, 170), (w - 12, 36, 8, 16))
            
            # Roues
            for wx, wy in [(0, 8), (w - 6, 8), (0, h - 20), (w - 6, h - 20)]:
                pygame.draw.rect(car_surf, (30, 30, 30), (wx, wy, 6, 12), border_radius=2)
                
            # Phares
            pygame.draw.rect(car_surf, S.C_YELLOW, (6, 0, 8, 4))
            pygame.draw.rect(car_surf, S.C_YELLOW, (w - 14, 0, 8, 4))
            
            Player._cache[state_key] = car_surf

        # Rotate the car based on anim_tilt
        base_car = Player._cache[state_key]
        rotated_car = pygame.transform.rotate(base_car, -self.anim_tilt)
        rot_rect = rotated_car.get_rect(center=(px + w // 2, py + h // 2))

        # ---- Draw Trail (unrotated, behind the car) ----
        if self.nitro_active or self.speed > 6:
            trail_key = ("trail", w, self.nitro_active)
            if trail_key not in Player._cache:
                alpha  = 180 if self.nitro_active else 60
                col    = S.C_YELLOW if self.nitro_active else S.C_CYAN
                trail  = pygame.Surface((w, 50), pygame.SRCALPHA)
                points = [(0, 0), (w, 0), (w // 2 + 3, 50), (w // 2 - 3, 50)]
                pygame.draw.polygon(trail, (*col, alpha), points)
                Player._cache[trail_key] = trail
            
            # trail shifts slightly based on tilt
            ox = self.anim_tilt * 0.5
            surface.blit(Player._cache[trail_key], (px - ox, py + h - 5))

        # ---- Draw Glow ----
        if self.nitro_active:
            glow_key = ("glow", w, h)
            if glow_key not in Player._cache:
                glow = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (*S.C_YELLOW, 60), (0, 0, w + 16, h + 16))
                Player._cache[glow_key] = glow
            surface.blit(Player._cache[glow_key], (px - 8, py - 8))

        # ---- Draw Bouclier bubble ----
        if self.shield_active:
            shield_key = ("shield", w, h)
            if shield_key not in Player._cache:
                shield_surf = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
                pygame.draw.ellipse(shield_surf, (*S.C_CYAN, 60), (0, 0, w + 24, h + 24), 3)
                Player._cache[shield_key] = shield_surf
            surface.blit(Player._cache[shield_key], (px - 12, py - 12))
            
        # ---- Draw Ghost aura ----
        if self.ghost_mode:
            ghost_key = ("ghost", w, h)
            if ghost_key not in Player._cache:
                ghost_surf = pygame.Surface((w + 32, h + 32), pygame.SRCALPHA)
                for i in range(3):
                    offset = i * 4
                    pygame.draw.ellipse(ghost_surf, (200, 200, 255, 30 - i * 8), 
                                      (offset, offset, w + 32 - offset*2, h + 32 - offset*2), 2)
                Player._cache[ghost_key] = ghost_surf
            surface.blit(Player._cache[ghost_key], (px - 16, py - 16))

        # ---- Draw Rotated Car ----
        surface.blit(rotated_car, rot_rect.topleft)
