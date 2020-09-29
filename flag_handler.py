# Flags:
# -i <interface ip> -l <loop times> -t <sleep time>
# -o <output path> -f <comma separated ips>, -sniff
# -save <startdate, in YYYY,MM,DD,HH,MM,SS> <enddate, in YYYY,MM,DD,HH,MM,SS>
# -csv, -pdf, -graph, -onefile, -verbose_onefile
#                               -relaxed <drop threshold>

# if the interface flag doesn't exist, the program will prompt the user to select

# if save flag exists, the program will only output data file
# and it will not run. if the save flag exists,
# the -o flag must also be present, specifying an absolute save path
# If save flag exists, at least one of the output specifier flags must exist:
#   -csv, -pdf, -graph
# if -onefile exists, a pdf will be outputted with some data, and a graph for the datetime specified
# if -verbose_onefile exists, a pdf will be outputted with the data explained in detail, for the datetime specified
#   if -verbose_onefile exists, -relaxed <drop threshold> can be used to relax the output calculations

from math import inf
from sys  import argv

class InvalidParameterError(Exception):
    def __init__(self, flag : str, value : str, description : str):
        self.flag = flag
        self.val  = value
        self.desc = description

    def __str__(self):
        return f"Invalid parameter {self.flag}, with value {self.val}. Description: {self.desc}"

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
        return f"Didn't find {self.args_404}. Description: {self.desc}"

class CMDHandler:
    VALID_FLAGS = ["-I", "-L", "-T", "-SNIFF", "-F",
                   "-SAVE", "-O", "-CSV", "-PDF",
                   "-ONEFILE", "-VERBOSE_ONEFILE", "-RELAXED"]
    SAVE_FOUND = False

    SPECIAL_OUTPUT_FLAGS = ["-CSV", "-PDF", "-GRAPH"]
    FOUND_SPECIAL_FLAGS = [False for _ in SPECIAL_OUTPUT_FLAGS]

    ONE_FILE_OUTPUT_FLAGS = ["-ONEFILE", "-VERBOSE_ONEFILE"]
    FOUND_ONE_FILE_OUTPUT_FLAGS_FLAGS = [False for _ in ONE_FILE_OUTPUT_FLAGS]

    def __init__(self):
        self.INTERFACE = None
        self.LOOP_TIMES = inf
        self.SLEEP_TIME = 1
        self.OUTPUT_PATH = None
        self.IP_FILTER = None
        self.SNIFF_FLAG = False
        self.SAVE_FLAG = False
        self.CSV_FLAG = False
        self.PDF_FLAG = False
        self.GRAPH_FLAG = False
        self.ONEFILE_FLAG = False

        self.VERBOSE_ONEFILE_FLAG = False
        self.DROP_THRESHOLD = 1


    def argHasValue(self, arg : str, arg_index : int , argl : list,
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

    def argIsCommaSeparatedList(self, arg : str, length : int):
        if len(arg.split(",")) != length:
            raise InvalidValueError(None, arg, f"Wanted comma separated list of "
                                               f"length {length} got {len(arg.split(','))}")
        return True

    def parseSysArgs(self):
        argv_len = len(argv)

        index = 0
        args_skip = 0
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
                if self.argHasValue(arg, index, argv):
                    self.INTERFACE = arg[index + 1]
                    args_skip += 1

            if upper_arg == "-L":
                if self.argHasValue(arg, index, argv, type_check = int):
                    self.LOOP_TIMES = int(arg[index + 1])
                    args_skip += 1

            if upper_arg == "-T":
                if self.argHasValue(arg, index, argv, type_check = float):
                    self.SLEEP_TIME = float(arg[index + 1])
                    args_skip += 1

            if upper_arg == "-SNIFF":
                self.SNIFF_FLAG = True

            if upper_arg == "-F":
                if self.argHasValue(arg, index, argv):
                    self.IP_FILTER = arg[index + 1]
                    args_skip += 1

            if upper_arg == "-SAVE":
                #if arg has value
                CMDHandler.SAVE_FOUND = True
                args_skip += 1

            if upper_arg == "-O":
                #if arg has value
                args_skip += 1

            if upper_arg == "-CSV":
                pass

            if upper_arg == "-PDF":
                pass

            if upper_arg == "-GRAPH":
                pass

            if upper_arg == "-ONEFILE":
                pass

            if upper_arg == "-VERBOSE_ONEFILE":
                pass

            if upper_arg == "-RELAXED":
                args_skip += 1

        index += 1

    #if -save flag was found, then -o flag must have been found, as well as either -CSV, -PDF, -GRAPH,
    # (-onefile OR -verbose_onefile).
    # If -relaxed was found, -verbose_onefile must've been found as well.