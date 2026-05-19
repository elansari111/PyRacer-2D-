# ============================================================
#  PyRacer: Ultimate Neon Highway
#  bonus.py — Apparition, collecte, jauges, effets des bonus
# ============================================================

import pygame
import random
import math
import settings as S


class BonusEffect:
    """
    Effet de bonus appliqué à la voiture.

    Rôle: Encapsuler type, durée et magnitude.
    Paramètres: type (str), duration (frames), magnitude.
    Dépendances: car.Player.
    """

    DURATION = {
        "slow": S.BONUS_SLOW_DURATION,
        "magnet": S.BONUS_MAGNET_DURATION,
        "ghost": S.BONUS_GHOST_DURATION,
        "time_freeze": S.BONUS_TIME_FREEZE_DURATION,
    }

    def __init__(self, effect_type: str, duration: float = None, magnitude: float = 1.0):
        self.effect_type = effect_type
        self.duration = duration if duration is not None else self.DURATION.get(effect_type, 0)
        self.magnitude = magnitude
        self.timer = self.duration

    def apply_to(self, car) -> dict:
        """
        Applique l'effet immédiat sur la voiture.

        Returns:
            dict des modifications (nitro_add, shield_add, etc.)
        """
        result = {"nitro_add": 0, "shield_add": 0, "life_add": 0, "activated": self.effect_type}
        t = self.effect_type
        if t == "nitro":
            result["nitro_add"] = int(S.BONUS_NITRO_ADD * self.magnitude)
        elif t == "shield":
            result["shield_add"] = int(S.BONUS_SHIELD_ADD * self.magnitude)
        elif t == "life":
            result["life_add"] = 1
        elif t == "ghost" and hasattr(car, "activate_ghost"):
            car.activate_ghost(int(self.duration * self.magnitude))
        return result

    def tick(self, dt: float) -> bool:
        """Retourne True si l'effet est terminé."""
        self.timer -= dt
        return self.timer <= 0


class Bonus:
    """Un bonus collectible sur la route."""

    def __init__(self, road_x: int, road_w: int, lane_count: int, use_extended: bool = True):
        lane_w = road_w // lane_count
        lane   = random.randrange(lane_count)

        self.use_extended = use_extended
        self.kind   = self._pick_kind()
        self.w      = S.BONUS_SIZE
        self.h      = S.BONUS_SIZE
        self.x      = float(road_x + lane_w * lane + lane_w // 2 - self.w // 2)
        self.y      = float(-self.h - 10)
        
        # Utilise les couleurs étendues si disponible
        if use_extended and self.kind in S.BONUS_COLORS_EXTENDED:
            self.color = S.BONUS_COLORS_EXTENDED[self.kind]
            self.icon = S.BONUS_ICONS_EXTENDED[self.kind]
        else:
            self.color = S.BONUS_COLORS.get(self.kind, (255, 255, 255))
            self.icon = S.BONUS_ICONS.get(self.kind, "?")
        self._age   = 0.0   # pour l'animation flottante

    def _pick_kind(self) -> str:
        r = random.random() * 100
        acc = 0
        
        if self.use_extended:
            types_list = S.BONUS_TYPES_EXTENDED
            weights_list = S.BONUS_WEIGHTS_EXTENDED
        else:
            types_list = S.BONUS_TYPES
            weights_list = S.BONUS_WEIGHTS
            
        for kind, weight in zip(types_list, weights_list):
            acc += weight
            if r < acc:
                return kind
        return "nitro"

    def update(self, speed: float, dt: float):
        self.y    += speed * S.BONUS_SPEED_MULT * dt
        self._age += dt

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def is_off_screen(self) -> bool:
        return self.y > S.SCREEN_H + 60

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        bob    = math.sin(self._age * 0.08) * 4
        cx     = int(self.x) + self.w // 2
        cy     = int(self.y) + self.h // 2 + int(bob)
        radius = self.w // 2

        # Lueur pulsante
        glow_a = int(40 + 25 * math.sin(self._age * 0.1))
        glow   = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, glow_a),
                           (radius * 2, radius * 2), radius * 2)
        surface.blit(glow, (cx - radius * 2, cy - radius * 2))

        # Cercle principal
        pygame.draw.circle(surface, self.color, (cx, cy), radius, 2)

        # Icône texte
        txt = font.render(self.icon, True, self.color)
        surface.blit(txt, txt.get_rect(center=(cx, cy)))


# ============================================================
#  BonusManager — spawn et application des effets
# ============================================================

class BonusManager:
    """Gère la liste des bonus actifs et applique leurs effets."""

    def __init__(self, road_x: int, road_w: int, lane_count: int, use_extended: bool = True,
                 difficulty_mult: float = 1.0):
        self.road_x     = road_x
        self.road_w     = road_w
        self.lane_count = lane_count
        self.use_extended = use_extended
        self.bonuses: list[Bonus] = []
        dm = max(0.5, min(1.5, float(difficulty_mult)))
        # Facile : un peu plus de bonus ; difficile : un peu moins
        self._spawn_scale = 1.0 + (1.0 - dm) * 0.35 - max(0.0, dm - 1.0) * 0.25

        # Timers pour les bonus à durée
        self.slow_timer = 0.0
        self.magnet_timer = 0.0
        self.ghost_timer = 0.0
        self.time_freeze_timer = 0.0
        
        # Position du joueur pour le magnet
        self.player_x = 0
        self.player_y = 0

        # Police d'icône (initialisée dans update si absente)
        self._font: pygame.font.Font | None = None

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("segoeuiemoji,dejavusans", 18)
        return self._font

    # ----------------------------------------------------------
    def update(self, dt: float, speed: float, player_rect: pygame.Rect,
               player_x: float = None, player_y: float = None, car=None,
               rivals: list = None) -> dict:
        """
        Met à jour les bonus et détecte les collectes.

        Retourne un dict d'effets à appliquer dans main.py :
        {
          "nitro_add": int,
          "shield_add": int,
          "life_add": int,
          "slow": bool,
          "magnet": bool,
          "ghost": bool,
          "time_freeze": bool,
          "score_add": int,
          "collected": [kind, ...],   # pour popups / particules
          "rival_collected": [(r, kind, color), ...] # collectés par les rivaux
        }
        """
        result = {"nitro_add": 0, "shield_add": 0, "life_add": 0,
                  "slow": False, "magnet": False, "ghost": False, 
                  "time_freeze": False, "score_add": 0, "collected": [],
                  "rival_collected": []}
        
        # Met à jour la position du joueur pour le magnet
        if player_x is not None:
            self.player_x = player_x
        if player_y is not None:
            self.player_y = player_y

        # Spawn aléatoire (probabilité liée à la difficulté menu)
        if random.random() < S.BONUS_SPAWN_PROB * dt * self._spawn_scale:
            self.bonuses.append(
                Bonus(self.road_x, self.road_w, self.lane_count, self.use_extended)
            )

        # Mise à jour des timers
        if self.slow_timer > 0:
            self.slow_timer -= dt
        if self.magnet_timer > 0:
            self.magnet_timer -= dt
        if self.ghost_timer > 0:
            self.ghost_timer -= dt
        if self.time_freeze_timer > 0:
            self.time_freeze_timer -= dt

        # Mise à jour et collecte
        to_remove = []
        magnet_active = self.magnet_timer > 0
        
        for b in self.bonuses:
            # Effet magnet: attire les bonus vers le joueur
            if magnet_active and self.player_x > 0:
                dx = self.player_x - b.x
                dy = self.player_y - b.y
                dist = (dx**2 + dy**2) ** 0.5
                if dist < S.BONUS_MAGNET_RANGE and dist > 5:
                    b.x += (dx / dist) * 5 * dt  # Vitesse d'attraction
                    b.y += (dy / dist) * 5 * dt
            
            b.update(speed, dt)

            if b.is_off_screen():
                to_remove.append(b)
                continue

            # Collecte par le joueur
            if player_rect.colliderect(b.get_rect()):
                to_remove.append(b)
                result["score_add"] += S.BONUS_SCORE
                result["collected"].append(b.kind)

                effect = BonusEffect(b.kind)
                applied = effect.apply_to(car) if car is not None else effect.apply_to(
                    type("_Car", (), {"activate_ghost": lambda s, d: None})())
                result["nitro_add"] += applied.get("nitro_add", 0)
                result["shield_add"] += applied.get("shield_add", 0)
                result["life_add"] += applied.get("life_add", 0)

                if b.kind == "slow":
                    self.slow_timer = effect.duration
                    result["slow"] = True
                elif b.kind == "magnet":
                    self.magnet_timer = effect.duration
                    result["magnet"] = True
                elif b.kind == "ghost":
                    self.ghost_timer = effect.duration
                    result["ghost"] = True
                elif b.kind == "time_freeze":
                    self.time_freeze_timer = effect.duration
                    result["time_freeze"] = True
                continue

            # Collecte par les rivaux (si en mode course/circuit)
            if rivals is not None:
                rival_collision = False
                for r in rivals:
                    if hasattr(r, "get_rect") and r.get_rect().colliderect(b.get_rect()):
                        to_remove.append(b)
                        result["rival_collected"].append((r, b.kind, b.color))
                        
                        # Applique l'effet au rival
                        if b.kind == "nitro":
                            r._nitro_timer = 120.0  # nitro boost pendant 2 sec
                        elif b.kind == "shield":
                            r.shield_timer = 150.0  # shield actif pendant 2.5 sec
                            
                        rival_collision = True
                        break
                if rival_collision:
                    continue

        for b in to_remove:
            if b in self.bonuses:
                self.bonuses.remove(b)

        return result

    # ----------------------------------------------------------
    @property
    def slow_active(self) -> bool:
        return self.slow_timer > 0
        
    @property
    def magnet_active(self) -> bool:
        return self.magnet_timer > 0
        
    @property
    def ghost_active(self) -> bool:
        return self.ghost_timer > 0
        
    @property
    def time_freeze_active(self) -> bool:
        return self.time_freeze_timer > 0
        
    def get_active_effects(self) -> list:
        """Retourne la liste des effets actifs avec leur temps restant."""
        effects = []
        if self.slow_timer > 0:
            effects.append(("slow", self.slow_timer / S.BONUS_SLOW_DURATION))
        if self.magnet_timer > 0:
            effects.append(("magnet", self.magnet_timer / S.BONUS_MAGNET_DURATION))
        if self.ghost_timer > 0:
            effects.append(("ghost", self.ghost_timer / S.BONUS_GHOST_DURATION))
        if self.time_freeze_timer > 0:
            effects.append(("time_freeze", self.time_freeze_timer / S.BONUS_TIME_FREEZE_DURATION))
        return effects

    # ----------------------------------------------------------
    def draw(self, surface: pygame.Surface):
        font = self._get_font()
        for b in self.bonuses:
            b.draw(surface, font)
