from random import Random
from time import sleep

import pygame

from user_io.pygameplotter import Scene, Engine


pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.font.init()
pygame.init()


class StartScene(Scene):
    def __init__(self):
        super().__init__()
        self.btn_Set = False

    def onTransition(self) -> int:
        # if the button is "set" (clicked, and everything is ready to go), return 1 (so we go to the next scene)
        # and set btn to False again
        if self.btn_Set:
            self.btn_Set = False
            return 1
        return 0

    def pushEvent(self, event: pygame.event):
        pass

    def render(self, screen):
        pass


if __name__ == "__main__":
    start_scene = StartScene()
    engine = Engine([start_scene])
    while True:
        if engine.is_shut_down:
            break
        engine.main_loop()

        # for reducing main loop CPU burden
        sleep(0.1)

    pygame.quit()
