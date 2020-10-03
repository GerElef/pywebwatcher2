import os
from json import load
from threading import Event
from time import sleep

import ping3
from ping3 import ping
from errors import PingError, Timeout

from db.dao import Dao

ping3.EXCEPTIONS = True

class StabilityTester:
    UPPER_LIMIT = 1000 #upper limit in ms
    SLEEP_TIME = 1 #sleep time between calls in seconds -- ideally should be the same as upper limit

    def __init__(self, src_addr : str):
        with open("servers.json", 'r', encoding="utf-8") as file:
            data = load(file)

        self.servers = data[0]
        self.servers_readable = data[1]
        self.local_history = []

        self.db = Dao()
        self.interface = src_addr

        for _ in self.servers:
            self.local_history.append(0)

        if len(self.servers) != len(self.servers_readable):
            raise ServerHostNameMismatchException()

    def ping_forever(self):
        while True:
            self.loop_servers()

    def ping_with_event(self, evt : Event):
        while True:
            if evt.is_set():
                break
            self.loop_servers()

    def ping_with_event_counter(self, evt : Event, c):
        for i in range(c):
            if evt.is_set():
                break
            self.loop_servers()

    def loop_servers(self):
        tts = StabilityTester.SLEEP_TIME

        for i in range(len(self.servers)):
            try:
                ms = int(self.ping_server(self.servers[i]))
                ping_in_s = ms/1000

                time_left = tts - ping_in_s if ping_in_s < tts else 0

                self.db.timestamp(ms, StabilityTester.UPPER_LIMIT,
                                  self.servers[i], self.servers_readable[i],
                                  self.interface)

                print(f"Server Name: {self.servers_readable[i]}\n"
                      f"\tReplied in: {ms}ms\n"
                      f"\tPing Variation: {ms - self.local_history[i]}ms")

                self.local_history[i] = ms

                sleep(time_left)

            except Timeout:
                self.db.timestamp(0, StabilityTester.UPPER_LIMIT,
                                  self.servers[i], self.servers_readable[i],
                                  self.interface, True)

                print(f"Server Name: {self.servers_readable[i]}\n"
                      f"\t\tConnection timed out.")

            except PingError as pe:
                print(f"Encountered unexpected PingError {pe} when pinging {self.servers_readable[i]}")
            except Exception:
                #silently pass if our adapter dies or something, we do not care
                pass

    def ping_server(self, server : str):
        return ping(server, src_addr = self.interface, unit = 'ms', timeout = StabilityTester.SLEEP_TIME)


class ServerHostNameMismatchException(Exception):
    pass

if __name__ == "__main__":
    pass

