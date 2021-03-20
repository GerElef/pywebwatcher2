import pygame

from user_io.pygameplotter import Scene


pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.font.init()
pygame.init()


class TrafficScene(Scene):
    def __init__(self):
        super().__init__()

    def onTransition(self) -> int:
        pass

    def pushEvent(self, event: pygame.event):
        pass

    def render(self, screen):
        pass