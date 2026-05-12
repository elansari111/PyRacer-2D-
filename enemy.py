# ============================================================
#  PyRacer: Ultimate Neon Highway
#  enemy.py — Classe Enemy : types, comportements, spawn
# ============================================================

import pygame
import random
import settings as S


class Enemy:
    """Voiture adverse avec comportement semi-intelligent selon son type."""
    _glow_cache = {}

    # type 0 = standard    : tient sa voie, rare changement de voie lent
    # type 1 = rapide      : accélérations soudaines, dépasse parfois le joueur
    # type 2 = camion      : très lent, occupe 1.5 voie, bloque les trajectoires
    # type 3 = imprévisible: changements de voie fréquents et aléatoires

    def __init__(self, road_x: int, road_w: int, lane_count: int,
                 enemy_type: int, player_speed: float):
        self.type      = enemy_type
        self.road_x    = road_x
        self.road_w    = road_w
        self.lane_count = lane_count
        self.lane_w    = road_w // lane_count

        # Taille selon type
        self.w, self.h = S.ENEMY_SIZES[enemy_type]

        # Voie et position initiale (au-dessus de l'écran)
        self.lane      = random.randrange(lane_count)
        self.x         = float(road_x + self.lane_w * self.lane
                               + self.lane_w // 2 - self.w // 2)
        self.y         = float(-self.h - 10)
        self.target_x  = self.x

        # Vitesse de base
        self.base_speed = player_speed * S.ENEMY_SPEED_MULT[enemy_type]
        self.speed      = self.base_speed

        # Indicateurs
        self.passed     = False   # le joueur l'a dépassé
        self.color      = S.ENEMY_COLORS[enemy_type]

        # Timers internes
        self._lane_timer   = random.randint(60, 180)
        self._burst_timer  = random.randint(30, 120)
        self._speed_boost  = 0.0
        
        # NOUVEAU: Comportement agressif et anticipation
        self._aggressive_timer = random.randint(180, 360)
        self._is_aggressive = False
        self._collision_predicted = False
        self._avoid_direction = 0

    # ----------------------------------------------------------
    def update(self, dt: float, player_speed: float, player_lane: int = None,
               player_x: float = None, player_y: float = None, player_w: float = None):
        """Déplace et met à jour le comportement de l'ennemi."""
        self.base_speed = player_speed * S.ENEMY_SPEED_MULT[self.type]
        
        # NOUVEAU: Prédiction de collision et comportement agressif
        if player_lane is not None and player_y is not None:
            self._update_collision_avoidance(dt, player_lane, player_x, player_y, player_w)
            self._update_aggressive_behavior(dt, player_y)

        if self.type == 0:
            self._behavior_standard(dt)
        elif self.type == 1:
            self._behavior_fast(dt, player_speed)
        elif self.type == 2:
            self._behavior_truck(dt)
        elif self.type == 3:
            self._behavior_unpredictable(dt)

        # Déplacement vertical
        self.y += self.speed * dt

        # Glissement latéral vers target_x (vitesse augmentée pour évitement)
        lerp_speed = 0.08 if self._collision_predicted else 0.04
        if abs(self.target_x - self.x) > 0.5:
            self.x += (self.target_x - self.x) * lerp_speed * dt
        else:
            self.x = self.target_x

        # Clamp dans la route
        self.x = max(self.road_x,
                     min(self.road_x + self.road_w - self.w, self.x))

    # NOUVEAU: Prédiction de collision et évitement
    def _update_collision_avoidance(self, dt: float, player_lane: int, 
                                     player_x: float, player_y: float, player_w: float):
        """Détecte si une collision est imminente et évite intelligemment."""
        # Même voie et ennemi devant le joueur (qui va plus lentement)
        if self.lane == player_lane and self.y > player_y and self.y < player_y + 200:
            # Prédiction: le joueur va nous rattraper
            relative_speed = self.speed  # joueur = baseline
            if relative_speed > 0:
                time_to_collision = (self.y - player_y - self.h) / relative_speed
                
                if 0 < time_to_collision < 60:  # Collision dans 1 seconde à 60fps
                    self._collision_predicted = True
                    
                    # Choisir la meilleure direction d'évitement
                    left_clear = self.lane > 0
                    right_clear = self.lane < self.lane_count - 1
                    
                    if left_clear and right_clear:
                        # Choisir la voie avec le plus d'espace
                        left_dist = abs(player_x - (self.x - self.lane_w))
                        right_dist = abs(player_x - (self.x + self.lane_w))
                        self._avoid_direction = -1 if left_dist > right_dist else 1
                    elif left_clear:
                        self._avoid_direction = -1
                    elif right_clear:
                        self._avoid_direction = 1
                    else:
                        self._avoid_direction = 0
                    
                    if self._avoid_direction != 0:
                        new_lane = max(0, min(self.lane_count - 1, 
                                             self.lane + self._avoid_direction))
                        if new_lane != self.lane:
                            self.lane = new_lane
                            self.target_x = (self.road_x + self.lane_w * self.lane
                                           + self.lane_w // 2 - self.w // 2)
                else:
                    self._collision_predicted = False
        else:
            self._collision_predicted = False
    
    # NOUVEAU: Comportement agressif
    def _update_aggressive_behavior(self, dt: float, player_y: float):
        """Comportement agressif occasionnel vers le joueur."""
        self._aggressive_timer -= dt
        
        if self._aggressive_timer <= 0:
            self._aggressive_timer = random.randint(240, 480)
            # 25% de chance de devenir agressif si proche du joueur
            if (not self.passed and abs(self.y - player_y) < 300 and 
                random.random() < 0.25 and self.type in [1, 3]):
                self._is_aggressive = True
            else:
                self._is_aggressive = False
        
        # Si agressif: essayer de bloquer la voie du joueur
        if self._is_aggressive and not self.passed:
            self.speed *= 0.9  # Ralentir pour bloquer
            # Indicateur visuel (clignotant rapide)
            if int(pygame.time.get_ticks() / 100) % 2 == 0:
                self.color = (255, 100, 100)  # Rouge clignotant
            else:
                self.color = S.ENEMY_COLORS[self.type]
        elif not self._is_aggressive:
            self.color = S.ENEMY_COLORS[self.type]

    # ---------- COMPORTEMENTS ----------
    def _behavior_standard(self, dt: float):
        """Changement de voie rare et lent."""
        self._lane_timer -= dt
        if self._lane_timer <= 0:
            self._lane_timer = random.randint(200, 360)
            if random.random() < 0.35:
                direction = random.choice([-1, 1])
                new_lane  = max(0, min(self.lane_count - 1, self.lane + direction))
                if new_lane != self.lane:
                    self.lane     = new_lane
                    self.target_x = (self.road_x
                                     + self.lane_w * self.lane
                                     + self.lane_w // 2
                                     - self.w // 2)
        self.speed = self.base_speed

    def _behavior_fast(self, dt: float, player_speed: float):
        """Accélérations courtes, peut dépasser le joueur."""
        self._burst_timer -= dt
        if self._burst_timer <= 0:
            self._burst_timer = random.randint(90, 180)
            self._speed_boost = player_speed * 0.8 if random.random() < 0.45 else 0.0
        self.speed = self.base_speed + self._speed_boost

        # Rare changement de voie
        self._lane_timer -= dt
        if self._lane_timer <= 0:
            self._lane_timer = random.randint(120, 240)
            if random.random() < 0.4:
                direction = random.choice([-1, 1])
                new_lane  = max(0, min(self.lane_count - 1, self.lane + direction))
                self.lane     = new_lane
                self.target_x = (self.road_x
                                 + self.lane_w * self.lane
                                 + self.lane_w // 2
                                 - self.w // 2)

    def _behavior_truck(self, dt: float):
        """Très lent, large, ne change jamais de voie."""
        self.speed = self.base_speed * 0.85   # encore plus lent
        # Largeur étendue visuellement (camion couvre ~1.5 voie)
        # Pas de changement de voie

    def _behavior_unpredictable(self, dt: float):
        """Changements de voie fréquents et aléatoires."""
        self._lane_timer -= dt
        if self._lane_timer <= 0:
            self._lane_timer = random.randint(40, 100)
            new_lane = random.randrange(self.lane_count)
            self.lane     = new_lane
            self.target_x = (self.road_x
                             + self.lane_w * new_lane
                             + self.lane_w // 2
                             - self.w // 2)

        # Vitesse variable
        self._burst_timer -= dt
        if self._burst_timer <= 0:
            self._burst_timer = random.randint(60, 120)
            self._speed_boost = random.uniform(-0.5, 1.2)
        self.speed = max(0.5, self.base_speed + self._speed_boost)

    # ----------------------------------------------------------
    def get_rect(self) -> pygame.Rect:
        """Hitbox légèrement réduite pour plus de fairplay."""
        return pygame.Rect(int(self.x) + 4, int(self.y) + 4,
                           self.w - 8, self.h - 8)

    def is_off_screen(self) -> bool:
        return self.y > S.SCREEN_H + 120

    # ----------------------------------------------------------
    def draw(self, surface: pygame.Surface):
        """Dessine l'ennemi selon son type."""
        ex, ey = int(self.x), int(self.y)
        w, h   = self.w, self.h
        col    = self.color

        # Lueur
        if (w, h, col) not in Enemy._glow_cache:
            glow = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*col, 40), (0, 0, w + 16, h + 16))
            Enemy._glow_cache[(w, h, col)] = glow
        surface.blit(Enemy._glow_cache[(w, h, col)], (ex - 8, ey - 8))

        # Corps principal
        pygame.draw.rect(surface, col, (ex + 3, ey, w - 6, h), border_radius=6)

        # Pare-brise (sombre)
        pg_h = int(h * 0.22)
        pg_y = ey + int(h * 0.28)
        pygame.draw.rect(surface, (0, 0, 0, 100), (ex + 5, pg_y, w - 10, pg_h))

        # Blinker (clignotant) si changement de voie
        if abs(self.target_x - self.x) > 5.0:
            is_right = self.target_x > self.x
            if int(pygame.time.get_ticks() / 150) % 2 == 0:
                bx = ex + w - 5 if is_right else ex + 1
                pygame.draw.rect(surface, (255, 170, 0), (bx, ey + 4, 4, 8), border_radius=2)

        # Feux arrière rouges
        pygame.draw.rect(surface, (255, 0, 0), (ex + 4, ey + h - 6, 8, 4))
        pygame.draw.rect(surface, (255, 0, 0), (ex + w - 12, ey + h - 6, 8, 4))

        # Roues
        for wx, wy in [(ex, ey + 8), (ex + w - 5, ey + 8),
                       (ex, ey + h - 18), (ex + w - 5, ey + h - 18)]:
            pygame.draw.rect(surface, (20, 20, 20), (wx, wy, 5, 10), border_radius=2)

        # Marqueurs visuels par type
        if self.type == 2:      # camion — bande centrale
            pygame.draw.rect(surface, (255, 255, 255, 40),
                             (ex + 3, ey + h // 2, w - 6, 4))
        elif self.type == 1:    # rapide — stripe verticale
            pygame.draw.rect(surface, (255, 255, 255, 80),
                             (ex + w // 2 - 2, ey + 4, 4, h - 8))
        elif self.type == 3:    # imprévisible — contour pointillé violet
            for i in range(0, w - 6, 10):
                pygame.draw.rect(surface, S.C_PURPLE,
                                 (ex + 2 + i, ey + 2, 5, 2))
                pygame.draw.rect(surface, S.C_PURPLE,
                                 (ex + 2 + i, ey + h - 4, 5, 2))


# ============================================================
#  EnemySpawner — gestion du spawn avec montée de difficulté
# ============================================================

class EnemySpawner:
    """Contrôle l'apparition des ennemis avec difficulté adaptative progressive."""

    def __init__(self, level: int, road_x: int, road_w: int):
        self.level      = level
        self.road_x     = road_x
        self.road_w     = road_w
        self.lane_count = S.LANE_COUNT[level]
        self._timer     = 0
        self._diff_time = 0     # temps écoulé pour la difficulté
        
        # NOUVEAU: Système de difficulté adaptative
        self._player_skill_rating = 1.0  # 0.5 = facile, 1.0 = normal, 1.5 = difficile
        self._consecutive_overtakes = 0
        self._spawn_count = 0
        self._intensity_phase = 0  # 0-3 phases d'intensité

    def update(self, dt: float, player_speed: float) -> list:
        """Retourne une liste de nouveaux Enemy à ajouter avec difficulté adaptative."""
        self._timer    += dt
        self._diff_time += dt

        # NOUVEAU: Difficulté adaptative basée sur le temps et la vitesse
        base_interval = S.SPAWN_INTERVAL[self.level]
        
        # 1. Réduction progressive du temps de spawn
        time_factor = self._diff_time * 0.25
        
        # 2. Augmentation si joueur rapide (skill-based)
        speed_ratio = player_speed / (S.MAX_SPEED[self.level] * 0.7)
        speed_factor = max(0, (speed_ratio - 1.0) * 20)  # Bonus si joueur va vite
        
        # 3. Phase d'intensité (vagues)
        phase_intensity = self._intensity_phase * 15
        
        interval = max(
            S.SPAWN_INTERVAL_MIN,
            base_interval - time_factor - speed_factor - phase_intensity
        )

        new_enemies = []
        if self._timer >= interval:
            self._timer = 0
            self._spawn_count += 1
            
            # NOUVEAU: Sélection de type pondérée par difficulté
            etype = self._select_enemy_type(player_speed)
            
            # NOUVEAU: Spawn double pendant les phases intenses
            spawn_count = 1
            if self._intensity_phase >= 2 and random.random() < 0.3:
                spawn_count = 2  # Spawn double occasionnel
            
            for _ in range(spawn_count):
                enemy = Enemy(self.road_x, self.road_w,
                             self.lane_count, etype, player_speed)
                # NOUVEAU: Vitesse augmentée selon difficulté
                speed_boost = 1.0 + (self._intensity_phase * 0.1) + (self._diff_time * 0.001)
                enemy.speed *= min(1.3, speed_boost)  # Max 30% plus vite
                new_enemies.append(enemy)
            
            # NOUVEAU: Augmenter la phase d'intensité toutes les 30 spawns
            if self._spawn_count % 30 == 0 and self._intensity_phase < 3:
                self._intensity_phase += 1

        return new_enemies
    
    # NOUVEAU: Sélection intelligente du type d'ennemi
    def _select_enemy_type(self, player_speed: float) -> int:
        """Sélectionne le type d'ennemi selon la situation."""
        types = S.ENEMY_TYPES_BY_LEVEL[self.level].copy()
        
        # Pondération selon difficulté
        weights = [1.0] * len(types)
        
        # Si joueur va vite: plus d'ennemis rapides et imprévisibles
        if player_speed > S.MAX_SPEED[self.level] * 0.8:
            for i, t in enumerate(types):
                if t in [1, 3]:  # rapide, imprévisible
                    weights[i] = 1.5
        
        # Phase intense: plus de camions (obstacles) et imprévisibles
        if self._intensity_phase >= 2:
            for i, t in enumerate(types):
                if t in [2, 3]:  # camion, imprévisible
                    weights[i] = 1.8
        
        return random.choices(types, weights=weights, k=1)[0]
    
    # NOUVEAU: Notifier le spawner d'un dépassement réussi
    def on_overtake(self, streak: int):
        """Appelé quand le joueur dépasse pour ajuster la difficulté."""
        self._consecutive_overtakes += 1
        # Récompense: ralentir un peu le spawn après une série
        if streak > 5:
            self._timer = max(0, self._timer - 20)  # Petite pause
