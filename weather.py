# ============================================================
#  PyRacer: Ultimate Neon Highway
#  weather.py — Effets météo (pluie, brouillard, néon)
# ============================================================

import pygame
import random
import math
import settings as S


class RainDrop:
    """Une goutte de pluie individuelle."""
    
    def __init__(self, screen_w, screen_h, intensity=1.0):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.intensity = intensity
        self.reset()
        
    def reset(self):
        """Réinitialise la goutte en haut de l'écran."""
        self.x = random.randint(0, self.screen_w)
        self.y = random.randint(-100, -10)
        self.speed = random.uniform(8, 15) * (1 + self.intensity * 0.5)
        self.length = random.randint(10, 25)
        self.thickness = random.randint(1, 2)
        self.alpha = random.randint(80, 150)
        
    def update(self, dt, wind=0):
        """Met à jour la position de la goutte."""
        self.y += self.speed * dt
        self.x += wind * dt
        
        if self.y > self.screen_h:
            self.reset()
            
    def draw(self, surface):
        """Dessine la goutte."""
        end_y = int(self.y + self.length)
        pygame.draw.line(surface, (180, 200, 255, self.alpha),
                        (int(self.x), int(self.y)),
                        (int(self.x), end_y), self.thickness)


class WeatherSystem:
    """
    Système météo complet avec pluie, éclairs et brouillard.
    """
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # État météo
        self.weather_type = "clear"  # clear, rain, storm, fog
        self.intensity = 0.5
        self.wind = 0.0
        
        # Particules
        self.rain_drops = []
        self.max_drops = 200
        
        # Éclairs
        self.flash_timer = 0
        self.flash_duration = 0
        
        # Brouillard
        self.fog_surface = None
        self._init_fog()
        
        # Splash sur la route
        self.splashes = []
        
    def _init_fog(self):
        """Initialise la surface de brouillard."""
        self.fog_surface = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        
    def set_weather(self, weather_type: str, intensity: float = 0.5):
        """Change le type de météo."""
        self.weather_type = weather_type
        self.intensity = max(0.0, min(1.0, intensity))
        
        # Ajuste le nombre de gouttes selon la météo
        if weather_type == "clear":
            self.rain_drops = []
        elif weather_type == "rain":
            self.max_drops = int(100 + self.intensity * 200)
            self._ensure_drops()
        elif weather_type == "storm":
            self.max_drops = int(300 + self.intensity * 400)
            self.wind = random.uniform(-2, 2)
            self._ensure_drops()
        elif weather_type == "fog":
            self.rain_drops = []
            
    def _ensure_drops(self):
        """Assure qu'il y a assez de gouttes."""
        while len(self.rain_drops) < self.max_drops:
            self.rain_drops.append(RainDrop(self.screen_w, self.screen_h, self.intensity))
            
    def update(self, dt, player_speed=0):
        """Met à jour tous les effets météo."""
        if self.weather_type in ("rain", "storm"):
            # Mise à jour des gouttes
            for drop in self.rain_drops:
                # La pluie tombe plus vite quand la voiture avance
                effective_speed = drop.speed + player_speed * 0.5
                drop.y += effective_speed * dt
                drop.x += self.wind * dt
                
                if drop.y > self.screen_h:
                    # Crée un splash sur la route si dans la zone de route
                    if S.ROAD_X < drop.x < S.ROAD_X + S.ROAD_WIDTH:
                        if random.random() < 0.1:
                            self.splashes.append({
                                "x": drop.x,
                                "y": self.screen_h - 20,
                                "life": 10,
                                "max_life": 10,
                                "radius": random.randint(3, 8)
                            })
                    drop.reset()
                    
            # Éclairs aléatoires en tempête
            if self.weather_type == "storm" and random.random() < 0.001 * self.intensity:
                self.trigger_flash()
                
        # Gestion des éclairs
        if self.flash_timer > 0:
            self.flash_timer -= dt
            
        # Mise à jour des splashes
        for splash in self.splashes[:]:
            splash["life"] -= dt
            if splash["life"] <= 0:
                self.splashes.remove(splash)
                
    def trigger_flash(self):
        """Déclenche un éclair."""
        self.flash_timer = 8
        self.flash_duration = 8
        
    def draw(self, surface):
        """Dessine tous les effets météo."""
        # Éclair
        if self.flash_timer > 0:
            alpha = int(200 * (self.flash_timer / self.flash_duration))
            flash = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            surface.blit(flash, (0, 0))
            
        # Pluie
        if self.weather_type in ("rain", "storm"):
            rain_surface = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            for drop in self.rain_drops:
                drop.draw(rain_surface)
            surface.blit(rain_surface, (0, 0))
            
        # Splashes
        for splash in self.splashes:
            life_ratio = splash["life"] / splash["max_life"]
            alpha = int(150 * life_ratio)
            radius = int(splash["radius"] * (2 - life_ratio))
            pygame.draw.circle(surface, (200, 220, 255, alpha),
                             (int(splash["x"]), int(splash["y"])), radius)
            
        # Brouillard
        if self.weather_type in ("fog", "storm"):
            self._draw_fog(surface)
            
    def _draw_fog(self, surface):
        """Dessine le brouillard."""
        fog_intensity = int(80 * self.intensity)
        # Gradient de brouillard
        for i in range(0, self.screen_h, 20):
            alpha = int(fog_intensity * (0.5 + 0.5 * math.sin(i * 0.01)))
            pygame.draw.rect(surface, (200, 210, 230, alpha),
                           (0, i, self.screen_w, 20))


class ParticleEffects:
    """
    Système de particules avancé pour effets visuels.
    """
    
    def __init__(self):
        self.particles = []
        self.skid_marks = []  # Traces de pneus
        self.max_skid_marks = 50
        
    def add_smoke(self, x, y, color=(100, 100, 100), count=5):
        """Ajoute de la fumée d'échappement."""
        for _ in range(count):
            self.particles.append({
                "type": "smoke",
                "x": x + random.randint(-5, 5),
                "y": y + random.randint(-5, 5),
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(-2, -0.5),
                "life": random.randint(30, 60),
                "max_life": 60,
                "size": random.randint(4, 12),
                "color": color,
                "alpha": random.randint(100, 200)
            })
            
    def add_spark(self, x, y, color=(255, 200, 50), count=8):
        """Ajoute des étincelles."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            self.particles.append({
                "type": "spark",
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(20, 40),
                "max_life": 40,
                "size": random.randint(2, 4),
                "color": color,
                "alpha": 255
            })
            
    def add_exhaust_trail(self, x, y, speed_ratio):
        """Ajoute une traînée d'échappement."""
        if random.random() < 0.3:
            self.add_smoke(x, y, (80, 80, 90), 1)
            
    def add_skid_mark(self, x, y, width=6):
        """Ajoute une trace de dérapage."""
        if len(self.skid_marks) >= self.max_skid_marks:
            self.skid_marks.pop(0)
        self.skid_marks.append({
            "x": x,
            "y": y,
            "width": width,
            "life": 120,
            "alpha": 180
        })
        
    def add_nitro_flame(self, x, y):
        """Ajoute des flammes de nitro."""
        for _ in range(3):
            self.particles.append({
                "type": "flame",
                "x": x + random.randint(-8, 8),
                "y": y + random.randint(0, 10),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(2, 5),
                "life": random.randint(15, 30),
                "max_life": 30,
                "size": random.randint(6, 14),
                "color": (random.randint(200, 255), random.randint(100, 200), 0),
                "alpha": 200
            })
            
    def update(self, dt):
        """Met à jour toutes les particules."""
        # Particules
        for p in self.particles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            
            # Fade out
            life_ratio = p["life"] / p["max_life"]
            p["alpha"] = int(255 * life_ratio)
            
            if p["life"] <= 0:
                self.particles.remove(p)
                
        # Skid marks
        for mark in self.skid_marks[:]:
            mark["life"] -= dt
            mark["alpha"] = int(180 * (mark["life"] / 120))
            if mark["life"] <= 0:
                self.skid_marks.remove(mark)
                
    def draw(self, surface):
        """Dessine toutes les particules."""
        # Skid marks (dessinés d'abord, en dessous)
        for mark in self.skid_marks:
            pygame.draw.ellipse(surface, (20, 20, 25, mark["alpha"]),
                              (int(mark["x"] - mark["width"]//2),
                               int(mark["y"] - 3),
                               mark["width"], 6))
        
        # Particules
        for p in self.particles:
            if p["type"] == "smoke":
                pygame.draw.circle(surface, (*p["color"], p["alpha"]),
                                 (int(p["x"]), int(p["y"])),
                                 int(p["size"] * (p["life"] / p["max_life"])))
            elif p["type"] == "spark":
                pygame.draw.circle(surface, (*p["color"], p["alpha"]),
                                 (int(p["x"]), int(p["y"])),
                                 p["size"])
            elif p["type"] == "flame":
                # Gradient de flamme
                size = int(p["size"] * (p["life"] / p["max_life"]))
                pygame.draw.circle(surface, (*p["color"], p["alpha"]),
                                 (int(p["x"]), int(p["y"])), size)
