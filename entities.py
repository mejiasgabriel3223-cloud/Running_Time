# entities.py
import pygame
import random
from settings import GRAVITY, JUMP_FORCE, SPACE_JUMP_FORCE

class Player:
    def __init__(self, x, y, w, h, ground_y, frames_carrera=None, frames_salto=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.vy = 0
        self.ground_y = ground_y
        self.holding_jump = False
        self.fast_fall = False
        self.holding_down = False
        self.space_jumping = False
        self.last_space_jump_time = 0

        # ANIMACIONES SEPARADAS 
        self.frames_carrera = frames_carrera or []
        self.frames_salto = frames_salto or []
        self.frame_actual = 0
        self.timer_animacion = 0
        self.velocidad_animacion = 100
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
        gravity = GRAVITY * 2.0 if self.fast_fall and self.vy >= 0 else GRAVITY

        if self.vy < 0 and self.holding_jump:
            self.vy += gravity * 0.5
        else:
            self.vy += gravity

        if self.fast_fall and self.rect.bottom < self.ground_y:
            if self.vy < 0:
                self.vy -= 0.7
            else:
                self.vy += GRAVITY * 0.8

        if self.space_jumping and self.rect.bottom >= self.ground_y:
            now = pygame.time.get_ticks()
            if now - self.last_space_jump_time >= 140:
                self.vy = SPACE_JUMP_FORCE
                self.holding_jump = True
                self.last_space_jump_time = now
            
        self.rect.y += self.vy
        
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vy = 0
            self.holding_jump = False

    def draw(self, screen):
        pygame.draw.rect(screen, (40, 40, 40), self.rect)


class Obstacle:
    def __init__(self, x, w, h, ground_y):
        self.rect = pygame.Rect(x, ground_y - h, w, h)

    def update(self, speed):
        self.rect.x -= speed

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 180, 0), self.rect)


class DiagonalObstacle(Obstacle):
    def __init__(self, x, w, h, ground_y, speed_x=10, speed_y=4):
        self.rect = pygame.Rect(x, 0, w, h)
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.ground_y = ground_y

    def update(self):

        gravity = GRAVITY * 2.0 if self.fast_fall and self.vy >= 0 else GRAVITY

        if self.vy < 0 and self.holding_jump:
            self.vy += gravity * 0.5
        else:
            self.vy += gravity

        if self.fast_fall and self.rect.bottom < self.ground_y:
            if self.vy < 0:
                self.vy -= 0.7
            else:
                self.vy += GRAVITY * 0.8

        if self.space_jumping and self.rect.bottom >= self.ground_y:
            now = pygame.time.get_ticks()
            if now - self.last_space_jump_time >= 140:
                self.vy = SPACE_JUMP_FORCE
                self.holding_jump = True
                self.last_space_jump_time = now
            
        self.rect.y += self.vy
        
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vy = 0
            self.holding_jump = False

        #Lógica de Animación 
        if self.frames:
            now = pygame.time.get_ticks()
            if now - self.timer_animacion > self.velocidad_animacion:
                self.timer_animacion = now
                # Actualizamos el frame de la carrera solo si está tocando el suelo
                if self.rect.bottom >= self.ground_y:
                    self.frame_actual = (self.frame_actual + 1) % len(self.frames)

    def draw(self, screen):
        if self.frames:
            # Si el jugador está en el aire (saltando), forzamos un frame específico
            if self.rect.bottom < self.ground_y:
                imagen_a_dibujar = self.frames[0] # Puedes cambiar el índice para tu sprite de salto
            else:
                imagen_a_dibujar = self.frames[self.frame_actual]
            
            # Dibujamos el sprite en las coordenadas del rectángulo de colisión
            screen.blit(imagen_a_dibujar, self.rect)
        else:
            # Fallback a tu rectángulo original[cite: 2]
            pygame.draw.rect(screen, (40, 40, 40), self.rect)

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
            if self.pool:
                obs = self.pool.pop()
                obs.rect = pygame.Rect(current_x, self.ground_y - h, w, h)
            else:
                obs = Obstacle(current_x, w, h, self.ground_y)
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
        return any(player_rect.colliderect(o.rect) for o in self.active)