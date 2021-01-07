import datetime
from calendar import monthrange

from peewee import SqliteDatabase

from db.tables import Timeframe, Packet


class InvalidMagicConstant(Exception):
    pass


# https://docs.peewee-orm.com/en/latest/peewee/quickstart.html
class Dao:
    YEAR_MAGIC_CONST = 1
    MONTH_MAGIC_CONST = 2
    DAY_MAGIC_CONST = 3
    HOUR_MAGIC_CONST = 4
    MINUTE_MAGIC_CONST = 5

    def __init__(self):
        self.db = SqliteDatabase('data.db')

        self.db.connect()
        self.db.create_tables([Timeframe, Packet])
        self.db.close()

    def timestamp(self, ms: int, l: int, r: str, rr: str, i: str, iface_dead: bool = False):
        self.db.connect()
        Timeframe.create(ms=ms, limit=l,
                         receiver=r, receiver_readable=rr,
                         interface=i, interface_dead=iface_dead,
                         datetime=datetime.datetime.now(datetime.timezone.utc))
        self.db.close()

    # refactor this, should probably take less args
    def save_packet(self, se: str, r: str, iface: str, si: int):
        self.db.connect()
        Packet.create(sender=se, receiver=r, interface_used=iface, size=si,
                      datetime=datetime.datetime.now(datetime.timezone.utc))
        self.db.close()

    def dt_calc(self, date, const):
        if const == Dao.YEAR_MAGIC_CONST:
            dt = 0
            # sum (1440 * days in each month) to get
            for i in range(1, 13):
                # second element in tuple is the days in the month
                dt += 1440 * monthrange(date.year, date.month)[1]

        elif const == Dao.MONTH_MAGIC_CONST:
            # 1440 * days in month to get minutes in month
            dt = 1440 * monthrange(date.year, date.month)[1]

        elif const == Dao.DAY_MAGIC_CONST:
            # 1440 minutes in day
            dt = 1440

        elif const == Dao.HOUR_MAGIC_CONST:
            # 60 minutes in hour
            dt = 60

        elif const == Dao.MINUTE_MAGIC_CONST:
            dt = 1

        else:
            raise InvalidMagicConstant

        return dt

    def get_timestamp_number_of_records_in(self, date, const):
        minutes_dt = self.dt_calc(date, const)
        # https://stackoverflow.com/questions/52194872/peewee-query-to-fetch-all-records-on-a-specific-date
        index = Timeframe.select() \
            .where((Timeframe.datetime > date) & (Timeframe.datetime < (date + datetime.timedelta(minutes=minutes_dt)))) \
            .count()

        return index

    # query for getting M timestamp records skipping past first N records
    def get_n_timestamp_records_starting_from(self, starting_index: int, interval=1000) -> list[Timeframe]:
        query = Timeframe.select().order_by(Timeframe.datetime.desc()).limit(interval).offset(starting_index)

        frames = []
        for frame in query:
            frames.append(frame)

        return frames

    # generator for all records in given date, gives back records every set interval
    def get_all_timestamp_records_in(self, date, const, interval=1000):
        minutes_dt = self.dt_calc(date, const)
        # https://stackoverflow.com/questions/52194872/peewee-query-to-fetch-all-records-on-a-specific-date
        query = Timeframe.select() \
            .where(Timeframe.datetime > date & Timeframe.datetime < date + datetime.timedelta(minutes=minutes_dt))

        index = 1
        frames = []
        for frame in query:
            if index % interval == 0:
                yield frames
                index = 1
                frames.clear()

            frames.append(frame)
            index += 1

        yield frames

        return

    def get_all_timestamp_records_in_dates(self, datestart, dateend, interval=1000):
        query = Timeframe.select() \
            .where(Timeframe.datetime > datestart & Timeframe.datetime < dateend)

        index = 1
        frames = []
        for frame in query:
            if index % interval == 0:
                yield frames
                index = 1
                frames.clear()

            frames.append(frame)
            index += 1

        yield frames

        return

    def get_packet_number_of_records_in(self, date, const):
        minutes_dt = self.dt_calc(date, const)
        # https://stackoverflow.com/questions/52194872/peewee-query-to-fetch-all-records-on-a-specific-date
        index = Packet.select() \
            .where((Packet.datetime > date) & (Packet.datetime < (date + datetime.timedelta(minutes=minutes_dt)))) \
            .count()

        return index

    def get_all_packet_records_in(self, date, const, interval=1000):
        minutes_dt = self.dt_calc(date, const)

        query = Packet.select() \
            .where(Packet.datetime > date & Packet.datetime < date + datetime.timedelta(minutes=minutes_dt))

        index = 1
        packets = []
        for frame in query:
            if index % interval == 0:
                yield packets
                index = 1
                packets.clear()

            packets.append(frame)
            index += 1

        yield packets

        return

    def get_all_packet_records_in_dates(self, datestart, dateend, interval=1000):
        query = Packet.select() \
            .where(Packet.datetime > datestart & Packet.datetime < dateend)

        index = 1
        packets = []
        for frame in query:
            if index % interval == 0:
                yield packets
                index = 1
                packets.clear()

            packets.append(frame)
            index += 1

        yield packets

        return
