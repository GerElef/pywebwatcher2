from random import Random
from time import time, sleep
from abc import ABC, abstractmethod
import pygame
from pygame.locals import RESIZABLE, QUIT, K_ESCAPE, K_LSHIFT, K_RSHIFT, VIDEORESIZE, MOUSEBUTTONDOWN

from db.dao import Dao


class Stamp:
    def __init__(self, label: str, ping: int, offset: int):
        self.label: str = label
        self.ping: int = ping
        self.label_offset = offset


#TODO drawable class?

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


class PingScene(Scene):

    def __init__(self, time_step, ylim, element_count=10, title=None, timer=False):
        super().__init__()

        self.DB_PULL_INTERVAL = 100
        self.STEP_UP = 2
        self.STEP_DOWN = 2
        self.scroll_offset = 0
        self.start_sticky = True
        self.total_stamps = 0
        self.display_stamps: list[Stamp] = []
        self.plot_font = pygame.font.Font(pygame.font.get_default_font(), 14)

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
        #TODO
        # self.JUMP_BTN = PyBtn(pygame.rect(l, t, w, h))
        #TODO
        # fill the area under the "plot line", e.g. if the ping is 305, 0-305 should be filled with the same colour...
        self.MARGIN_W = 30
        self.MARGIN_H = 30
        self.MARGIN_SMALL_H = 10
        self.MARGIN_SMALL_W = 10

        self.label_offset_y = self.MARGIN_SMALL_H

        self.reset = False

    def pushEvent(self, event: pygame.event):
        if event.type == MOUSEBUTTONDOWN:
            #TODO
            # if it's button 1 (left click), and it's on top of a button (any button), execute that button's
            # code

            # scroll up
            if event.button == 4:
                self.scroll_offset += self.STEP_UP
                self.start_sticky = False
            if event.button == 5:
                self.scroll_offset -= self.STEP_DOWN

                # if we're at the "top" of the graph, declare it sticky
                if self.scroll_offset <= 0:
                    self.start_sticky = True
                    self.scroll_offset = 0

    def onTransition(self) -> int:
        return 0

    def draw_axes(self, screen):
        # draws vertical lines along the X axis
        def draw_x_gaps(colour, ghost_colour, height_start, height_end, width):
            current_width = self.MARGIN_W
            for i in range(self.element_count):
                current_width += horizontal_step
                pygame.draw.aaline(screen, colour,
                                   (current_width, height_start),
                                   (current_width, height_end))
                current_height = self.MARGIN_H
                for j in range(self.element_count):
                    x = current_width - round(width / 2)
                    y = current_width + round(width / 2)
                    if i == self.element_count - 1:
                        y = current_width
                    pygame.draw.aaline(screen, ghost_colour,
                                       (x, current_height),
                                       (y, current_height))
                    current_height += vertical_step
                self.draw_text(screen, str(get_x_label(i)), ghost_colour, (current_width, height_start), offset_y=10)

        # draws horizontal lines along the Y axis
        def draw_y_gaps(colour, ghost_colour, width_start, width_end, height):
            current_height = self.MARGIN_H
            for i in range(self.element_count):
                pygame.draw.aaline(screen, colour,
                                   (width_start, current_height),
                                   (width_end, current_height))
                current_width = self.MARGIN_W
                for j in range(self.element_count):
                    current_width += horizontal_step
                    x = current_height - round(height / 2)
                    y = current_height + round(height / 2)
                    if i == 0:
                        x = current_height
                    pygame.draw.aaline(screen, ghost_colour,
                                       (current_width, x),
                                       (current_width, y))

                self.draw_text(screen, str(get_y_label(self.element_count - 1 - i)), ghost_colour, (0, current_height),
                               offset_y=5)
                current_height += vertical_step

        def get_x_label(index):
            count = self.stepx * (self.element_count + self.scroll_offset)
            for k in range(self.element_count - 1):
                count -= self.stepx
                if k == index:
                    return count

            if self.scroll_offset > 0:
                return count - self.stepx
            return "LIVE"

        def get_y_label(index):
            count = self.stepy
            for k in range(self.element_count):
                if index == k:
                    return count
                count += self.stepy

        screen.fill(self.BLACK)

        # draws Y axis
        y_axis_x = (self.MARGIN_W, self.MARGIN_H)
        y_axis_y = (self.MARGIN_W, screen.get_height() - self.MARGIN_SMALL_H)
        pygame.draw.aaline(screen, self.WHITE, y_axis_x, y_axis_y)

        # draws X axis
        x_axis_x = (self.MARGIN_SMALL_H, screen.get_height() - self.MARGIN_H)
        x_axis_y = (screen.get_width() - self.MARGIN_W, screen.get_height() - self.MARGIN_H)
        pygame.draw.aaline(screen, self.WHITE, x_axis_x, x_axis_y)

        # draws Y axis gaps
        y_axis_true_h = screen.get_height() - self.MARGIN_H * 2
        vertical_step = round(y_axis_true_h / self.element_count)

        # draws X axis gaps
        x_axis_true_w = screen.get_width() - self.MARGIN_W * 2
        horizontal_step = round(x_axis_true_w / self.element_count)

        # draw from top to bottom
        draw_y_gaps(self.WHITE, self.GRAY, self.MARGIN_SMALL_W * 2, self.MARGIN_SMALL_W * 4, self.MARGIN_SMALL_W * 2)

        # draw from left to right
        draw_x_gaps(self.WHITE, self.GRAY, screen.get_height() - self.MARGIN_SMALL_W * 2,
                    screen.get_height() - self.MARGIN_SMALL_W * 4, self.MARGIN_SMALL_W * 2)

    def draw_stamps(self, screen, colour_alive, colour_dead):
        def is_dead(stamp: Stamp):
            return stamp.ping <= 0

        offset_x = self.MARGIN_W
        offset_y = self.MARGIN_H

        end = min(len(self.display_stamps), self.element_count + 1)
        for i in range(0, end - 1):
            curr_stamp = self.display_stamps[i + self.scroll_offset]
            next_stamp = self.display_stamps[i + 1 + self.scroll_offset]

            curr_point = (offset_x + self.map_x_to_plot(screen, i), offset_y + self.map_y_to_plot(screen, curr_stamp))
            next_point = (offset_x + self.map_x_to_plot(screen, i + 1), offset_y + self.map_y_to_plot(screen, next_stamp))
            line_colour = colour_dead if is_dead(curr_stamp) else colour_alive
            text_offset_y = self.label_offset_y if curr_point[1] > next_point[1] else -self.label_offset_y

            self.draw_text(screen, curr_stamp.label, line_colour, curr_point, offset_y=text_offset_y)
            pygame.draw.line(screen, line_colour, curr_point, next_point, 2)

    def draw_misc(self, screen):
        if self.timer:
            minutes, seconds = divmod(time() - self.start_time, 60)
            hours, minutes = divmod(minutes, 60)
            self.draw_text(screen, f"Active For: {hours:02.0f}:{minutes:02.0f}", self.WHITE,
                           (int(self.MARGIN_W), int(self.MARGIN_H / 2)), offset_x=10)

        if self.title:
            self.draw_text(screen, self.title, self.WHITE, (int(self.MARGIN_W) * 8, int(self.MARGIN_H / 2)))

        # TODO button
        if self.scroll_offset > 0:
            pass

        self.draw_text(screen, f"Total stamps: {self.total_stamps}", self.WHITE,
                       (screen.get_width() + self.MARGIN_W, int(self.MARGIN_H / 2)), offset_x=-100)
        self.draw_text(screen, f"Dead: {round(100 * (self.dead_counter / (self.total_stamps + 1)), 2)}%", self.WHITE,
                       (screen.get_width(), int(self.MARGIN_W / 2)), offset_x=-200)

    def draw_text(self, screen, s: str, colour, pos: tuple[int, int], offset_x: int = 0, offset_y: int = 0):
        surface = self.plot_font.render(s, True, colour)
        x = int(pos[0] - surface.get_width() / 2) + offset_x
        y = int(pos[1] - surface.get_height() / 2) + offset_y
        if x < 0:
            x = 0
        elif x > screen.get_width():
            x = screen.get_width()

        if y < 0:
            y = 0
        elif y > screen.get_width():
            y = screen.get_height()
        screen.blit(surface, (x, y))

    def map_y_to_plot(self, screen, stamp: Stamp) -> int:
        # https://stackoverflow.com/questions/929103/convert-a-number-range-to-another-range-maintaining-ratio
        inverted_ping = self.ylim - stamp.ping  # invert because we display inverted
        y_axis_true_h = screen.get_height() - self.MARGIN_H * 2
        return round((((inverted_ping - 0) * y_axis_true_h) / self.ylim))

    def map_x_to_plot(self, screen, index) -> int:
        x_axis_true_w = screen.get_width() - self.MARGIN_W * 2
        if index == 0:
            return int(x_axis_true_w)
        else:
            return int(x_axis_true_w - (x_axis_true_w / self.element_count) * index)

    def add_stamp(self, label, ping):
        if not self.start_sticky:
            self.scroll_offset += 1

        if ping <= 0:
            self.dead_counter += 1
        stamp: Stamp = Stamp(label, ping, self.label_offset_y)
        self.display_stamps.insert(0, stamp)
        self.total_stamps += 1

    def render(self, screen):
        # if it's not sticky, e.g. we're not on the latest and greatest, and the user is scrolling...
        if not self.start_sticky:
            # pull from db if we don't have enough records to display without crashing
            end = min(len(self.display_stamps), self.element_count + 1)
            if len(self.display_stamps) < end + self.scroll_offset + 1:
                # pull records
                d = Dao()
                timestamps = d.get_n_timestamp_records_starting_from(self.total_stamps,
                                                                     interval=self.DB_PULL_INTERVAL)
                self.total_stamps += self.DB_PULL_INTERVAL
                stamps: list[Stamp] = []
                # convert into stamps
                for timestamp in timestamps:
                    if timestamp.ms <= 0:
                        self.dead_counter += 1
                    stamps.append(Stamp(timestamp.receiver_readable, timestamp.ms, offset=self.label_offset_y))
                self.display_stamps.extend(stamps)

                # if we still don't have enough records, remove the last step the user did...
                if len(self.display_stamps) < end + self.scroll_offset + 1:
                    if self.scroll_offset > self.STEP_UP:
                        self.scroll_offset -= self.STEP_UP
                    else:
                        self.scroll_offset = 0

        self.draw_axes(screen)
        self.draw_stamps(screen, self.GREEN, self.MARINE)
        self.draw_misc(screen)


class StartScene(Scene):
    def __init__(self):
        super().__init__()

    def onTransition(self) -> int:
        pass

    def pushEvent(self, event: pygame.event):
        pass

    def render(self, screen):
        pass


class TrafficScene(Scene):
    def __init__(self):
        super().__init__()

    def onTransition(self) -> int:
        pass

    def pushEvent(self, event: pygame.event):
        pass

    def render(self, screen):
        pass


class Engine:
    tickrate = 30

    def __init__(self, scenes_list: list[Scene], min_width_height: tuple[int, int] = (300, 250),
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

                #TODO
                # if resized create rect w/ new height, width

            self.scenes[self.scene_index].pushEvent(event)

        key_press = pygame.key.get_pressed()
        if key_press[K_ESCAPE] and (key_press[K_LSHIFT] or key_press[K_RSHIFT]):
            self.shutdown()

        self.scene_index += self.scenes[self.scene_index].onTransition()
        if self.scene_index >= len(self.scenes):
            self.shutdown()

        self.scenes[self.scene_index].render(self.screen)

        pygame.display.update()
        self.clock.tick(Engine.tickrate)

    def shutdown(self):
        self.is_shut_down = True


if __name__ == "__main__":
    ping_scene = PingScene(1, 1000, title="Test", timer=True)
    engine = Engine([ping_scene])
    h = 0
    sum1 = -100
    STEP = 25
    while True:
        if engine.is_shut_down:
            break
        engine.main_loop()
        # for testing
        if h < 500:
            ping_scene.add_stamp(f"test{h}", Random().randint(0, 750))
        sum1 += STEP

        h += 1
        # for reducing main loop CPU burden
        sleep(0.2)

    pygame.quit()
