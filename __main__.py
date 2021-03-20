from math import inf
from sys import argv
from threading import Thread, Event
from time import sleep

import pygame

from db.dao import Dao
from net_test.nettest import StabilityTester
from net_test.sniffer import Sniffer
from user_io.PingScene import PingScene
from user_io.flag_handler import CMDHandler
from user_io.output import Generator
from user_io.pygameplotter import Engine


def get_interfaces():
    ifaces = Sniffer.get_interface_list()

    interfaces = [[], []]
    for i in range(len(ifaces[0])):
        if ifaces[3][i] is None:
            continue

        interfaces[0].append(ifaces[0][i])
        interfaces[1].append(ifaces[3][i])

    return interfaces


def get_record_count(dao, date, record_type):
    # e.g. if YYYY was given,
    ts_count = dao.get_timestamp_number_of_records_in(date, record_type)
    pk_count = dao.get_packet_number_of_records_in(date, record_type)
    return ts_count, pk_count


def start_tester(iface, evt, loop_times, dp_scene: PingScene):
    tester = StabilityTester(iface)
    if loop_times == inf:
        Thread(target=tester.ping_with_event, args=(evt, dp_scene,)).start()
    else:
        Thread(target=tester.ping_with_event_counter, args=(evt, loop_times, dp_scene)).start()


def start_sniffer(iface, ifaceipv4, evt, count):
    sniffer = Sniffer(iface, ifaceipv4, evt, packet_count=count)
    Thread(target=sniffer.start_sniffing).start()


if __name__ == '__main__':
    handler = CMDHandler()
    handler.parse_sys_args(argv)
    handler.post_processing(get_interfaces())

    # if we encounter any exceptions, bail
    if handler.exceptions:
        for e in handler.exceptions:
            print(e.__str__() + "\n")
        exit(0)

    any_special_flag = handler.RECORDS_FLAG or handler.PICKLE_FOUND or handler.SAVE_FOUND
    any_output_flag = handler.PICKLE_FOUND or handler.SAVE_FOUND

    if handler.RECORDS_FLAG:
        # if we found records flag, for each MM/DD/HH/MM/SS (depending on if YYYY/MM/DD/HH/MM was given),
        # print number of unique records and then exit
        tsc, pkc = get_record_count(Dao(), handler.RECORDS_DATE, handler.RECORDS_TYPE)
        print(f"Found {tsc} timestamps and {pkc} sniff records in the given date.")

    if any_output_flag:
        generator = Generator()

    if handler.PICKLE_FOUND:
        # if cmd handler found any pickles as an arg, open
        # noinspection PyUnboundLocalVariable
        generator.open_saved_pickles(handler.pickles)

    if handler.SAVE_FOUND:
        # do stuff for output here
        # noinspection PyUnboundLocalVariable
        generator.start_new_pass(handler.OUTPUT_PATH, handler.ANON_FLAG)
        d = Dao()

        if handler.CSV_FLAG:
            # generate csv
            print("Generating CSV...")
            generator.generate_timestamp_csv(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            generator.generate_packet_csv(
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                  interval=handler.DATA_CHUNK)
            )
            print("Done generating CSV!")

        if handler.PDF_FLAG:
            # generate pdf
            print("Generating PDF...")
            generator.generate_timestamp_pdf(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            generator.generate_packet_pdf(
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                  interval=handler.DATA_CHUNK)
            )
            print("Done generating PDF!")

        if handler.GRAPH_FLAG:
            # generate graph
            print("Generating graph...")
            generator.generate_timestamp_graph(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK),
                pickle_dump=handler.PICKLE_FLAG
            )
            generator.generate_packet_graph(
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                  interval=handler.DATA_CHUNK),
                pickle_dump=handler.PICKLE_FLAG
            )
            print("Done generating graph!")

        if handler.ONEFILE_FLAG:
            # generate non-descriptive onefile with graph
            print("Generating onefile...")
            generator.generate_onefile(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK),
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                  interval=handler.DATA_CHUNK)
            )
            print("Done generating onefile!")

        if handler.VERBOSE_ONEFILE_FLAG:
            # generate descriptive onefile with graph
            print("Generating verbose onefile...")
            generator.generate_onefile_verbose(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK),
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                  interval=handler.DATA_CHUNK),
                handler.DROP_THRESHOLD
            )
            print("Done generating verbose onefile!")

        generator.close()
        # then exit

    if any_special_flag:
        exit(0)

    StabilityTester.UPPER_LIMIT = int(handler.SLEEP_TIME * 1000)
    StabilityTester.SLEEP_TIME = handler.SLEEP_TIME

    Sniffer.IP_FILTER = handler.IP_FILTER

    ping_scene = PingScene(handler.SLEEP_TIME, StabilityTester.UPPER_LIMIT,
                           title=f"Interface {handler.INTERFACE_IPV4 if handler.INTERFACE_IPV4 else 'dynamic'}",
                           timer=True)
    engine = Engine([ping_scene])

    tester_event = Event()
    start_tester(handler.INTERFACE_IPV4, tester_event, handler.LOOP_TIMES, ping_scene)

    scapy_event = Event()
    if handler.SNIFF_FLAG:
        start_sniffer(handler.INTERFACE_READABLE, handler.INTERFACE_IPV4, scapy_event, handler.PACKET_COUNT)

    try:
        while True:
            if engine.is_shut_down:
                raise KeyboardInterrupt()
            engine.main_loop()
            sleep(0.03)  # ~40 frames a second
    except KeyboardInterrupt:
        print("Shutting down threads...")
        tester_event.set()
        scapy_event.set()
    finally:
        pygame.quit()
        exit(0)
