from math import inf
from threading import Thread, Event

from flag_handler import CMDHandler
from sys import argv
from net_test.nettest import StabilityTester
from net_test.sniffer import Sniffer
from time import sleep

def start_sniffing():
    pass

def get_interfaces():
    ifaces = Sniffer.get_interface_list()

    interfaces = [[], []]
    for i in range(len(ifaces[0])):
        if ifaces[3][i] is None:
            continue

        interfaces[0].append(ifaces[0][i])
        interfaces[1].append(ifaces[3][i])

    return interfaces

def start_tester(iface, evt, loop_times):
    tester = StabilityTester(iface)
    if loop_times == inf:
        Thread(target=tester.ping_with_event, args=(evt,)).start()
    else:
        Thread(target=tester.ping_with_event_counter, args=(evt, loop_times,)).start()

def start_sniffer(iface, ifaceipv4, evt, count):
    sniffer = Sniffer(iface, ifaceipv4, evt, packet_count = count)
    Thread(target=sniffer.start_sniffing).start()

#TODO add exporter and join CMD args

if __name__ == '__main__':
    handler = CMDHandler()
    handler.parse_sys_args(argv)
    handler.post_processing(get_interfaces())

    StabilityTester.SLEEP_TIME = handler.SLEEP_TIME

    #if we encounter any exceptions, bail
    if handler.exceptions:
        for e in handler.exceptions:
            print(e.__str__() + "\n")

        exit(0)

    if handler.SAVE_FOUND:
        #do stuff for output here

        #then exit
        exit(0)

    tester_event = Event()
    start_tester(handler.INTERFACE_IPV4, tester_event, handler.LOOP_TIMES)

    scapy_event = Event()
    if handler.SNIFF_FLAG:
        start_sniffer(handler.INTERFACE_READABLE, handler.INTERFACE_IPV4, scapy_event, handler.PACKET_COUNT)

    try:
        while True:
            sleep(999999)
    except KeyboardInterrupt:
        print("Shutting down threads...")
        tester_event.set()
        scapy_event.set()
    finally:
        exit(0)