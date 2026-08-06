import pygame

def recortar_sprite_sheet(sheet, ancho_frame, alto_frame, columnas, escala_w=None, escala_h=None):
    frames = []
    for i in range(columnas):
        # Recorta el frame original 
        rect = pygame.Rect(i * ancho_frame, 0, ancho_frame, alto_frame)
        frame = sheet.subsurface(rect).copy()
        
        # Si le pasamos un tamaño para escalar, lo encoge suavemente
        if escala_w is not None and escala_h is not None:
            frame = pygame.transform.smoothscale(frame, (escala_w, escala_h))
            
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

   
def cargar_spritesheet(ruta, cantidad_frames, escala=None):
    try:
        sheet = pygame.image.load(ruta).convert_alpha()
        frames = []
        
        # El código calcula el tamaño automáticamente dividiendo el ancho total entre los frames
        ancho_frame = sheet.get_width() // cantidad_frames
        alto_frame = sheet.get_height()
        
        for i in range(cantidad_frames):
            frame = sheet.subsurface((i * ancho_frame, 0, ancho_frame, alto_frame)).copy()
            crop_rect = frame.get_bounding_rect()
            if crop_rect.width and crop_rect.height:
                frame = frame.subsurface(crop_rect).copy()
            if escala:
                escala_w, escala_h = escala
                if escala_w is None and escala_h is not None:
                    escala_w = int(frame.get_width() * (escala_h / frame.get_height()))
                elif escala_h is None and escala_w is not None:
                    escala_h = int(frame.get_height() * (escala_w / frame.get_width()))
                frame = pygame.transform.smoothscale(frame, (escala_w, escala_h))
            frames.append(frame)
        return frames
    except Exception as e:
        print(f"Error cargando sprite {ruta}: {e}")
        return []
