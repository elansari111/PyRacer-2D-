# ============================================================
#  PyRacer: Ultimate Neon Highway
#  visual_effects.py — Système d'effets visuels avancé
# ============================================================

import pygame
import math
import random
import settings as S


class GlowEffect:
    """Gère les effets de lueur néon dynamiques."""
    
    _glow_cache = {}
    
    @classmethod
    def get_glow_surface(cls, width: int, height: int, color: tuple, intensity: float = 1.0) -> pygame.Surface:
        """Crée ou récupère une surface de lueur mise en cache."""
        key = (width, height, color, intensity)
        if key not in cls._glow_cache:
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            center = (width // 2, height // 2)
            max_radius = min(width, height) // 2
            
            for r in range(max_radius, 0, -1):
                alpha = int(255 * (1 - r / max_radius) * 0.3 * intensity)
                if alpha > 0:
                    pygame.draw.circle(surf, (*color[:3], alpha), center, r)
            
            cls._glow_cache[key] = surf
        return cls._glow_cache[key]
    
    @classmethod
    def draw_glow_rect(cls, surface: pygame.Surface, rect: pygame.Rect, color: tuple, 
                       intensity: float = 1.0, border_radius: int = 0):
        """Dessine un rectangle avec effet de lueur."""
        glow_size = 20
        glow_surf = cls.get_glow_surface(rect.width + glow_size * 2, 
                                         rect.height + glow_size * 2, 
                                         color, intensity)
        surface.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size), 
                    special_flags=pygame.BLEND_ADD)


class AdvancedParticle:
    """Particule avancée avec physique réaliste et effets visuels."""
    
    TYPES = {
        'spark': {'life': 30, 'gravity': 0.3, 'friction': 0.98, 'size': (2, 4)},
        'smoke': {'life': 60, 'gravity': -0.1, 'friction': 0.95, 'size': (8, 20)},
        'fire': {'life': 40, 'gravity': -0.3, 'friction': 0.97, 'size': (3, 8)},
        'debris': {'life': 50, 'gravity': 0.4, 'friction': 0.99, 'size': (3, 6)},
        'trail': {'life': 25, 'gravity': 0, 'friction': 0.90, 'size': (4, 10)},
        'star': {'life': 45, 'gravity': -0.05, 'friction': 0.96, 'size': (2, 5)},
    }
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 color: tuple, ptype: str = 'spark', size: float = None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.type = ptype
        self.config = self.TYPES.get(ptype, self.TYPES['spark'])
        self.life = self.config['life'] + random.randint(-5, 5)
        self.max_life = self.life
        self.size = size or random.uniform(*self.config['size'])
        self.initial_size = self.size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        
    def update(self, dt: float):
        """Met à jour la physique de la particule."""
        self.vy += self.config['gravity'] * dt
        self.vx *= self.config['friction']
        self.vy *= self.config['friction']
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        
        self.rotation += self.rotation_speed * dt
        
        # Réduction de taille avec la vie
        life_pct = self.life / self.max_life
        self.size = self.initial_size * max(0.1, life_pct)
        
    def draw(self, surface: pygame.Surface):
        """Dessine la particule avec effets avancés."""
        if self.life <= 0:
            return
            
        alpha = int(255 * (self.life / self.max_life))
        
        if self.type == 'spark':
            # Étincelles avec trail
            end_x = self.x - self.vx * 3
            end_y = self.y - self.vy * 3
            pygame.draw.line(surface, (*self.color[:3], alpha), 
                           (int(self.x), int(self.y)), 
                           (int(end_x), int(end_y)), 
                           max(1, int(self.size)))
            
        elif self.type == 'smoke':
            # Fumée avec gradient
            for i in range(3):
                offset = i * 2
                size = self.size + i * 3
                a = max(0, alpha - i * 40)
                pygame.draw.circle(surface, (*self.color[:3], a), 
                                 (int(self.x + offset), int(self.y - offset)), 
                                 int(size))
                                 
        elif self.type == 'fire':
            # Feu avec lueur
            glow = GlowEffect.get_glow_surface(int(self.size * 4), int(self.size * 4), 
                                                self.color, 0.8)
            surface.blit(glow, (int(self.x - self.size * 2), int(self.y - self.size * 2)), 
                        special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(surface, (255, 255, 200, alpha), 
                             (int(self.x), int(self.y)), 
                             max(1, int(self.size * 0.5)))
                             
        elif self.type == 'trail':
            # Trail avec fade
            pygame.draw.circle(surface, (*self.color[:3], alpha // 2), 
                             (int(self.x), int(self.y)), 
                             int(self.size))
                             
        else:
            # Défaut: cercle simple
            pygame.draw.circle(surface, (*self.color[:3], alpha), 
                             (int(self.x), int(self.y)), 
                             max(1, int(self.size)))


class ParticleSystem:
    """Système de gestion des particules."""
    
    def __init__(self):
        self.particles = []
        
    def emit(self, x: float, y: float, count: int, color: tuple, 
             ptype: str = 'spark', spread: float = 5.0, speed: float = 3.0):
        """Émet un burst de particules."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            v = random.uniform(speed * 0.5, speed * 1.5)
            vx = math.cos(angle) * v
            vy = math.sin(angle) * v
            
            # Variation de couleur
            color_var = tuple(min(255, max(0, c + random.randint(-20, 20))) 
                            for c in color[:3])
            
            self.particles.append(AdvancedParticle(
                x + random.uniform(-spread, spread),
                y + random.uniform(-spread, spread),
                vx, vy, color_var, ptype
            ))
            
    def emit_trail(self, x: float, y: float, color: tuple, 
                   direction: tuple = (0, 1), intensity: float = 1.0):
        """Émet une traînée continue."""
        for _ in range(int(3 * intensity)):
            vx = direction[0] * random.uniform(0.5, 1.5) + random.uniform(-0.5, 0.5)
            vy = direction[1] * random.uniform(0.5, 1.5) + random.uniform(-0.5, 0.5)
            self.particles.append(AdvancedParticle(
                x + random.uniform(-3, 3), y + random.uniform(-3, 3),
                vx, vy, color, 'trail', size=random.uniform(3, 6)
            ))
            
    def emit_exhaust(self, x: float, y: float, speed_ratio: float, 
                     nitro_active: bool = False):
        """Émet de la fumée d'échappement."""
        if nitro_active:
            # Flammes nitro
            color = (255, 100 + random.randint(0, 50), 0)
            self.emit(x, y, 2, color, 'fire', spread=3, speed=4)
        elif speed_ratio > 0.3:
            # Fumée normale
            gray = int(150 - speed_ratio * 50)
            color = (gray, gray, gray)
            self.emit(x, y, 1, color, 'smoke', spread=2, speed=1)
            
    def emit_sparks(self, x: float, y: float, count: int = 8, 
                   color: tuple = None, intensity: float = 1.0):
        """Émet des étincelles (collision, friction)."""
        color = color or S.C_YELLOW
        self.emit(x, y, int(count * intensity), color, 'spark', spread=5, speed=6)
        
    def emit_collision(self, x: float, y: float, intensity: float = 1.0):
        """Émet un effet de collision spectaculaire."""
        # Étincelles jaunes/oranges
        self.emit(x, y, int(15 * intensity), (255, 200, 50), 'spark', spread=8, speed=8)
        # Débris gris
        self.emit(x, y, int(8 * intensity), (150, 150, 150), 'debris', spread=6, speed=5)
        # Fumée
        self.emit(x, y, int(5 * intensity), (100, 100, 100), 'smoke', spread=10, speed=2)
        
    def update(self, dt: float):
        """Met à jour toutes les particules."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        
    def draw(self, surface: pygame.Surface):
        """Dessine toutes les particules."""
        for p in self.particles:
            p.draw(surface)
            
    def clear(self):
        """Efface toutes les particules."""
        self.particles.clear()


class ScreenEffects:
    """Effets d'écran (shake, flash, transition)."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.shake_amount = 0.0
        self.shake_decay = 0.9
        self.flash_color = None
        self.flash_alpha = 0
        self.time_dilation = 1.0
        self.vignette = self._create_vignette()
        self.vignette_enabled = True
        
    def _create_vignette(self) -> pygame.Surface:
        """Crée une vignette pour l'effet de bord d'écran."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self.width // 2, self.height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(0, self.height, 4):
            for x in range(0, self.width, 4):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                alpha = int(80 * (dist / max_dist) ** 2)
                if alpha > 8:
                    pygame.draw.rect(surf, (0, 0, 5, min(alpha, 55)), 
                                   (x, y, 4, 4))
        return surf
        
    def shake(self, intensity: float):
        """Déclenche un effet de tremblement d'écran."""
        self.shake_amount = min(intensity, 30)
        
    def flash(self, color: tuple = (255, 255, 255), duration: int = 10):
        """Déclenche un flash d'écran."""
        self.flash_color = color
        self.flash_alpha = 255
        self.flash_duration = duration
        self.flash_timer = duration
        
    def update(self, dt: float):
        """Met à jour les effets d'écran."""
        # Shake decay
        self.shake_amount *= self.shake_decay
        if self.shake_amount < 0.5:
            self.shake_amount = 0
            
        # Flash fade
        if self.flash_alpha > 0:
            self.flash_alpha = int(255 * (self.flash_timer / self.flash_duration))
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_alpha = 0
                
    def apply(self, surface: pygame.Surface, screen_shake_enabled: bool = True) -> pygame.Surface:
        """Applique tous les effets d'écran et retourne la surface modifiée."""
        # Shake offset
        if screen_shake_enabled and self.shake_amount > 0:
            offset_x = random.uniform(-self.shake_amount, self.shake_amount)
            offset_y = random.uniform(-self.shake_amount, self.shake_amount)
            
            # Créer une surface plus grande pour le shake
            shaken = pygame.Surface((self.width + 40, self.height + 40), pygame.SRCALPHA)
            shaken.fill((5, 5, 15, 255))
            shaken.blit(surface, (20 + offset_x, 20 + offset_y))
            # Rogner au centre
            result = pygame.Surface((self.width, self.height))
            result.blit(shaken, (0, 0), (20, 20, self.width, self.height))
        else:
            result = surface.copy()
            
        # Flash overlay
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surf.fill((*self.flash_color[:3], self.flash_alpha))
            result.blit(flash_surf, (0, 0), special_flags=pygame.BLEND_ADD)
            
        # Vignette légère (optionnelle via config dans main)
        if getattr(self, "vignette_enabled", True):
            result.blit(self.vignette, (0, 0))
        
        return result


class AnimatedBackground:
    """Arrière-plan animé avec grille néon et étoiles."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid_offset = 0
        self.stars = [(random.randint(0, width), 
                      random.randint(0, height), 
                      random.uniform(0.5, 2)) for _ in range(100)]
        self.star_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
    def update(self, dt: float, speed: float = 1.0):
        """Met à jour l'animation de l'arrière-plan."""
        self.grid_offset = (self.grid_offset + speed * dt) % 40
        
        # Animation des étoiles
        self.star_surf.fill((0, 0, 0, 0))
        for i, (x, y, size) in enumerate(self.stars):
            twinkle = abs(math.sin(pygame.time.get_ticks() * 0.003 + i)) * 255
            pygame.draw.circle(self.star_surf, (255, 255, 255, int(twinkle)), 
                             (int(x), int(y)), int(size))
            
    def draw(self, surface: pygame.Surface, level: int = 0):
        """Dessine l'arrière-plan animé."""
        # Couleur de base selon le niveau
        base_colors = [(10, 10, 25), (8, 8, 20), (15, 10, 8)]
        surface.fill(base_colors[level])
        
        # Étoiles
        surface.blit(self.star_surf, (0, 0))
        
        # Grille néon
        grid_color = (*S.LEVEL_COLORS[level][:3], 15)
        
        # Lignes verticales
        for x in range(0, self.width, 40):
            pygame.draw.line(surface, grid_color, (x, 0), (x, self.height), 1)
            
        # Lignes horizontales animées
        y = self.grid_offset
        while y < self.height:
            pygame.draw.line(surface, grid_color, (0, int(y)), (self.width, int(y)), 1)
            y += 40
            
        # Perspective lines (effet de profondeur)
        center_x = self.width // 2
        for i in range(-5, 6):
            x = center_x + i * 80
            pygame.draw.line(surface, (*grid_color[:3], 8), 
                           (center_x, self.height // 2), (x, self.height), 2)


class CarRenderer:
    """Rendu avancé des voitures avec effets visuels."""
    
    @staticmethod
    def draw_enhanced_player(surface: pygame.Surface, player, color: tuple, 
                             tilt: float = 0, nitro_active: bool = False,
                             ghost_mode: bool = False):
        """Dessine la voiture du joueur avec effets avancés."""
        x, y = int(player.x), int(player.y)
        w, h = player.w, player.h
        
        # Effet ghost
        if ghost_mode:
            ghost_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            for i in range(3):
                offset = i * 3
                alpha = 80 - i * 20
                pygame.draw.rect(ghost_surf, (200, 200, 255, alpha), 
                               (offset, offset, w + 20 - offset * 2, h + 20 - offset * 2),
                               border_radius=6)
            surface.blit(ghost_surf, (x - 10, y - 10))
        
        # Lueur nitro
        if nitro_active:
            glow = GlowEffect.get_glow_surface(w + 40, h + 40, (255, 150, 0), 1.5)
            surface.blit(glow, (x - 20, y - 20), special_flags=pygame.BLEND_ADD)
            
        # Ombre portée
        shadow_offset = 4 + abs(tilt) * 0.5
        pygame.draw.ellipse(surface, (0, 0, 0, 60), 
                          (x + shadow_offset, y + h - 10 + shadow_offset, 
                           w, 15))
        
        # Corps principal avec inclinaison
        tilt_x = int(tilt * 2)
        body_points = [
            (x + 4 + tilt_x, y + 4),      # Haut gauche
            (x + w - 4 + tilt_x, y + 4),  # Haut droit
            (x + w - tilt_x, y + h - 4),  # Bas droit
            (x + tilt_x, y + h - 4),      # Bas gauche
        ]
        body_col = (
            min(255, color[0] + 30),
            min(255, color[1] + 30),
            min(255, color[2] + 30),
        )
        pygame.draw.polygon(surface, body_col, body_points)
        pygame.draw.polygon(surface, color, body_points, 2)
        
        # Lignes de détail
        pygame.draw.line(surface, (*S.C_WHITE[:3], 100), 
                        (x + w//2 + tilt_x, y + 8), 
                        (x + w//2 - tilt_x, y + h - 8), 2)
        
        # Cockpit/fenêtre
        cockpit_color = (20, 30, 50)
        cockpit_points = [
            (x + 8 + tilt_x * 0.5, y + 12),
            (x + w - 8 + tilt_x * 0.5, y + 12),
            (x + w - 4 - tilt_x * 0.5, y + 28),
            (x + 4 - tilt_x * 0.5, y + 28),
        ]
        pygame.draw.polygon(surface, cockpit_color, cockpit_points)
        pygame.draw.polygon(surface, (100, 150, 200), cockpit_points, 1)
        
        # Feux arrière
        if nitro_active:
            # Flammes nitro
            for i, offset in enumerate([-8, w + 8]):
                flame_points = [
                    (x + w//2 + offset, y + h - 2),
                    (x + w//2 + offset + random.randint(-5, 5), y + h + 15 + random.randint(0, 10)),
                    (x + w//2 + offset + (6 if offset < 0 else -6), y + h - 2),
                ]
                pygame.draw.polygon(surface, (255, 100 + random.randint(0, 50), 0), flame_points)
        else:
            # Feux normaux
            light_color = (255, 50, 50) if player.speed > 0 else (150, 0, 0)
            pygame.draw.rect(surface, light_color, (x + 4, y + h - 4, 8, 4), border_radius=2)
            pygame.draw.rect(surface, light_color, (x + w - 12, y + h - 4, 8, 4), border_radius=2)
            
        # Feux avant
        pygame.draw.rect(surface, (200, 220, 255), (x + 2, y, 6, 4), border_radius=1)
        pygame.draw.rect(surface, (200, 220, 255), (x + w - 8, y, 6, 4), border_radius=1)
        
        # Lueur des phares
        if nitro_active or player.speed > 5:
            headlight_glow = GlowEffect.get_glow_surface(60, 60, (200, 220, 255), 0.5)
            surface.blit(headlight_glow, (x - 25, y - 20), special_flags=pygame.BLEND_ADD)
            
    @staticmethod
    def draw_enhanced_enemy(surface: pygame.Surface, enemy, color: tuple, 
                           speed_ratio: float = 1.0):
        """Dessine un ennemi avec effets avancés."""
        x, y = int(enemy.x), int(enemy.y)
        w, h = enemy.w, enemy.h
        
        # Ombre
        pygame.draw.ellipse(surface, (0, 0, 0, 40), 
                          (x + 3, y + h - 8, w, 12))
        
        # Corps avec style selon le type
        if enemy.type == 0:  # Standard
            # Forme classique
            pygame.draw.rect(surface, color, (x, y, w, h), border_radius=4)
            # Rayures
            pygame.draw.line(surface, (*S.C_WHITE[:3], 80), 
                           (x + w//2, y + 5), (x + w//2, y + h - 5), 2)
            
        elif enemy.type == 1:  # Rapide - aérodynamique
            # Forme pointue
            points = [
                (x + w//2, y),        # Nez pointu
                (x + w, y + h//3),
                (x + w, y + h - 5),
                (x + w//2, y + h),    # Arrière arrondi
                (x, y + h - 5),
                (x, y + h//3),
            ]
            pygame.draw.polygon(surface, color, points)
            # Ligne centrale
            pygame.draw.line(surface, (255, 255, 255, 100), 
                           (x + w//2, y + 3), (x + w//2, y + h - 3), 2)
            
        elif enemy.type == 2:  # Camion - robuste
            # Forme rectangulaire massive
            pygame.draw.rect(surface, color, (x, y, w, h - 5), border_radius=2)
            # Cabine
            pygame.draw.rect(surface, (*color[:3], 150), (x + 2, y, w - 4, 20), border_radius=2)
            # Détails
            pygame.draw.rect(surface, (100, 100, 100), (x + 3, y + h - 12, w - 6, 6), border_radius=1)
            
        else:  # Imprévisible - forme irrégulière
            # Forme asymétrique
            points = [
                (x + 4, y + 2),
                (x + w - 2, y + 5),
                (x + w - 4, y + h - 3),
                (x + 2, y + h - 6),
            ]
            pygame.draw.polygon(surface, color, points)
            
        # Feux selon vitesse
        if speed_ratio > 1.0:
            # Feux arrière brillants
            pygame.draw.rect(surface, (255, 100, 100), (x + 2, y + h - 4, 6, 3))
            pygame.draw.rect(surface, (255, 100, 100), (x + w - 8, y + h - 4, 6, 3))
        
        # Effet de vitesse (lignes de flou)
        if speed_ratio > 1.2:
            for i in range(3):
                blur_y = y + h + 5 + i * 4
                alpha = int(100 - i * 30)
                pygame.draw.rect(surface, (255, 255, 255, alpha), 
                               (x + 4, int(blur_y), w - 8, 2))


class SkidmarkLayer:
    """Traces de pneus persistantes (quadrilatères alpha décroissant)."""

    def __init__(self, max_marks: int = 80):
        self.marks: list = []
        self.max_marks = max_marks

    def add(self, x: float, y: float, angle: float, width: float = 8):
        self.marks.append({"x": x, "y": y, "angle": angle, "w": width, "alpha": 200})
        if len(self.marks) > self.max_marks:
            self.marks.pop(0)

    def update(self, dt: float):
        for m in self.marks:
            m["alpha"] = max(0, m["alpha"] - 3 * dt)

    def draw(self, surface: pygame.Surface):
        for m in self.marks:
            if m["alpha"] <= 0:
                continue
            s = pygame.Surface((int(m["w"] * 3), 6), pygame.SRCALPHA)
            pygame.draw.rect(s, (30, 30, 30, int(m["alpha"])), (0, 0, int(m["w"] * 3), 6))
            rot = pygame.transform.rotate(s, m["angle"])
            surface.blit(rot, (int(m["x"]), int(m["y"])))

    def clear(self):
        self.marks.clear()


class PostFXProcessor:
    """Motion blur, bloom, heat haze (numpy si disponible)."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        try:
            import numpy as np
            self.np = np
            self.has_numpy = True
        except ImportError:
            self.np = None
            self.has_numpy = False

    def apply_motion_blur(self, surface: pygame.Surface, alpha: int = 40) -> pygame.Surface:
        blur = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        blur.fill((255, 255, 255, alpha))
        out = surface.copy()
        out.blit(blur, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        return out

    def apply_bloom(self, surface: pygame.Surface) -> pygame.Surface:
        if not self.has_numpy:
            return surface
        arr = self.np.array(pygame.surfarray.pixels3d(surface))
        if not (arr > 200).any():
            return surface
        small = pygame.transform.smoothscale(surface, (self.width // 2, self.height // 2))
        small = pygame.transform.smoothscale(small, (self.width, self.height))
        out = surface.copy()
        out.blit(small, (0, 0), special_flags=pygame.BLEND_ADD)
        return out

    def apply_heat_haze(self, surface: pygame.Surface, strength: float = 1.0) -> pygame.Surface:
        if not self.has_numpy or strength <= 0:
            return surface
        arr = self.np.array(pygame.surfarray.pixels3d(surface))
        shift = int(2 * strength)
        arr[:, ::3] = self.np.roll(arr[:, ::3], shift, axis=0)
        return pygame.surfarray.make_surface(arr)


class VisualEffectsManager:
    """Gestionnaire central de tous les effets visuels."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.particles = ParticleSystem()
        self.screen_effects = ScreenEffects(screen_width, screen_height)
        self.background = AnimatedBackground(screen_width, screen_height)
        self.car_renderer = CarRenderer()
        self.skidmarks = SkidmarkLayer()
        self.post_fx = PostFXProcessor(screen_width, screen_height)
        self._lod_particles = True
        self._fps_estimate = 60.0
        
    def update(self, dt: float, speed: float = 0, fps: float = 60.0):
        """Met à jour tous les effets."""
        self._fps_estimate = fps
        self.particles.update(dt)
        self.skidmarks.update(dt)
        self.screen_effects.update(dt)
        self.background.update(dt, speed * 0.1)
        
    def draw_background(self, surface: pygame.Surface, level: int):
        """Dessine l'arrière-plan animé."""
        self.background.draw(surface, level)
        
    def draw_particles(self, surface: pygame.Surface):
        """Dessine les particules."""
        self.particles.draw(surface)
        
    def apply_screen_effects(self, surface: pygame.Surface, screen_shake_enabled: bool = True) -> pygame.Surface:
        """Applique les effets d'écran."""
        return self.screen_effects.apply(surface, screen_shake_enabled=screen_shake_enabled)
        
    def reset(self):
        """Réinitialise tous les effets."""
        self.particles.clear()
        self.screen_effects.shake_amount = 0
        self.skidmarks.clear()
