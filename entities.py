import pygame
import random
from pathlib import Path

from settings import GRAVITY, JUMP_FORCE, SPACE_JUMP_FORCE
from animador import cargar_spritesheet

BASE_DIR = Path(__file__).parent
IMAGENES_DIR = BASE_DIR / 'assets'


class BackgroundTree:
    def __init__(self, x, y, height, screen_width, screen_height, sprite=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = self._load_or_create_image(height, sprite)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = max(115, min(y + 150, screen_height - self.rect.height - 20))
        self.hitbox = self.rect.copy()
        self.is_waiting = False
        self.wait_frames = 0
        self.reappear_delay_frames = 0

    def _load_or_create_image(self, height, sprite):
        if sprite is not None:
            try:
                image = pygame.image.load(sprite).convert_alpha()
                size = max(90, int(height * 0.8))
                return pygame.transform.smoothscale(image, (size, size))
            except Exception:
                pass

        size = max(90, int(height * 0.8))
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surface, (90, 60, 35), (0, 0, size, size))
        return surface

    def update(self, speed):
        if self.is_waiting:
            self.wait_frames += 1
            if self.wait_frames >= self.reappear_delay_frames:
                self.is_waiting = False
                self.wait_frames = 0
                self.rect.x = self.screen_width + 120
                self.rect.y = max(40, min(self.rect.y, self.screen_height - self.rect.height - 120))
                self.hitbox = self.rect.copy()
            return

        self.rect.x -= speed
        self.hitbox.x = self.rect.x
        self.hitbox.y = self.rect.y

        if self.rect.right < -80:
            self.is_waiting = True
            self.wait_frames = 0
            self.reappear_delay_frames = max(140, int(((self.screen_width + self.rect.width) / max(1.0, speed)) * 2))
            self.rect.x = self.screen_width + 1200
            self.hitbox = self.rect.copy()

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Player:
    def __init__(self, x, y, w, h, ground_y, frames_carrera=None, frames_salto=None):
        self.rect = pygame.Rect(x, ground_y - h, w, h)
        self.vy = 0
        self.ground_y = ground_y
        self.holding_jump = False
        self.fast_fall = False
        self.holding_down = False
        self.space_jumping = False
        self.last_space_jump_time = 0

        carrera_valida = frames_carrera or []
        salto_valido = frames_salto or []

        self.frames_carrera = [pygame.transform.smoothscale(img, (w, h)) for img in carrera_valida]
        self.frames_salto = [pygame.transform.smoothscale(img, (w, h)) for img in salto_valido]

        self.current_frame = 0
        self.animacion_timer = 0
        self.en_suelo_anterior = True

        if self.frames_carrera:
            self.image = self.frames_carrera[0]
        else:
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            self.image.fill((255, 0, 255))

    def jump(self):
        if self.rect.bottom >= self.ground_y and not self.space_jumping:
            self.vy = JUMP_FORCE
            self.holding_jump = True

    def keep_jump(self):
        if self.rect.bottom >= self.ground_y and not self.holding_jump:
            self.vy = JUMP_FORCE
            self.holding_jump = True

    def release_jump(self):
        self.holding_jump = False

    def start_space_jump(self):
        self.space_jumping = True
        self.last_space_jump_time = pygame.time.get_ticks()
        if self.rect.bottom >= self.ground_y:
            self.vy = SPACE_JUMP_FORCE
            self.holding_jump = True

    def stop_space_jump(self):
        self.space_jumping = False

    def start_fast_fall(self):
        if not self.space_jumping:
            self.fast_fall = True
            self.holding_down = True

    def stop_fast_fall(self):
        self.fast_fall = False
        self.holding_down = False

    def update(self, game_speed=1.0):
        if self.fast_fall and self.rect.bottom < self.ground_y:
            self.vy += GRAVITY * 3
        else:
            self.vy += GRAVITY
        self.rect.y += self.vy
        self.update_animacion(saltando=self.rect.bottom < self.ground_y, game_speed=game_speed)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vy = 0

    def update_animacion(self, saltando=False, game_speed=1.0):
        frames_actuales = self.frames_salto if saltando else self.frames_carrera
        if not frames_actuales:
            return

        if saltando != self.en_suelo_anterior:
            self.current_frame = 0
            self.animacion_timer = 0
            self.en_suelo_anterior = saltando

        frame_rate = max(2, int(6 - min(3.5, max(0.0, game_speed - 9.2) * 0.3)))
        self.animacion_timer += 1
        if saltando:
            if self.animacion_timer >= frame_rate:
                if self.current_frame < len(frames_actuales) - 1:
                    self.current_frame += 1
                self.animacion_timer = 0
        else:
            if self.animacion_timer >= frame_rate:
                self.current_frame = (self.current_frame + 1) % len(frames_actuales)
                self.animacion_timer = 0

        self.image = frames_actuales[self.current_frame]

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)


class Obstacle:
    def __init__(self, x, y, w, h):
        self.image = self._load_obstacle_image(w, h)
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)
        # Hitbox reducida: la imagen puede ser más ancha visualmente,
        # así que mantenemos una caja de colisión más ajustada al centro.
        # Reducimos más el ancho para que la columna de colisión quede delgada.
        w_reduc = max(0, int(self.rect.width * 0.45))
        h_reduc = max(0, int(self.rect.height * 0.10))
        self.hitbox = self.rect.inflate(-w_reduc, -h_reduc)
        # Alineamos la hitbox un poco a la derecha de la imagen.
        self.hitbox.left = self.rect.left + 6
        self.hitbox.bottom = self.rect.bottom
        self.image_offset_x = 6
        self.hitbox_offset_x = 6

    def _load_obstacle_image(self, w, h):
        candidates = [
            IMAGENES_DIR / 'Valla.png',
            IMAGENES_DIR / 'Valla.jpg',
            IMAGENES_DIR / 'valla.png',
            IMAGENES_DIR / 'valla.jpg',
            BASE_DIR / 'Valla.png',
            BASE_DIR / 'Valla.jpg',
        ]

        for ruta in candidates:
            if not ruta.exists():
                continue
            try:
                imagen_bruta = pygame.image.load(str(ruta)).convert_alpha()
                caja_visible = imagen_bruta.get_bounding_rect()
                if caja_visible.width <= 0 or caja_visible.height <= 0:
                    continue

                imagen_limpia = imagen_bruta.subsurface(caja_visible)
                proporcion = imagen_limpia.get_width() / max(1, imagen_limpia.get_height())
                ancho_visible = max(24, int(h * proporcion))
                return pygame.transform.smoothscale(imagen_limpia, (ancho_visible, h))
            except Exception:
                continue

        ancho_visible = max(24, int(w * 0.7))
        surface = pygame.Surface((ancho_visible, h), pygame.SRCALPHA)
        surface.fill((180, 50, 50))
        pygame.draw.rect(surface, (255, 255, 255), (4, 4, ancho_visible - 8, h - 8), 2)
        for i in range(3):
            line_y = 8 + i * (h - 16) // 2
            pygame.draw.line(surface, (220, 220, 220), (8, line_y), (ancho_visible - 8, line_y), 2)
        return surface

    def update(self, speed):
        self.rect.x -= speed
        # Mantener la hitbox sincronizada con la posición visual
        if hasattr(self, "hitbox"):
            self.hitbox.x = self.rect.x + (self.rect.width - self.hitbox.width) // 2 + self.hitbox_offset_x
            self.hitbox.y = self.rect.y + (self.rect.height - self.hitbox.height) // 2

    def draw(self, screen):
        screen.blit(self.image, (self.rect.x - self.image_offset_x, self.rect.y))


class DiagonalObstacle(Obstacle):
    def __init__(self, x, w, h, ground_y, speed_x=7, speed_y=4):
        self.base_speed_x = speed_x
        self.base_speed_y = speed_y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.ground_y = ground_y

        try:
            ruta_pelota = IMAGENES_DIR / 'pelota.png'
            self.frames = cargar_spritesheet(str(ruta_pelota), 4, escala=(w, h))
            if not self.frames:
                raise ValueError('No frames loaded')
        except Exception:
            self.frames = []

        if self.frames:
            self.current_frame = 0
            self.anim_timer = 0
            self.image = self.frames[0]
        else:
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (255, 255, 255), self.image.get_rect())
            self.current_frame = 0
            self.anim_timer = 0

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, 0)
        w_reduc = max(0, int(self.rect.width * 0.25))
        h_reduc = max(0, int(self.rect.height * 0.15))
        self.hitbox = self.rect.inflate(-w_reduc, -h_reduc)
        self.hitbox.bottomleft = self.rect.bottomleft

    def update(self, speed=None):
        horizontal_speed = self.speed_x if speed is None else max(self.base_speed_x + 1.0, speed * 1.2)
        vertical_speed = self.speed_y if speed is None else max(self.base_speed_y + 1.4, self.base_speed_y + speed * 0.2)

        self.rect.x -= horizontal_speed
        if hasattr(self, 'hitbox'):
            self.hitbox.x = self.rect.x + (self.rect.width - self.hitbox.width) // 2
            self.hitbox.y = self.rect.y + (self.rect.height - self.hitbox.height) // 2

        if self.rect.bottom < self.ground_y:
            self.rect.y += vertical_speed
            if self.rect.bottom > self.ground_y:
                self.rect.bottom = self.ground_y
        else:
            self.rect.bottom = self.ground_y

        if self.frames:
            frame_rate = max(2, int(6 - min(3.5, max(0.0, (speed or 9.2) - 9.2) * 0.3)))
            self.anim_timer += 1
            if self.anim_timer >= frame_rate:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]

    def draw(self, screen):
        if hasattr(self, 'image') and self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, (180, 0, 0), self.rect)


class ObstaclePoolManager:
    def __init__(self, ground_y, types):
        self.ground_y = ground_y
        self.types = types
        self.pool = [Obstacle(0, 10, 10, ground_y) for _ in range(6)]
        self.active = []
        self.last_spawned_gap = None
        self.last_spawned_positions = []

    def spawn_pair(self, start_x, gap_variants):
        dist = random.choice(gap_variants)
        current_x = start_x
        self.last_spawned_gap = dist
        self.last_spawned_positions = []
        for _ in range(2):
            w, h = random.choice(self.types)
            obs = Obstacle(current_x, self.ground_y, w, h)
            self.active.append(obs)
            self.last_spawned_positions.append(current_x)
            current_x += w + dist

    def update(self, speed):
        for obs in self.active:
            obs.update(speed)
        for i in range(len(self.active) - 1, -1, -1):
            if self.active[i].rect.right < 0:
                self.pool.append(self.active.pop(i))

    def draw(self, screen):
        for obs in self.active:
            obs.draw(screen)

    def check_collision(self, player_rect):
        for o in self.active:
            target = getattr(o, "hitbox", o.rect)
            if player_rect.colliderect(target):
                return True
        return False
