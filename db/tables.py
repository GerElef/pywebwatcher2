# https://github.com/coleifer/peewee/issues/1747
from peewee import TimestampField, TextField, IntegerField, Model, SqliteDatabase, BooleanField


class Timeframe(Model):
    ms = IntegerField()
    limit = IntegerField()

    receiver = TextField()
    receiver_readable = TextField()
    interface = TextField(null=True)
    interface_dead = BooleanField(default=False)

    datetime = TimestampField(primary_key=True, resolution=1e3)

    class Meta:
        database = db = SqliteDatabase('data.db')


class Packet(Model):
    size = IntegerField()

    sender = TextField()
    receiver = TextField()
    interface_used = TextField()

    datetime = TimestampField(resolution=1e3)  # ms

    class Meta:
        database = db = SqliteDatabase('data.db')
