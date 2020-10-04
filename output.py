import collections
from time import time
#TODO pdf

#TODO graph with vaex

#TODO onefile

#TODO verbose_onefile with relaxed threshold
#TODO should dump pdf with graph in landscape (not portrait)
#TODO should report minimum time of continuous internet record
#TODO should report maximum time of continuous internet record
#TODO should report average time of continuous internet record

class Generator:
    TIMESTAMP_INFIX = "TIMESTAMP"
    PACKET_INFIX    = "PACKET"

    def __init__(self):
        #self.generator = generator
        self.output_path = None
        self.postfix = 0
        pass

    def start_new_pass(self, output_path):
        self.postfix = int(time())
        self.output_path = output_path + "\\"

    def generate_timestamp_csv(self, generator : collections.Generator):
        with open(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{self.postfix}.csv", "w") as file:
            for timestamps in generator:
                for timestamp in timestamps:
                    line = f"{timestamp.ms},{timestamp.limit},{timestamp.receiver},{timestamp.receiver_readable}," \
                           f"{timestamp.interface},{timestamp.interface_dead},{timestamp.datetime}\n"
                    file.write(line)
                    print(f"Writing:\n\t{line}")

    def generate_packet_csv(self, generator : collections.Generator):
        with open(f"{self.output_path}{Generator.PACKET_INFIX}{self.postfix}.csv", "w") as file:
            for packets in generator:
                for packet in packets:
                    line = f"{packet.size},{packet.sender},{packet.receiver},{packet.interface_used}," \
                           f"{packet.datetime}\n"
                    file.write(line)
                    print(f"Writing:\n\t{line}")

    def generate_timestamp_pdf(self, generator : collections.Generator):
        pass

    def generate_packet_pdf(self, generator : collections.Generator):
        pass

    def generate_timestamp_graph(self, generator : collections.Generator):
        pass

    def generate_packet_graph(self, generator : collections.Generator):
        pass

    def generate_onefile(self, timestamp_generator : collections.Generator,
                                 packet_generator : collections.Generator):
        # do a first pass check from the packet generator, and if nothing exists, bail doing output for the packets
        pass

    def generate_onefile_verbose(self, timestamp_generator : collections.Generator,
                                 packet_generator : collections.Generator, drop_threshold):
        #do a first pass check from the packet generator, and if nothing exists, bail doing output for the packets
        pass

