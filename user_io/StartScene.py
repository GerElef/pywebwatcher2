from abc import ABC, abstractmethod
from time import sleep

import pygame
from pygame.constants import MOUSEBUTTONDOWN

from user_io.pygameplotter import Scene, Engine

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.font.init()
pygame.init()


class UIComponent(ABC):

    @abstractmethod
    def draw(self, surface: pygame.surface.Surface, color, active: bool, pos: tuple[int, int]):
        pass

    @abstractmethod
    def resize(self, newWidthHeight: tuple[int, int]):
        pass

    @abstractmethod
    def getSize(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def collides(self, pos: tuple[int, int]):
        pass

    @abstractmethod
    def pushEvent(self, event: pygame.event):
        pass

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def deactivate(self):
        pass


# empty defines if the object should have a text input field
class Option(UIComponent):
    text_font = pygame.font.Font(pygame.font.get_default_font(), 18)

    def __init__(self, text: str, checkboxed=True, empty=True):
        self.text = text
        self.checkboxed: bool = checkboxed
        self.empty: bool = empty
        self.mock = Option.text_font.render(self.text, True, (0, 0, 0))

    def draw(self, screen: pygame.surface.Surface, color, active: bool, pos: tuple[int, int]):
        surface = Option.text_font.render(self.text, True, color)
        screen.blit(surface, pos)

    def getSize(self) -> tuple[int, int]:
        return self.mock.get_width(), self.mock.get_height()

    def resize(self, newWidthHeight: tuple[int, int]):
        pass

    def collides(self, pos: tuple[int, int]):
        pass

    def pushEvent(self, event: pygame.event):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass


class SimpleTogglableOption(Option):
    def __init__(self, text, pos):
        super().__init__(text, checkboxed=True, empty=True)


class StaticInterface(Option):
    def __init__(self):
        super().__init__("i", checkboxed=True, empty=False)


# ----------------------- PING OPTIONS START -----------------------------
class DynamicInterfaceToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("dynamic", (0, 0))


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
        super().__init__("sniff", (0, 0))


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
        super().__init__("csv", (0, 0))


class PDFToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("pdf", (0, 0))


class GraphToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("graph", (0, 0))


class OnefileToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("onefile", (0, 0))


class VerboseOnefileToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("verbose_onefile", (0, 0))


class OutputRelaxed(Option):
    def __init__(self):
        super().__init__("relaxed", checkboxed=True, empty=False)


class OutputDataChunk(Option):
    def __init__(self):
        super().__init__("data", checkboxed=True, empty=False)


class AnonToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("anon", (0, 0))


class PickleToggle(SimpleTogglableOption):
    def __init__(self):
        super().__init__("pickle", (0, 0))


# ----------------------- OUTPUT OPTIONS END -----------------------------


class Checkbox(UIComponent):
    def __init__(self, width_height: int = 15, line_thickness: int = 2):
        self.width_height = width_height
        self.line_thickness = line_thickness
        self.drawn_rect: pygame.rect.Rect = pygame.rect.Rect(0, 0, 0, 0)

    def draw(self, surface: pygame.surface.Surface, color, active: bool, pos: tuple[int, int]):
        # defined in the following order: top left, top right, bottom right, bottom left
        checkbox_points = (pos,
                           (pos[0] + self.width_height, pos[1]),
                           (pos[0] + self.width_height, pos[1] + self.width_height),
                           (pos[0], pos[1] + self.width_height))
        self.drawn_rect = \
            pygame.draw.polygon(surface, color, checkbox_points, self.line_thickness if not active else 0)

    def resize(self, newWidthHeight: int):
        self.width_height = newWidthHeight

    def move(self, newPos: tuple[int, int]):
        pass

    def pushEvent(self, event: pygame.event):
        pass

    def getSize(self) -> tuple[int, int]:
        return self.drawn_rect.width, self.drawn_rect.height

    def collides(self, pos: tuple[int, int]):
        return self.drawn_rect.collidepoint(pos)

    def activate(self):
        pass

    def deactivate(self):
        pass


class SimpleTextInput(UIComponent):
    def __init__(self, start_str: str = "", width_height: tuple[int, int] = (50, 20)):
        # TODO find a way to display text inside the rect
        # TODO find a way to make it scrollable, both as the player types, and with the mousewheel
        self.rect_str = start_str
        self.width_height = width_height
        self.input_rect = pygame.rect.Rect(0, 0, 0, 0)

    def draw(self, surface: pygame.surface.Surface, color, active: bool, pos: tuple[int, int], line_thickness: int = 2):
        self.input_rect = pygame.rect.Rect(pos, self.width_height)
        pygame.draw.rect(surface, color, self.input_rect, line_thickness)

    def move(self, newPos: tuple[int, int]):
        pass

    def resize(self, newWidthHeight: tuple[int, int]):
        pass

    def getSize(self) -> tuple[int, int]:
        pass

    def collides(self, pos: tuple[int, int]):
        return self.input_rect.collidepoint(pos)

    def pushEvent(self, event: pygame.event):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass


class AbstractButton(UIComponent, ABC):
    def __init__(self, start_str: str = "",
                 state=False, width_height: tuple[int, int] = (50, 20)):
        # TODO find a way to display text inside the rect
        self.rect_str = start_str
        self.active = state
        self.width_height = width_height
        self.input_rect = pygame.rect.Rect(0, 0, 0, 0)

    def draw(self, surface: pygame.surface.Surface, color, active: bool, pos: tuple[int, int], line_thickness: int = 0):
        rect = pygame.rect.Rect(pos, self.width_height)
        pygame.draw.rect(surface, color, rect, line_thickness)

    def collides(self, pos: tuple[int, int]):
        return self.input_rect.collidepoint(pos)

    def pushEvent(self, event: pygame.event):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1 and self.collides(event.pos):
                self.onPress()

    @abstractmethod
    def onPress(self):
        pass


class OKButton(AbstractButton):

    def __init__(self, start_str: str = "", state=False,
                 width_height: tuple[int, int] = (50, 20)):
        super().__init__(start_str, state, width_height)

    def onPress(self):
        print(f"Called onPress on button with str {self.rect_str}")
        pass

    def resize(self, newWidthHeight: tuple[int, int]):
        pass

    def getSize(self) -> tuple[int, int]:
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass


class OptionLine:
    def __init__(self, line_y, option, checkbox: Checkbox = None, text_input: SimpleTextInput = None):
        if (option.checkboxed and checkbox is None) or (not option.empty and text_input is None):
            raise Exception(f"option is checkboxed {option.checkboxed} and empty {option.empty},\t\n"
                            f"checkbox is {checkbox} and text input {text_input}")

        self.GAP_X = 15
        self.state = False
        self.line_y = line_y
        self.option: Option = option
        self.checkbox: Checkbox = checkbox
        self.text_input: SimpleTextInput = text_input
        self.active_colour: tuple[int, int, int] = (220, 220, 220)
        self.inactive_colour: tuple[int, int, int] = (55, 55, 55)

    def resize_components(self, surface, old_res, new_res):
        pass

    def composite_draw(self, surface: pygame.surface.Surface, offset_y):
        offset_x = self.GAP_X
        color_to_use = self.inactive_colour
        if self.state:
            color_to_use = self.active_colour

        if self.checkbox:
            self.checkbox.draw(surface, color_to_use, self.state, (offset_x, self.line_y + offset_y))
            offset_x += self.checkbox.getSize()[0]
            offset_x += self.GAP_X
        self.option.draw(surface, color_to_use, self.state, (offset_x, self.line_y + offset_y))
        offset_x += self.option.getSize()[0] + self.GAP_X
        if self.text_input:
            self.text_input.draw(surface, color_to_use, self.state, (offset_x, self.line_y + offset_y))


class StartScene(Scene):
    def __init__(self):
        super().__init__()
        # TODO add app_icon_round on the top height and middle width of the screen
        self.options: list[Option] = [StaticInterface(), DynamicInterfaceToggle(), PingLoopCounter(), PingTimeToSleep(),
                                      SniffToggle(), SnifferIPFilter(), SnifferPacketCounter(), OutputSaveDates(),
                                      OutputSaveLocation(), CSVToggle(), PDFToggle(), GraphToggle(), OnefileToggle(),
                                      VerboseOnefileToggle(), OutputRelaxed(), OutputDataChunk(), AnonToggle(),
                                      PickleToggle()]
        self.scroll_lines: list[OptionLine] = self.createOptionLines()
        self.x_scroll_offset = 0
        self.PX_STEP_UP = 30
        self.PX_STEP_DOWN = 30
        self.btn_Set = False

    def createOptionLines(self) -> list[OptionLine]:
        GAP_STEP = 30
        ypos = 5
        scroll_lines: list[OptionLine] = []
        for option in self.options:
            cbx = None
            txt_fld = None
            if option.checkboxed:
                cbx = Checkbox()

            if not option.empty:
                txt_fld = SimpleTextInput()

            scroll_lines.append(OptionLine(ypos, option, cbx, txt_fld))

            print(ypos)
            ypos += GAP_STEP

        return scroll_lines

    def onTransition(self) -> int:
        # if the button is "set" (clicked, and everything is ready to go), return 1 (so we go to the next scene)
        # and set btn to False again
        if self.btn_Set:
            self.btn_Set = False
            return 1
        return 0

    def pushEvent(self, event: pygame.event):
        if event.type == MOUSEBUTTONDOWN:
            # TODO check where the mouse is right now and if it collides with any scrollable object
            #  if it does, scroll the object instead and not the main screen
            if event.button == 4:
                self.x_scroll_offset += self.PX_STEP_UP
            if event.button == 5:
                self.x_scroll_offset -= self.PX_STEP_DOWN

            # if we're at the max top or bottom of the view, set to 0

            # TODO implement max and up scroll

    def render(self, screen):
        screen.fill((0, 0, 0))
        for scroll_line in self.scroll_lines:
            scroll_line.composite_draw(screen, self.x_scroll_offset)


if __name__ == "__main__":
    start_scene = StartScene()
    engine = Engine([start_scene])
    while True:
        if engine.is_shut_down:
            break
        engine.main_loop()

    pygame.quit()
