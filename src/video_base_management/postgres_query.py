
import logging

from config_utils import *
from sqlalchemy import *
from sqlalchemy_utils import database_exists, create_database

from datetime import datetime
from arc4 import ARC4


logger = logging.getLogger()

db_user, db_pass, db_name, server_ip = read_db_config()


class Postgres_Query(object):
    def __init__(self):

        connection_str = 'postgresql://{}:{}@{}/{}'.format(
            db_user, db_pass, server_ip, db_name)

        self.db = create_engine(connection_str)
        self.database_init()

    def database_init(self):
        if not database_exists(self.db.url):
            print('create danger_detection databeas')
            create_database(self.db.url)
        self.connect_database()

        self.create_cameras_table()
        self.create_areas_table()
        self.create_safety_gear_table()
        self.create_movinglogs_table()
        #self.create_user_info_table()
        # self.create_user_registering_table()
        # self.create_working_session_table()

        # User
        self.create_user_table()
        self.create_user_info_table()
        self.create_user_session()
        self.create_user_authorization()

    def connect_database(self):
        try:
            self.conn = self.db.connect()
        except Exception as e:
            print("Error occru", e)
            print(type(e).__name__)

    def get_db_connection(self):
        return self.conn

    def create_cameras_table(self):
        print(inspect(self.db).has_table("cameras"))
        if not inspect(self.db).has_table("cameras"):
            print('create cameras table')
            metadata = MetaData()
            user = Table('cameras', metadata,
                         Column('camera_id', String(50), primary_key=True),
                         Column('location', String(50), nullable=False),
                         Column('coordinate', String(50), nullable=False),
                         Column('address', String(50), nullable=False),
                         Column('port', Integer, nullable=False),
                         Column('uri', String(50))
                         )
            metadata.create_all(self.db)

    def create_areas_table(self):
        if not inspect(self.db).has_table("areas"):
            print('create areas table')
            metadata = MetaData()
            user = Table('areas', metadata,
                         Column('camera_id', String(50), primary_key=True),
                         # format [warning_name1, warning_name2, ..., danger_name1, danger_name2, ...]
                         Column('names', String(50), nullable=False),
                         # format [ [ [123,345], [234,345], ...], [[123,345], [234,345], ...], ...]
                         Column('warning', String, nullable=False),
                         # format [ [ [123,345], [234,345], ...], [[123,345], [234,345], ...], ...]
                         Column('danger', String, nullable=False),
                         )
            metadata.create_all(self.db)

    def create_safety_gear_table(self):
        if not inspect(self.db).has_table("safety_gears"):
            print('create safety_gears table')
            metadata = MetaData()
            user = Table('safety_gears', metadata,
                         Column('camera_id', String(50), primary_key=True),
                         # format ['helmet', 'vest', 'shoes', ...]
                         Column('gears', String, nullable=False), 
                         )
            metadata.create_all(self.db)

    def create_movinglogs_table(self):
        if not inspect(self.db).has_table("movinglogs"):
            print('create movinglogs table')
            metadata = MetaData()
            user = Table("movinglogs", metadata,
                         Column('time', String(50), primary_key=True),
                         Column('camera_id', String(50), nullable=False),
                         Column('zone_name', String(50), nullable=False),
                         Column('person_id', String(50), nullable=False),
                         Column('pose', String(50), nullable=False),
                         Column('state', String(50), nullable=False),
                         Column('equipment', String(50))
                         )
            metadata.create_all(self.db)
    
    def create_user_table(self):
        if not inspect(self.db).has_table("tbuser"):
            print('create tbuser table')
            metadata = MetaData()
            user = Table("tbuser", metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user_name', String(50), nullable=True),
                         Column('password', String(50), nullable=True),
                         Column('mobile_number', String(50), nullable=False, unique=True),
                         )
            metadata.create_all(self.db)

    def create_user_info_table(self):
        if not inspect(self.db).has_table("user_info"):
            print('create user_info table')
            metadata = MetaData()
            user = Table("user_info", metadata,
                         Column('user_id', Integer, nullable=True),
                         Column('birth_date', String(50), nullable=False),
                         Column('address', String(50), nullable=False),
                         Column('email', String(50), nullable=False)
                         )
            metadata.create_all(self.db)

    def create_user_session(self):
        if not inspect(self.db).has_table("user_session"):
            print('create user_session table')
            metadata = MetaData()
            user = Table("user_session", metadata,
                         Column('user_id', Integer),
                         Column('session_id', String(80), nullable=False),
                         Column('created_at', DateTime(), default=datetime.now(), nullable=True),
                         Column('updated_at', DateTime(), default=datetime.now(), onupdate=datetime.now(), nullable=True),
                         Column('duration', Integer, nullable=True),
                         Column('expired', Boolean, nullable=True),
                         Column('check_in', DateTime(), nullable=True),
                         Column('check_out', DateTime(), nullable=True)
                         )
            metadata.create_all(self.db)
    
    def create_user_authorization(self):
        if not inspect(self.db).has_table("user_autho"):
            print('create user_autho table')
            metadata = MetaData()
            user = Table("user_autho", metadata,
                        Column('user_id', Integer),
                        Column('autho_id', String(80), nullable=False),
                        Column('created_at', DateTime(), default=datetime.now(), nullable=True),
                        Column('updated_at', DateTime(), default=datetime.now(), onupdate=datetime.now(), nullable=True),
                        Column('duration', Integer, nullable=True),
                        Column('role', String(20), nullable=True),
                        Column('expired', Boolean, nullable=True)
                        )
            metadata.create_all(self.db)

    def create_zone_user_table(self):
        if not inspect(self.db).has_table("zone_user"):
            print('create zone_user table')
            metadata = MetaData()
            user = Table("zone_user", metadata,
                         Column('user_id', String(50), primary_key=True),
                         Column('zone_permit', String(50), primary_key=True),
                         Column('time', String(50), nullable=False)
                         )
            metadata.create_all(self.db)

    def create_user_registering_table(self):
        if not inspect(self.db).has_table("user_registering"):
            print('create user_registering table')
            metadata = MetaData()
            user = Table("user_registering", metadata,
                         Column('user_id', String(50), primary_key=True),
                         Column('password', String(50), nullable=False),
                         Column('birth_date', String(50), nullable=False),
                         Column('phone_num', String(50), nullable=False),
                         Column('address', String(50), nullable=False),
                         Column('email', String(50), nullable=False),
                         )
            metadata.create_all(self.db)

    def create_working_session_table(self):
        if not inspect(self.db).has_table("working_session"):
            print('create working_session table')
            metadata = MetaData()
            user = Table("working_session", metadata,
                         Column('working_id', String(50), primary_key=True),
                         # list of users working on this session
                         Column('user_id', String(50), nullable=False),
                         Column('session_id', String(50), primary_key=True),
                         Column('time_start', String(50), nullable=False),
                         Column('time_out', String(50), nullable=False)
                         )
            metadata.create_all(self.db)


def sql_query_action(conn, query, key_name=None):
    stmt = text(query)
    try:
        # print(stmt)
        conn.execute(stmt)
    except Exception as e:
        if type(e).__name__ == "IntegrityError":
            if key_name is not  None:
                return False, "Duplicate entry {} for key 'PRIMARY'".format(key_name)
            else:
                return False, e.message
        print(e)
        return False, "500 : Unable to successfully !."
    return True, ""

def sql_query_run(conn, query):
    stmt = text(query)
    try:
        # print(stmt)
        result = conn.execute(stmt)
    except Exception as e:
        print(e)
        return None
    return result