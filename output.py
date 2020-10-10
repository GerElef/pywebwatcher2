import collections
from datetime import datetime
from time import time
from matplotlib import pyplot
from matplotlib import rcParams
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

    def get_all_data_points_for_ip_server_combo_from_timestamp(self, chunk, ip, server) -> Tuple[list, list, int]:
        from db.tables import Timeframe
        data = []
        dates = []
        date_lim = 0
        max_data_val = 0

        timestamp : Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver == server:
                data.append(timestamp.ms)
                dates.append(timestamp.datetime)
                if timestamp.ms > max_data_val:
                    max_data_val = timestamp.ms

                if timestamp.limit > date_lim:
                    date_lim = timestamp.limit

        if date_lim < max_data_val:
            lim = date_lim
        else:
            lim = max_data_val

        return data, dates, lim

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
                y, x, ylim = self.get_all_data_points_for_ip_server_combo_from_timestamp(chunk, ip, server_ip)

                if x_format is not None:
                    x = x_format(x)
                if y_format is not None:
                    y = y_format(y)

                plotpoints.append(DataPlotPoint(name, x, y, receiver = server_readable, ylim = ylim))

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
        #https://stackoverflow.com/questions/8270981/in-a-matplotlib-plot-can-i-highlight-specific-x-value-ranges
        from db.tables import Timeframe

        index = 0
        chunk : List[Timeframe]
        for chunk in generator:
            rcParams['figure.figsize'] = (11.7, 8.3)
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
