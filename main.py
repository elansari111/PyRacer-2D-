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
from visual_effects import VisualEffectsManager, GlowEffect, CarRenderer


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

        # Sous-systèmes
        self.player: Player | None = None
        self.road: Road | None = None
        self.spawner: EnemySpawner | None = None
        self.bonus_mgr: BonusManager | None = None
        self.hud: HUD | None = None
        self.score_mgr: ScoreManager = ScoreManager()
        
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
        self._shake_timer = 0.0
        
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
                            self._start_game()
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

                # --- PLAYING ---
                elif self.state == State.PLAYING:
                    if event.key == pygame.K_p:
                        self.state = State.PAUSE
                        self.sound_mgr.play("menu_select")
                    elif event.key == pygame.K_SPACE:
                        if self.player.activate_nitro():
                            self.sound_mgr.play("nitro_activate")
                            self.hud.add_popup(
                                self.player.x + self.player.w // 2,
                                self.player.y, "⚡ NITRO !", S.C_YELLOW)
                            self.achievements.on_nitro_activated()
                            self.particle_effects.add_nitro_flame(
                                self.player.x + self.player.w // 2, 
                                self.player.y + self.player.h)
                    elif event.key == pygame.K_b:
                        if self.player.activate_shield():
                            self.sound_mgr.play("shield_activate")
                            self.hud.add_popup(
                                self.player.x + self.player.w // 2,
                                self.player.y, "🛡 BOUCLIER", S.C_CYAN)
                            self.achievements.on_shield_activated()

                # --- PAUSE ---
                elif self.state == State.PAUSE:
                    if event.key == pygame.K_p:
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
        self.current_level = self.selected_level
        self.score_mgr.reset_level()
        self._init_level()
        self.state = State.PLAYING
        self.sound_mgr.play_music("race")
        self.achievements.session_stats["level_damage"] = {0: False, 1: False, 2: False}
        self._session_distance = 0.0

    def _init_level(self):
        lvl = self.current_level
        self.road = Road(lvl)
        car_color = config.get("car_color", "cyan")
        self.player = Player(S.ROAD_X, S.ROAD_WIDTH, S.LANE_COUNT[lvl], car_color)
        self.player.speed = S.BASE_SPEED[lvl]
        self.spawner = EnemySpawner(lvl, S.ROAD_X, S.ROAD_WIDTH)
        self.bonus_mgr = BonusManager(S.ROAD_X, S.ROAD_WIDTH, S.LANE_COUNT[lvl])
        self.hud = HUD()
        self.enemies = []
        self.particles = []
        self.score_mgr.reset_level()
        self._survive_timer = float(S.SURVIVE_TIME)
        self._damage_taken_this_level = False
        
        # NOUVEAU: Système de slow-motion
        self._slow_motion_timer = 0
        self._slow_motion_factor = 1.0
        
        # Météo selon le niveau
        weather_type = S.WEATHER_BY_LEVEL[lvl] if lvl < len(S.WEATHER_BY_LEVEL) else "clear"
        self.weather.set_weather(weather_type, intensity=0.3 + lvl * 0.2)
        
        # Réinitialiser les effets visuels
        self.visual_effects.reset()

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
            if self._shake_timer > 0:
                self._shake_timer -= dt

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

            # Bonus "slow" et "ghost"
            effective_max = (S.MAX_SPEED[lvl] * S.BONUS_SLOW_FACTOR
                             if self.bonus_mgr.slow_active
                             else S.MAX_SPEED[lvl])

            # --- Joueur ---
            self.player.handle_input(keys, effective_dt, S.BASE_SPEED[lvl], effective_max)
            self.player.update(effective_dt)
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

            # --- Spawn ennemis ---
            new_enemies = self.spawner.update(effective_dt, speed)
            self.enemies.extend(new_enemies)

            # --- Ennemis ---
            lane_w = S.ROAD_WIDTH // self.spawner.lane_count
            player_lane = self.player.get_lane(S.ROAD_X, lane_w)
            near_miss_detected = False
            
            for e in self.enemies[:]:
                # NOUVEAU: Passer les infos joueur pour comportement intelligent
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
                if can_collide and self.player.get_rect().colliderect(e.get_rect()):
                    self._handle_collision(enemy_type=e.type)
                    return

            # --- Obstacles (Circuit) ---
            if lvl == 2:
                for rect in self.road.get_obstacle_rects():
                    can_collide = (not self.player.invincible 
                                   and not self.player.shield_active
                                   and not self.player.ghost_mode)
                    if can_collide and self.player.get_rect().colliderect(rect):
                        self._handle_collision(obstacle=True)
                        return

            # --- Bonus ---
            effects = self.bonus_mgr.update(
                effective_dt, speed, self.player.get_rect(),
                self.player.x + self.player.w // 2,
                self.player.y + self.player.h // 2
            )
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
        
        # NOUVEAU: Intensité scale selon type d'ennemi
        intensity_multipliers = {0: 1.0, 1: 1.3, 2: 1.8, 3: 1.2}  # rapide, camion, imprévisible
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

        if lvl == 0 and sc.score >= S.TARGET_SCORE:
            self._show_transition(lvl)
        elif lvl == 1 and sc.overtakes >= S.TARGET_OVERTAKES:
            self._show_transition(lvl)
        elif lvl == 2:
            self._survive_timer -= dt / S.FPS
            self.achievements.on_survival_time(
                S.SURVIVE_TIME - self._survive_timer, lvl)
            if self._survive_timer <= 0:
                self._show_transition(lvl)
                
        # Achievements score
        self.achievements.check_score_achievements(int(sc.total_score + sc.score))
        self.achievements.on_distance_traveled(self._session_distance)

    def _show_transition(self, lvl: int):
        self.score_mgr.commit_level(lvl)
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
        self.score_mgr.commit_level(self.current_level)
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
                self.score_mgr.hi_scores, 1.0)

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
            
            # Particules de skid marks (derrière)
            self.particle_effects.draw(canvas)
            
            # Nouveau système de particules avancées
            self.visual_effects.draw_particles(canvas)
            
            # Bonus
            self.bonus_mgr.draw(canvas)
            
            # Ennemis avec rendu amélioré
            car_renderer = CarRenderer()
            for e in self.enemies:
                enemy_color = S.ENEMY_COLORS[e.type]
                speed_ratio = e.speed / self.player.speed if self.player.speed > 0 else 1.0
                car_renderer.draw_enhanced_enemy(canvas, e, enemy_color, speed_ratio)
                
            # Particules (devant) - ancien système
            for p in self.particles:
                p.draw(canvas)
                
            # Joueur avec rendu amélioré
            player_color = S.CAR_COLORS.get(self.player.car_color, S.C_CYAN)
            car_renderer.draw_enhanced_player(
                canvas, self.player, player_color,
                tilt=self.player.anim_tilt,
                nitro_active=self.player.nitro_active,
                ghost_mode=self.player.ghost_mode
            )
            
            # Météo
            if config.get("show_weather", True):
                self.weather.draw(canvas)

            # HUD
            lvl = self.current_level
            obj_pct, obj_label = self._get_objective_display()
            
            active_effects = self.bonus_mgr.get_active_effects()
            
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
            )

            if self.state == State.PAUSE:
                self.renderer.draw_pause(canvas)

            # Appliquer les effets d'écran (shake, flash, vignette)
            final_canvas = self.visual_effects.apply_screen_effects(canvas)
            
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
                hi_score=self.score_mgr.get_hi(self.current_level),
                new_record=self.score_mgr.is_new_record(self.current_level))

        elif self.state == State.WIN:
            self.renderer.draw_win(
                self.screen,
                total_score=int(self.score_mgr.total_score),
                hi_scores=self.score_mgr.hi_scores)

    def _get_objective_display(self):
        lvl = self.current_level
        sc  = self.score_mgr
        if lvl == 0:
            pct   = sc.score / S.TARGET_SCORE
            label = f"{sc.get_display():,} / {S.TARGET_SCORE:,} pts"
        elif lvl == 1:
            pct   = sc.overtakes / S.TARGET_OVERTAKES
            label = f"{sc.overtakes} / {S.TARGET_OVERTAKES} dépassements"
        else:
            t   = max(0, self._survive_timer)
            pct = t / S.SURVIVE_TIME
            label = f"Survivre : {int(t)}s restantes"
        return pct, label


# ============================================================

if __name__ == "__main__":
    game = Game()
    game.run()
