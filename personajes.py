import pygame

class Personaje:
    def __init__(self, name, icon_path, run_paths, jump_paths, width=50, height=75):
        self.name = name
        self.width = width
        self.height = height
        

        self.icon = pygame.image.load(icon_path).convert_alpha()
        self.frames_carrera = [pygame.image.load(p).convert_alpha() for p in run_paths]
        self.frames_salto = [pygame.image.load(p).convert_alpha() for p in jump_paths]