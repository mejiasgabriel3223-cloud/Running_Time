# game.py 
import pygame
import random
from settings import S_WIDTH, S_HEIGHT
from entities import Player, DiagonalObstacle, ObstaclePoolManager, BackgroundTree
from personajes import Personaje
from selector_de_personajes import CharacterSelector

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
        
        self.personajes_disponibles = [
            Personaje("Finn", "fin_quieto.png", "fin_corriendo.png", 10, "fin_saltando.png", 9),
            Personaje("Jake", "jake_quieto.png", "jake_corriendo.png", 8, "jake_saltando.png", 10),
            Personaje("Gunther", "gunter_quieto.png", "gunter_corriendo.png", 8, "gunter_saltando.png", 7)
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
        self.fondo = pygame.image.load("Fondo pista.jpeg").convert()
        self.fondo = pygame.transform.scale(self.fondo, (self.S_WIDTH, self.S_HEIGHT))
        self.bg_offset = 0.0

        self.diagonal_obstacle = None
        self.next_diagonal_trigger = 180
        self.base_speed = 9.2
        self.speed = self.base_speed
        self.score = 0
        
        self.boost_active = False
        self.boost_multiplier = 1.0
        self.next_boost_trigger = 300
        self.boost_duration_points = 150
        self.boost_end_score = 0
        self.challenge_mode = False
        self.frenzy_alert_timer = 0.0
        self.frenzy_alert_active = False
        
        self.last_fps_time = pygame.time.get_ticks()
        self.frames_count = 0
        self.current_fps = 0
      
        scale_factor = 1.4  # 40% más grande
        target_height = int(126 * scale_factor)  # 126 * 1.4 = 176

        personaje = self.personaje_actual
        base_width = int(68 * scale_factor)

        def escalar_frame(frame, width=None):
            if frame is None:
                return None
            if width is None:
                width = base_width
            aspect_ratio = frame.get_width() / frame.get_height()
            scaled_width = int(width)
            scaled_height = int(scaled_width / aspect_ratio)
            if scaled_height != target_height:
                scaled_height = target_height
                scaled_width = int(scaled_height * aspect_ratio)
            return pygame.transform.smoothscale(frame, (scaled_width, scaled_height))

        frames_correr = [escalar_frame(img, base_width) for img in personaje.frames_carrera]
        frames_saltar = [escalar_frame(img, base_width) for img in personaje.frames_salto]

        target_width = max(frame.get_width() for frame in frames_correr + frames_saltar) if frames_correr or frames_saltar else base_width
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
            sprite="decor_sprite.png"
        )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "MENU"
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.challenge_mode = not self.challenge_mode
                self.player.stop_space_jump()
                self.player.stop_fast_fall()
                self.player.release_jump()

            if not self.challenge_mode:
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

    def update(self, dt):
        self.frames_count += 1
        curr = pygame.time.get_ticks()
        if curr - self.last_fps_time >= 1000:
            self.current_fps = self.frames_count
            self.frames_count = 0
            self.last_fps_time = curr

        self.update_speed(dt)
        self.update_autoplay()
        self.bg_offset = (self.bg_offset + self.speed) % self.S_WIDTH
        self.background_tree.update(self.speed)
        self.player.update(game_speed=self.speed)
        self.obstacle_manager.update(self.speed)
        
        if self.obstacle_manager.check_collision(self.player.rect):
            return "MENU" 

        if (self.score // 10) >= self.next_diagonal_trigger and not self.diagonal_obstacle:
            if self._can_spawn_diagonal_obstacle():
                spawn_x = self.S_WIDTH + 280
                self.diagonal_obstacle = DiagonalObstacle(spawn_x, 30, 30, self.ground_y)
                self.next_diagonal_trigger += 50 if self.boost_active else 100

        if self.diagonal_obstacle:
            self.diagonal_obstacle.update(self.speed)
            if self.player.rect.colliderect(self.diagonal_obstacle.rect):
                return "MENU"
            if self.diagonal_obstacle.rect.right < 0:
                self.diagonal_obstacle = None

        if not self.obstacle_manager.active:
            self.obstacle_manager.spawn_pair(self.S_WIDTH + random.randint(180, 320), self.gap_variants)

        self.score += 1
        return None

    def update_autoplay(self):
        if not self.challenge_mode:
            return

        active_obs = [obs for obs in self.obstacle_manager.active if obs.rect.right > self.player.rect.left]
        if self.diagonal_obstacle and self.diagonal_obstacle.rect.right > self.player.rect.left:
            active_obs.append(self.diagonal_obstacle)
        
        active_obs.sort(key=lambda x: x.rect.left)

        if not active_obs:
            self.player.release_jump()
            if self.player.rect.bottom < self.ground_y:
                self.player.start_fast_fall()
            return

        first = active_obs[0]

        if isinstance(first, DiagonalObstacle):
            self.player.release_jump()
            if self.player.rect.bottom < self.ground_y:
                self.player.start_fast_fall()
            return

        # Detección de distancia corta entre obstáculos (~20 de separación)
        has_short_gap = False
        target_obs = first
        cluster_end_x = first.rect.right

        if len(active_obs) > 1 and not isinstance(active_obs[1], DiagonalObstacle):
            gap = active_obs[1].rect.left - first.rect.right
            if gap <= 35:
                has_short_gap = True
                target_obs = active_obs[1]  # Tomamos el SEGUNDO obstáculo como referencia
                cluster_end_x = active_obs[1].rect.right

        # Distancia al objetivo (al primero normalmente, o al segundo si hay distancia corta)
        dist_to_target = target_obs.rect.left - self.player.rect.right

        # Umbral: si hay espacio corto, salta antes (añadiendo la anticipación de 30)
        if has_short_gap:
            multiplier = 36 if self.boost_active else 32
            jump_threshold = (self.speed * multiplier) + 30
        else:
            multiplier = 30 if self.boost_active else 26
            jump_threshold = self.speed * multiplier

        should_jump = (0 < dist_to_target <= jump_threshold)

        if should_jump:
            self.player.stop_fast_fall()
            if self.player.rect.bottom >= self.ground_y:
                self.player.jump()
            else:
                self.player.holding_jump = True

        # Control de vuelo: mantiene el salto hasta rebasar por completo el último obstáculo del grupo
        if self.player.rect.bottom < self.ground_y:
            if self.player.rect.left < cluster_end_x + 10:
                self.player.holding_jump = True
            else:
                self.player.release_jump()
                self.player.start_fast_fall()
        else:
            self.player.release_jump()
            self.player.stop_fast_fall()

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

        challenge_state = "Modo Prueba: ON" if self.challenge_mode else "Modo Prueba: OFF"
        challenge_text = self.font.render(challenge_state, True, (0, 120, 220) if self.challenge_mode else (100, 100, 100))
        self.screen.blit(challenge_text, (20, 86))

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