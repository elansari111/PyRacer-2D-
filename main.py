#!/usr/bin/env python3
# ============================================================
#  PyRacer: Ultimate Neon Highway - ENHANCED EDITION v2.0
#  main.py — Point d'entrée, boucle principale, delta-time
# ============================================================

import pygame
import sys
import random

import settings as S
from car        import Player
from enemy      import EnemySpawner
from road       import Road
from bonus      import BonusManager
from score      import ScoreManager
from hud        import HUD
from game_states import State, ScreenRenderer
from sound_manager import SoundManager
from weather   import WeatherSystem, ParticleEffects
from achievements import AchievementManager
from config    import config
from visual_effects import VisualEffectsManager
from ui.map_select_screen import MapSelectScreen
from maps.map_config import MapConfig, get_map_definition
from maps.city_map import CityMap
from maps.highway_map import HighwayMap
from maps.circuit_map import CircuitMap
from render.renderer import SceneRenderer
from render.road_renderer import RoadRenderer
from render.lighting import LightingSystem


# ============================================================
#  Particules légères (effets visuels)
# ============================================================

class Particle:
    _cache = {}

    def __init__(self, x, y, color):
        self.x   = float(x)
        self.y   = float(y)
        self.vx  = random.uniform(-3, 3)
        self.vy  = random.uniform(-5, 1)
        self.r   = random.uniform(2, 4)
        self.col = color
        self.life     = random.randint(20, 45)
        self.max_life = self.life

    def update(self, dt):
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self.vy   += 0.15 * dt
        self.life -= dt

    def draw(self, surface):
        a  = max(0, int(220 * self.life / self.max_life))
        r_int = int(self.r)
        key = (r_int, self.col, a)
        if key not in Particle._cache:
            s = pygame.Surface((r_int * 2, r_int * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.col[:3], a), (r_int, r_int), r_int)
            Particle._cache[key] = s
        surface.blit(Particle._cache[key], (int(self.x - self.r), int(self.y - self.r)))


# ============================================================
#  Classe principale
# ============================================================

class Game:

    def __init__(self):
        pygame.init()
        
        # Configuration display
        if config.get("fullscreen"):
            self.screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
        pygame.display.set_caption(S.TITLE)
        self.clock = pygame.time.Clock()

        self.state = State.MENU
        self.renderer = ScreenRenderer()
        self.frame_buffer = pygame.Surface((S.SCREEN_W, S.SCREEN_H))

        self.selected_level = 0
        self.current_level = 0
        self.current_map_id = "city"
        self.current_map_level = 1
        self.map_select = MapSelectScreen()
        self.active_map = None
        self.map_defn = None
        self.scene_renderer = SceneRenderer(S.SCREEN_W, S.SCREEN_H)
        self.road_renderer = RoadRenderer(S.SCREEN_W, S.SCREEN_H)
        self.lighting = LightingSystem(S.SCREEN_W, S.SCREEN_H)

        # Sous-systèmes
        self.player: Player | None = None
        self.road: Road | None = None
        self.spawner: EnemySpawner | None = None
        self.bonus_mgr: BonusManager | None = None
        self.score_mgr: ScoreManager = ScoreManager()
        # Reset des scores élevés pour chaque démarrage du jeu sur l'appareil
        self.score_mgr.hi_scores = {}
        self.score_mgr.hi_scores_legacy = [0, 0, 0]
        self.score_mgr._save()
        
        # Nouveaux systèmes v2.0
        self.sound_mgr = SoundManager()
        self.weather = WeatherSystem(S.SCREEN_W, S.SCREEN_H)
        self.particle_effects = ParticleEffects()
        self.achievements = AchievementManager()
        self.visual_effects = VisualEffectsManager(S.SCREEN_W, S.SCREEN_H)
        
        # Configuration audio depuis config
        self.sound_mgr.enabled = config.get("audio_enabled", True)
        self.sound_mgr.music_enabled = config.get("music_enabled", True)
        self.sound_mgr.sfx_enabled = config.get("sfx_enabled", True)
        self.sound_mgr.volume_music = config.get("music_volume", 0.5)
        self.sound_mgr.volume_sfx = config.get("sfx_volume", 0.8)

        self.enemies: list = []
        self.particles: list = []

        # Données de transition
        self._transition_stats: dict = {}
        self._is_last_level: bool = False

        # Survie timer niveau 3
        self._survive_timer = 0.0
        self._slow_motion_factor = 1.0
        self._slow_motion_timer = 0
        self._level_complete_shown = False
        self.play_road_x = S.ROAD_X
        self.play_road_w = S.ROAD_WIDTH
        self._circuit_grip = 1.0
        self._circuit_drs = 1.0
        self._circuit_state = {}
        self._last_dt = 1.0
        self._has_tire_wear = False

        # Callback achievements
        self.achievements.register_callback(self._on_achievement_unlocked)
        
        # Stats de session
        self._damage_taken_this_level = False
        self._session_distance = 0.0
        
        # Démarrer la musique du menu
        self.sound_mgr.play_music("menu")
        
    def _on_achievement_unlocked(self, achievement):
        """Callback quand un achievement est débloqué."""
        if self.hud:
            self.hud.show_achievement(achievement)
        self.sound_mgr.play("level_complete")

    # ----------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(S.FPS) / (1000 / S.FPS)   # delta-time normalisé à 1.0
            dt = min(dt, 3.0)   # cap pour éviter les sauts

            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ----------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_progress()
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # --- MENU ---
                if self.state == State.MENU:
                    if event.key == pygame.K_UP:
                        changed = self.renderer.menu_prev()
                        if changed:
                            self.sound_mgr.play("menu_select")
                    elif event.key == pygame.K_DOWN:
                        changed = self.renderer.menu_next()
                        if changed:
                            self.sound_mgr.play("menu_select")
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        selected = self.renderer.menu_get_selected()
                        self.sound_mgr.play("menu_confirm")
                        if selected == "JOUER":
                            self.state = State.MAP_SELECT
                            self.sound_mgr.play("menu_select")
                        elif selected == "PARAMETRES":
                            self.state = State.SETTINGS
                        elif selected == "SUCCES":
                            self.state = State.ACHIEVEMENTS
                        elif selected == "QUITTER":
                            self._save_progress()
                            pygame.quit()
                            sys.exit()
                    elif event.key == pygame.K_LEFT:
                        self.selected_level = max(0, self.selected_level - 1)
                        self.sound_mgr.play("menu_select")
                    elif event.key == pygame.K_RIGHT:
                        self.selected_level = min(2, self.selected_level + 1)
                        self.sound_mgr.play("menu_select")

                # --- SETTINGS ---
                elif self.state == State.SETTINGS:
                    if event.key == pygame.K_UP:
                        self.renderer.settings_prev()
                    elif event.key == pygame.K_DOWN:
                        self.renderer.settings_next()
                    elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        selected = self.renderer.settings_get_selected()
                        if selected == 5 or event.key == pygame.K_ESCAPE:  # Retour
                            self.state = State.MENU
                    elif event.key == pygame.K_LEFT:
                        self._adjust_setting(-1)
                    elif event.key == pygame.K_RIGHT:
                        self._adjust_setting(1)
                        
                # --- ACHIEVEMENTS ---
                elif self.state == State.ACHIEVEMENTS:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        self.state = State.MENU

                # --- MAP SELECT ---
                elif self.state == State.MAP_SELECT:
                    action = self.map_select.handle_event(
                        event, self.score_mgr.unlocked)
                    if action == "start":
                        self.current_map_id, self.current_map_level = self.map_select.get_selection()
                        self._start_game()
                    elif action == "menu":
                        self.state = State.MENU
                        self.sound_mgr.play_music("menu")

                # --- LEVEL COMPLETE / RACE RANKING ---
                elif self.state in (State.LEVEL_COMPLETE, State.RACE_RANKING):
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        self.state = State.MAP_SELECT

                # --- PLAYING ---
                elif self.state == State.PLAYING:
                    if event.key == config.get_key_binding("pause"):
                        self.state = State.PAUSE
                        self.sound_mgr.play("menu_select")
                    elif event.key == config.get_key_binding("nitro"):
                        if self.player.activate_nitro():
                            self.sound_mgr.play("nitro_activate")
                            self.hud.add_popup(
                                self.player.x + self.player.w // 2,
                                self.player.y, "⚡ NITRO !", S.C_YELLOW)
                            self.achievements.on_nitro_activated()
                            self.particle_effects.add_nitro_flame(
                                self.player.x + self.player.w // 2, 
                                self.player.y + self.player.h)
                    elif event.key == config.get_key_binding("shield"):
                        if self.player.activate_shield():
                            self.sound_mgr.play("shield_activate")
                            self.hud.add_popup(
                                self.player.x + self.player.w // 2,
                                self.player.y, "🛡 BOUCLIER", S.C_CYAN)
                            self.achievements.on_shield_activated()

                # --- PAUSE ---
                elif self.state == State.PAUSE:
                    if event.key == config.get_key_binding("pause"):
                        self.state = State.PLAYING
                        self.sound_mgr.play("menu_select")
                    elif event.key == pygame.K_ESCAPE:
                        self.state = State.MENU
                        self.sound_mgr.play_music("menu")

                # --- TRANSITION ---
                elif self.state == State.TRANSITION:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        # Alterne entre les deux options
                        self.renderer.transition_next() if event.key == pygame.K_DOWN else self.renderer.transition_prev()
                        self.sound_mgr.play("menu_select")
                    elif event.key == pygame.K_RETURN:
                        selected_option = self.renderer.transition_get_selected()
                        if selected_option == 0:  # Continuer / Victoire
                            if self._is_last_level:
                                self.state = State.WIN
                                self.achievements.on_victory()
                                self.sound_mgr.play("level_complete")
                                self.sound_mgr.stop_music()
                            else:
                                self._next_level()
                                self.sound_mgr.play("menu_confirm")
                        else:  # Retour Menu
                            self.state = State.MENU
                            self.sound_mgr.play_music("menu")
                            self.renderer.transition_reset()

                # --- GAMEOVER / WIN ---
                elif self.state in (State.GAMEOVER, State.WIN):
                    if event.key == pygame.K_RETURN:
                        if self.state == State.GAMEOVER:
                            self._start_game()
                        else:
                            self.state = State.MENU
                            self.sound_mgr.play_music("menu")
                    elif event.key == pygame.K_ESCAPE:
                        self.state = State.MENU
                        self.sound_mgr.play_music("menu")

    # ----------------------------------------------------------
    def _adjust_setting(self, direction: int):
        """Ajuste un paramètre des settings."""
        selected = self.renderer.settings_get_selected()
        if selected == 0:  # Audio
            current = config.get("audio_enabled", True)
            config.set("audio_enabled", not current)
            self.sound_mgr.enabled = config.get("audio_enabled", True)
        elif selected == 1:  # Musique
            vol = config.get("music_volume", 0.5)
            vol = max(0.0, min(1.0, vol + direction * 0.1))
            config.set("music_volume", vol)
            self.sound_mgr.set_music_volume(vol)
        elif selected == 2:  # SFX
            vol = config.get("sfx_volume", 0.8)
            vol = max(0.0, min(1.0, vol + direction * 0.1))
            config.set("sfx_volume", vol)
            self.sound_mgr.set_sfx_volume(vol)
        elif selected == 3:  # Difficulté
            difficulties = ["easy", "normal", "hard"]
            current = config.get("difficulty", "normal")
            idx = difficulties.index(current) if current in difficulties else 1
            new_idx = (idx + direction) % len(difficulties)
            config.set("difficulty", difficulties[new_idx])
        elif selected == 4:  # Couleur voiture
            colors = list(S.CAR_COLORS.keys())
            current = config.get("car_color", "cyan")
            idx = colors.index(current) if current in colors else 0
            new_idx = (idx + direction) % len(colors)
            config.set("car_color", colors[new_idx])

    def _save_progress(self):
        """Sauvegarde la progression."""
        config.increment_stat("total_games", 1)
        config.increment_stat("total_distance", int(self._session_distance))

    def _start_game(self):
        lvl_index = {"city": 0, "highway": 1, "circuit": 2}.get(self.current_map_id, 0)
        self.current_level = lvl_index
        self.selected_level = lvl_index
        self.score_mgr.set_map_level(self.current_map_id, self.current_map_level)
        self._init_level()
        self.state = State.PLAYING
        self.sound_mgr.play_music("race")
        self.achievements.session_stats["level_damage"] = {0: False, 1: False, 2: False}
        self._session_distance = 0.0

    def _init_level(self):
        cfg_map = {
            "city": MapConfig.CITY,
            "highway": MapConfig.HIGHWAY,
            "circuit": MapConfig.CIRCUIT,
        }
        mcfg = cfg_map.get(self.current_map_id, MapConfig.CITY)
        self.map_defn = get_map_definition(mcfg, self.current_map_level)
        lvl = min(self.current_level, len(S.LANE_COUNT) - 1)
        road_w = int(S.ROAD_WIDTH * self.map_defn.road_width_mod)
        lane_count = 4 if self.current_map_id == "highway" else S.LANE_COUNT[lvl]
        self.play_road_w = road_w
        self.play_road_x = S.ROAD_X + (S.ROAD_WIDTH - road_w) // 2

        self.road = Road(lvl, is_circuit=(self.current_map_id == "circuit"))
        car_color = config.get("car_color", "cyan")
        self.player = Player(self.play_road_x, road_w, lane_count, car_color)
        self.player.speed = S.BASE_SPEED[lvl] * self.map_defn.friction_mod
        dm = config.get_difficulty_multiplier()
        spawner_lvl = min(self.current_map_level - 1, len(S.SPAWN_INTERVAL) - 1)
        self.spawner = EnemySpawner(
            spawner_lvl, self.play_road_x, road_w, dm,
            map_id=self.current_map_id, max_enemies=self.map_defn.max_enemies)
        self.bonus_mgr = BonusManager(self.play_road_x, road_w, lane_count, True, dm)
        self.active_map = None
        self._has_tire_wear = False
        if self.current_map_id == "city":
            self.active_map = CityMap(self.current_map_level, self.play_road_x, road_w)
        elif self.current_map_id == "highway":
            self.active_map = HighwayMap(self.current_map_level, self.play_road_x, road_w)
        elif self.current_map_id == "circuit":
            self.active_map = CircuitMap(
                self.current_map_level, self.play_road_x, road_w, lane_count)
            self.enemies = []
            self._has_tire_wear = self.active_map.tires_wear
        self._level_complete_shown = False
        self._circuit_grip = 1.0
        self._circuit_drs = 1.0
        self._circuit_state = {}
        self.hud = HUD()
        self.enemies = []
        self.particles = []
        self.score_mgr.reset_level()
        self._survive_timer = float(S.SURVIVE_TIME)
        self._damage_taken_this_level = False
        
        # NOUVEAU: Système de slow-motion
        self._slow_motion_timer = 0
        self._slow_motion_factor = 1.0
        
        # Météo selon la carte (pas l'index legacy — circuit ≠ tempête automatique)
        weather_by_map = {
            "city":    ["clear", "clear", "fog"],
            "highway": ["clear", "rain", "storm"],
            "circuit": ["clear", "clear", "rain"],
        }
        wlist = weather_by_map.get(self.current_map_id, ["clear", "clear", "clear"])
        widx = min(self.current_map_level - 1, len(wlist) - 1)
        weather_type = wlist[widx]
        if self.map_defn and self.map_defn.extra.get("fog"):
            weather_type = "fog"
        if self.map_defn and self.map_defn.extra.get("storm"):
            weather_type = "storm"
        self.weather.set_weather(weather_type, intensity=0.15 + self.current_map_level * 0.12)
        
        # Réinitialiser les effets visuels
        self.visual_effects.reset()
        self.visual_effects.screen_effects.vignette_enabled = config.get(
            "glow_effects", True)

    def _next_level(self):
        self.achievements.on_level_completed(
            self.current_level, 
            self.player.lives,
            self._damage_taken_this_level
        )
        self.current_level += 1
        self._init_level()
        self.state = State.PLAYING

    # ----------------------------------------------------------
    def _update(self, dt: float):
        if self.state == State.MENU:
            return
            
        if self.state == State.PLAYING:

            lvl = self.current_level
            keys = pygame.key.get_pressed()
            
            # NOUVEAU: Slow-motion system sur crash
            if self._slow_motion_timer > 0:
                self._slow_motion_timer -= dt
                if self._slow_motion_timer <= 0:
                    self._slow_motion_factor = 1.0  # Retour normal
            
            # Time freeze: ralentit le temps (bonus) + slow-motion (crash)
            time_scale = 0.3 if self.bonus_mgr.time_freeze_active else 1.0
            time_scale *= self._slow_motion_factor  # Multiplier avec slow-motion crash
            effective_dt = dt * time_scale

            self.lighting.set_tunnel(0.0)
            effective_max = (S.MAX_SPEED[lvl] * S.BONUS_SLOW_FACTOR
                             if self.bonus_mgr.slow_active
                             else S.MAX_SPEED[lvl])
            is_circuit = isinstance(self.active_map, CircuitMap)
            circuit_cd = is_circuit and self.active_map.race._countdown > 0

            if is_circuit:
                effective_max *= self._circuit_grip * self._circuit_drs

            # --- Joueur ---
            if not circuit_cd:
                self.player.handle_input(keys, effective_dt, S.BASE_SPEED[lvl], effective_max)
                
                # NOUVEAU: Collision avec les glissières de sécurité latérales
                left_border = self.play_road_x + 5
                right_border = self.play_road_x + self.play_road_w - self.player.w - 5
                if self.player.x <= left_border:
                    self.player.x = left_border + 2
                    if self.player.speed > 2.0:
                        self.player.speed *= 0.72  # Pénalité de vitesse significative
                        self.sound_mgr.play("crash")  # Bruit d'impact métallique
                        self.visual_effects.screen_effects.shake(2.0)
                        self.visual_effects.particles.emit_sparks(
                            self.player.x, self.player.y + self.player.h // 2,
                            count=6, color=S.C_YELLOW, intensity=0.7
                        )
                elif self.player.x >= right_border:
                    self.player.x = right_border - 2
                    if self.player.speed > 2.0:
                        self.player.speed *= 0.72
                        self.sound_mgr.play("crash")
                        self.visual_effects.screen_effects.shake(2.0)
                        self.visual_effects.particles.emit_sparks(
                            self.player.x + self.player.w, self.player.y + self.player.h // 2,
                            count=6, color=S.C_YELLOW, intensity=0.7
                        )
                        
            self.player.update(effective_dt)
            self.player.update_animation(effective_dt)
            speed = self.player.speed
            
            # Mise à jour distance session
            self._session_distance += speed * dt * S.PIXELS_TO_METERS

            # Son du moteur
            speed_ratio = speed / S.MAX_SPEED[lvl]
            self.sound_mgr.play_engine(speed_ratio, self.player.nitro_active)

            # Particules de roues avec nouveau système
            if abs(self.player.anim_tilt) > 2.5 and speed > 4:
                if random.random() < 0.4:
                    wx = self.player.x + (self.player.w if self.player.anim_tilt > 0 else 0)
                    self.visual_effects.particles.emit_sparks(
                        wx, self.player.y + self.player.h - 5,
                        count=3, color=S.C_YELLOW, intensity=0.5
                    )

            # Traînée d'échappement améliorée
            if speed > 3:
                self.visual_effects.particles.emit_exhaust(
                    self.player.x + self.player.w // 2,
                    self.player.y + self.player.h,
                    speed_ratio,
                    self.player.nitro_active
                )

            # --- Route ---
            self.road.update(speed, effective_dt)

            # --- Météo ---
            self.weather.update(effective_dt, speed)

            # --- Effets visuels avancés ---
            self.visual_effects.update(effective_dt, speed)
            self.particle_effects.update(effective_dt)

            # --- Score survie ---
            self.score_mgr.add_time(speed, effective_dt, self.player.nitro_active)

            lane_w = max(1, self.play_road_w // max(1, self.player.lane_count))
            player_lane = self.player.get_lane(self.play_road_x, lane_w)
            near_miss_detected = False

            # --- Course circuit vs IA ---
            if is_circuit:
                self._circuit_state = self.active_map.update(
                    effective_dt, speed, self.player.y,
                    player_lane, self.player.x, self.player.w,
                    bonuses=self.bonus_mgr.bonuses,
                    obstacles=self.road.obstacles)
                self._circuit_grip = self._circuit_state.get("grip_mod", 1.0)
                self._circuit_drs = self._circuit_state.get("drs_boost", 1.0)
                self.enemies = self.active_map.get_rivals()
                if self._circuit_state.get("lap_complete"):
                    lap_n = self.active_map.race.player_laps
                    self.hud.add_popup(
                        S.SCREEN_W // 2, 180,
                        f"TOUR {lap_n} / {self.active_map.total_laps}",
                        S.C_YELLOW)
                    self.sound_mgr.play("level_complete")
                pos = self._circuit_state.get("player_position", 1)
                if pos <= 3 and random.random() < 0.02:
                    self.score_mgr.add(25)
            else:
                new_enemies = self.spawner.update(effective_dt, speed, len(self.enemies))
                self.enemies.extend(new_enemies)

            # --- Ennemis / Rivaux ---
            for e in self.enemies[:]:
                if not is_circuit:
                    e.update(effective_dt, speed, player_lane,
                             self.player.x, self.player.y, self.player.w)
                    if e.is_off_screen():
                        self.enemies.remove(e)
                        continue
                    
                # NOUVEAU: Near-Miss Detection (manque de peu)
                enemy_rect = e.get_rect()
                player_rect = self.player.get_rect()
                expanded_rect = player_rect.inflate(40, 40)  # Zone near-miss
                
                if (not e.passed and 
                    expanded_rect.colliderect(enemy_rect) and 
                    not player_rect.colliderect(enemy_rect) and
                    not near_miss_detected and
                    abs(self.player.y - e.y) < 60):  # Proche verticalement
                    near_miss_detected = True
                    # Bonus near-miss
                    self.score_mgr.add(50, near_miss=True)
                    self.hud.add_popup(int(self.player.x + self.player.w//2), 
                                       int(self.player.y), "NEAR MISS! +50", 
                                       S.C_MAGENTA)
                    # Effet sonore subtil
                    self.sound_mgr.play("overtake")  # réutiliser son overtake
                    self.visual_effects.particles.emit_sparks(
                        self.player.x + self.player.w//2, 
                        self.player.y + self.player.h//2,
                        count=5, color=S.C_MAGENTA, intensity=0.8
                    )
                    
                # Dépassement amélioré
                if not e.passed and e.y > self.player.y + self.player.h:
                    e.passed = True
                    pts = self.score_mgr.add_overtake(self.player.nitro_active)
                    self.achievements.check_overtake_achievements(self.score_mgr.overtakes)
                    self.achievements.check_streak_achievements(self.score_mgr.streak)
                    self.player.shield_charge = min(
                        S.SHIELD_MAX,
                        self.player.shield_charge + S.SHIELD_OVERTAKE)
                    
                    # NOUVEAU: Notifier spawner pour difficulté adaptative
                    self.spawner.on_overtake(self.score_mgr.streak)
                    
                    # NOUVEAU: Feedback visuel amélioré pour dépassement
                    label = f"+{pts}" + (" NITRO" if self.player.nitro_active else "")
                    if self.score_mgr.streak >= S.STREAK_MIN:
                        label += f" (x{self.score_mgr.streak})"
                        # Effet spécial pour combo
                        self.visual_effects.screen_effects.shake(3.0)  # Shake léger
                    
                    self.hud.add_popup(int(e.x + e.w // 2), int(e.y), label, S.C_YELLOW)
                    self.sound_mgr.play("overtake")
                    
                    # NOUVEAU: Particules sur dépassement
                    self.visual_effects.particles.emit(
                        e.x + e.w//2, e.y + e.h//2, 
                        count=8, color=S.C_YELLOW, ptype='star',
                        spread=20, speed=4
                    )
                    
                # Collision
                can_collide = (not self.player.invincible 
                               and not self.player.shield_active 
                               and not self.player.ghost_mode)
                if self.player.get_rect().colliderect(e.get_rect()):
                    if self.player.shield_active:
                        rival_name = getattr(e, "name", None)
                        if is_circuit:
                            if hasattr(e, "hit") and getattr(e, "collision_timer", 0.0) <= 0.0:
                                e.hit()
                                if rival_name:
                                    self.hud.add_popup(
                                        e.x, e.y - 30,
                                        f"SHIELD SMASH {rival_name}", S.C_CYAN)
                                self.sound_mgr.play("shield_hit")
                                self.visual_effects.particles.emit_sparks(
                                    e.x + e.w//2, e.y + e.h//2,
                                    count=12, color=S.C_CYAN, intensity=1.0
                                )
                        else:
                            # Hors circuit: le bouclier détruit les voitures de trafic
                            if e in self.enemies:
                                self.enemies.remove(e)
                            self.score_mgr.add_overtake(self.player.nitro_active)
                            self.sound_mgr.play("shield_hit")
                            self.visual_effects.particles.emit_sparks(
                                e.x + e.w//2, e.y + e.h//2,
                                count=12, color=S.C_CYAN, intensity=1.0
                            )
                            continue
                    elif can_collide:
                        rival_name = getattr(e, "name", None)
                        if rival_name:
                            self.hud.add_popup(
                                self.player.x, self.player.y - 30,
                                f"CONTACT {rival_name}", S.C_RED)
                            if hasattr(e, "hit"):
                                e.hit()
                        self._handle_collision(enemy_type=getattr(e, "type", 0))
                        return

            # --- Obstacles (carrés jaunes / obstacles de route) ---
            for obs in self.road.obstacles[:]:
                obs_rect = pygame.Rect(obs["x"], obs["y"], obs["w"], obs["h"])
                
                # Collision avec le joueur
                if self.player.get_rect().colliderect(obs_rect):
                    if self.player.shield_active:
                        self.sound_mgr.play("shield_hit")
                        self.visual_effects.particles.emit_sparks(
                            obs["x"] + obs["w"] // 2, obs["y"] + obs["h"] // 2,
                            count=12, color=S.C_CYAN, intensity=0.8
                        )
                    else:
                        self.player.speed = max(1.5, self.player.speed * 0.5)  # Ralentissement de 50%
                        self.sound_mgr.play("crash")
                        self.visual_effects.screen_effects.shake(3.0)
                        self.visual_effects.particles.emit_sparks(
                            obs["x"] + obs["w"] // 2, obs["y"] + obs["h"] // 2,
                            count=12, color=S.C_YELLOW, intensity=0.8
                        )
                        self.hud.add_popup(
                            int(self.player.x + self.player.w // 2), int(self.player.y),
                            "OBSTACLE! -50%", S.C_RED)
                    self.road.reset_obstacle(obs)
                    
                # Collision avec les rivaux (seulement en mode circuit)
                elif is_circuit:
                    for r in self.enemies:
                        if hasattr(r, "get_rect") and r.get_rect().colliderect(obs_rect):
                            if getattr(r, "shield_timer", 0.0) > 0.0:
                                self.sound_mgr.play("shield_hit")
                                self.visual_effects.particles.emit_sparks(
                                    obs["x"] + obs["w"] // 2, obs["y"] + obs["h"] // 2,
                                    count=8, color=S.C_CYAN, intensity=0.6
                                )
                            else:
                                r.actual_speed = max(1.0, r.actual_speed * 0.5)  # L'IA est ralentie aussi !
                                self.sound_mgr.play("crash")
                                self.visual_effects.particles.emit_sparks(
                                    obs["x"] + obs["w"] // 2, obs["y"] + obs["h"] // 2,
                                    count=8, color=S.C_YELLOW, intensity=0.6
                                )
                                self.hud.add_popup(
                                    int(r.x + r.w // 2), int(r.y),
                                    f"{r.name} -50%", S.C_YELLOW)
                            self.road.reset_obstacle(obs)
                            break

            # --- Bonus ---
            effects = self.bonus_mgr.update(
                effective_dt, speed, self.player.get_rect(),
                self.player.x + self.player.w // 2,
                self.player.y + self.player.h // 2,
                car=self.player,
                rivals=self.enemies if is_circuit else None
            )
            if effects.get("rival_collected"):
                for r, kind, color in effects["rival_collected"]:
                    self.hud.add_popup(
                        int(r.x + r.w // 2), int(r.y),
                        f"{r.name} +{kind.upper()}", color)
                    self.sound_mgr.play("overtake")
                    self.visual_effects.particles.emit_sparks(
                        r.x + r.w // 2, r.y + r.h // 2,
                        count=8, color=color, intensity=0.7
                    )
            # Logique carte active (après déplacement joueur)
            if self.active_map is not None:
                if isinstance(self.active_map, CityMap):
                    city_fx = self.active_map.update(effective_dt, speed)
                    city_fx = self.active_map.check_collisions(
                        self.player.get_rect(), city_fx, effective_dt)
                    if city_fx.get("score_penalty"):
                        self.score_mgr.score = max(
                            0, self.score_mgr.score + city_fx["score_penalty"])
                    if city_fx.get("force_slow"):
                        self.player.speed = min(self.player.speed, 2.5)
                    if city_fx.get("hit_pedestrian"):
                        self._handle_collision()
                        return
                elif isinstance(self.active_map, HighwayMap):
                    hw_fx = self.active_map.update(
                        effective_dt, speed, speed * 30)
                    self.player.x += hw_fx.get("lateral_drift", 0)
                    self.player.x = max(
                        self.play_road_x + 4,
                        min(self.play_road_x + self.play_road_w - self.player.w - 4,
                            self.player.x))
                    if hw_fx.get("visibility", 1.0) < 0.9:
                        self.lighting.set_tunnel(
                            max(0.0, 1.0 - hw_fx["visibility"]) * 0.55)
                    if hw_fx.get("tunnel_boost"):
                        # Slipstream exit boost
                        self.player.speed = min(self.player.speed + 0.12 * effective_dt, S.MAX_SPEED[lvl] * 1.25)
                        if random.random() < 0.25:
                            self.visual_effects.particles.emit_sparks(
                                self.player.x + self.player.w // 2, self.player.y + self.player.h,
                                count=2, color=S.C_CYAN, intensity=0.6
                            )
                elif isinstance(self.active_map, CircuitMap):
                    if self._circuit_state.get("race_finished") and not self._level_complete_shown:
                        self._level_complete_shown = True
                        self._show_level_complete()
                        return
            self.player.nitro_charge = min(S.NITRO_MAX,
                                            self.player.nitro_charge + effects["nitro_add"])
            self.player.shield_charge = min(S.SHIELD_MAX,
                                            self.player.shield_charge + effects["shield_add"])
            if effects["life_add"] and self.player.lives < S.MAX_LIVES:
                self.player.lives += 1
                self.sound_mgr.play("life_up")
            
            # Ghost mode
            if effects["ghost"]:
                self.player.activate_ghost(S.BONUS_GHOST_DURATION)
                
            self.score_mgr.add_bonus(effects["score_add"])
            
            for kind in effects["collected"]:
                col = S.BONUS_COLORS_EXTENDED.get(kind, (255, 255, 255))
                icon = S.BONUS_ICONS_EXTENDED.get(kind, "?")
                self.hud.add_popup(
                    S.SCREEN_W // 2,
                    S.SCREEN_H // 2 - 40,
                    f"{icon} +BONUS",
                    col)
                self.particle_effects.add_spark(S.SCREEN_W // 2, S.SCREEN_H // 2, col, 8)
                self.sound_mgr.play("bonus_collect")
                self.achievements.on_bonus_collected()
                
                if kind == "slow":
                    self.achievements.on_slow_activated()

            # --- Particules ---
            for p in self.particles[:]:
                p.update(effective_dt)
                if p.life <= 0:
                    self.particles.remove(p)

            self._last_dt = effective_dt

            # --- HUD ---
            self.hud.update(effective_dt)

            # --- Objectifs ---
            self._check_objective(lvl, speed, effective_dt)
            
            # --- Achievements: vitesse ---
            self.achievements.on_speed_reached(speed * 30)

    def _handle_collision(self, obstacle: bool = False, enemy_type: int = 0):
        """Gère une collision avec effets visuels améliorés et scaled feedback."""
        dead = self.player.take_hit()
        self._damage_taken_this_level = True
        self.score_mgr.break_streak()
        self.hud.trigger_flash()
        self.sound_mgr.play("crash")
        
        # Effets visuels avancés
        collision_x = self.player.x + self.player.w // 2
        collision_y = self.player.y + self.player.h // 2
        
        # NOUVEAU: Intensité scale selon type d'ennemi (0=standard, 1=rapide, 2=camion, 3=imprévisible)
        intensity_multipliers = {0: 1.0, 1: 1.3, 2: 1.8, 3: 1.2}
        intensity = intensity_multipliers.get(enemy_type, 1.0) * (1.5 if obstacle else 1.0)
        
        # NOUVEAU: Shake scale selon intensité (max 35)
        shake_amount = min(35, 15.0 * intensity)
        self.visual_effects.screen_effects.shake(shake_amount)
        
        # NOUVEAU: Slow-motion sur crash (0.2x speed pendant 30 frames)
        self._slow_motion_timer = 30
        self._slow_motion_factor = 0.2
        
        # Particules de collision spectaculaires
        self.visual_effects.particles.emit_collision(collision_x, collision_y, intensity)
        
        # Flash color selon intensité
        flash_color = S.C_RED if intensity > 1.5 else S.C_MAGENTA
        self.visual_effects.screen_effects.flash(flash_color, int(15 * intensity))
        
        if dead:
            # Effet de mort plus spectaculaire
            self.visual_effects.particles.emit(collision_x, collision_y, 30, 
                                              (255, 50, 50), 'fire', spread=15, speed=8)
            # Shake final intense
            self.visual_effects.screen_effects.shake(40.0)
            self._end_game()

    # ----------------------------------------------------------
    def _check_objective(self, lvl: int, speed: float, dt: float):
        """Vérifie si l'objectif du niveau est atteint."""
        sc = self.score_mgr

        if self.map_defn and not self._level_complete_shown:
            if self.current_map_id == "city":
                target = int(S.TARGET_SCORE * (0.55 + 0.2 * self.current_map_level))
                if sc.score >= target:
                    self._level_complete_shown = True
                    self._show_level_complete()
                    return
            elif self.current_map_id == "highway":
                target_ot = 8 + self.current_map_level * 6
                if sc.overtakes >= target_ot:
                    self._level_complete_shown = True
                    self._show_level_complete()
                    return
            elif self.current_map_id == "circuit":
                return  # géré par tours dans CircuitMap

        if lvl == 0 and sc.score >= S.TARGET_SCORE:
            self._show_transition(lvl)
        elif lvl == 1 and sc.overtakes >= S.TARGET_OVERTAKES:
            self._show_transition(lvl)
        elif lvl == 2:
            self._survive_timer -= dt
            self.achievements.on_survival_time(
                S.SURVIVE_TIME - self._survive_timer, lvl)
            if self._survive_timer <= 0:
                self._show_transition(lvl)
                
        # Achievements score
        self.achievements.check_score_achievements(int(sc.total_score + sc.score))
        self.achievements.on_distance_traveled(self._session_distance)

    def _show_level_complete(self):
        if self.state != State.PLAYING:
            return
        self.score_mgr.commit_level(
            map_id=self.current_map_id, map_level=self.current_map_level)
        pos = 1
        if isinstance(self.active_map, CircuitMap):
            pos = self.active_map.race.player_finish_pos
        self._transition_stats = {
            "score": self.score_mgr.get_display(),
            "overtakes": self.score_mgr.overtakes,
            "bonuses": self.score_mgr.bonuses_col,
            "max_streak": self.score_mgr.max_streak,
            "race_position": pos,
        }
        if self.current_map_id == "circuit":
            self.state = State.RACE_RANKING
        else:
            self.state = State.LEVEL_COMPLETE
        self.sound_mgr.play("level_complete")

    def _show_transition(self, lvl: int):
        self.score_mgr.commit_level(
            lvl, map_id=self.current_map_id, map_level=self.current_map_level)
        self._transition_stats = {
            "score": self.score_mgr.get_display(),
            "overtakes": self.score_mgr.overtakes,
            "bonuses": self.score_mgr.bonuses_col,
            "max_streak": self.score_mgr.max_streak,
        }
        self._is_last_level = (lvl >= 2)
        self.renderer.transition_reset()  # Réinitialise la sélection
        self.state = State.TRANSITION
        self.sound_mgr.play("level_complete")

    def _end_game(self):
        self.score_mgr.commit_level(
            self.current_level,
            map_id=self.current_map_id,
            map_level=self.current_map_level,
        )
        self.state = State.GAMEOVER
        self.sound_mgr.stop_engine()
        self.sound_mgr.play("game_over")
        self.sound_mgr.stop_music()
        self.achievements.on_game_over()
        self._save_progress()

    # ----------------------------------------------------------
    def _draw(self):
        if self.state == State.MENU:
            self.renderer.draw_menu(
                self.screen, self.selected_level,
                self.score_mgr.hi_scores_legacy, 1.0)

        elif self.state == State.MAP_SELECT:
            self.map_select.draw(
                self.screen, self.score_mgr.hi_scores, self.score_mgr.unlocked)

        elif self.state == State.LEVEL_COMPLETE:
            self.renderer.draw_transition(
                self.screen, self.current_level,
                self._transition_stats, True)

        elif self.state == State.RACE_RANKING:
            self.screen.fill(S.C_BG)
            font_big = pygame.font.SysFont("orbitron,consolas", 32, bold=True)
            font = pygame.font.SysFont("consolas", 20, bold=True)
            pos = self._transition_stats.get("race_position", 1)
            if pos == 1:
                title = font_big.render("VICTOIRE !", True, S.C_YELLOW)
            elif pos <= 3:
                title = font_big.render(f"PODIUM — {pos}e", True, S.C_CYAN)
            else:
                title = font_big.render(f"COURSE TERMINEE — {pos}e", True, S.C_MAGENTA)
            self.screen.blit(title, title.get_rect(centerx=S.SCREEN_W // 2, centery=70))
            if isinstance(self.active_map, CircuitMap):
                secs = self.active_map.race.player_finish_time / S.FPS
                tm = font.render(
                    f"Temps: {int(secs) // 60}:{secs % 60:05.2f}", True, (180, 180, 200))
                self.screen.blit(tm, tm.get_rect(centerx=S.SCREEN_W // 2, centery=115))
                for i, (name, rk, lap) in enumerate(self.active_map.get_ranking_display()):
                    is_you = name == "Joueur"
                    col = S.C_CYAN if is_you else S.C_WHITE
                    if rk == 1:
                        col = S.C_YELLOW
                    line = font.render(f"{rk}. {name}  —  {lap} tours", True, col)
                    self.screen.blit(line, (S.SCREEN_W // 2 - 160, 150 + i * 34))
            hint = pygame.font.SysFont("consolas", 14).render(
                "ENTER: Retour sélection carte", True, (120, 120, 140))
            self.screen.blit(hint, hint.get_rect(centerx=S.SCREEN_W // 2, centery=S.SCREEN_H - 40))

        elif self.state == State.SETTINGS:
            config_data = {
                "audio_enabled": self.sound_mgr.enabled,
                "music_volume": self.sound_mgr.volume_music,
                "sfx_volume": self.sound_mgr.volume_sfx,
                "difficulty": config.get("difficulty", "normal"),
                "car_color": config.get("car_color", "cyan"),
            }
            self.renderer.draw_settings(self.screen, config_data)
            
        elif self.state == State.ACHIEVEMENTS:
            self.renderer.draw_achievements(self.screen, self.achievements)

        elif self.state in (State.PLAYING, State.PAUSE):
            canvas = self.frame_buffer

            # Fond + route
            self.road.draw(canvas, self.player.speed)
            if isinstance(self.active_map, CityMap):
                self.active_map.draw_decor(canvas, self.player.speed)
            elif isinstance(self.active_map, HighwayMap):
                self.active_map.draw_decor(canvas, self.player.speed)
            elif isinstance(self.active_map, CircuitMap):
                self.active_map.draw_decor(canvas, self.player.speed)
                self.active_map.draw_race_ui(canvas, self._circuit_state)
            if isinstance(self.active_map, CityMap):
                self.active_map.draw_hazards(canvas)

            # Particules de skid marks (derrière)
            self.particle_effects.draw(canvas)
            
            # Nouveau système de particules avancées
            self.visual_effects.draw_particles(canvas)
            
            # Bonus
            self.bonus_mgr.draw(canvas)
            
            # Ennemis avec rendu amélioré
            car_renderer = self.visual_effects.car_renderer
            for e in self.enemies:
                if hasattr(e, "draw"):
                    e.draw(canvas)
                else:
                    enemy_color = getattr(e, "color", S.ENEMY_COLORS[min(e.type, len(S.ENEMY_COLORS) - 1)])
                    speed_ratio = e.speed / self.player.speed if self.player.speed > 0 else 1.0
                    car_renderer.draw_enhanced_enemy(canvas, e, enemy_color, speed_ratio)
                
            # Particules (devant) - ancien système
            for p in self.particles:
                p.draw(canvas)
                
            # Joueur (sprite néon fiable + lueur nitro)
            player_color = S.CAR_COLORS.get(self.player.car_color, S.C_CYAN)
            if self.player.nitro_active:
                car_renderer.draw_enhanced_player(
                    canvas, self.player, player_color,
                    tilt=self.player.anim_tilt, nitro_active=True,
                    ghost_mode=self.player.ghost_mode)
            else:
                self.player.draw(canvas)
            
            # Météo (sous le HUD, pas par-dessus tout l'écran blanc)
            if config.get("show_weather", True) and self.weather.weather_type != "clear":
                self.weather.draw(canvas)

            self.visual_effects.skidmarks.draw(canvas)
            # Éclairage désactivé en jeu normal (évite halo blanc) — tunnel autoroute seulement
            if isinstance(self.active_map, HighwayMap) and self.lighting.tunnel_darkness > 0.25:
                self.lighting.apply(
                    canvas, (int(self.player.x), int(self.player.y), self.player.w),
                    enable_headlights=True)
            self.road_renderer.draw_rearview(canvas, self.enemies, self.player.y)

            # HUD
            lvl = self.current_level
            obj_pct, obj_label = self._get_objective_display()
            
            active_effects = self.bonus_mgr.get_active_effects()
            
            # Calcul du temps de course restant sur circuit
            time_left = None
            if self.current_map_id == "circuit" and self.active_map is not None:
                time_left = max(0.0, 90.0 - self.active_map.race.race_time / 60.0)

            self.hud.draw(
                canvas,
                score=self.score_mgr.get_display(),
                lives=self.player.lives,
                speed=self.player.speed,
                nitro_charge=self.player.nitro_charge,
                nitro_active=self.player.nitro_active,
                shield_charge=self.player.shield_charge,
                shield_active=self.player.shield_active,
                streak=self.score_mgr.streak,
                level=lvl,
                objective_pct=obj_pct,
                objective_label=obj_label,
                active_effects=active_effects,
                enemies=self.enemies,
                player_y=self.player.y,
                map_id=self.current_map_id,
                map_level=self.current_map_level,
                grip_mod=self._circuit_grip,
                has_tire_wear=self._has_tire_wear,
                drs_active=self._circuit_state.get("drs_active", False),
                time_left=time_left,
            )

            if self.state == State.PAUSE:
                self.renderer.draw_pause(canvas)

            # Appliquer les effets d'écran (shake, flash, vignette)
            if self.current_map_id == "circuit":
                self.visual_effects.screen_effects.vignette_enabled = False
            else:
                self.visual_effects.screen_effects.vignette_enabled = config.get(
                    "glow_effects", True)
            final_canvas = self.visual_effects.apply_screen_effects(
                canvas, config.get("screen_shake", True))
            
            self.screen.fill((0, 0, 0))
            self.screen.blit(final_canvas, (0, 0))

        elif self.state == State.TRANSITION:
            self.renderer.draw_transition(
                self.screen, self.current_level,
                self._transition_stats, self._is_last_level)

        elif self.state == State.GAMEOVER:
            self.renderer.draw_gameover(
                self.screen,
                score=self.score_mgr.get_display(),
                hi_score=self.score_mgr.get_hi_map(
                    self.current_map_id, self.current_map_level),
                new_record=self.score_mgr.is_new_record(
                    map_id=self.current_map_id, map_level=self.current_map_level))

        elif self.state == State.WIN:
            hi_vals = list(self.score_mgr.hi_scores.values()) or [0]
            self.renderer.draw_win(
                self.screen,
                total_score=int(self.score_mgr.total_score),
                hi_scores=hi_vals)

    def _get_objective_display(self):
        lvl = self.current_level
        sc  = self.score_mgr
        if self.current_map_id == "city":
            target = int(S.TARGET_SCORE * (0.55 + 0.2 * self.current_map_level))
            pct = sc.score / max(1, target)
            label = f"{sc.get_display():,} / {target:,} pts"
        elif self.current_map_id == "highway":
            target = 8 + self.current_map_level * 6
            pct = sc.overtakes / max(1, target)
            label = f"{sc.overtakes} / {target} dépassements"
        elif self.current_map_id == "circuit" and isinstance(self.active_map, CircuitMap):
            pct = self.active_map.lap_progress
            pos = self._circuit_state.get("player_position", 1)
            label = (f"Tour {self.active_map.current_lap}/{self.active_map.total_laps}"
                     f"  ·  {pos}e")
        elif lvl == 0:
            pct   = sc.score / S.TARGET_SCORE
            label = f"{sc.get_display():,} / {S.TARGET_SCORE:,} pts"
        elif lvl == 1:
            pct   = sc.overtakes / S.TARGET_OVERTAKES
            label = f"{sc.overtakes} / {S.TARGET_OVERTAKES} dépassements"
        else:
            t   = max(0, self._survive_timer)
            pct = t / S.SURVIVE_TIME
            label = f"Survivre : {int(t)}s restantes"
        return min(1.0, pct), label


# ============================================================

if __name__ == "__main__":
    game = Game()
    game.run()
