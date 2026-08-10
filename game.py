# game.py 
import json
import pygame
import random
from pathlib import Path
from settings import S_WIDTH, S_HEIGHT
from entities import Player, DiagonalObstacle, ObstaclePoolManager, BackgroundTree
from personajes import Personaje
from selector_de_personajes import CharacterSelector
from animador import Animador

BASE_DIR = Path(__file__).parent
IMAGENES_DIR = BASE_DIR / "assets"

class CarreraDeObstaculos:
    def __init__(self, screen):
        self.screen = screen
        self.S_WIDTH = S_WIDTH
        self.S_HEIGHT = S_HEIGHT
        from settings import load_game_font
        self.font = load_game_font(24)
        self.frenzy_alert_font = load_game_font(48, bold=True)
        self.player_name = "Jugador"
        self.sound_player = None

        self.base_dir = Path(__file__).parent
        self.imagenes_dir = self.base_dir / "assets"
        self.personajes_disponibles = [
            Personaje("Finn", str(self.imagenes_dir / "fin_quieto.png"), str(self.imagenes_dir / "fin_corriendo.png"), 10, str(self.imagenes_dir / "fin_saltando.png"), 9),
            Personaje("Jake", str(self.imagenes_dir / "jake_quieto.png"), str(self.imagenes_dir / "jake_corriendo.png"), 8, str(self.imagenes_dir / "jake_saltando.png"), 10),
            Personaje("Gunther", str(self.imagenes_dir / "gunter_quieto.png"), str(self.imagenes_dir / "gunter_corriendo.png"), 8, str(self.imagenes_dir / "gunter_saltando.png"), 7)
        ]

        self.selector = CharacterSelector(self.personajes_disponibles, self.S_WIDTH, self.S_HEIGHT)
        self.personaje_actual = self.personajes_disponibles[0]
        self.reset_game()

    def reset_game(self):
        player_scale = 1.4  # tamaño perfecto del jugador
        obstacle_scale = 2.0  # 100% más grande para obstáculos terrestres
        self.ground_y = self.S_HEIGHT - 120
        self.player = Player(80, 0, 60, 85, self.ground_y, None, None)
        self.gap_variants = [140, 220, 300, 380, 460]
        self.player_name = getattr(self, "player_name", "Jugador")
        
        self.obstacle_types = [
            (int(24 * obstacle_scale), int(45 * obstacle_scale)),
            (int(28 * obstacle_scale), int(52 * obstacle_scale)),
        ]
        self.obstacle_manager = ObstaclePoolManager(self.ground_y, self.obstacle_types)
        self.obstacle_manager.spawn_pair(self.S_WIDTH + 260, self.gap_variants)
        ruta_fondo = self.base_dir / "assets" / "Fondo pista.jpeg"
        self.fondo = pygame.image.load(str(ruta_fondo)).convert()
        self.fondo = pygame.transform.scale(self.fondo, (self.S_WIDTH, self.S_HEIGHT))
        self.bg_offset = 0.0

        self.diagonal_obstacle = None
        self.next_diagonal_trigger = 180
        self.base_speed = 9.2
        self.speed = self.base_speed
        self.score = 0
        self.record_summary = None
        
        self.boost_active = False
        self.boost_multiplier = 1.0
        self.next_boost_trigger = 300
        self.boost_duration_points = 150
        self.boost_end_score = 0
        self.frenzy_alert_timer = 0.0
        self.frenzy_alert_active = False
        
        self.last_fps_time = pygame.time.get_ticks()
        self.frames_count = 0
        self.current_fps = 0
      
        scale_factor = 1.4  # 40% más grande
        target_height = int(126 * scale_factor)  # 126 * 1.4 = 176
        base_width = int(68 * scale_factor)

        personaje = self.personaje_actual

        def escalar_frame(frame):
            if frame is None:
                return None
            aspect_ratio = frame.get_width() / frame.get_height()
            scaled_height = target_height
            scaled_width = int(scaled_height * aspect_ratio)
            return pygame.transform.smoothscale(frame, (scaled_width, scaled_height))

        frames_correr = [escalar_frame(img) for img in personaje.frames_carrera]
        frames_saltar = [escalar_frame(img) for img in personaje.frames_salto]

        if not frames_correr:
            frames_correr = [pygame.Surface((base_width, target_height), pygame.SRCALPHA)]
        if not frames_saltar:
            frames_saltar = [pygame.Surface((base_width, target_height), pygame.SRCALPHA)]

        target_width = max(frame.get_width() for frame in frames_correr + frames_saltar)
        for index, frame in enumerate(frames_correr):
            frames_correr[index] = pygame.transform.smoothscale(frame, (target_width, target_height))
        for index, frame in enumerate(frames_saltar):
            frames_saltar[index] = pygame.transform.smoothscale(frame, (target_width, target_height))

        ancho_hitbox = int(target_height * 0.55)  # 55% del alto de la animación
        offset_x = 70 + max(0, (target_width - ancho_hitbox) // 2)
        
        self.player = Player(
            offset_x,
            self.ground_y - target_height,
            ancho_hitbox, target_height, self.ground_y,
            frames_carrera=frames_correr,
            frames_salto=frames_saltar
        )

        self.background_tree = BackgroundTree(
            self.S_WIDTH + 140,
            24,
            target_height + 40,
            self.S_WIDTH,
            self.S_HEIGHT,
            sprite=str(IMAGENES_DIR / "decor_sprite.png")
        )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "MENU"
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_w:
                if not self.player.space_jumping and not self.player.fast_fall:
                    self.player.jump()
            if event.type == pygame.KEYUP and event.key == pygame.K_w:
                self.player.release_jump()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not self.player.fast_fall:
                    self.player.stop_space_jump()
                    self.player.start_space_jump()
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                self.player.stop_space_jump()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                if not self.player.space_jumping and not self.player.holding_jump:
                    self.player.start_fast_fall()
            if event.type == pygame.KEYUP and event.key == pygame.K_s:
                self.player.stop_fast_fall()
        return None

    def _restart_frenzy_music(self):
        """Método protegido para reiniciar o mantener la música sin que el juego colapse"""
        if self.sound_player is None:
            return
        try:
            track = getattr(self.sound_player, "current_game_track", 0)
            if track is None:
                track = 0
            if hasattr(self.sound_player, "play_game_music"):
                self.sound_player.play_game_music(track)
        except Exception:
            pass

    def update_speed(self, dt):
        score_points = self.score // 10
        self.speed = self.base_speed + min(4.4, score_points * 0.03)

        if self.boost_active:
            self.speed = self.base_speed + min(4.4, score_points * 0.03) + 0.8
            self.frenzy_alert_timer += dt
            if score_points >= self.boost_end_score:
                self.boost_active = False
                self.boost_end_score = 0
                self.frenzy_alert_active = False
                self._restart_frenzy_music()
        elif score_points >= self.next_boost_trigger:
            self.boost_active = True
            self.boost_end_score = score_points + self.boost_duration_points
            self.next_boost_trigger += 300
            self.frenzy_alert_active = True
            self.frenzy_alert_timer = 0.0
            self._restart_frenzy_music()

    def _can_spawn_diagonal_obstacle(self):
        player_window_left = self.player.rect.right + 40
        player_window_right = self.player.rect.right + 320

        for obs in self.obstacle_manager.active:
            if obs.rect.right >= player_window_left and obs.rect.left <= player_window_right:
                return False

        spawn_x = self.S_WIDTH + 280
        for obs in self.obstacle_manager.active:
            if obs.rect.right >= spawn_x - 120 and obs.rect.left <= spawn_x + 120:
                return False

        return True

    def _get_record_summary(self, score_value):
        clean_name = (self.player_name or "Jugador").strip() or "Jugador"
        records_file = self.base_dir / "records.json"
        records = []

        if records_file.exists():
            try:
               with open(records_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    if isinstance(data, list):
                        records = data
            except (json.JSONDecodeError, OSError):
                records = []

        matching_records = [entry for entry in records if str(entry.get("name", "")).lower() == clean_name.lower()]
        best_score = max((entry.get("score", 0) for entry in matching_records), default=0)

        return {
            "player_name": clean_name,
            "score": score_value,
            "best_score": best_score,
            "is_new_record": score_value > best_score,
        }

    def _update_record_summary(self):
        self.record_summary = self._get_record_summary(self.score // 10)

    def update(self, dt):
        self.frames_count += 1
        curr = pygame.time.get_ticks()
        if curr - self.last_fps_time >= 1000:
            self.current_fps = self.frames_count
            self.frames_count = 0
            self.last_fps_time = curr

        self.update_speed(dt)
        self.bg_offset = (self.bg_offset + self.speed) % self.S_WIDTH
        self.background_tree.update(self.speed)
        self.player.update(game_speed=self.speed)
        self.obstacle_manager.update(self.speed)
        
        if self.obstacle_manager.check_collision(self.player.rect):
            self._update_record_summary()
            return "GAMEOVER"

        if (self.score // 10) >= self.next_diagonal_trigger and not self.diagonal_obstacle:
            if self._can_spawn_diagonal_obstacle():
                spawn_x = self.S_WIDTH + 280
                self.diagonal_obstacle = DiagonalObstacle(spawn_x, 30, 30, self.ground_y)
                self.next_diagonal_trigger += 50 if self.boost_active else 100

        if self.diagonal_obstacle:
            self.diagonal_obstacle.update(self.speed)

        if not self.obstacle_manager.active:
            self.obstacle_manager.spawn_pair(self.S_WIDTH + random.randint(180, 320), self.gap_variants)

        self.score += 1
        return None

    def draw(self):
        offset = int(self.bg_offset)
        self.screen.blit(self.fondo, (-offset, 0))
        if offset > 0:
            self.screen.blit(self.fondo, (self.S_WIDTH - offset, 0))
        self.background_tree.draw(self.screen)
        self.player.draw(self.screen)
        self.obstacle_manager.draw(self.screen)
        
        if self.diagonal_obstacle:
            self.diagonal_obstacle.draw(self.screen)
        
        pygame.draw.line(self.screen, (120, 120, 120), (0, self.ground_y), (self.S_WIDTH, self.ground_y), 2)
        
        score_text = self.font.render(f"Score: {self.score // 10}", True, (0, 0, 0))
        self.screen.blit(score_text, (20, 20))

        boost_state = "Modo Frenesi: ON" if self.boost_active else "Modo Frenesi: OFF"
        boost_text = self.font.render(boost_state, True, (220, 90, 0) if self.boost_active else (100, 100, 100))
        self.screen.blit(boost_text, (20, 56))

        if self.frenzy_alert_active:
            elapsed = self.frenzy_alert_timer
            if elapsed < 0.25:
                scale = 0.8 + elapsed / 0.25 * 1.4
            else:
                scale = 2.2 - (elapsed / 0.7) * 1.5
            scale = max(0.2, min(scale, 2.2))
            text_surface = self.frenzy_alert_font.render("MODO FRENESI", True, (220, 0, 0))
            rect = text_surface.get_rect(center=(self.S_WIDTH // 2, self.S_HEIGHT // 2 - 40))
            scaled_surface = pygame.transform.scale_by(text_surface, scale)
            scaled_rect = scaled_surface.get_rect(center=rect.center)
            self.screen.blit(scaled_surface, scaled_rect)
        
        fps_text = self.font.render(f"FPS: {self.current_fps}", True, (0, 0, 180))
        self.screen.blit(fps_text, (self.S_WIDTH - 140, 20))

    def draw_gameover(self):
        overlay = pygame.Surface((self.S_WIDTH, self.S_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont("consolas", 60, bold=True)
        text_font = pygame.font.SysFont("consolas", 28)

        record_status = self.record_summary or self._get_record_summary(self.score // 10)
        title_surface = title_font.render("GAME OVER", True, (255, 255, 255))
        score_surface = text_font.render(f"Puntaje: {self.score // 10}", True, (255, 255, 255))
        personal_record_surface = text_font.render(f"Record personal: {record_status['best_score']}", True, (255, 255, 255))
        comparison_surface = text_font.render(
            "Nuevo record!" if record_status["is_new_record"] else "No superaste tu record",
            True,
            (255, 220, 100) if record_status["is_new_record"] else (220, 220, 220),
        )
        retry_surface = text_font.render("Presiona Enter para reiniciar", True, (220, 220, 220))
        menu_surface = text_font.render("Presiona ESC para volver al menú", True, (220, 220, 220))

        self.screen.blit(title_surface, title_surface.get_rect(center=(self.S_WIDTH // 2, 220)))
        self.screen.blit(score_surface, score_surface.get_rect(center=(self.S_WIDTH // 2, 290)))
        self.screen.blit(personal_record_surface, personal_record_surface.get_rect(center=(self.S_WIDTH // 2, 335)))
        self.screen.blit(comparison_surface, comparison_surface.get_rect(center=(self.S_WIDTH // 2, 375)))
        self.screen.blit(retry_surface, retry_surface.get_rect(center=(self.S_WIDTH // 2, 430)))
        self.screen.blit(menu_surface, menu_surface.get_rect(center=(self.S_WIDTH // 2, 480)))