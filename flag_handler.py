# Flags:
# -i <interface ip> -l <loop times> -t <sleep time> -c <packet count>
# -o <output path> -f <comma separated ips> -sniff
# -save <startdate, in YYYY,MM,DD,HH,MM,SS> <enddate, in YYYY,MM,DD,HH,MM,SS>
# -csv, -pdf, -graph, -onefile, -verbose_onefile -relaxed <drop threshold>

from math import inf
from datetime import datetime

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

    VALID_FLAGS = ["-I", "-L", "-T", "-SNIFF", "-F", "-C",
                   "-SAVE", "-O", "-CSV", "-PDF", "-GRAPH",
                   "-ONEFILE", "-VERBOSE_ONEFILE", "-RELAXED", "-KALM"]
    SAVE_FOUND = False
    OUTPUT_FOUND = False

    SPECIAL_OUTPUT_FLAGS = ["-CSV", "-PDF", "-GRAPH"]
    FOUND_SPECIAL_FLAGS = [False for _ in SPECIAL_OUTPUT_FLAGS]

    ONE_FILE_OUTPUT_FLAGS = ["-ONEFILE", "-VERBOSE_ONEFILE"]
    FOUND_ONE_FILE_OUTPUT_FLAGS = [False for _ in ONE_FILE_OUTPUT_FLAGS]

    def __init__(self):
        self.INTERFACE_IPV4 = None
        self.INTERFACE_READABLE = None

        self.PACKET_COUNT = inf
        self.LOOP_TIMES = inf
        self.SLEEP_TIME = 1
        self.OUTPUT_PATH = None
        self.IP_FILTER = None
        self.SAVE_STARTDATE = None
        self.SAVE_ENDDATE = None

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

    def parse_sys_args(self, argv : list):

        index = 0
        args_skip = 1 #skip the first argument because it's the script path lulw
        for arg in argv:
            if args_skip > 0:
                args_skip -= 1
                index += 1
                continue

            #main stuff here
            upper_arg = arg.upper()

            if upper_arg not in CMDHandler.VALID_FLAGS:
                raise InvalidFlagError(arg, None, f"Encountered non valid flag {arg}.")

            if upper_arg == "-I":
                if self.arg_has_value(arg, index, argv):
                    self.INTERFACE_IPV4 = argv[index + 1]
                    args_skip += 1

            if upper_arg == "-L":
                if self.arg_has_value(arg, index, argv, type_check = int):
                    self.LOOP_TIMES = int(argv[index + 1])
                    args_skip += 1

            if upper_arg == "-T":
                if self.arg_has_value(arg, index, argv, type_check = float):
                    self.SLEEP_TIME = float(argv[index + 1])
                    args_skip += 1

            if upper_arg == "-SNIFF":
                self.SNIFF_FLAG = True

            if upper_arg == "-F":
                if self.arg_has_value(arg, index, argv):
                    self.IP_FILTER = argv[index + 1].split(",")
                    args_skip += 1

            if upper_arg == "-C":
                if self.arg_has_value(arg, index, argv, type_check=int):
                    self.PACKET_COUNT = int(argv[index + 1])
                    args_skip += 1

            if upper_arg == "-SAVE":
                #if arg has value ... do stuff
                argHasStartEndDate = self.arg_has_value(arg, index, argv, offset = 2, type_check=str) and \
                                     self.arg_has_value(arg, index, argv, offset=1, type_check=str)

                argHasCorrectFormatting = self.arg_is_comma_separated_list(argv[index + 1], 6) and \
                                          self.arg_is_comma_separated_list(argv[index + 2], 6)

                if argHasStartEndDate and argHasCorrectFormatting:
                    self.SAVE_STARTDATE = argv[index + 1].split(",")
                    self.SAVE_ENDDATE = argv[index + 2].split(",")

                CMDHandler.SAVE_FOUND = True
                args_skip += 2

            if upper_arg == "-O":
                #if arg has value... do stuff
                if self.arg_has_value(arg, index, argv, type_check=str):
                    self.OUTPUT_PATH = argv[index + 1]

                #misc
                CMDHandler.OUTPUT_FOUND = True
                args_skip += 1

            if upper_arg == "-CSV":
                self.CSV_FLAG = True
                CMDHandler.FOUND_SPECIAL_FLAGS[0] = True

            if upper_arg == "-PDF":
                self.PDF_FLAG = True
                CMDHandler.FOUND_SPECIAL_FLAGS[1] = True

            if upper_arg == "-GRAPH":
                self.GRAPH_FLAG = True
                CMDHandler.FOUND_SPECIAL_FLAGS[2] = True

            if upper_arg == "-ONEFILE":
                self.ONEFILE_FLAG = True
                CMDHandler.FOUND_ONE_FILE_OUTPUT_FLAGS[0] = True

            if upper_arg == "-VERBOSE_ONEFILE":
                self.VERBOSE_ONEFILE_FLAG = True
                CMDHandler.FOUND_ONE_FILE_OUTPUT_FLAGS[1] = True

            if upper_arg == "-RELAXED":
                # if arg has value... do stuff
                if self.arg_has_value(arg, index, argv, type_check=int):
                    self.DROP_THRESHOLD = int(argv[index + 1])

                # misc
                args_skip += 1

            if upper_arg == "-KALM":
                self.DROP_THRESHOLD = 10000


            index += 1

    def post_processing(self, ips : list):

        if not CMDHandler.SAVE_FOUND and CMDHandler.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException(["-save"], "If -o <save path> flag is specified, "
                                                  "-save <STARTDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS> "
                                                  "must also be specified."))

        if CMDHandler.SAVE_FOUND and not CMDHandler.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException(["-o"], "If -save flag is specified, "
                                                             "-o <save path> must also be specified."))

        out_specifier_found = True in CMDHandler.FOUND_SPECIAL_FLAGS or True in CMDHandler.FOUND_ONE_FILE_OUTPUT_FLAGS

        if CMDHandler.SAVE_FOUND and CMDHandler.OUTPUT_FOUND and not out_specifier_found:
            self.exceptions.append(InvalidFormatException(["an output specifier"], "An output specifier must be present"
                                                                               " to specify in what format the output "
                                                                               "will be in. Valid flags are: "
                                                                               "-csv, -pdf, -graph, -onefile, "
                                                                               "-verbose_onefile ."))

        if self.SAVE_STARTDATE is not None and self.SAVE_ENDDATE is not None:
            try:
                startdate = datetime(
                    int(self.SAVE_STARTDATE[0]),
                    int(self.SAVE_STARTDATE[1]),
                    int(self.SAVE_STARTDATE[2]),
                    int(self.SAVE_STARTDATE[3]),
                    int(self.SAVE_STARTDATE[4]),
                    int(self.SAVE_STARTDATE[5]),
                    000
                )

                enddate = datetime(
                    int(self.SAVE_ENDDATE[0]),
                    int(self.SAVE_ENDDATE[1]),
                    int(self.SAVE_ENDDATE[2]),
                    int(self.SAVE_ENDDATE[3]),
                    int(self.SAVE_ENDDATE[4]),
                    int(self.SAVE_ENDDATE[5]),
                    000
                )

                self.SAVE_STARTDATE = startdate
                self.SAVE_ENDDATE = enddate

            except Exception as e:
                self.exceptions.append(e)

        if out_specifier_found and not CMDHandler.SAVE_FOUND and CMDHandler.OUTPUT_FOUND:
            self.exceptions.append(InvalidFormatException(
                ["-save <STARDATE YYYY,MM,DD,HH,MM,SS> <ENDDATE YYYY,MM,DD,HH,MM,SS","-o <save path>"],
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
            self.exceptions.append(InvalidFormatException(["-verbose_onefile"], "Relaxed threshold is specified, but "
                                                                           "-verbose_onefile is not specified. "
                                                                           "Without the verbose onefile flag, the "
                                                                           "argument has no effect."))

