# main.py
import pygame
import sys
from settings import S_WIDTH, S_HEIGHT, FPS
from menu import EstadoMenu
from game import CarreraDeObstaculos
from audio import SoundPlayer


def main():
    pygame.init()
    screen = pygame.display.set_mode((S_WIDTH, S_HEIGHT))
    pygame.display.set_caption("Carrera de Obstáculos")
    clock = pygame.time.Clock()

    sound_player = SoundPlayer()
    menu = EstadoMenu(screen)
    juego = CarreraDeObstaculos(screen)
    juego.sound_player = sound_player
    menu.sound_player = sound_player
    sound_player.play_menu_music()

    estado_actual = "MENU"
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if estado_actual == "MENU":
            resultado = menu.manejar_eventos(events)
            if resultado == "JUGANDO":
                # CAMBIO AQUÍ: Guardamos el nombre y vamos al SELECTOR en lugar del juego
                juego.player_name = menu.player_name
                estado_actual = "SELECTOR" 
            elif resultado == "SALIR":
                running = False

            menu.actualizar()
            menu.dibujar()

        elif estado_actual == "SELECTOR":
            for event in events:
                personaje_elegido = juego.selector.handle_event(event)
                
                if personaje_elegido:
                    juego.personaje_actual = personaje_elegido
                    juego.reset_game()
                    sound_player.play_game_music(0) 
                    estado_actual = "JUGANDO"
                    
            juego.selector.draw(screen)

        elif estado_actual == "JUGANDO":
            resultado_eventos = juego.handle_events(events)
            if resultado_eventos == "MENU":
                estado_actual = "MENU"

            resultado_update = juego.update(dt)
            if resultado_update == "MENU":
                estado_actual = "MENU"
                score = juego.score // 10
                menu.finalizar_partida(score, juego.player_name)
                sound_player.play_menu_music()

            juego.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()