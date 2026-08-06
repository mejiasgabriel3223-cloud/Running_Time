import pygame
from animador import cargar_spritesheet

class Personaje:
    # Le ponemos un tamaño por defecto manejable (60x80)
    def __init__(self, name, icon_path, run_sheet, run_count, jump_sheet, jump_count, width=60, height=80):
        self.name = name
        self.width = width
        self.height = height

        # El icono del selector se queda igual
        self.icon = pygame.image.load(icon_path).convert_alpha()

        # Cargamos las tiras completas de animación
        self.frames_carrera = cargar_spritesheet(run_sheet, run_count)
        self.frames_salto = cargar_spritesheet(jump_sheet, jump_count)

        if not self.frames_carrera:
            fallback = pygame.transform.scale(self.icon, (width, height))
            self.frames_carrera = [fallback]
        if not self.frames_salto:
            fallback = pygame.transform.scale(self.icon, (width, height))
            self.frames_salto = [fallback]