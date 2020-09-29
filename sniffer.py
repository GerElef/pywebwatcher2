from math import inf

from scapy.all import sniff, IFACES

from db.dao import Dao


# https://scapy.readthedocs.io/en/latest/api/scapy.sendrecv.html
class Sniffer:
    def __init__(self, interface, readable_interface, evt, packet_count = inf):
        self.interface = interface
        self.readable_interface = readable_interface
        self.evt = evt
        self.max_packets = packet_count

        self.db = Dao()

    def start_sniffing(self):
        if self.max_packets == inf:
            sniff(filter="ip", prn=self.process_packet, iface=self.interface,
                  stop_filter = lambda x: self.evt.is_set)
        else:
            sniff(filter="ip",prn=self.process_packet, count=self.max_packets, iface=self.interface,
                  stop_filter = lambda x: self.evt.is_set)

    #https://thepacketgeek.com/scapy/sniffing-custom-actions/part-1/
    def process_packet(self, packet):
        self.db.save_packet(packet[0][1].src, self.readable_interface, packet[0][1].dst, packet[0][1].len)

    #use column 0 for arguments to sniff with scapy i think
    @staticmethod
    def get_interface_list():
        interfaces = [[],[],[],[]]

        interface_keys = IFACES.data.keys()

        for key in interface_keys:
            subinterface = IFACES.data[key]

            interfaces[0].append(subinterface.description)
            interfaces[1].append(subinterface.name)
            interfaces[2].append(subinterface.ips)
            interfaces[3].append(subinterface.ip)

        return interfaces