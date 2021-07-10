import os
import pickle as pl
from datetime import datetime
from time import time
from typing import Generator as PyGenerator
from typing import List, Callable, Tuple, AnyStr

from fpdf import FPDF
from matplotlib import pyplot
from matplotlib import rcParams

from db.tables import Packet, Timeframe


# TODO implement anon dictionary and matching
# TODO graph split to different graph per 5 subplots

# TODO onefile

# TODO verbose_onefile with relaxed threshold
# TODO should dump pdf with graph in landscape (not portrait)
# TODO should report minimum time of continuous internet record
# TODO should report maximum time of continuous internet record
# TODO should report average time of continuous internet record
# TODO maybe have a few nice graphs for averages, and a normal distribution graph

# TODO make everything multiprocessed with a pool of processes as many as the computer's cores
#  when the pool is filled, wait for a process to end then create a new one for a new chunk, ad naseum
#  when the chunks end wait for all the processes to finish
#  make all IO-bound activities with threads on these subprocesses
#  possibly, make it flag activated


class DataPlotPoint:

    def __init__(self, title: AnyStr, x, y, z=None, receiver=None, xlim=None, ylim=None, zlim=None):
        self.title: str = title

        self.x: List = x
        self.y: List = y
        self.z: List = z
        self.r = receiver
        self.xlim: int = xlim
        self.ylim: int = ylim
        self.zlim: int = zlim

    def __str__(self):
        return f"Title: {self.title}\nReceiver: {self.r}\n\tX axis: {self.x}\n\tY axis: {self.y}\n\tZ axis: {self.z}"


class Generator:
    TIMESTAMP_INFIX = "TIMESTAMP"
    PACKET_INFIX = "PACKET"

    def __init__(self):
        self.output_path = None
        self.postfix = 0

        self.anonymize = False
        self.packet_plot_flag = False
        self.timestamp_plot_flag = False
        self.timestamp_graphs = []
        self.packet_graphs = []

    def start_new_pass(self, output_path, anon):
        self.postfix = datetime.fromtimestamp(time()).strftime("%Y %m %d %H %M %S").replace(" ", "-")
        self.output_path = output_path + "\\"
        self.anonymize = anon

        try:
            newdir = f"{self.output_path}DUMP-{self.postfix}"
            os.mkdir(newdir)
            self.output_path = newdir + "\\"
            self.postfix = ""  # get rid of the postfix, we don't need it as there wont be a namespace collision
        except OSError:
            # silently ignore this, we don't have rights to create subdirectories on root
            pass

        self.packet_plot_flag = False
        self.timestamp_plot_flag = False
        self.timestamp_graphs = []
        self.packet_graphs = []

    def close(self):
        # clean up any files / reset all
        pass

    def get_all_ips_from_timestamp(self, chunk: List[Timeframe]) -> List:
        ips = []

        timestamp: Timeframe
        for timestamp in chunk:
            if timestamp.interface not in ips:
                ips.append(timestamp.interface)

        return ips

    def get_all_servers_for_ip_from_timestamp(self, chunk: List[Timeframe], ip) -> List:
        servers = []
        servers_return = []

        timestamp: Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver not in servers:
                servers.append(timestamp.receiver)

                servers_return.append((timestamp.receiver, timestamp.receiver_readable))

        return servers_return

    def get_all_data_points_for_ip_server_combo_from_timestamp(self, chunk: List[Timeframe],
                                                               ip, server) -> Tuple[List, List, int]:
        data = []
        dates = []
        maxy = 1

        timestamp: Timeframe
        for timestamp in chunk:
            if timestamp.interface == ip and timestamp.receiver == server:
                data.append(timestamp.ms)
                dates.append(timestamp.datetime)

                if timestamp.limit > timestamp.ms > maxy:
                    maxy = timestamp.ms

        return data, dates, maxy

    def generate_timestamp_data_plot_obj_from(self, chunk: List[Timeframe],
                                              x_format: Callable[[List], List] = None,
                                              y_format: Callable[[List], List] = None) -> List[DataPlotPoint]:
        ips: List = self.get_all_ips_from_timestamp(chunk)
        servers: List = []

        plotpoints: List[DataPlotPoint] = []

        for ip in ips:
            servers.append(self.get_all_servers_for_ip_from_timestamp(chunk, ip))

        # ips and servers are parallel lists, for each val in ip, a list of servers exists in servers[[]]
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

                plotpoints.append(DataPlotPoint(name, dates, data, receiver=server_readable, ylim=ylim))

        return plotpoints

    def get_all_interfaces_from(self, chunk: List[Packet]) -> List:
        interfaces = []

        for packet in chunk:
            if packet.interface_used not in interfaces:
                interfaces.append(packet.interface_used)

        return interfaces

    def format_packet_datetimes_for_interface_from(self, chunk: List[Packet], interface) -> List:
        dates = []

        packet: Packet
        for packet in chunk:
            if packet.interface_used == interface:
                dates.append(packet.datetime.strftime('%M %S %f'))

        return dates

    def get_all_packet_sizes_for_interface_from(self, chunk: List[Packet], interface) -> Tuple[List[int], int]:
        sizes = []
        avg = 0
        maxy = 0
        maxy_lower = 0
        ls = len(chunk)  # list size

        packet: Packet
        for packet in chunk:
            if packet.interface_used == interface:
                sizes.append(packet.size)
                avg += packet.size / ls
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
                                           x_format: Callable[[List], List] = None,
                                           y_format: Callable[[List], List] = None) -> List[DataPlotPoint]:
        plotpoints = []
        ifaces = self.get_all_interfaces_from(chunk)

        for iface in ifaces:
            dates = self.format_packet_datetimes_for_interface_from(chunk, iface)
            sizes, ylim = self.get_all_packet_sizes_for_interface_from(chunk, iface)

            if x_format is not None:
                dates = x_format(dates)
            if y_format is not None:
                sizes = y_format(sizes)

            plotpoints.append(DataPlotPoint("", dates, sizes, ylim=ylim))

        return plotpoints

    def generate_timestamp_csv(self, generator: PyGenerator[List[Timeframe], None, None]):
        print("Generating packet csv(s)...")
        lc = 1
        with open(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{self.postfix}.csv", "w") as file:
            for timestamps in generator:
                for timestamp in timestamps:
                    line = f"{timestamp.ms},{timestamp.limit},{timestamp.receiver},{timestamp.receiver_readable}," \
                           f"{timestamp.interface},{timestamp.interface_dead},{timestamp.datetime}\n"
                    file.write(line)
                    print(f"{lc}Writing:\t{line}")
                    lc += 1

    def generate_packet_csv(self, generator: PyGenerator[List[Packet], None, None]):
        print("Generating packet csv(s)...")
        lc = 1
        with open(f"{self.output_path}{Generator.PACKET_INFIX}{self.postfix}.csv", "w") as file:
            for packets in generator:
                for packet in packets:
                    line = f"{packet.size},{packet.sender},{packet.receiver},{packet.interface_used}," \
                           f"{packet.datetime}\n"
                    file.write(line)
                    print(f"{lc}Writing:\t{line}")
                    lc += 1

    def generate_timestamp_graph(self, generator: PyGenerator[List[Timeframe], None, None],
                                 pickle_dump=False):
        print("Generating timestamp graph(s)...")
        index = 0
        chunk: List[Timeframe]
        for chunk in generator:
            rcParams['figure.figsize'] = (11.7, 16.6)
            pyplot.subplots_adjust(hspace=1.5)

            graph_data: List[DataPlotPoint] = self.generate_timestamp_data_plot_obj_from(chunk)
            ax = None
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
            # I kid you not, he turns himself into a pickle.
            if pickle_dump and ax is not None:
                print(f"Dumping pickle...{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.p")
                pl.dump(ax, open(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.p", 'wb'))

            print(f"Outputting...{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg")
            pyplot.savefig(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg",
                           bbox_inches="tight", dpi=300)
            pyplot.close()

            self.timestamp_graphs.append(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{index}{self.postfix}.jpg")

            index += 1

        self.timestamp_plot_flag = True

    def generate_packet_graph(self, generator: PyGenerator[List[Packet], None, None],
                              pickle_dump=False):
        print("Generating packet graph(s)...")
        # do stuff
        index = 0

        chunk: List[Packet]
        for chunk in generator:
            rcParams['figure.figsize'] = (11.7, 16.6)
            pyplot.subplots_adjust(hspace=1.5)

            graph_data: List[DataPlotPoint] = self.generate_packet_data_plot_obj_from(chunk)
            ax = None
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
            # I kid you not, he turns himself into a pickle.
            if pickle_dump and ax is not None:
                print(f"Dumping pickle...{Generator.PACKET_INFIX}{index}{self.postfix}.p")
                pl.dump(ax, open(f"{self.output_path}{Generator.PACKET_INFIX}{index}{self.postfix}.p", 'wb'))

            print(f"Outputting...{Generator.PACKET_INFIX}{index}{self.postfix}.jpg")
            pyplot.savefig(f"{self.output_path}{Generator.PACKET_INFIX}{index}{self.postfix}.jpg",
                           bbox_inches="tight", dpi=300)
            pyplot.close()

            self.packet_graphs.append(f"{self.output_path}{Generator.PACKET_INFIX}{index}{self.postfix}.jpg")

            index += 1

        self.packet_plot_flag = True

    def get_new_pdf_instance(self):
        pdf = FPDF()
        pdf.set_font('Courier', '', 14)
        pdf.add_page()
        return pdf

    def generate_timestamp_pdf(self, generator: PyGenerator[List[Timeframe], None, None]):
        print("Generating timestamp pdf(s)...")
        pdf = self.get_new_pdf_instance()
        lines = 0
        prev_line = 0
        closed = False

        for chunk in generator:
            local_lines = 0

            data_list = self.generate_timestamp_data_plot_obj_from(chunk)
            # add title here
            print(f"Got chunk, data list {len(data_list)}")
            for data in data_list:
                pdf.multi_cell(0, 12, data.title, 1, "C")
                # x list holds date vals
                # y list holds ms vals
                for ms, date in enumerate(zip(data.y, data.x)):
                    pdf.multi_cell(0, 8, f"{ms} ms, {date}", 1, "C")
                    lines += 1
                    local_lines += 1
            closed = False

            if lines > 50000:
                print("Wrote too many lines in one pdf -- writing and starting on new file...")
                pdf.close()

                print(f"Saving pdf... {Generator.TIMESTAMP_INFIX}{self.postfix}_{prev_line + 1}_{prev_line + lines}")
                pdf.output(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{self.postfix}_"
                           f"{prev_line + 1}_{prev_line + lines}.pdf", "F")

                # update counters
                prev_line += lines
                lines = 0
                closed = True

                # reset to new instance
                pdf = self.get_new_pdf_instance()

            print("Wrote to pdf, moving to next chunk...")

        if not closed:
            print(f"Closing output stream having written {lines} lines.")
            pdf.close()

            print(f"Outputting {self.output_path}{Generator.TIMESTAMP_INFIX}{self.postfix}_{prev_line + 1}_{lines}.pdf"
                  f" with {lines} lines.")
            pdf.output(f"{self.output_path}{Generator.TIMESTAMP_INFIX}{self.postfix}_"
                       f"{prev_line + 1}_{prev_line + lines}.pdf", "F")

    def generate_packet_pdf(self, generator: PyGenerator[List[Packet], None, None]):
        print("Generating packet pdf(s)...")
        pdf = self.get_new_pdf_instance()
        lines = 0
        prev_line = 0
        closed = False

        for chunk in generator:
            local_lines = 0

            data_list = self.generate_packet_data_plot_obj_from(chunk)
            # add title here
            print(f"Got chunk, data list {len(data_list)}")
            for data in data_list:
                pdf.multi_cell(0, 12, data.title, 1, "C")
                # x list holds date vals
                # y list holds ms vals
                for ms, date in enumerate(zip(data.y, data.x)):
                    pdf.multi_cell(0, 8, f"{ms} ms, {date}", 1, "C")
                    lines += 1
                    local_lines += 1
            closed = False

            if lines > 50000:
                print("Wrote too many lines in one pdf -- writing and starting on new file...")
                pdf.close()

                print(f"Saving pdf... {Generator.PACKET_INFIX}{self.postfix}_{prev_line + 1}_{prev_line + lines}")
                pdf.output(f"{self.output_path}{Generator.PACKET_INFIX}{self.postfix}_"
                           f"{prev_line + 1}_{prev_line + lines}.pdf", "F")

                # update counters
                prev_line += lines
                lines = 0
                closed = True

                # reset to new instance
                pdf = self.get_new_pdf_instance()

            print("Wrote to pdf, moving to next chunk...")

        if not closed:
            print(f"Closing output stream having written {lines} lines.")
            pdf.close()

            print(f"Outputting {self.output_path}{Generator.PACKET_INFIX}{self.postfix}_{prev_line + 1}_{lines}.pdf"
                  f" with {lines} lines.")
            pdf.output(f"{self.output_path}{Generator.PACKET_INFIX}{self.postfix}_"
                       f"{prev_line + 1}_{prev_line + lines}.pdf", "F")

    def generate_onefile(self, timestamp_generator: PyGenerator[List[Timeframe], None, None],
                         packet_generator: PyGenerator[List[Packet], None, None]):
        pass

    def generate_onefile_verbose(self, timestamp_generator: PyGenerator[List[Timeframe], None, None],
                                 packet_generator: PyGenerator[List[Packet], None, None], drop_threshold):
        pass

    def open_saved_pickles(self, pickles: List[AnyStr]):
        # I'm pickle riiiiiiiiiick
        for pickle_rick in pickles:
            ax = pl.load(open(pickle_rick, 'rb'))
            ax.figure.show()
            input("Press Enter to continue.")
