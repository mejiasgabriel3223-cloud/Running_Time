import pygame
import random
from settings import GRAVITY, JUMP_FORCE, SPACE_JUMP_FORCE
from animador import cargar_spritesheet

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
        
        carrera_valida = frames_carrera if (frames_carrera and frames_carrera is not ...) else []
        salto_valido = frames_salto if (frames_salto and frames_salto is not ...) else []

        # Escalamos los frames al tamaño exacto w y h
        self.frames_carrera = [pygame.transform.smoothscale(img, (w, h)) for img in carrera_valida]
        self.frames_salto = [pygame.transform.smoothscale(img, (w, h)) for img in salto_valido]
        
        self.current_frame = 0
        self.animacion_timer = 0
        self.en_suelo_anterior = True
        
        if self.frames_carrera:
            self.image = self.frames_carrera[0]
        else:
            # Cuadro rosado de respaldo por si acaso falta algún frame
            self.image = pygame.Surface((w, h))
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
        try:
            # 1. Cargamos la imagen y recortamos el espacio transparente
            imagen_bruta = pygame.image.load("Valla.png").convert_alpha()
            caja_visible = imagen_bruta.get_bounding_rect()
            imagen_limpia = imagen_bruta.subsurface(caja_visible)
            
            # 2. Usamos EXACTAMENTE la altura 'h' que le pases, sin mínimos forzados
            proporcion = imagen_limpia.get_width() / imagen_limpia.get_height()
            ancho_visible = int(h * proporcion)
            
            # 3. Escalamos la valla
            self.image = pygame.transform.smoothscale(imagen_limpia, (ancho_visible, h))
            
            # 4. Creamos el rect para dibujar y una hitbox delgada centrada en el eje vertical de la valla
            self.rect = self.image.get_rect()
            self.rect.bottomleft = (x, y)
            hitbox_width = max(4, int(self.rect.width * 0.2))
            self.hitbox = pygame.Rect(0, 0, hitbox_width, h)
            self.hitbox.midbottom = self.rect.midbottom
            
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.image = pygame.Surface((w, h))
            self.image.fill((255, 0, 0))
            self.rect = self.image.get_rect()
            self.rect.bottomleft = (x, y)
            self.hitbox = pygame.Rect(0, 0, max(4, int(w * 0.2)), h)
            self.hitbox.midbottom = self.rect.midbottom

    def update(self, speed):
        self.rect.x -= speed
        if hasattr(self, 'hitbox'):
            self.hitbox.x = self.rect.x + (self.rect.width - self.hitbox.width) // 2
            self.hitbox.y = self.rect.y

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 1)
        else:
            pygame.draw.rect(screen, (0, 200, 0), self.rect)
class DiagonalObstacle(Obstacle):
    def __init__(self, x, w, h, ground_y, speed_x=7, speed_y=4):
        self.base_speed_x = speed_x
        self.base_speed_y = speed_y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.ground_y = ground_y

        try:
            self.frames = cargar_spritesheet("pelota.png", 4, escala=(w, h))
            if not self.frames:
                raise ValueError("No frames loaded")
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

    def update(self, speed=None):
        horizontal_speed = self.speed_x if speed is None else max(self.base_speed_x + 1.0, speed * 1.2)
        vertical_speed = self.speed_y if speed is None else max(self.base_speed_y + 1.4, self.base_speed_y + speed * 0.2)

        self.rect.x -= horizontal_speed
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
        if hasattr(self, "image") and self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, (180, 0, 0), self.rect)


class ObstaclePoolManager:
    """Gestiona la memoria y la aleatoriedad de los obstáculos"""
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
        return any(player_rect.colliderect(o.hitbox) for o in self.active)