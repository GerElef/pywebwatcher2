# Flags:
# -i <interface ip> -dynamic -l <loop times> -t <sleep time> -c <packet count>
# -o <output path> -f <comma separated ips> -sniff -records <YYYY,MM,DD,HH,MM>
# -save <startdate, in YYYY,MM,DD,HH,MM,SS> <enddate, in YYYY,MM,DD,HH,MM,SS>
# -csv, -pdf, -graph, -onefile, -verbose_onefile -relaxed <drop threshold>
# -data <int 0> -anon -pickle
# to open pickle files just drag and drop all .p files or pass the files as arguments
from datetime import datetime, timedelta
from math import inf


class InvalidParameterError(Exception):
    def __init__(self, flag, value, description: str, str_keyword: str = "parameter"):
        self.flag = flag
        self.val = value
        self.desc = description
        self.str_keyword = str_keyword

    def __str__(self):
        return f"Invalid {self.str_keyword} {self.flag}, with value {self.val}.\nDescription: {self.desc}"


class InvalidFlagError(InvalidParameterError):
    def __init__(self, flag, value, description: str):
        super().__init__(flag, value, description, str_keyword="flag")


class InvalidValueError(InvalidParameterError):
    pass


class InvalidLengthError(InvalidParameterError):
    pass


class InvalidFormatException(Exception):
    def __init__(self, args_404: list, description: str):
        self.args_404 = args_404
        self.desc = description

    def __str__(self):
        formatted_args_404 = ""

        index = 0
        for arg in self.args_404:
            formatted_args_404 += arg
            index += 1

            if index < len(self.args_404):
                formatted_args_404 += ","

        return f"Didn't find {formatted_args_404}.\nDescription: {self.desc}"


class CMDHandler:
    INTERFACE_TO_USE_ARG = "-I"
    LOOP_TIMES_ARG = "-L"
    SLEEP_TIME_ARG = "-T"
    SNIFF_ARG = "-SNIFF"
    IP_FORMAT_ARG = "-F"
    PACKET_COUNT_ARG = "-C"
    RECORDS_ARG = "-RECORDS"
    SAVE_FLAG_ARG = "-SAVE"
    OUTPUT_PATH_ARG = "-O"
    CSV_OUT_ARG = "-CSV"
    PDF_OUT_ARG = "-PDF"
    GRAPH_OUT_ARG = "-GRAPH"
    ONEFILE_OUT_ARG = "-ONEFILE"
    VERBOSE_ONEFILE_OUT_ARG = "-VERBOSE_ONEFILE"
    RELAXED_ARG = "-RELAXED"
    KALM_ARG = "-KALM"
    DYNAMIC_ARG = "-DYNAMIC"
    DATA_ARG = "-DATA"
    ANON_ARG = "-ANON"
    PICKLE_ARG = "-PICKLE"

    RECORDS_ARG_TYPE_YEAR_MAGIC_CONSTANT = 1
    RECORDS_ARG_TYPE_MONTH_MAGIC_CONSTANT = 2
    RECORDS_ARG_TYPE_DAY_MAGIC_CONSTANT = 3
    RECORDS_ARG_TYPE_HOUR_MAGIC_CONSTANT = 4
    RECORDS_ARG_TYPE_MINUTE_MAGIC_CONSTANT = 5

    VALID_FLAGS = [INTERFACE_TO_USE_ARG, LOOP_TIMES_ARG, SLEEP_TIME_ARG, SNIFF_ARG, IP_FORMAT_ARG, PACKET_COUNT_ARG,
                   SAVE_FLAG_ARG, OUTPUT_PATH_ARG, CSV_OUT_ARG, PDF_OUT_ARG, GRAPH_OUT_ARG, RECORDS_ARG, DYNAMIC_ARG,
                   ONEFILE_OUT_ARG, VERBOSE_ONEFILE_OUT_ARG, RELAXED_ARG, KALM_ARG, DATA_ARG, ANON_ARG, PICKLE_ARG]

    SPECIAL_OUTPUT_FLAGS = [CSV_OUT_ARG, PDF_OUT_ARG, GRAPH_OUT_ARG]

    ONE_FILE_OUTPUT_FLAGS = [ONEFILE_OUT_ARG, VERBOSE_ONEFILE_OUT_ARG]

    def __init__(self):
        self.INTERFACE_IPV4 = None
        self.INTERFACE_READABLE = None
        self.DYNAMIC_FLAG = False

        self.PACKET_COUNT = inf
        self.LOOP_TIMES = inf
        self.SLEEP_TIME = 1

        self.SAVE_FOUND = False
        self.OUTPUT_FOUND = False
        self.DATA_CHUNK_FOUND = False
        self.PICKLE_FOUND = False

        self.SAVE_STARTDATE = None
        self.SAVE_ENDDATE = None
        self.OUTPUT_PATH = None

        self.IP_FILTER = None

        self.RECORDS_FLAG = False
        self.RECORDS_DATE = None
        self.RECORDS_TYPE = None

        self.PICKLE_FLAG = False
        self.ANON_FLAG = False
        self.SNIFF_FLAG = False
        self.CSV_FLAG = False
        self.PDF_FLAG = False
        self.GRAPH_FLAG = False
        self.ONEFILE_FLAG = False

        self.VERBOSE_ONEFILE_FLAG = False
        self.DROP_THRESHOLD = 1
        self.DATA_CHUNK = 10000

        self.pickles = []
        self.exceptions = []

    def arg_has_value(self, arg: str, arg_index: int, argl: list,
                      offset: int = 1, type_check: type = None, val_check=None):
        if arg_index + offset < len(argl):
            val = argl[arg_index + offset]
            if type_check is not None:
                try:
                    type_check(val)
                except Exception as e:
                    raise InvalidValueError(arg, val, "Found value, but was of different type "
                                                      f"than expected. Error {e}")

            if val_check is not None:
                if val != val_check:
                    raise InvalidValueError(arg, val, "Found value, but was of different value than expected.")

            return True

        raise InvalidLengthError(arg, "List length smaller than expected", "Was looking for argument of type "
                                                                           f"{type_check}, at position "
                                                                           f"{arg_index + offset} but found "
                                                                           f"end of list")

    def arg_is_comma_separated_list(self, arg: str, length: int):
        if len(arg.split(",")) != length:
            raise InvalidValueError(None, arg, f"Wanted comma separated list of "
                                               f"length {length} got {len(arg.split(','))}")
        return True

    def arg_sanity_check(self, flag: str, arg: str, sanity_check, fail_check_descr):
        if not sanity_check(arg):
            raise InvalidValueError(flag, arg, fail_check_descr)

        return True

    # noinspection PyTypeChecker
    def convert_list_datetime(self, date_val_list: list[int], flag: str):

        def destructor(y=1, mm=1, d=1, h=0, m=0, s=0):
            return datetime(int(y), int(mm), int(d), int(h), int(m), int(s), 000)

        if 0 < len(date_val_list) < 6:
            date = destructor(*date_val_list)
        else:
            raise InvalidFormatException(
                [flag],
                f"Unexpected comma separated length {len(date_val_list)} on arg for flag {flag}"
            )


        return date

    def parse_sys_args(self, argv: list):
        def int_check(x):
            return int(x) > 0

        def length_check(lst):
            return 1 <= len(lst.split(',')) <= 6

        index = 0
        args_skip = 1  # skip the first argument because it's the script path lulw
        try:
            for arg in argv:
                if args_skip > 0:
                    args_skip -= 1
                    index += 1
                    continue

                # main stuff here
                upper_arg = arg.upper()

                if upper_arg not in CMDHandler.VALID_FLAGS:
                    # if arg ends in .p (pickle file)
                    if len(arg) > 2 and arg[len(arg) - 2: len(arg)] == ".p":
                        self.PICKLE_FOUND = True
                        self.pickles.append(arg)
                        continue
                    else:
                        raise InvalidFlagError(arg, None, f"Encountered non valid flag {arg}.")

                if upper_arg == CMDHandler.INTERFACE_TO_USE_ARG:
                    if self.arg_has_value(arg, index, argv):
                        self.INTERFACE_IPV4 = argv[index + 1]
                        args_skip += 1

                if upper_arg == CMDHandler.LOOP_TIMES_ARG:
                    if self.arg_has_value(arg, index, argv, type_check=int):
                        self.LOOP_TIMES = int(argv[index + 1])
                        args_skip += 1

                if upper_arg == CMDHandler.SLEEP_TIME_ARG:
                    if self.arg_has_value(arg, index, argv, type_check=float):
                        self.SLEEP_TIME = float(argv[index + 1])
                        args_skip += 1

                if upper_arg == CMDHandler.SNIFF_ARG:
                    self.SNIFF_FLAG = True

                if upper_arg == CMDHandler.IP_FORMAT_ARG:
                    if self.arg_has_value(arg, index, argv):
                        self.IP_FILTER = argv[index + 1].split(",")
                        args_skip += 1

                if upper_arg == CMDHandler.PACKET_COUNT_ARG:
                    if self.arg_has_value(arg, index, argv, type_check=int):
                        self.PACKET_COUNT = int(argv[index + 1])
                        args_skip += 1

                if upper_arg == CMDHandler.DATA_ARG:
                    int_check_fail = "Value must be integer > 0"
                    val_is_valid = self.arg_sanity_check(CMDHandler.DATA_ARG, argv[index + 1],
                                                         int_check, int_check_fail)
                    arg_has_int_val = self.arg_has_value(arg, index, argv, type_check=int)

                    if arg_has_int_val and val_is_valid:
                        self.DATA_CHUNK = int(argv[index + 1])
                        args_skip += 1
                        self.DATA_CHUNK_FOUND = True

                if upper_arg == CMDHandler.SAVE_FLAG_ARG:
                    # if arg has value ... do stuff
                    arg_has_start_end_date = self.arg_has_value(arg, index, argv, offset=2) and \
                                             self.arg_has_value(arg, index, argv, offset=1)

                    length_check_fail = "Wanted comma separated list of style YYYY,MM,DD,HH,MM,SS got unexpected length"

                    arg_has_correct_length = self.arg_sanity_check(CMDHandler.SAVE_FLAG_ARG, argv[index + 1],
                                                                   length_check, length_check_fail) and \
                                             self.arg_sanity_check(CMDHandler.SAVE_FLAG_ARG, argv[index + 1],
                                                                   length_check, length_check_fail)

                    if arg_has_start_end_date and arg_has_correct_length:
                        self.SAVE_STARTDATE = argv[index + 1].split(",")
                        self.SAVE_ENDDATE = argv[index + 2].split(",")

                    self.SAVE_FOUND = True
                    args_skip += 2

                if upper_arg == CMDHandler.RECORDS_ARG:
                    length_check_fail = "Wanted comma separated list of style YYYY,MM,DD,HH,MM got unexpected length"

                    arg_has_val = self.arg_has_value(arg, index, argv)
                    arg_has_correct_length = self.arg_sanity_check(CMDHandler.RECORDS_ARG, argv[index + 1],
                                                                   length_check, length_check_fail)

                    if arg_has_val and arg_has_correct_length:
                        self.RECORDS_DATE = argv[index + 1].split(",")

                    self.RECORDS_FLAG = True
                    args_skip += 1

                if upper_arg == CMDHandler.OUTPUT_PATH_ARG:
                    # if arg has value... do stuff
                    if self.arg_has_value(arg, index, argv, type_check=str):
                        self.OUTPUT_PATH = argv[index + 1]

                    # misc
                    self.OUTPUT_FOUND = True
                    args_skip += 1

                if upper_arg == CMDHandler.ANON_ARG:
                    self.ANON_FLAG = True

                if upper_arg == CMDHandler.PICKLE_ARG:
                    self.PICKLE_FLAG = True

                if upper_arg == CMDHandler.DYNAMIC_ARG:
                    self.DYNAMIC_FLAG = True

                if upper_arg == CMDHandler.CSV_OUT_ARG:
                    self.CSV_FLAG = True

                if upper_arg == CMDHandler.PDF_OUT_ARG:
                    self.PDF_FLAG = True

                if upper_arg == CMDHandler.GRAPH_OUT_ARG:
                    self.GRAPH_FLAG = True

                if upper_arg == CMDHandler.ONEFILE_OUT_ARG:
                    self.ONEFILE_FLAG = True

                if upper_arg == CMDHandler.VERBOSE_ONEFILE_OUT_ARG:
                    self.VERBOSE_ONEFILE_FLAG = True

                if upper_arg == CMDHandler.RELAXED_ARG:
                    # if arg has value... do stuff
                    if self.arg_has_value(arg, index, argv, type_check=int):
                        self.DROP_THRESHOLD = int(argv[index + 1])

                    # misc
                    args_skip += 1

                if upper_arg == CMDHandler.KALM_ARG:
                    self.DROP_THRESHOLD = 10000

                index += 1
        except Exception as e:
            self.exceptions.append(e)

    def post_processing(self, interfaces: list, interfaces_ip: list):

        if self.RECORDS_FLAG:
            # if the year was provided, the len will be 1, so the
            # magic constant will point to RECORDS_ARG_TYPE_YEAR_MAGIC_CONSTANT... etc for all others.
            self.RECORDS_TYPE = len(self.RECORDS_DATE)
            # noinspection PyTypeChecker
            self.RECORDS_DATE = self.convert_list_datetime(self.RECORDS_DATE, CMDHandler.RECORDS_ARG)

        if not self.SAVE_FOUND and self.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException([CMDHandler.SAVE_FLAG_ARG],
                                                          "If -o <save path> flag is specified, "
                                                          "-save <STARTDATE YYYY,MM,DD,HH,MM,SS> "
                                                          "<ENDDATE YYYY,MM,DD,HH,MM,SS> must also be specified."))

        if self.SAVE_FOUND and not self.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException([CMDHandler.OUTPUT_PATH_ARG], "If -save flag is specified, "
                                                                                        "-o <save path> must also be "
                                                                                        "specified."))

        out_specifier_found = self.CSV_FLAG or \
                              self.PDF_FLAG or \
                              self.GRAPH_FLAG or \
                              self.ONEFILE_FLAG or \
                              self.VERBOSE_ONEFILE_FLAG

        if self.SAVE_FOUND and self.OUTPUT_FOUND and not out_specifier_found:
            self.exceptions.append(InvalidFormatException(["an output specifier"], "An output specifier must be present"
                                                                                   " to specify in what format the "
                                                                                   "output "
                                                                                   "will be in. Valid flags are: "
                                                                                   "-csv, -pdf, -graph, -onefile, "
                                                                                   "-verbose_onefile ."))

        if self.VERBOSE_ONEFILE_FLAG and not self.GRAPH_FLAG:
            self.exceptions.append(InvalidFormatException(["-graph"], "-graph output specifier is required to be "
                                                                      "present in order to provide the graphs for the "
                                                                      "verbose output pdf. Please use -graph flag if "
                                                                      "you want the verbose output."))

        if self.SAVE_STARTDATE is not None and self.SAVE_ENDDATE is not None:
            try:
                # noinspection PyTypeChecker
                startdate = self.convert_list_datetime(self.SAVE_STARTDATE, CMDHandler.SAVE_FLAG_ARG)
                # noinspection PyTypeChecker
                enddate = self.convert_list_datetime(self.SAVE_ENDDATE, CMDHandler.SAVE_FLAG_ARG)

                # sanity check that startdate is before enddate
                order_sanity_check = enddate - startdate > timedelta(seconds=1)

                # if it fails...
                if not order_sanity_check:
                    raise InvalidFormatException(
                        ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS", "-o <save path>"],
                        "Save startdate must be a time before the enddate. Please check if your input is reversed."
                    )

                self.SAVE_STARTDATE = startdate
                self.SAVE_ENDDATE = enddate

            except Exception as e:
                self.exceptions.append(e)

        if out_specifier_found and not self.SAVE_FOUND and self.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException(
                ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS", "-o <save path>"],
                "An output specifier must be present "
                "to specify in what format the output "
                "will be in. Valid flags are: "
                "-csv, -pdf, -graph, -onefile, "
                "-verbose_onefile .")
            )

        if self.DATA_CHUNK_FOUND and not self.SAVE_FOUND:
            self.exceptions.append(InvalidFormatException(
                ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS"],
                "save flag is required for -data arg to take effect."
            ))

        if self.ANON_FLAG and not self.SAVE_FOUND:
            self.exceptions.append(InvalidFormatException(
                ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS"],
                "save flag is required for -anon arg to take effect."
            ))

        if self.PICKLE_FLAG and not self.SAVE_FOUND:
            self.exceptions.append(InvalidFormatException(
                ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS"],
                "save flag is required for -pickle arg to take effect."
            ))

        if self.PICKLE_FLAG and not self.GRAPH_FLAG:
            self.exceptions.append(InvalidFormatException(
                ["-graph"],
                "graph flag is required for -pickle arg to take effect."
            ))

        if self.DYNAMIC_FLAG and self.SNIFF_FLAG:
            self.exceptions.append(InvalidFormatException(["-dynamic"], "If -dynamic argument is specified, you cannot "
                                                                        "sniff on any interface."))

        if self.INTERFACE_IPV4 is None and not self.SAVE_FOUND and not self.DYNAMIC_FLAG and not self.PICKLE_FOUND:
            self.exceptions.append(InvalidFormatException(["-i <interface ipv4>"], "-i argument is required and should "
                                                                                   "always be present, with a valid "
                                                                                   "ipv4 "
                                                                                   "address corresponding to an "
                                                                                   "interface."))

        if self.INTERFACE_IPV4 is not None:
            found = False

            index = 0
            for ip in interfaces_ip:
                if self.INTERFACE_IPV4 == ip:
                    found = True
                    self.INTERFACE_READABLE = interfaces[index]
                    break

                index += 1

            if not found:
                self.exceptions.append(InvalidFormatException(["valid ipv4 address"], "A valid IPV4 address must be "
                                                                                      "specified. The one currently "
                                                                                      "provided doesn't match any "
                                                                                      "ip on the system. Valid IPV4s "
                                                                                      "are: "
                                                                                      f"{interfaces_ip}"))

        if self.SLEEP_TIME < 0:
            self.exceptions.append(
                InvalidFormatException(["positive sleep time"], "A valid sleep time must be specified. "
                                                                "The sleep time must be a positive "
                                                                "floating point or integer number."))

        if self.LOOP_TIMES != inf and self.LOOP_TIMES < 0:
            self.exceptions.append(
                InvalidFormatException(["positive loop number"], "A valid loop number must be specified. "
                                                                 "The loop time argument must be a "
                                                                 "positive integer."))

        if self.DROP_THRESHOLD < 0:
            self.exceptions.append(InvalidFormatException(["positive drop threshold"], "A valid drop threshold must be "
                                                                                       "specified. The threshold "
                                                                                       "must be "
                                                                                       "a positive integer."))

        if self.PACKET_COUNT != inf and self.PACKET_COUNT < 0:
            self.exceptions.append(InvalidFormatException(["positive packet count"], "A valid packet count must be "
                                                                                     "specified. The count must be "
                                                                                     "a positive integer."))

        if self.DROP_THRESHOLD != 1 and not self.VERBOSE_ONEFILE_FLAG:
            self.exceptions.append(InvalidFormatException([CMDHandler.VERBOSE_ONEFILE_OUT_ARG],
                                                          "Relaxed threshold is specified, but "
                                                          "-verbose_onefile is not specified. "
                                                          "Without the verbose onefile flag, the "
                                                          "argument has no effect."))
