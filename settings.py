# settings.py

import os
import pygame

# Resolución (Debe coincidir con la de tu launcher si quieres consistencia)
S_WIDTH = 1280
S_HEIGHT = 720
FPS = 60

# Física del juego
GRAVITY = 0.92
JUMP_FORCE = -23.0
SPACE_JUMP_FORCE = -20.5


def _find_project_font_path():
    root = os.path.dirname(__file__)
    font_dir = os.path.join(root, "Fuentes")
    default_font_name = "Adventure Time Logo.ttf"

    if os.path.isdir(font_dir):
        font_path = os.path.join(font_dir, default_font_name)
        if os.path.isfile(font_path):
            return font_path

    font_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.git', '.venv', '__pycache__', '.pytest_cache')]
        for filename in filenames:
            if filename.lower().endswith(('.ttf', '.otf')):
                font_files.append(os.path.join(dirpath, filename))

    if not font_files:
        return None

    for path in font_files:
        name = os.path.basename(path).lower()
        if 'adventure' in name or 'time' in name or 'logo' in name:
            return path

    return font_files[0]


FONT_SCALE = 1.0

def load_game_font(size, bold=False):
    scaled_size = max(1, int(round(size * FONT_SCALE)))
    font_path = _find_project_font_path()
    if font_path is not None:
        try:
            font = pygame.font.Font(font_path, scaled_size)
            font.set_bold(bold)
            return font
        except Exception:
            pass
    return pygame.font.SysFont(None, scaled_size, bold=bold)


def load_default_font(size, bold=False):
    scaled_size = max(1, int(round(size * FONT_SCALE)))
    return pygame.font.SysFont(None, scaled_size, bold=bold)
