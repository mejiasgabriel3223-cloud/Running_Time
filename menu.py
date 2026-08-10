import json
import math
import random
import pygame
from pathlib import Path
from abc import ABC, abstractmethod

BASE_DIR = Path(__file__).parent
IMAGENES_DIR = BASE_DIR / "assets"

from animador import Animador, recortar_sprite_sheet
class EstadoJuego(ABC):
    def __init__(self, pantalla):
        self.pantalla = pantalla

    @abstractmethod
    def manejar_eventos(self, eventos):
        pass

    @abstractmethod
    def actualizar(self):
        pass

    @abstractmethod
    def dibujar(self):
        pass


class EstadoMenu(EstadoJuego):
    def __init__(self, pantalla):
        super().__init__(pantalla)
        self.options = ["Jugar", "Records", "Configuracion", "Creditos", "Salir"]
        self.selected_index = 0
        self.state = "MENU"
        self.player_name = ""
        self.input_text = ""
        self.message = ""
        self.pending_score = None
        self.pending_name = None
        self.records_file = BASE_DIR / "records.json"
        self.records = self._load_records()
        self.sound_player = None

        from settings import load_game_font

        self.font_title = load_game_font(82)
        self.font_option = load_game_font(46)
        self.font_text = load_game_font(32)
        self.font_small = load_game_font(26)
        self.font_message = load_game_font(32)
        self.fondo = pygame.image.load(str(IMAGENES_DIR / "Fondo pista.jpeg")).convert()
        raw_logo = pygame.image.load(str(IMAGENES_DIR / "Logo_sin_fondo.png")).convert_alpha()
        logo_rect = raw_logo.get_bounding_rect()
        self.imagen_titulo = raw_logo.subsurface(logo_rect).copy()
        self.menu_messages = self._load_menu_messages()
        self.current_menu_message = self._pick_random_menu_message()

        # Posición fija del mensaje del menú (centro x, y fijo) - 40% de la altura
        self.menu_message_pos = (self.pantalla.get_width() // 2, int(self.pantalla.get_height() * 0.40))
        self.menu_message_scale = 1.0

        animacion_sheet_jake = pygame.image.load(str(IMAGENES_DIR / "baile jake.png")).convert_alpha()
        frames_1 = recortar_sprite_sheet(animacion_sheet_jake, 357, 357, 27)
        self.animacion_jake = Animador(frames_1, velocidad=8)

        animacion_sheet_finn = pygame.image.load(str(IMAGENES_DIR / "fin bailando.png")).convert_alpha()
        frames_2 = recortar_sprite_sheet(animacion_sheet_finn, 386, 386, 4)
        self.animacion_finn = Animador(frames_2, velocidad=8)
    def _load_records(self):
        if not self.records_file.exists():
            return []

        try:
            with open(self.records_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_records(self):
        ordered = sorted(self.records, key=lambda item: item.get("score", 0), reverse=True)
        self.records = ordered
        with open(self.records_file, "w", encoding="utf-8") as file:
            json.dump(ordered, file, indent=2, ensure_ascii=False)

    def _show_message(self, text):
        self.message = text

    def _load_menu_messages(self):
        messages_file = BASE_DIR / "menu_messages.json"
        if not messages_file.exists():
            return [
                "¡Cuidado con los saltos!",
                "La pista nunca perdona a los distraidos.",
                "Hoy corre como si el tiempo volara.",
                "Los mejores resultados vienen con practica.",
                "Un salto perfecto es un salto seguro."
            ]

        try:
            with open(messages_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list) and all(isinstance(item, str) for item in data):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
        return [
            "¡Cuidado con los saltos!",
            "La pista nunca perdona a los distraídos.",
            "Hoy corre como si el tiempo volara.",
            "Los mejores resultados vienen con práctica.",
            "Un salto perfecto es un salto seguro."
        ]

    def _pick_random_menu_message(self):
        if not self.menu_messages:
            return ""
        return random.choice(self.menu_messages)

    def _enter_menu_state(self):
        self.current_menu_message = self._pick_random_menu_message()

    def finalizar_partida(self, score, player_name):
        if not player_name:
            return

        self.pending_score = score
        self.pending_name = player_name.strip() or "Jugador"
        self.pending_old_score = None
        self.records = self._load_records()

        existing = [entry for entry in self.records if str(entry.get("name", "")).lower() == self.pending_name.lower()]
        if not existing:
            self.records.append({"name": self.pending_name, "score": score})
            self._save_records()
            self._show_message(f"Nuevo record guardado para {self.pending_name}: {score}")
            return

        self.pending_old_score = max(entry.get("score", 0) for entry in existing)
        self.state = "REPLACE_PROMPT"
        self._show_message("")

    def _apply_prompt(self, replace):
        if self.pending_name is None or self.pending_score is None:
            self.state = "MENU"
            return

        if replace:
            self.records = [entry for entry in self.records if str(entry.get("name", "")).lower() != self.pending_name.lower()]
            self.records.append({"name": self.pending_name, "score": self.pending_score})
            self._save_records()
            self._show_message(f"Record actualizado para {self.pending_name}: {self.pending_score}")
        else:
            self.records.append({"name": self.pending_name, "score": self.pending_score})
            self._save_records()
            self._show_message(f"Se guardo otra entrada para {self.pending_name}: {self.pending_score}")

        self.state = "MENU"

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue

            if self.state == "MENU":
                if evento.key in (pygame.K_UP, pygame.K_w):
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif evento.key == pygame.K_RETURN:
                    option = self.options[self.selected_index]
                    if option == "Jugar":
                        self.state = "NAME_INPUT"
                        self.input_text = ""
                        self._show_message("Escribe tu nombre y presiona Enter")
                        return None
                    if option == "Records":
                        self.state = "RECORDS"
                        return None
                    if option == "Configuracion":
                        self.state = "CONFIGURATION"
                        return None
                    if option == "Creditos":
                        self.state = "CREDITS"
                        return None
                    if option == "Salir":
                        return "SALIR"
                elif evento.key == pygame.K_ESCAPE:
                    return "SALIR"

            elif self.state == "NAME_INPUT":
                if evento.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif evento.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                    self.input_text = ""
                    self._show_message("")
                    self._enter_menu_state()
                elif evento.key == pygame.K_RETURN:
                    self.player_name = self.input_text.strip() or "Jugador"
                    self.state = "MENU"
                    self._show_message("")
                    self._enter_menu_state()
                    return "JUGANDO"
                elif evento.unicode and evento.unicode.isprintable() and len(self.input_text) < 16:
                    self.input_text += evento.unicode

            elif self.state == "REPLACE_PROMPT":
                if evento.key in (pygame.K_y, pygame.K_s):
                    self._apply_prompt(True)
                elif evento.key in (pygame.K_n, pygame.K_ESCAPE):
                    self._apply_prompt(False)

            else:
                if evento.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                    self._show_message("")
                    self._enter_menu_state()

        return None

    def actualizar(self):
        if self.state == "MENU":
            self.animacion_jake.actualizar()
            self.animacion_finn.actualizar()
            elapsed = pygame.time.get_ticks() / 1000.0
            self.menu_message_scale = 1.0 + 0.1 * math.sin(elapsed * 2.5)
            
        if self.sound_player is not None and self.state == "MENU" and self.message != "":
            pass
        return None

    def _draw_centered_text(self, text, y, font, color=(255, 255, 255)):
        rendered = font.render(text, True, color)
        rect = rendered.get_rect(center=(self.pantalla.get_width() // 2, y))
        self.pantalla.blit(rendered, rect)

    def _draw_menu(self):
        # Ajuste del título: pegado al borde superior
        rect_titulo = self.imagen_titulo.get_rect(midtop=(self.pantalla.get_width() // 2, 0))
        self.pantalla.blit(self.imagen_titulo, rect_titulo)
        # start_y (primera opción) se calcula antes para pasarla al mensaje
        start_y = 340
        self._draw_menu_message(rect_titulo, start_y)
        self.pantalla.blit(self.animacion_jake.obtener_imagen_actual(), (self.pantalla.get_width() - 460, 360))
        self.pantalla.blit(self.animacion_finn.obtener_imagen_actual(), (self.pantalla.get_width() - 1180, 260))

        for index, option in enumerate(self.options):
            color = (255, 255, 255)
            if index == self.selected_index:
                color = (255, 220, 100)
            text = self.font_option.render(option, True, color)
            rect = text.get_rect(center=(self.pantalla.get_width() // 2, start_y + index * 58))
            self.pantalla.blit(text, rect)

        if self.message:
            message_text = self.font_small.render(self.message, True, (220, 220, 220))
            message_rect = message_text.get_rect(center=(self.pantalla.get_width() // 2, 620))
            self.pantalla.blit(message_text, message_rect)

    def _draw_menu_message(self, rect_titulo, first_option_y):
        if not self.current_menu_message:
            return
        message_surface = self.font_message.render(self.current_menu_message, True, (255, 255, 255))
        scale = max(0.7, min(1.3, self.menu_message_scale))
        scaled_surface = pygame.transform.smoothscale(
            message_surface,
            (max(1, int(message_surface.get_width() * scale)), max(1, int(message_surface.get_height() * scale)))
        )
        center_x, center_y = self.menu_message_pos
        message_rect = scaled_surface.get_rect(center=(center_x, center_y))
        self.pantalla.blit(scaled_surface, message_rect)

    def _draw_name_input(self):
        self._draw_centered_text("Ingresa tu nombre", 140, self.font_title)
        prompt = self.font_option.render("Nombre:", True, (255, 255, 255))
        prompt_rect = prompt.get_rect(center=(self.pantalla.get_width() // 2 - 110, 290))
        self.pantalla.blit(prompt, prompt_rect)

        name_surface = self.font_option.render(self.input_text + "_", True, (255, 220, 100))
        name_rect = name_surface.get_rect(center=(self.pantalla.get_width() // 2 + 90, 290))
        self.pantalla.blit(name_surface, name_rect)

        instructions = self.font_small.render("Presiona Enter para empezar", True, (220, 220, 220))
        instructions_rect = instructions.get_rect(center=(self.pantalla.get_width() // 2, 420))
        self.pantalla.blit(instructions, instructions_rect)

        if self.message:
            msg_surface = self.font_small.render(self.message, True, (220, 220, 220))
            msg_rect = msg_surface.get_rect(center=(self.pantalla.get_width() // 2, 620))
            self.pantalla.blit(msg_surface, msg_rect)

    def _draw_records(self):
        self._draw_centered_text("Records", 120, self.font_title)
        top_records = sorted(self.records, key=lambda item: item.get("score", 0), reverse=True)[:8]

        if not top_records:
            empty_text = self.font_text.render("Aun no hay records guardados", True, (255, 255, 255))
            empty_rect = empty_text.get_rect(center=(self.pantalla.get_width() // 2, 340))
            self.pantalla.blit(empty_text, empty_rect)
            return

        for index, entry in enumerate(top_records):
            nombre = entry.get("name", "Jugador")
            puntaje = entry.get("score", 0)
            line = f"{index + 1}. {nombre} - {puntaje}"
            rendered = self.font_text.render(line, True, (255, 255, 255))
            rect = rendered.get_rect(center=(self.pantalla.get_width() // 2, 300 + index * 40))
            self.pantalla.blit(rendered, rect)

        hint = self.font_small.render("Presiona ESC para volver", True, (220, 220, 220))
        hint_rect = hint.get_rect(center=(self.pantalla.get_width() // 2, 560))
        self.pantalla.blit(hint, hint_rect)

    def _draw_configuration(self):
        self._draw_centered_text("Configuracion", 120, self.font_title)
        lines = [
            "Resolucion: 1280x720",
            "FPS: 60",
            "Controles: Flechas/W-S para mover el cursor",
            "Enter para confirmar"
        ]
        for index, line in enumerate(lines):
            rendered = self.font_text.render(line, True, (255, 255, 255))
            rect = rendered.get_rect(center=(self.pantalla.get_width() // 2, 250 + index * 45))
            self.pantalla.blit(rendered, rect)

        hint = self.font_small.render("Presiona ESC para volver", True, (220, 220, 220))
        hint_rect = hint.get_rect(center=(self.pantalla.get_width() // 2, 560))
        self.pantalla.blit(hint, hint_rect)

    def _draw_credits(self):
        self._draw_centered_text("Creditos", 120, self.font_title)
        lines = [
            "Colaboradores: Gabriel Mejias, Sofia Marquez",
            "Musica: creditos musicales incluidos en la presentacion",
            "Efectos: sonidos basicos del juego",
            "Gracias por jugar"
        ]
        for index, line in enumerate(lines):
            rendered = self.font_text.render(line, True, (255, 255, 255))
            rect = rendered.get_rect(center=(self.pantalla.get_width() // 2, 250 + index * 45))
            self.pantalla.blit(rendered, rect)

        hint = self.font_small.render("Presiona ESC para volver", True, (220, 220, 220))
        hint_rect = hint.get_rect(center=(self.pantalla.get_width() // 2, 560))
        self.pantalla.blit(hint, hint_rect)

    def dibujar(self):
        self.pantalla.blit(self.fondo, (0, 0))

        if self.state == "MENU":
            self._draw_menu()
        elif self.state == "NAME_INPUT":
            self._draw_name_input()
        elif self.state == "RECORDS":
            self._draw_records()
        elif self.state == "CONFIGURATION":
            self._draw_configuration()
        elif self.state == "CREDITS":
            self._draw_credits()
        elif self.state == "REPLACE_PROMPT":
            self._draw_centered_text("Guardar record", 140, self.font_title)
            old_text = f"Record anterior: {self.pending_old_score}" if self.pending_old_score is not None else "Record anterior: --"
            new_text = f"Puntaje actual: {self.pending_score}"
            self._draw_centered_text(old_text, 290, self.font_text)
            self._draw_centered_text(new_text, 340, self.font_text)
            self._draw_centered_text("Presiona S para reemplazar o N para conservar", 410, self.font_small)