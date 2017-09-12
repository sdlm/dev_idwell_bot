from datetime import datetime
from pony.orm import *

db = Database()


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    chat_id = Required(int)
    active = Required(bool, default=1)
    created = Required(datetime)
    last_msg = Optional(datetime)
    servers = Set('Server')


class Server(db.Entity):
    id = PrimaryKey(int, auto=True)
    alias = Required(str)
    url = Required(str)
    prev_state = Optional(bool)
    users = Set(User)


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)

db.generate_mapping(create_tables=True)
