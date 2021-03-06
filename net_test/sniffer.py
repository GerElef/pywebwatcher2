from math import inf
from typing import List

from scapy.all import sniff, get_if_list, get_if_addr, get_if_addr6#, IFACES

from db.dao import Dao


# https://scapy.readthedocs.io/en/latest/api/scapy.sendrecv.html
class Sniffer:
    IP_FILTER: List = None

    def __init__(self, interface, readable_interface, evt, packet_count=inf):
        self.interface = interface
        self.readable_interface = readable_interface
        self.evt = evt
        self.max_packets = packet_count

        self.db = Dao()

    def start_sniffing(self):
        if self.max_packets == inf:
            sniff(filter="ip", prn=self.process_packet, iface=self.interface,
                  stop_filter=lambda x: self.evt.is_set(), store=0)
        else:
            sniff(filter="ip", prn=self.process_packet, count=self.max_packets, iface=self.interface,
                  stop_filter=lambda x: self.evt.is_set(), store=0)

    # https://thepacketgeek.com/scapy/sniffing-custom-actions/part-1/
    def process_packet(self, packet):
        if Sniffer.IP_FILTER is not None:
            if not (packet[0][1].src in Sniffer.IP_FILTER or packet[0][1].dst in Sniffer.IP_FILTER):
                return

        self.db.save_packet(packet[0][1].src, packet[0][1].dst, self.readable_interface, packet[0][1].len)

    # use column 0 for arguments to sniff with scapy i think
    @staticmethod
    def get_interface_list() -> List:
        return get_if_list()

    @staticmethod
    def get_interface_ip_list() -> List:
        ifaces = get_if_list()

        ip_list = []
        for iface in ifaces:
            ip_list.append(get_if_addr(iface))

        return ip_list
