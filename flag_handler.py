# Flags:
# -i <interface ip> -l <loop times> -t <sleep time> -c <packet count>
# -o <output path> -f <comma separated ips> -sniff -records <YYYY,MM,DD,HH,MM>
# -save <startdate, in YYYY,MM,DD,HH,MM,SS> <enddate, in YYYY,MM,DD,HH,MM,SS>
# -csv, -pdf, -graph, -onefile, -verbose_onefile -relaxed <drop threshold>
from math import inf
from datetime import datetime, timedelta

class InvalidParameterError(Exception):
    def __init__(self, flag, value, description : str):
        self.flag = flag
        self.val  = value
        self.desc = description

    def __str__(self):
        return f"Invalid parameter {self.flag}, with value {self.val}.\nDescription: {self.desc}"

class InvalidFlagError(InvalidParameterError):
    pass

class InvalidValueError(InvalidParameterError):
    pass

class InvalidLengthError(InvalidParameterError):
    pass

class InvalidFormatException(Exception):
    def __init__(self, args_404 : list, description : str):
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

    RECORDS_ARG_TYPE_YEAR_MAGIC_CONSTANT   = 1
    RECORDS_ARG_TYPE_MONTH_MAGIC_CONSTANT  = 2
    RECORDS_ARG_TYPE_DAY_MAGIC_CONSTANT    = 3
    RECORDS_ARG_TYPE_HOUR_MAGIC_CONSTANT   = 4
    RECORDS_ARG_TYPE_MINUTE_MAGIC_CONSTANT = 5

    VALID_FLAGS = [INTERFACE_TO_USE_ARG, LOOP_TIMES_ARG, SLEEP_TIME_ARG, SNIFF_ARG, IP_FORMAT_ARG, PACKET_COUNT_ARG,
                   SAVE_FLAG_ARG, OUTPUT_PATH_ARG, CSV_OUT_ARG, PDF_OUT_ARG, GRAPH_OUT_ARG, RECORDS_ARG,
                   ONEFILE_OUT_ARG, VERBOSE_ONEFILE_OUT_ARG, RELAXED_ARG, KALM_ARG]

    SPECIAL_OUTPUT_FLAGS = [CSV_OUT_ARG, PDF_OUT_ARG, GRAPH_OUT_ARG]
    FOUND_SPECIAL_FLAGS = [False for _ in SPECIAL_OUTPUT_FLAGS]

    ONE_FILE_OUTPUT_FLAGS = [ONEFILE_OUT_ARG, VERBOSE_ONEFILE_OUT_ARG]
    FOUND_ONE_FILE_OUTPUT_FLAGS = [False for _ in ONE_FILE_OUTPUT_FLAGS]

    def __init__(self):
        self.INTERFACE_IPV4 = None
        self.INTERFACE_READABLE = None

        self.PACKET_COUNT = inf
        self.LOOP_TIMES = inf
        self.SLEEP_TIME = 1

        self.SAVE_FOUND = False
        self.OUTPUT_FOUND = False

        self.SAVE_STARTDATE = None
        self.SAVE_ENDDATE = None
        self.OUTPUT_PATH = None

        self.IP_FILTER = None

        self.RECORDS_FLAG = False
        self.RECORDS_DATE = None
        self.RECORDS_TYPE = None

        self.SNIFF_FLAG = False
        self.CSV_FLAG = False
        self.PDF_FLAG = False
        self.GRAPH_FLAG = False
        self.ONEFILE_FLAG = False

        self.VERBOSE_ONEFILE_FLAG = False
        self.DROP_THRESHOLD = 1

        self.exceptions = []

    def arg_has_value(self, arg : str, arg_index : int, argl : list,
                      offset : int = 1, type_check : type = None, val_check = None):
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

    def arg_is_comma_separated_list(self, arg : str, length : int):
        if len(arg.split(",")) != length:
            raise InvalidValueError(None, arg, f"Wanted comma separated list of "
                                               f"length {length} got {len(arg.split(','))}")
        return True

    def arg_sanity_check(self, flag : str, arg : str, sanity_check, fail_check_descr):
        if not sanity_check(arg):
            raise InvalidValueError(flag, arg, fail_check_descr)

        return True

    # noinspection PyTypeChecker
    def convert_list_datetime(self, l: list, flag: str):
        if len(l) == 1:
            date = datetime(
                int(l[0]),
                1,
                1,
                0,
                0,
                0,
                000
            )
        elif len(l) == 2:
            date = datetime(
                int(l[0]),
                int(l[1]),
                1,
                0,
                0,
                0,
                000
            )
        elif len(l) == 3:
            date = datetime(
                int(l[0]),
                int(l[1]),
                int(l[2]),
                0,
                0,
                0,
                000
            )
        elif len(l) == 4:
            date = datetime(
                int(l[0]),
                int(l[1]),
                int(l[2]),
                int(l[3]),
                0,
                0,
                000
            )
        elif len(l) == 5:
            date = datetime(
                int(l[0]),
                int(l[1]),
                int(l[2]),
                int(l[3]),
                int(l[4]),
                0,
                000
            )
        elif len(l) == 6:
            date = datetime(
                int(l[0]),
                int(l[1]),
                int(l[2]),
                int(l[3]),
                int(l[4]),
                int(l[5]),
                000
            )
        else:
            raise InvalidFormatException(
                [flag],
                f"Unexpected comma separated length {len(l)} on arg for flag {flag}"
            )

        return date

    def parse_sys_args(self, argv : list):
        index = 0
        args_skip = 1 #skip the first argument because it's the script path lulw
        try:
            for arg in argv:
                if args_skip > 0:
                    args_skip -= 1
                    index += 1
                    continue

                #main stuff here
                upper_arg = arg.upper()

                if upper_arg not in CMDHandler.VALID_FLAGS:
                    raise InvalidFlagError(arg, None, f"Encountered non valid flag {arg}.")

                if upper_arg == CMDHandler.INTERFACE_TO_USE_ARG:
                    if self.arg_has_value(arg, index, argv):
                        self.INTERFACE_IPV4 = argv[index + 1]
                        args_skip += 1

                if upper_arg == CMDHandler.LOOP_TIMES_ARG:
                    if self.arg_has_value(arg, index, argv, type_check = int):
                        self.LOOP_TIMES = int(argv[index + 1])
                        args_skip += 1

                if upper_arg == CMDHandler.SLEEP_TIME_ARG:
                    if self.arg_has_value(arg, index, argv, type_check = float):
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

                if upper_arg == CMDHandler.SAVE_FLAG_ARG:
                    #if arg has value ... do stuff
                    argHasStartEndDate = self.arg_has_value(arg, index, argv, offset = 2) and \
                                         self.arg_has_value(arg, index, argv, offset = 1)

                    formatCheck = lambda l: 1 <= len(l.split(',')) <= 6
                    formatCheckFailDesc = "Wanted comma separated list of style YYYY,MM,DD,HH,MM,SS got unexpected length"

                    argHasCorrectFormatting = self.arg_sanity_check(CMDHandler.SAVE_FLAG_ARG, argv[index + 1],
                                                                    formatCheck, formatCheckFailDesc) and \
                                              self.arg_sanity_check(CMDHandler.SAVE_FLAG_ARG, argv[index + 1],
                                                                    formatCheck, formatCheckFailDesc)

                    if argHasStartEndDate and argHasCorrectFormatting:
                        self.SAVE_STARTDATE = argv[index + 1].split(",")
                        self.SAVE_ENDDATE = argv[index + 2].split(",")

                    self.SAVE_FOUND = True
                    args_skip += 2

                if upper_arg == CMDHandler.RECORDS_ARG:
                    formatCheck = lambda l: 1 <= len(l.split(',')) <= 6
                    formatCheckFailDesc = "Wanted comma separated list of style YYYY,MM,DD,HH,MM got unexpected length"

                    argHasVal = self.arg_has_value(arg, index, argv)
                    argHasCorrectFormatting = self.arg_sanity_check(CMDHandler.RECORDS_ARG, argv[index + 1],
                                                                    formatCheck, formatCheckFailDesc)

                    if argHasVal and argHasCorrectFormatting:
                        self.RECORDS_DATE = argv[index + 1].split(",")

                    self.RECORDS_FLAG = True
                    args_skip += 1

                if upper_arg == CMDHandler.OUTPUT_PATH_ARG:
                    #if arg has value... do stuff
                    if self.arg_has_value(arg, index, argv, type_check=str):
                        self.OUTPUT_PATH = argv[index + 1]

                    #misc
                    self.OUTPUT_FOUND = True
                    args_skip += 1

                if upper_arg == CMDHandler.CSV_OUT_ARG:
                    self.CSV_FLAG = True
                    CMDHandler.FOUND_SPECIAL_FLAGS[0] = True

                if upper_arg == CMDHandler.PDF_OUT_ARG:
                    self.PDF_FLAG = True
                    CMDHandler.FOUND_SPECIAL_FLAGS[1] = True

                if upper_arg == CMDHandler.GRAPH_OUT_ARG:
                    self.GRAPH_FLAG = True
                    CMDHandler.FOUND_SPECIAL_FLAGS[2] = True

                if upper_arg == CMDHandler.ONEFILE_OUT_ARG:
                    self.ONEFILE_FLAG = True
                    CMDHandler.FOUND_ONE_FILE_OUTPUT_FLAGS[0] = True

                if upper_arg == CMDHandler.VERBOSE_ONEFILE_OUT_ARG:
                    self.VERBOSE_ONEFILE_FLAG = True
                    CMDHandler.FOUND_ONE_FILE_OUTPUT_FLAGS[1] = True

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

    def post_processing(self, ips : list):

        if self.RECORDS_FLAG:
            #if the year was provided, the len will be 1, so the
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
                                                             "-o <save path> must also be specified."))

        out_specifier_found = True in CMDHandler.FOUND_SPECIAL_FLAGS or True in CMDHandler.FOUND_ONE_FILE_OUTPUT_FLAGS

        if self.SAVE_FOUND and self.OUTPUT_FOUND and not out_specifier_found:
            self.exceptions.append(InvalidFormatException(["an output specifier"], "An output specifier must be present"
                                                                               " to specify in what format the output "
                                                                               "will be in. Valid flags are: "
                                                                               "-csv, -pdf, -graph, -onefile, "
                                                                               "-verbose_onefile ."))

        if self.SAVE_STARTDATE is not None and self.SAVE_ENDDATE is not None:
            try:
                # noinspection PyTypeChecker
                startdate = self.convert_list_datetime(self.SAVE_STARTDATE, CMDHandler.SAVE_FLAG_ARG)
                # noinspection PyTypeChecker
                enddate = self.convert_list_datetime(self.SAVE_ENDDATE, CMDHandler.SAVE_FLAG_ARG)

                #sanity check that startdate is before enddate
                order_sanity_check = enddate - startdate > timedelta(seconds=1)

                #if it fails...
                if not order_sanity_check:
                    raise InvalidFormatException(
                        ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS","-o <save path>"],
                        "Save startdate must be a time before the enddate. Please check if your input is reversed."
                    )

                self.SAVE_STARTDATE = startdate
                self.SAVE_ENDDATE = enddate

            except Exception as e:
                self.exceptions.append(e)

        if out_specifier_found and not self.SAVE_FOUND and self.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException(
                ["-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS","-o <save path>"],
                "An output specifier must be present"
                " to specify in what format the output "
                "will be in. Valid flags are: "
                "-csv, -pdf, -graph, -onefile, "
                "-verbose_onefile .")
            )

        if self.INTERFACE_IPV4 is None:
            self.exceptions.append(InvalidFormatException(["-i <interface ipv4>"], "-i argument is required and should "
                                                                              "always be present, with a valid ipv4 "
                                                                              "address corresponding to an interface."))

        if self.INTERFACE_IPV4 is not None:
            found = False

            index = 0
            for ip in ips[1]:
                if self.INTERFACE_IPV4 == ip:
                    found = True
                    self.INTERFACE_READABLE = ips[0][index]
                    break

                index += 1

            if not found:
                self.exceptions.append(InvalidFormatException(["valid ipv4 address"], "A valid IPV4 address must be "
                                                                                  "specified. The one currently "
                                                                                  "provided doesn't match any "
                                                                                  "ip on the system. Valid IPV4s are: "
                                                                                  f"{ips[1]}"))

        if self.SLEEP_TIME < 0:
            self.exceptions.append(InvalidFormatException(["positive sleep time"], "A valid sleep time must be specified. "
                                                                            "The sleep time must be a positive "
                                                                            "floating point or integer number."))

        if self.LOOP_TIMES != inf and self.LOOP_TIMES < 0:
            self.exceptions.append(InvalidFormatException(["positive loop number"], "A valid loop number must be specified. "
                                                                               "The loop time argument must be a "
                                                                               "positive integer."))

        if self.DROP_THRESHOLD < 0:
            self.exceptions.append(InvalidFormatException(["positive drop threshold"], "A valid drop threshold must be "
                                                                                 "specified. The threshold must be "
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

