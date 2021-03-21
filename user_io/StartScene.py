from abc import ABC, abstractmethod
from time import sleep

import pygame

from user_io.pygameplotter import Scene, Engine

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.font.init()
pygame.init()


# empty defines if the object should have a text input field
class Option:
    def __init__(self, text: str, checkboxed=True, empty=True):
        self.text = text
        self.checkboxed = checkboxed
        self.empty = empty
        self.active = True
        self.active_colour = (255, 255, 255)
        self.inactive_colour = (55, 55, 55)

    def turn_off(self):
        self.active = False

    def turn_on(self):
        self.active = True


class SimpleTogglableOption(Option):
    def __init__(self, text):
        super().__init__(text, checkboxed=True, empty=True)


class StaticInterface(Option):
    def __init__(self):
        super().__init__("i", checkboxed=False, empty=False)


# ----------------------- PING OPTIONS START -----------------------------
class DynamicInterfaceToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("dynamic")


class PingLoopCounter(Option):
    def __init__(self):
        super().__init__("l", checkboxed=True, empty=False)


class PingTimeToSleep(Option):
    def __init__(self):
        super().__init__("t", checkboxed=True, empty=False)


# ----------------------- PING OPTIONS END -----------------------------
# ----------------------- SNIFF OPTIONS START -----------------------------
class SniffToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("sniff")


class SnifferIPFilter(Option):
    def __init__(self):
        super().__init__("f", checkboxed=True, empty=False)


class SnifferPacketCounter(Option):
    def __init__(self):
        super().__init__("c", checkboxed=True, empty=False)


# ----------------------- SNIFF OPTIONS END -----------------------------
# ----------------------- OUTPUT OPTIONS START -----------------------------
class OutputSaveDates(Option):
    def __init__(self):
        super().__init__("save", checkboxed=True, empty=False)


class OutputSaveLocation(Option):
    def __init__(self):
        super().__init__("o", checkboxed=True, empty=False)


class CSVToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("csv")


class PDFToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("pdf")


class GraphToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("graph")


class OnefileToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("onefile")


class VerboseOnefileToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("verbose_onefile")


class OutputRelaxed(Option):
    def __init__(self):
        super().__init__("o", checkboxed=True, empty=False)


class OutputDataChunk(Option):
    def __init__(self):
        super().__init__("o", checkboxed=True, empty=False)


class AnonToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("onefile")


class PickleToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("onefile")


# ----------------------- OUTPUT OPTIONS END -----------------------------


class UIComponent(ABC):
    @abstractmethod
    def draw(self, surface: pygame.surface.Surface, color):
        pass

    @abstractmethod
    def move(self, newPos: tuple[int, int]):
        pass

    @abstractmethod
    def collides(self, pos: tuple[int, int]):
        pass

    @abstractmethod
    def pushEvent(self):
        pass

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def deactivate(self):
        pass


class Checkbox(UIComponent):
    def __init__(self, top_left_pos: tuple[int, int], state=False, width_height: int = 10, line_thickness: int = 2):
        self.top_left_pos = top_left_pos
        self.active = state
        self.width_height = width_height
        self.line_thickness = line_thickness
        self.drawn_rect = pygame.rect.Rect(0, 0, 0, 0)

    def draw(self, surface: pygame.surface.Surface, color):
        # defined in the following order: top left, top right, bottom right, bottom left
        checkbox_points = (self.top_left_pos,
                           (self.top_left_pos[0] + self.width_height, self.top_left_pos[1]),
                           (self.top_left_pos[0] + self.width_height, self.top_left_pos[1] + self.width_height),
                           (self.top_left_pos[0], self.top_left_pos[1] + self.width_height))
        self.drawn_rect = \
            pygame.draw.polygon(surface, color, checkbox_points, self.line_thickness if not self.active else 0)

    def move(self, newPos: tuple[int, int]):
        self.top_left_pos = newPos

    def collides(self, pos: tuple[int, int]):
        return self.drawn_rect.collidepoint(pos)

    def pushEvent(self):
        pass

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


class SimpleTextInput(UIComponent):
    def __init__(self, top_left_pos: tuple[int, int], start_str: str = "",
                 state=False, width_height: tuple[int, int] = (50, 20)):
        # TODO find a way to display text inside the rect
        # TODO find a way to make it scrollable, both as the player types, and with the mousewheel
        self.rect_str = start_str
        self.top_left_pos = top_left_pos
        self.active = state
        self.width_height = width_height
        self.input_rect = pygame.rect.Rect(top_left_pos, width_height)

    def draw(self, surface: pygame.surface.Surface, color, line_thickness: int = 2):
        pygame.draw.rect(surface, color, self.input_rect, line_thickness)

    def move(self, newPos: tuple[int, int]):
        self.top_left_pos = newPos
        self.input_rect = pygame.rect.Rect(newPos, self.width_height)

    def collides(self, pos: tuple[int, int]):
        return self.input_rect.collidepoint(pos)

    def pushEvent(self):
        pass

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


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
