import pygame

import pygame

def recortar_sprite_sheet(sheet, ancho_frame, alto_frame, columnas, escala_w=None, escala_h=None):
    frames = []
    for i in range(columnas):
        # Recorta el frame original 
        rect = pygame.Rect(i * ancho_frame, 0, ancho_frame, alto_frame)
        frame = sheet.subsurface(rect).copy()
        
        # Si le pasamos un tamaño para escalar, lo encoge
        if escala_w is not None and escala_h is not None:
            frame = pygame.transform.scale(frame, (escala_w, escala_h))
            
        frames.append(frame)
    return frames

class Animador:
    def __init__(self, frames, velocidad):
        self.frames = frames
        self.velocidad = velocidad
        self.frame_actual = 0
        self.tiempo_acumulado = 0

    def actualizar(self):
        self.tiempo_acumulado += 1
        if self.tiempo_acumulado >= self.velocidad:
            self.tiempo_acumulado = 0
            self.frame_actual = (self.frame_actual + 1) % len(self.frames)

    def obtener_imagen_actual(self):
        return self.frames[self.frame_actual]