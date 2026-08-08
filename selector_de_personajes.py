import pygame

from settings import load_game_font

class CharacterCard:
    def __init__(self, x, y, character, width=140, height=180):
        self.character = character
        self.rect = pygame.Rect(x, y, width, height)
        self.icon_scaled = pygame.transform.scale(character.icon, (100, 100))
        self.font = load_game_font(28)
        
    def draw(self, screen, is_selected=False):
        # Colores y bordes según el foco
        border_color = (255, 215, 0) if is_selected else (100, 100, 100)
        bg_color = (255, 255, 255) if is_selected else (220, 220, 220)
        border_width = 5 if is_selected else 2
        
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, border_color, self.rect, width=border_width, border_radius=10)
        
        # Icono centrado
        icon_rect = self.icon_scaled.get_rect(center=(self.rect.centerx, self.rect.centery - 15))
        screen.blit(self.icon_scaled, icon_rect)
        
        # Nombre del personaje
        text_surf = self.font.render(self.character.name, True, (30, 30, 30))
        text_rect = text_surf.get_rect(center=(self.rect.centerx, self.rect.bottom - 25))
        screen.blit(text_surf, text_rect)


class CharacterSelector:
    def __init__(self, characters, screen_width, screen_height):
        self.characters = characters
        self.cards = []
        self.title_font = load_game_font(48)
        self.subtitle_font = load_game_font(24)
        
        # Cargar e integrar Fondo pista .jpeg
        self.bg_image = pygame.image.load("Fondo pista.jpeg").convert()
        self.bg_image = pygame.transform.scale(self.bg_image, (screen_width, screen_height))
        
        self.selected_index = 0
        
        # Posicionar tarjetas en pantalla
        start_x = (screen_width - (len(characters) * 160)) // 2
        for i, char in enumerate(characters):
            card_x = start_x + (i * 160)
            card_y = screen_height // 2 - 90
            self.cards.append(CharacterCard(card_x, card_y, char))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_index = (self.selected_index - 1) % len(self.cards)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_index = (self.selected_index + 1) % len(self.cards)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.cards[self.selected_index].character

        return None

    def draw(self, screen):
        screen.blit(self.bg_image, (0, 0))
        
        title_surf = self.title_font.render("SELECCIONA TU PERSONAJE", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(title_surf, title_rect)

        sub_surf = self.subtitle_font.render("Usa [A/D] o [Flechas] para moverte y [ENTER] para seleccionar", True, (240, 240, 240))
        sub_rect = sub_surf.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(sub_surf, sub_rect)
        
        for i, card in enumerate(self.cards):
            is_selected = (i == self.selected_index)
            card.draw(screen, is_selected)