from json import load
from threading import Event
from time import sleep
from typing import List

import ping3
from errors import PingError, Timeout
from ping3 import ping

from db.dao import Dao
from user_io.PingScene import PingScene

ping3.EXCEPTIONS = True


class StabilityTester:
    UPPER_LIMIT = 1000  # upper limit in ms
    SLEEP_TIME = 1  # sleep time between calls in seconds -- ideally should be the same as upper limit

    def __init__(self, src_addr: str):
        with open("servers.json", 'r', encoding="utf-8") as file:
            data: List[List[str], List[str]] = load(file)

        self.servers: List = data[0]
        self.servers_readable: List = data[1]
        self.local_history = []

        self.db = Dao()
        self.interface = src_addr

        for _ in self.servers:
            self.local_history.append(0)

        if len(self.servers) != len(self.servers_readable):
            raise ServerHostNameMismatchException()

    def ping_forever(self, scene):
        while True:
            self.loop_servers(scene)

    def ping_with_event(self, evt: Event, scene: PingScene):
        while True:
            if evt.is_set():
                break
            self.loop_servers(scene)

    def ping_with_event_counter(self, evt: Event, c, scene: PingScene):
        for i in range(c):
            if evt.is_set():
                break
            self.loop_servers(scene)

    def loop_servers(self, scene: PingScene):
        tts = StabilityTester.SLEEP_TIME

        for i in range(len(self.servers)):
            try:
                ms = int(self.ping_server(self.servers[i]))
                ping_in_s = ms / 1000

                time_left = tts - ping_in_s if ping_in_s < tts else 0

                self.db.timestamp(ms, StabilityTester.UPPER_LIMIT,
                                  self.servers[i], self.servers_readable[i],
                                  self.interface)

                scene.add_stamp(self.servers_readable[i], ms)

                print(f"Server Name: {self.servers_readable[i]}\n"
                      f"\tReplied in: {ms}ms\n"
                      f"\tPing Variation: {ms - self.local_history[i]}ms")

                self.local_history[i] = ms

                sleep(time_left)

            except Timeout:
                self.db.timestamp(0, StabilityTester.UPPER_LIMIT,
                                  self.servers[i], self.servers_readable[i],
                                  self.interface, True)
                scene.add_stamp(self.servers_readable[i], 0)

                print(f"Server Name: {self.servers_readable[i]}\n"
                      f"\t\tConnection timed out.")

            except PingError as pe:
                scene.add_stamp(self.servers_readable[i], 0)
                print(f"Encountered unexpected PingError {pe} when pinging {self.servers_readable[i]}")
                sleep(0.1)
            except Exception as e:
                # silently pass if our adapter dies or something, we do not care
                sleep(tts)

    def ping_server(self, server: str):
        return ping(server, src_addr=self.interface, unit='ms', timeout=StabilityTester.SLEEP_TIME)


class ServerHostNameMismatchException(Exception):
    pass


if __name__ == "__main__":
    pass
