from math import inf
from sys import argv
from threading import Thread, Event
from time import sleep

from db.dao import Dao
from flag_handler import CMDHandler
from net_test.nettest import StabilityTester
from net_test.sniffer import Sniffer
from output import Generator


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
    count = dao.get_timestamp_number_of_records_in(date, record_type)
    return count

def start_tester(iface, evt, loop_times):
    tester = StabilityTester(iface)
    if loop_times == inf:
        Thread(target=tester.ping_with_event, args=(evt,)).start()
    else:
        Thread(target=tester.ping_with_event_counter, args=(evt, loop_times,)).start()

def start_sniffer(iface, ifaceipv4, evt, count):
    sniffer = Sniffer(iface, ifaceipv4, evt, packet_count = count)
    Thread(target=sniffer.start_sniffing).start()

#TODO add exporter and finalize joining of CMD args

if __name__ == '__main__':
    handler = CMDHandler()
    handler.parse_sys_args(argv)
    handler.post_processing(get_interfaces())

    #if we encounter any exceptions, bail
    if handler.exceptions:
        for e in handler.exceptions:
            print(e.__str__() + "\n")
        exit(0)

    if handler.RECORDS_FLAG:
        #if we found records flag, for each MM/DD/HH/MM/SS (depending on if YYYY/MM/DD/HH/MM was given),
        # print number of unique records and then exit
        print(f"Found {get_record_count(Dao(), handler.RECORDS_DATE, handler.RECORDS_TYPE)} "
              f"records in the given date.")
        exit(0)

    if handler.SAVE_FOUND:
        #do stuff for output here
        generator = Generator()
        generator.start_new_pass(handler.OUTPUT_PATH)
        d = Dao()

        if handler.CSV_FLAG:
            #generate csv
            print("Generating CSV...")
            generator.generate_timestamp_csv(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            generator.generate_packet_csv(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            print("Done generating CSV!")

        if handler.PDF_FLAG:
            #generate pdf
            print("Generating PDF...")
            generator.generate_timestamp_pdf(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            generator.generate_packet_pdf(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            print("Done generating PDF!")

        if handler.GRAPH_FLAG:
            #generate graph
            print("Generating graph...")
            generator.generate_timestamp_graph(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            generator.generate_packet_graph(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            print("Done generating graph!")

        if handler.ONEFILE_FLAG:
            #generate non-descriptive onefile with graph
            print("Generating onefile...")
            generator.generate_onefile(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK),
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK)
            )
            print("Done generating onefile!")

        if handler.VERBOSE_ONEFILE_FLAG:
            #generate descriptive onefile with graph
            print("Generating verbose onefile...")
            generator.generate_onefile_verbose(
                d.get_all_timestamp_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK),
                d.get_all_packet_records_in_dates(handler.SAVE_STARTDATE, handler.SAVE_ENDDATE,
                                                     interval=handler.DATA_CHUNK),
                handler.DROP_THRESHOLD
            )
            print("Done generating verbose onefile!")

        #then exit
        exit(0)

    StabilityTester.UPPER_LIMIT = int(handler.SLEEP_TIME * 1000)
    StabilityTester.SLEEP_TIME = handler.SLEEP_TIME

    Sniffer.IP_FILTER = handler.IP_FILTER

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