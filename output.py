from datetime import datetime
from time import time
from matplotlib import pyplot
from matplotlib import rcParams
from typing import List, Callable, Tuple, AnyStr
from typing import Generator as PyGenerator
from db.tables import Packet, Timeframe
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

    def __init__(self, title : AnyStr, x, y, z = None, receiver = None, xlim = None, ylim = None, zlim = None):
        self.title : str = title

        self.x : List = x
        self.y : List = y
        self.z : List = z
        self.r = receiver
        self.xlim : int = xlim
        self.ylim : int = ylim
        self.zlim : int = zlim


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
        self.timestamp_graphs = []
        self.packet_graphs = []

    def start_new_pass(self, output_path):
        self.postfix = int(time())
        self.output_path = output_path + "\\"

        self.plot_count = 0
        self.packet_plot_flag = False
        self.timestamp_plot_flag = False
        self.timestamp_graphs = []
        self.packet_graphs = []

    def close(self):
        #clean up any files / reset all
        pass

    def get_all_ips_from_timestamp(self, chunk: List[Timeframe]) -> List:
        ips = []

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface not in ips:
                ips.append(timestamp.interface)

        return ips

    def get_all_servers_for_ip_from_timestamp(self, chunk: List[Timeframe], ip) -> List:
        servers = []
        servers_return = []

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver not in servers:
                servers.append(timestamp.receiver)

                servers_return.append((timestamp.receiver, timestamp.receiver_readable))

        return servers_return

    def get_all_data_points_for_ip_server_combo_from_timestamp(self, chunk: List[Timeframe],
                                                               ip, server) -> Tuple[list, list, int]:
        data  = []
        dates = []
        maxy  = 1

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver == server:
                data.append(timestamp.ms)
                dates.append(timestamp.datetime)

                if timestamp.limit > timestamp.ms > maxy:
                    maxy = timestamp.ms

        return data, dates, maxy

    def generate_timestamp_data_plot_obj_from(self, chunk: List[Timeframe],
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
                data, dates, ylim = self.get_all_data_points_for_ip_server_combo_from_timestamp(chunk, ip, server_ip)

                if x_format is not None:
                    dates = x_format(dates)
                if y_format is not None:
                    data = y_format(data)

                plotpoints.append(DataPlotPoint(name, dates, data, receiver = server_readable, ylim = ylim))

        return plotpoints

    def get_all_interfaces_from(self, chunk: List[Packet]) -> List:
        interfaces = []

        for packet in chunk:
            if packet.interface_used not in interfaces:
                interfaces.append(packet.interface_used)

        return interfaces

    def format_packet_datetimes_for_interface_from(self, chunk : List[Packet], interface) -> List:
        dates = []

        packet : Packet
        for packet in chunk:
            if packet.interface_used == interface:
                dates.append(packet.datetime.strftime('%M %S %f'))

        return dates

    def get_all_packet_sizes_for_interface_from(self, chunk : List[Packet], interface) -> Tuple[List[int], int]:
        sizes = []
        avg   = 0
        maxy  = 0
        maxy_lower = 0
        ls = len(chunk) #list size

        packet: Packet
        for packet in chunk:
            if packet.interface_used == interface:
                sizes.append(packet.size)
                avg += packet.size/ls
                if maxy < packet.size:
                    maxy = packet.size

                if maxy_lower < packet.size < maxy:
                    maxy_lower = packet.size

        lim = avg * 10

        if maxy_lower > avg * 2:
            lim = maxy_lower

        if maxy > maxy_lower * 2:
            lim = maxy

        return sizes, lim

    def generate_packet_data_plot_obj_from(self, chunk: List[Packet],
                                              x_format:Callable[[List], List] = None,
                                              y_format:Callable[[List], List] = None) -> List[DataPlotPoint]:
        plotpoints = []
        ifaces = self.get_all_interfaces_from(chunk)

        for iface in ifaces:
            dates = self.format_packet_datetimes_for_interface_from(chunk, iface)
            sizes, ylim = self.get_all_packet_sizes_for_interface_from(chunk, iface)

            if x_format is not None:
                dates = x_format(dates)
            if y_format is not None:
                sizes = y_format(sizes)

            plotpoints.append(DataPlotPoint("", dates, sizes, ylim = ylim))

        return plotpoints

    def generate_timestamp_csv(self, generator : PyGenerator[List[Timeframe]]):
        with open(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{self.postfix}.csv", "w") as file:
            for timestamps in generator:
                for timestamp in timestamps:
                    line = f"{timestamp.ms},{timestamp.limit},{timestamp.receiver},{timestamp.receiver_readable}," \
                           f"{timestamp.interface},{timestamp.interface_dead},{timestamp.datetime}\n"
                    file.write(line)
                    print(f"Writing:\n\t{line}")

    def generate_packet_csv(self, generator : PyGenerator[List[Packet]]):
        with open(f"{self.output_path}{Generator.PACKET_INFIX}{self.postfix}.csv", "w") as file:
            for packets in generator:
                for packet in packets:
                    line = f"{packet.size},{packet.sender},{packet.receiver},{packet.interface_used}," \
                           f"{packet.datetime}\n"
                    file.write(line)
                    print(f"Writing:\n\t{line}")

    def generate_timestamp_graph(self, generator : PyGenerator[List[Timeframe]]):
        #https://stackoverflow.com/questions/8270981/in-a-matplotlib-plot-can-i-highlight-specific-x-value-ranges

        index = 0
        chunk : List[Timeframe]
        for chunk in generator:
            rcParams['figure.figsize'] = (11.7, 16.6)
            pyplot.subplots_adjust(hspace=1.5)

            graph_data : List[DataPlotPoint] = self.generate_timestamp_data_plot_obj_from(chunk)

            pltnum = 1
            suptitle = f"{chunk[0].datetime.strftime('%y-%b-%d : %H %M')} - " \
                       f"{chunk[-1].datetime.strftime('%y-%b-%d : %H %M')}"
            for i in range(len(graph_data)):
                data = graph_data[i]
                ax = pyplot.subplot(len(graph_data), 1, pltnum)

                ax.plot(data.x, data.y)
                ax.set_title(data.title)
                ax.set_xlabel("Dates")
                ax.set_ylabel("ms")

                ax.set_ylim((0, data.ylim))
                pyplot.suptitle(suptitle)

                pltnum += 1
            print(f"Outputting...{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg")
            pyplot.savefig(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg",
                           bbox_inches="tight", dpi = 300)
            pyplot.close()

            self.timestamp_graphs.append(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg")

            index += 1

        self.timestamp_plot_flag = True

    def generate_packet_graph(self, generator : PyGenerator[List[Packet]]):
        #do stuff
        index = 0

        chunk : List[Packet]
        for chunk in generator:
            rcParams['figure.figsize'] = (11.7, 16.6)
            pyplot.subplots_adjust(hspace=1.5)

            graph_data : List[DataPlotPoint] = self.generate_packet_data_plot_obj_from(chunk)

            pltnum = 1
            suptitle = f"{chunk[0].datetime.strftime('%y-%b-%d : %H %M')} - " \
                       f"{chunk[-1].datetime.strftime('%y-%b-%d : %H %M')}"

            for i in range(len(graph_data)):
                data = graph_data[i]
                ax = pyplot.subplot(len(graph_data), 1, pltnum)

                ax.plot(data.x, data.y)
                ax.set_title(data.title)
                ax.set_xlabel("Dates")
                ax.set_ylabel("packet size")

                ax.set_ylim((0, data.ylim))
                pyplot.suptitle(suptitle)

                pltnum += 1

            print(f"Outputting...{Generator.PACKET_INFIX}{index}{self.postfix}.jpg")
            pyplot.savefig(f"{self.output_path}{Generator.PACKET_INFIX}{index}{self.postfix}.jpg",
                           bbox_inches="tight", dpi=300)
            pyplot.close()

            self.packet_graphs.append(f"{self.output_path}{Generator.PACKET_INFIX}{index}{self.postfix}.jpg")

            index += 1

        self.packet_plot_flag = True

    def generate_timestamp_pdf(self, generator : PyGenerator[List[Timeframe]]):
        pass

    def generate_packet_pdf(self, generator : PyGenerator[List[Packet]]):
        pass

    def generate_onefile(self, timestamp_generator : PyGenerator[List[Timeframe]],
                                 packet_generator : PyGenerator[List[Packet]]):
        pass

    def generate_onefile_verbose(self, timestamp_generator : PyGenerator[List[Timeframe]],
                                 packet_generator : PyGenerator[List[Packet]], drop_threshold):
        pass
