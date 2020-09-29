from threading import Thread, Event

from flag_handler import CMDHandler
from net_test.nettest import StabilityTester
from sniffer import Sniffer
from time import sleep

def start_sniffing():
    pass

#TODO add exporter and CMD args

if __name__ == '__main__':
    handler = CMDHandler()

    #interfaces = Sniffer.get_interface_list()
    #print("Pick interface:")
    #for i in range(len(interfaces[0])):
    #    if interfaces[3][i] is None:
    #        continue

    #    print(f"{i + 1} Name: {interfaces[0][i]}\n\t IP: {interfaces[3][i]}")

    #usr_in = int(input("Enter int input: ")) - 1

    #scapy_interface   = interfaces[0][usr_in]
    #libpcap_interface = interfaces[3][usr_in]

    #tester_event = Event()
    #tester = StabilityTester(libpcap_interface)
    #tester_thread = Thread(target=tester.ping_with_event, args=(tester_event,)).start()

    #scapy_event = Event()
    #sniffer = Sniffer(scapy_interface, libpcap_interface, scapy_event)
    #sniffer_thread = Thread(target=sniffer.start_sniffing).start()

    #try:
    #    while True:
    #        sleep(999999)
    #except KeyboardInterrupt:
    #    print("Shutting down threads...")
    #    tester_event.set()
    #    scapy_event.set()
    #finally:
    #    exit(0)