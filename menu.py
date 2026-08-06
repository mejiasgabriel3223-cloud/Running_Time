import json
import os
import pygame
from abc import ABC, abstractmethod

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
        self.options = ["Jugar", "Records", "Configuración", "Créditos", "Salir"]
        self.selected_index = 0
        self.state = "MENU"
        self.player_name = ""
        self.input_text = ""
        self.message = ""
        self.pending_score = None
        self.pending_name = None
        self.records_file = os.path.join(os.path.dirname(__file__), "records.json")
        self.records = self._load_records()
        self.sound_player = None

        self.font_title = pygame.font.SysFont(None, 82)
        self.font_option = pygame.font.SysFont(None, 46)
        self.font_text = pygame.font.SysFont(None, 32)
        self.font_small = pygame.font.SysFont(None, 26)
        self.fondo = pygame.image.load("Fondo pista.jpeg").convert()
        self.imagen_titulo = pygame.image.load("Logo_sin_fondo.png").convert_alpha()

        animacion_sheet_jake = pygame.image.load("baile jake.png").convert_alpha()
        frames_1 = recortar_sprite_sheet(animacion_sheet_jake, 357, 357, 27)
        self.animacion_jake = Animador(frames_1, velocidad=8)

        animacion_sheet_finn = pygame.image.load("fin bailando.png").convert_alpha()
        frames_2 = recortar_sprite_sheet(animacion_sheet_finn, 386, 386, 4)
        self.animacion_finn = Animador(frames_2, velocidad=8)
    def _load_records(self):
        if not os.path.exists(self.records_file):
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

    def finalizar_partida(self, score, player_name):
        if not player_name:
            return

        self.pending_score = score
        self.pending_name = player_name.strip() or "Jugador"
        self.records = self._load_records()

        existing = [entry for entry in self.records if str(entry.get("name", "")).lower() == self.pending_name.lower()]
        if not existing:
            self.records.append({"name": self.pending_name, "score": score})
            self._save_records()
            self._show_message(f"Nuevo record guardado para {self.pending_name}: {score}")
            return

        self.state = "REPLACE_PROMPT"
        self._show_message(f"Ya existe un record de {self.pending_name}. ¿Reemplazarlo? (S/N)")

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
            self._show_message(f"Se guardó otra entrada para {self.pending_name}: {self.pending_score}")

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
                    if option == "Configuración":
                        self.state = "CONFIGURATION"
                        return None
                    if option == "Créditos":
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
                elif evento.key == pygame.K_RETURN:
                    self.player_name = self.input_text.strip() or "Jugador"
                    self.state = "MENU"
                    self._show_message("")
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

        return None

    def actualizar(self):
        if self.state == "MENU":
            self.animacion_jake.actualizar()
            self.animacion_finn.actualizar()
            
        if self.sound_player is not None and self.state == "MENU" and self.message != "":
            pass
        return None

    def _draw_centered_text(self, text, y, font, color=(255, 255, 255)):
        rendered = font.render(text, True, color)
        rect = rendered.get_rect(center=(self.pantalla.get_width() // 2, y))
        self.pantalla.blit(rendered, rect)

    def _draw_menu(self):
        rect_titulo = self.imagen_titulo.get_rect(center=(self.pantalla.get_width() // 2, 165))
        self.pantalla.blit(self.imagen_titulo, rect_titulo)
        self.pantalla.blit(self.animacion_jake.obtener_imagen_actual(), (self.pantalla.get_width() - 460, 360))
        self.pantalla.blit(self.animacion_finn.obtener_imagen_actual(), (self.pantalla.get_width() - 1180, 260))
        start_y = 320
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
            empty_text = self.font_text.render("Aún no hay records guardados", True, (255, 255, 255))
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
        self._draw_centered_text("Configuración", 120, self.font_title)
        lines = [
            "Resolución: 1280x720",
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
        self._draw_centered_text("Créditos", 120, self.font_title)
        lines = [
            "Colaboradores: Gabriel Mejias, Sofia Marquez",
            "Música: créditos musicales incluidos en la presentación",
            "Efectos: sonidos básicos del juego",
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
            self._draw_centered_text(self.message, 300, self.font_text)
            self._draw_centered_text("Presiona S o N", 360, self.font_small)