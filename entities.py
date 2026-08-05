import pygame
import random
from settings import GRAVITY, JUMP_FORCE, SPACE_JUMP_FORCE

class Player:
    def __init__(self, x, y, w, h, ground_y, frames_carrera=None, frames_salto=None):
        # Usamos exactamente el ancho (w) y alto (h) que le pasas desde game.py
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
        self.image = None
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

    def update(self):
        if self.fast_fall and self.rect.bottom < self.ground_y:
            self.vy += GRAVITY * 3
        else:
            self.vy += GRAVITY
        self.rect.y += self.vy
        self.update_animacion()
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vy = 0
    def update_animacion(self):
        en_el_suelo = self.rect.bottom >= self.ground_y

        # Si Finn acaba de despegar o de aterrizar, reiniciamos el contador de frames
        if not hasattr(self, "en_suelo_anterior"):
            self.en_suelo_anterior = True

        if en_el_suelo != self.en_suelo_anterior:
            self.current_frame = 0
            self.animacion_timer = 0
            self.en_suelo_anterior = en_el_suelo

        frames_actuales = self.frames_carrera if en_el_suelo else self.frames_salto

        if frames_actuales:
            self.animacion_timer += 1
            
            if en_el_suelo:
                if self.animacion_timer >= 6: # Sube este número si quieres que corra más lento
                    self.current_frame = (self.current_frame + 1) % len(frames_actuales)
                    self.animacion_timer = 0
            else:
                # Saltar: Avanza una sola vez y se congela en el último frame del salto
                if self.animacion_timer >= 6:
                    if self.current_frame < len(frames_actuales) - 1:
                        self.current_frame += 1
                    self.animacion_timer = 0

            self.image = frames_actuales[self.current_frame]

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, (40, 40, 40), self.rect)
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
    def __init__(self, x, w, h, ground_y, speed_x=7, speed_y=3):
        self.rect = pygame.Rect(x, 0, w, h)
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.ground_y = ground_y


    def update(self, speed=None):
        self.rect.x -= self.speed_x
        if self.rect.bottom < self.ground_y:
            self.rect.y += self.speed_y
            if self.rect.bottom > self.ground_y:
                self.rect.bottom = self.ground_y
        else:
            self.rect.bottom = self.ground_y


    def draw(self, screen):
        pygame.draw.rect(screen, (180, 0, 0), self.rect)


class ObstaclePoolManager:
    """Gestiona la memoria y la aleatoriedad de los obstáculos"""
    def __init__(self, ground_y, types):
        self.ground_y = ground_y
        self.types = types
        self.pool = [Obstacle(0, 10, 10, ground_y) for _ in range(6)]
        self.active = []

    def spawn_pair(self, start_x, gap_variants):
        dist = random.choice(gap_variants)
        current_x = start_x
        for _ in range(2):
            w, h = random.choice(self.types)
            obs = Obstacle(current_x, self.ground_y, w, h)
            self.active.append(obs)
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