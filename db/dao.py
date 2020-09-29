import datetime

from peewee import SqliteDatabase

from db.tables import Timeframe, Packet


#https://docs.peewee-orm.com/en/latest/peewee/quickstart.html
class Dao:
    def __init__(self):
        self.db = SqliteDatabase('data.db')

        self.db.connect()
        self.db.create_tables([Timeframe, Packet])
        self.db.close()

    def save(self, thing):
        self.db.connect()
        thing.save()
        self.db.close()

    def timestamp(self, ms : int, l : int, r : str, rr : str, i :str, iface_dead : bool = False):
        self.save(Timeframe(ms=ms, limit=l,
                            receiver=r, receiver_readable=rr,
                            interface = i, interface_dead = iface_dead,
                            datetime = datetime.datetime.now(datetime.timezone.utc)))

    #refactor this, should probably take less args
    def save_packet(self, se : str, r : str, iface : str, si : int):
        self.save(Packet(sender=se, receiver=r, interface_used=iface, size=si,
                         datetime = datetime.datetime.now(datetime.timezone.utc)))
