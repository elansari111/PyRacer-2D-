# ============================================================
#  PyRacer: Ultimate Neon Highway
#  sound_manager.py — Gestion audio complète (SFX + Musique)
# ============================================================

import pygame
import numpy as np
import random
import settings as S


class SoundManager:
    """
    Gestionnaire audio avec génération procédurale de sons.
    Génère des effets sonores sans fichiers externes.
    """
    
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.enabled = True
        self.music_enabled = True
        self.sfx_enabled = True
        self.volume_master = 0.7
        self.volume_music = 0.5
        self.volume_sfx = 0.8
        
        # Buffers de sons générés
        self.sounds = {}
        self.music_channel = None
        self.current_music = None
        
        self._generate_all_sounds()
        
    def _generate_all_sounds(self):
        """Génère tous les effets sonores procéduralement."""
        self.sounds['engine_idle'] = self._generate_engine_sound(80, 0.3)
        self.sounds['engine_rev'] = self._generate_engine_sound(200, 0.5)
        self.sounds['engine_nitro'] = self._generate_engine_sound(350, 0.8, distortion=True)
        self.sounds['crash'] = self._generate_noise_burst(0.3, 0.8)
        self.sounds['shield_hit'] = self._generate_tone(440, 0.15, fade=True)
        self.sounds['nitro_activate'] = self._generate_sweep(200, 800, 0.5)
        self.sounds['shield_activate'] = self._generate_sweep(600, 200, 0.4)
        self.sounds['bonus_collect'] = self._generate_tone(880, 0.1, waveform='square')
        self.sounds['life_up'] = self._generate_arpeggio([523, 659, 784, 1047], 0.4)
        self.sounds['overtake'] = self._generate_tone(1200, 0.08, waveform='saw')
        self.sounds['level_complete'] = self._generate_arpeggio([440, 554, 659, 880], 1.0)
        self.sounds['game_over'] = self._generate_sweep(400, 100, 1.2)
        self.sounds['menu_select'] = self._generate_tone(600, 0.05)
        self.sounds['menu_confirm'] = self._generate_tone(800, 0.1)
        self.sounds['brake_screech'] = self._generate_noise_burst(0.4, 0.6, filtered=True)
        self.sounds['slow_motion'] = self._generate_sweep(300, 150, 0.3)
        self.sounds['streak'] = self._generate_tone(1500, 0.15, waveform='square')
        
    def _generate_tone(self, freq, duration, volume=0.5, waveform='sine', fade=True):
        """Génère un son simple."""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        if waveform == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif waveform == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif waveform == 'saw':
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))
        else:
            wave = np.sin(2 * np.pi * freq * t)
            
        if fade:
            # Fade in/out
            fade_len = min(int(0.01 * sample_rate), samples // 4)
            wave[:fade_len] *= np.linspace(0, 1, fade_len)
            wave[-fade_len:] *= np.linspace(1, 0, fade_len)
            
        wave = (wave * volume * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        sound = pygame.sndarray.make_sound(stereo)
        return sound
    
    def _generate_sweep(self, freq_start, freq_end, duration, volume=0.5):
        """Génère un sweep de fréquence."""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        freq = np.linspace(freq_start, freq_end, samples)
        wave = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
        wave = (wave * volume * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo)
    
    def _generate_noise_burst(self, duration, volume=0.5, filtered=False):
        """Génère un bruit (explosion, crash)."""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        wave = np.random.uniform(-1, 1, samples)
        
        if filtered:
            # Simple low-pass
            wave = np.convolve(wave, np.ones(10)/10, mode='same')
            
        # Enveloppe exponentielle décroissante
        env = np.exp(-np.linspace(0, 5, samples))
        wave *= env
        wave = (wave * volume * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo)
    
    def _generate_engine_sound(self, base_freq, volume, distortion=False):
        """Génère un son de moteur avec modulation."""
        sample_rate = 44100
        duration = 0.5  # Loop
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Moteur = sine + harmoniques avec LFO
        wave = np.sin(2 * np.pi * base_freq * t)
        wave += 0.3 * np.sin(2 * np.pi * base_freq * 2 * t)
        wave += 0.1 * np.sin(2 * np.pi * (base_freq + 10) * t)  # Battement
        
        if distortion:
            wave = np.tanh(wave * 2)  # Distorsion douce
            
        wave = (wave * volume * 32767 / max(abs(wave)) * 0.5).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo)
    
    def _generate_arpeggio(self, freqs, duration):
        """Génère une séquence de notes."""
        sample_rate = 44100
        note_duration = duration / len(freqs)
        all_samples = []
        
        for freq in freqs:
            samples = int(sample_rate * note_duration)
            t = np.linspace(0, note_duration, samples, False)
            wave = np.sin(2 * np.pi * freq * t)
            # Enveloppe ADSR simple
            attack = int(0.01 * samples)
            decay = int(0.1 * samples)
            release = int(0.1 * samples)
            sustain = samples - attack - decay - release
            env = np.concatenate([
                np.linspace(0, 1, attack),
                np.linspace(1, 0.7, decay),
                np.full(sustain, 0.7),
                np.linspace(0.7, 0, release)
            ])
            wave *= env
            wave = (wave * 0.5 * 32767).astype(np.int16)
            all_samples.extend(wave)
            
        stereo = np.column_stack((np.array(all_samples), np.array(all_samples)))
        return pygame.sndarray.make_sound(stereo)
    
    # ----------------------------------------------------------
    # Contrôles publics
    # ----------------------------------------------------------
    
    def play(self, sound_name, loops=0, fade_ms=0):
        """Joue un effet sonore."""
        if not self.enabled or not self.sfx_enabled:
            return
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(self.volume_master * self.volume_sfx)
            self.sounds[sound_name].play(loops=loops, fade_ms=fade_ms)
            
    def play_engine(self, speed_ratio, nitro_active=False):
        """Joue le son du moteur adapté à la vitesse."""
        if not self.enabled or not self.sfx_enabled:
            return
            
        # Sélectionne le bon son selon la vitesse
        if nitro_active:
            snd = self.sounds.get('engine_nitro')
            vol = 0.8
        elif speed_ratio > 0.7:
            snd = self.sounds.get('engine_rev')
            vol = 0.5 + speed_ratio * 0.3
        else:
            snd = self.sounds.get('engine_idle')
            vol = 0.3 + speed_ratio * 0.3
            
        if snd:
            snd.set_volume(self.volume_master * self.volume_sfx * vol)
            if pygame.mixer.get_busy() < 4:  # Limite les channels
                snd.play(loops=0)
    
    def stop_engine(self):
        """Arrête les sons de moteur."""
        for name in ['engine_idle', 'engine_rev', 'engine_nitro']:
            if name in self.sounds:
                self.sounds[name].stop()
    
    def play_music(self, track_name):
        """Joue une musique de fond (procédurale)."""
        if not self.enabled or not self.music_enabled:
            return
            
        # Génère une musique simple si demandée
        if track_name == 'menu':
            self._play_procedural_music('ambient')
        elif track_name == 'race':
            self._play_procedural_music('upbeat')
        elif track_name == 'boss':
            self._play_procedural_music('intense')
            
    def _play_procedural_music(self, style='ambient'):
        """Génère et joue une musique procédurale simple."""
        # Simplifié: utilise des boucles de sons générés
        base_freqs = {
            'ambient': [220, 277, 330, 440],
            'upbeat': [262, 330, 392, 523],
            'intense': [110, 165, 220, 277]
        }
        
        freqs = base_freqs.get(style, base_freqs['ambient'])
        # Crée une progression simple
        duration = 4.0
        music = self._generate_arpeggio(freqs * 2, duration)
        music.set_volume(self.volume_master * self.volume_music * 0.3)
        
        if self.music_channel:
            self.music_channel.stop()
        self.music_channel = music.play(loops=-1)
        
    def stop_music(self):
        """Arrête la musique."""
        if self.music_channel:
            self.music_channel.stop()
            
    def set_master_volume(self, vol):
        self.volume_master = max(0.0, min(1.0, vol))
        pygame.mixer.set_volume(self.volume_master)
        
    def set_music_volume(self, vol):
        self.volume_music = max(0.0, min(1.0, vol))
        
    def set_sfx_volume(self, vol):
        self.volume_sfx = max(0.0, min(1.0, vol))
        
    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()
        return self.enabled
