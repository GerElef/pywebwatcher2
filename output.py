import collections
from datetime import datetime
from time import time
from matplotlib import pyplot
from typing import List, Callable, Tuple, AnyStr
#TODO pdf

#TODO graph with matplotlib
#TODO graph for each IP, for each chunk each time. Keep track of each IP each time. (do not add on filename)
# None val should be accounted

#TODO onefile

#TODO verbose_onefile with relaxed threshold
#TODO should dump pdf with graph in landscape (not portrait)
#TODO should report minimum time of continuous internet record
#TODO should report maximum time of continuous internet record
#TODO should report average time of continuous internet record

class DataPlotPoint:

    def __init__(self, title : AnyStr, x, y, z = None, receiver = None):
        self.title : str = title

        self.x : List = x
        self.y : List = y
        self.z : List = z
        self.r = receiver

    def __str__(self):
        return f"Title: {self.title}\nReceiver: {self.r}\n\tX axis: {self.x}\n\tY axis: {self.y}\n\tZ axis: {self.z}"

class Generator:
    TIMESTAMP_INFIX = "TIMESTAMP"
    PACKET_INFIX    = "PACKET"

    def __init__(self):
        #self.generator = generator
        self.output_path = None
        self.postfix = 0

        self.packet_plot_flag = False
        self.timestamp_plot_flag = False
        self.graphs = []

    def start_new_pass(self, output_path):
        self.postfix = int(time())
        self.output_path = output_path + "\\"

        self.plot_count = 0
        self.packet_plot_flag = False
        self.timestamp_plot_flag = False
        self.graphs = []

    def close(self):
        #clean up any files / reset all
        pass

    def get_all_ips_from_timestamp(self, chunk) -> List:
        from db.tables import Timeframe
        ips = []

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface not in ips:
                ips.append(timestamp.interface)

        return ips

    def get_all_servers_for_ip_from_timestamp(self, chunk, ip) -> List:
        from db.tables import Timeframe
        servers = []
        servers_return = []

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver not in servers:
                servers.append(timestamp.receiver)

                servers_return.append((timestamp.receiver, timestamp.receiver_readable))

        return servers_return

    def get_all_data_points_for_ip_server_combo_from_timestamp(self, chunk, ip, server) -> Tuple[list, list]:
        from db.tables import Timeframe
        data = []
        dates = []

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver == server:
                data.append(timestamp.ms)
                dates.append(timestamp.datetime)

        return data, dates

    def generate_timestamp_data_plot_obj_from(self, chunk,
                                              x_format:Callable[[List], List] = None,
                                              y_format:Callable[[List], List] = None) -> List[DataPlotPoint]:
        ips : List = self.get_all_ips_from_timestamp(chunk)
        servers : List = []

        plotpoints : List[DataPlotPoint] = []

        for ip in ips:
            servers.append(self.get_all_servers_for_ip_from_timestamp(chunk, ip))

        #ips and servers are parallel lists, for each val in ip, a list of servers exists in servers[[]]
        for i in range(len(ips)):
            for server_tuple in servers[i]:
                ip = ips[i]
                server_ip = server_tuple[0]
                server_readable = server_tuple[1]

                name = f"Interface {ip if ip is not None else 'unknown'} server {server_readable}"
                x, y = self.get_all_data_points_for_ip_server_combo_from_timestamp(chunk, ip, server_ip)

                if x_format is not None:
                    x = x_format(x)
                if y_format is not None:
                    y = y_format(y)

                plotpoints.append(DataPlotPoint(name, x, y, receiver = server_readable))

        return plotpoints

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

    def generate_timestamp_graph(self, generator : collections.Generator):
        #do stuff
        index = 0
        for chunk in generator:
            graph_data = self.generate_timestamp_data_plot_obj_from(chunk)

            #fig, axes = pyplot.subplots(len(ips), 1, constrained_layout = True, figsize = (11.7,8.3))
            #second pass, for each plot plot ip for each server
            #for i in range(len(ips)):
            #    for j in range(len(ips_data[i])):
            #        #plot data, add to legend
            #        print("#########################################")
            #        print(f"Plotting {ips[i]}")
            #        if len(ips) == 1:
            #            axes.plot(ips_dates[i][j], ips_data[i][j], linewidth = "0.6")
            #        else:
            #            axes[i].plot(ips_dates[i][j], ips_data[i][j], linewidth = "0.6")
            #    print("Setting misc...")
            #    if len(ips) == 1:
            #        axes.set_title(f"IP {ips[i] if ips[i] is not None else 'Dynamic'}")
            #        axes.set_xlabel("Dates (YYYY-MM-DD HH-MM-SS)")
            #        axes.set_ylabel("Ping (ms)")
            #        axes.set_ylim((0, maxy))
            #        axes.legend(receivers[i])
            #    else:
            #        axes[i].set_title(f"IP {ips[i] if ips[i] is not None else 'Dynamic'}")
            #        axes[i].set_xlabel("Dates (YYYY-MM-DD HH-MM-SS)")
            #        axes[i].set_ylabel("Ping (ms)")
            #        axes[i].ylim((0, maxy))
            #        axes[i].legend(receivers[i])
            #fig.suptitle("Ping Server(s) Results")
            #print(f"Outputting...{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg")
            #fig.savefig(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg",
            #            bbox_inches="tight", dpi = 150)
            #pyplot.close(fig)
            #self.graphs.append(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg")

        self.timestamp_plot_flag = True

    def generate_packet_graph(self, generator : collections.Generator):
        #do stuff
        self.packet_plot_flag = True

    def generate_timestamp_pdf(self, generator : collections.Generator):
        pass

    def generate_packet_pdf(self, generator : collections.Generator):
        pass

    def generate_onefile(self, timestamp_generator : collections.Generator,
                                 packet_generator : collections.Generator):
        pass

    def generate_onefile_verbose(self, timestamp_generator : collections.Generator,
                                 packet_generator : collections.Generator, drop_threshold):
        pass
