from abc import ABC, abstractmethod
from typing import List, Tuple

import pygame
from pygame.locals import RESIZABLE, QUIT, K_ESCAPE, K_LSHIFT, K_RSHIFT, VIDEORESIZE


pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.font.init()
pygame.init()


class Stamp:
    def __init__(self, label: str, ping: int, offset: int):
        self.label: str = label
        self.ping: int = ping
        self.label_offset = offset


class Scene(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def pushEvent(self, event: pygame.event):
        pass

    @abstractmethod
    def onTransition(self) -> int:
        pass

    @abstractmethod
    def render(self, screen):
        pass


class Engine:
    tickrate = 30

    def __init__(self, scenes_list: List[Scene], min_width_height: Tuple[int, int] = (300, 250),
                 start_width=630, start_height=325):
        self.min_width, self.min_height = min_width_height
        self.clock = pygame.time.Clock()
        self.scenes = scenes_list
        self.scene_index = 0
        self.is_shut_down = False
        self.reset = False
        self.screen = pygame.display.set_mode((start_width, start_height), RESIZABLE)

    def main_loop(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.shutdown()
                return

            if event.type == VIDEORESIZE:
                width, height = event.size
                if width < self.min_width:
                    width = self.min_width
                    self.reset = True
                if height < self.min_height:
                    height = self.min_height
                    self.reset = True

                if self.reset:
                    self.screen = pygame.display.set_mode((width, height), RESIZABLE)
                    self.reset = False
                    continue

            self.scenes[self.scene_index].pushEvent(event)

        key_press = pygame.key.get_pressed()
        if key_press[K_ESCAPE] and (key_press[K_LSHIFT] or key_press[K_RSHIFT]):
            self.shutdown()

        self.scene_index += self.scenes[self.scene_index].onTransition()
        if self.scene_index >= len(self.scenes):
            self.shutdown()
            return

        self.scenes[self.scene_index].render(self.screen)

        pygame.display.update()
        self.clock.tick(Engine.tickrate)

    def shutdown(self):
        self.is_shut_down = True
