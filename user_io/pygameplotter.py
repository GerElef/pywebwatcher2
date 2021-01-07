from random import Random
from time import time, sleep

import pygame
from pygame.locals import RESIZABLE, QUIT, K_ESCAPE, K_LSHIFT, K_RSHIFT, VIDEORESIZE


class Stamp:
    def __init__(self, label: str, ping: int, offset: int):
        self.label: str = label
        self.ping: int = ping
        self.label_offset = offset


# TODO implement history scrolling with mouse wheel.
class PyEngine:
    tickrate = 5

    def __init__(self, time_step, ylim, width=630, height=325, element_count=10, title=None, timer=False):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        pygame.font.init()
        pygame.init()

        self.total_stamps = 0
        self.display_stamps: list[Stamp] = []
        self.clock = pygame.time.Clock()
        self.clock.tick(PyEngine.tickrate)
        self.plot_font = pygame.font.Font(pygame.font.get_default_font(), 14)
        self.screen = pygame.display.set_mode((width, height), RESIZABLE)

        self.element_count = element_count
        self.stepx = time_step
        self.stepy = round(ylim / element_count)
        self.ylim = ylim
        self.title = title
        self.timer = timer
        if self.timer:
            self.start_time = time()
        self.dead_counter = 0

        pygame.display.set_caption('pywebwatcher2')

        self.WHITE = pygame.color.Color(255, 255, 255)
        self.GRAY = pygame.color.Color(125, 125, 125)
        self.MARINE = pygame.color.Color(255, 65, 50)
        self.GREEN = pygame.color.Color(60, 255, 60)
        self.BLACK = pygame.color.Color(0, 0, 0)
        self.MARGIN_W = 30
        self.MARGIN_H = 30
        self.MARGIN_SMALL_H = 10
        self.MARGIN_SMALL_W = 10

        self.label_offset_y = self.MARGIN_SMALL_H
        self.y_axis_true_h = self.screen.get_height() - self.MARGIN_H * 2
        self.x_axis_true_w = self.screen.get_width() - self.MARGIN_W * 2
        self.is_shut_down = False

    def main_loop(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.shutdown()
            if event.type == VIDEORESIZE:
                width, height = event.size
                reset = False
                if width < 300:
                    width = 300
                    reset = True
                if height < 250:
                    height = 250
                    reset = True

                if reset:
                    self.screen = pygame.display.set_mode((width, height), RESIZABLE)

        key_press = pygame.key.get_pressed()
        if key_press[K_ESCAPE] and (key_press[K_LSHIFT] or key_press[K_RSHIFT]):
            self.shutdown()

        self.draw_axes()
        self.draw_stamps(self.GREEN, self.MARINE)
        self.draw_misc()

        # https://sivasantosh.wordpress.com/2012/07/21/renderupdates-pygame/
        # optimize the rendering process
        pygame.display.update()

    def draw_misc(self):
        if self.timer:
            minutes, seconds = divmod(time() - self.start_time, 60)
            hours, minutes = divmod(minutes, 60)
            self.draw_text(f"Active For: {hours:02.0f}:{minutes:02.0f}", self.WHITE,
                                         (int(self.MARGIN_W), int(self.MARGIN_H / 2)), offset_x=10)

        if self.title:
            self.draw_text(self.title, self.WHITE, (int(self.MARGIN_W) * 8, int(self.MARGIN_H / 2)))

        self.draw_text(f"Total stamps: {self.total_stamps}", self.WHITE,
                       (self.screen.get_width() + self.MARGIN_W, int(self.MARGIN_H / 2)), offset_x=-100)
        self.draw_text(f"Dead: {round(100 * (self.dead_counter / (self.total_stamps + 1)), 2)}%", self.WHITE,
                       (self.screen.get_width(), int(self.MARGIN_W / 2)), offset_x=-200)

    def draw_text(self, s: str, colour, pos: tuple[int, int], offset_x: int = 0, offset_y: int = 0):
        surface = self.plot_font.render(s, True, colour)
        x = int(pos[0] - surface.get_width() / 2) + offset_x
        y = int(pos[1] - surface.get_height() / 2) + offset_y
        if x < 0:
            x = 0
        elif x > self.screen.get_width():
            x = self.screen.get_width()

        if y < 0:
            y = 0
        elif y > self.screen.get_width():
            y = self.screen.get_height()
        self.screen.blit(surface, (x, y))

    def draw_stamps(self, colour_alive, colour_dead):
        def is_dead(stamp: Stamp):
            return stamp.ping <= 0

        offset_x = self.MARGIN_W
        offset_y = self.MARGIN_H

        for i in range(0, len(self.display_stamps) - 1):
            curr_point = (offset_x + self.map_x_to_plot(i), offset_y + self.map_y_to_plot(self.display_stamps[i]))
            next_point = (
                offset_x + self.map_x_to_plot(i + 1), offset_y + self.map_y_to_plot(self.display_stamps[i + 1]))
            line_colour = colour_dead if is_dead(self.display_stamps[i]) else colour_alive
            text_offset_y = self.label_offset_y if curr_point[1] > next_point[1] else -self.label_offset_y

            self.draw_text(self.display_stamps[i].label, line_colour, curr_point, offset_y=text_offset_y)
            pygame.draw.line(self.screen, line_colour, curr_point, next_point, 2)

    def map_y_to_plot(self, stamp: Stamp) -> int:
        # https://stackoverflow.com/questions/929103/convert-a-number-range-to-another-range-maintaining-ratio
        inverted_ping = self.ylim - stamp.ping  # invert because we display inverted
        return round((((inverted_ping - 0) * self.y_axis_true_h) / self.ylim))

    def map_x_to_plot(self, index) -> int:
        if index == 0:
            return round(self.x_axis_true_w)
        else:
            return round(self.x_axis_true_w - (self.x_axis_true_w / self.element_count) * index)

    def draw_axes(self):
        # draws vertical lines along the X axis
        def draw_x_gaps(colour, ghost_colour, height_start, height_end, width):
            current_width = self.MARGIN_W
            for i in range(self.element_count):
                current_width += horizontal_step
                pygame.draw.aaline(self.screen, colour,
                                   (current_width, height_start),
                                   (current_width, height_end))
                current_height = self.MARGIN_H
                for j in range(self.element_count):
                    x = current_width - round(width / 2)
                    y = current_width + round(width / 2)
                    if i == self.element_count - 1:
                        y = current_width
                    pygame.draw.aaline(self.screen, ghost_colour,
                                       (x, current_height),
                                       (y, current_height))
                    current_height += vertical_step
                self.draw_text(str(get_x_label(i)), ghost_colour, (current_width, height_start), offset_y=10)

        # draws horizontal lines along the Y axis
        def draw_y_gaps(colour, ghost_colour, width_start, width_end, height):
            current_height = self.MARGIN_H
            for i in range(self.element_count):
                pygame.draw.aaline(self.screen, colour,
                                   (width_start, current_height),
                                   (width_end, current_height))
                current_width = self.MARGIN_W
                for j in range(self.element_count):
                    current_width += horizontal_step
                    x = current_height - round(height / 2)
                    y = current_height + round(height / 2)
                    if i == 0:
                        x = current_height
                    pygame.draw.aaline(self.screen, ghost_colour,
                                       (current_width, x),
                                       (current_width, y))

                self.draw_text(str(get_y_label(self.element_count - 1 - i)), ghost_colour, (0, current_height),
                               offset_y=5)
                current_height += vertical_step

        def get_x_label(index):
            count = self.stepx * self.element_count
            for k in range(self.element_count - 1):
                count -= self.stepx
                if k == index:
                    return count
            return "LIVE"

        def get_y_label(index):
            count = self.stepy
            for k in range(self.element_count):
                if index == k:
                    return count
                count += self.stepy

        self.screen.fill(self.BLACK)

        # draws Y axis
        y_axis_x = (self.MARGIN_W, self.MARGIN_H)
        y_axis_y = (self.MARGIN_W, self.screen.get_height() - self.MARGIN_SMALL_H)
        pygame.draw.aaline(self.screen, self.WHITE, y_axis_x, y_axis_y)

        # draws X axis
        x_axis_x = (self.MARGIN_SMALL_H, self.screen.get_height() - self.MARGIN_H)
        x_axis_y = (self.screen.get_width() - self.MARGIN_W, self.screen.get_height() - self.MARGIN_H)
        pygame.draw.aaline(self.screen, self.WHITE, x_axis_x, x_axis_y)

        # draws Y axis gaps
        self.y_axis_true_h = self.screen.get_height() - self.MARGIN_H * 2
        vertical_step = round(self.y_axis_true_h / self.element_count)

        # draws X axis gaps
        self.x_axis_true_w = self.screen.get_width() - self.MARGIN_W * 2
        horizontal_step = round(self.x_axis_true_w / self.element_count)

        # draw from top to bottom
        draw_y_gaps(self.WHITE, self.GRAY, self.MARGIN_SMALL_W * 2, self.MARGIN_SMALL_W * 4, self.MARGIN_SMALL_W * 2)

        # draw from left to right
        draw_x_gaps(self.WHITE, self.GRAY, self.screen.get_height() - self.MARGIN_SMALL_W * 2,
                    self.screen.get_height() - self.MARGIN_SMALL_W * 4, self.MARGIN_SMALL_W * 2)

    def add_stamp(self, label, ping):
        if len(self.display_stamps) > self.element_count:
            self.display_stamps.pop(self.element_count)
        if ping <= 0:
            self.dead_counter += 1
        stamp: Stamp = Stamp(label, ping, self.label_offset_y)
        self.display_stamps.insert(0, stamp)
        self.total_stamps += 1

    def shutdown(self):
        self.is_shut_down = True


if __name__ == "__main__":
    engine = PyEngine(1, 1000, title="Test", timer=True)
    h = 0
    sum = -100
    STEP = 25
    while True:
        h += 1
        if engine.is_shut_down:
            break
        engine.main_loop()
        # for reducing main loop CPU burden
        engine.add_stamp(f"test{h}", Random().randint(-100, 100))
        sum += STEP

        sleep(0.5)

    pygame.quit()
