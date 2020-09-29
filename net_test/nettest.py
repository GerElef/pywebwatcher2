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
                ms = ping(self.servers[i])
                int_ms = int(ms * 1000)
                r_ms = round(ms,3)

                time_left = tts - r_ms if r_ms < tts else 0

                self.db.timestamp(int_ms, StabilityTester.UPPER_LIMIT,
                                  self.servers, self.servers_readable,
                                  self.interface)

                print(f"Server Name: {self.servers_readable[i]}\n"
                      f"\t\tReplied in: {int_ms}ms\n"
                      f"\t\tPing Variation: {int_ms - self.local_history[i]}ms")

                self.local_history[i] = int_ms

                sleep(time_left)

            except Timeout:
                self.db.timestamp(0, StabilityTester.UPPER_LIMIT,
                                  self.servers, self.servers_readable,
                                  self.interface, True)

                print(f"Server Name: {self.servers_readable[i]}\n"
                      f"\t\tConnection timed out.")

            except PingError as pe:
                print(f"Encountered unexpected PingError {pe} when pinging {self.servers_readable[i]}")
            except Exception as e:
                print(f"Encountered unexpected generic exception {e}")


    def ping(self, server : str):
        #timeout should be in seconds, not milliseconds
        timeout = int(StabilityTester.UPPER_LIMIT / 1000)

        return ping(server, interface = self.interface, unit = 'ms', timeout = timeout)


class ServerHostNameMismatchException(Exception):
    pass
