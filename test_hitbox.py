import pygame
from entities import Obstacle
from settings import load_game_font, _find_project_font_path, FONT_SCALE

pygame.init()
obs = Obstacle(200, 600, 32, 64)
print('rect size', obs.rect.size, 'hitbox size', getattr(obs,'hitbox').size)
print('hitbox tl', obs.hitbox.topleft, 'rect tl', obs.rect.topleft)
print('font path', _find_project_font_path())
font = load_game_font(32)
print('FONT_SCALE=', FONT_SCALE)
print('font object:', font)
print('done')
