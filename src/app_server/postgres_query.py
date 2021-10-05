
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

        # self.create_cameras_table()
        # self.create_areas_table()
        # self.create_safety_gear_table()
        # self.create_movinglogs_table()
        # self.create_user_info_table()
        # self.create_user_registering_table()
        
        # self.create_working_session_table()

        # User
        self.create_user_table()
        # self.create_user_info_table()
        self.create_working_session()
        self.create_user_authorization()
        self.create_user_zone()
        
        # Alarm
        self.create_alarm_table()

    def connect_database(self):
        try:
            self.conn = self.db.connect()
        except Exception as e:
            print("Error occru", e)
            print(type(e).__name__)

    def get_db_connection(self):
        return self.conn
    
    def create_user_table(self):
        if not inspect(self.db).has_table("tbuser"):
            print('create tbuser table')
            metadata = MetaData()
            user = Table("tbuser", metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user_name', String(50), nullable=True),
                         Column('password', String(50), nullable=True),
                         Column('mobile_number', String(50), nullable=False, unique=True),
                         Column('cer_number', Integer, nullable=True),
                         Column('birth_date', String(50), nullable=True),
                         Column('address', String(50), nullable=True),
                         Column('email', String(50), nullable=True)
                         )
            metadata.create_all(self.db)

    def create_working_session(self):
        if not inspect(self.db).has_table("working_session"):
            print('create working_session table')
            metadata = MetaData()
            session = Table("working_session", metadata,
                         Column('user_id', Integer),
                         Column('session_id', String(80), nullable=False),
                         Column('created_at', DateTime(), default=datetime.now(), nullable=True),
                         Column('updated_at', DateTime(), default=datetime.now(), onupdate=datetime.now(), nullable=True),
                         Column('duration', Integer, nullable=True),
                         Column('expired', Boolean, nullable=True),
                         Column('zone_code', String(15), nullable=True),
                         Column('check_in', DateTime(), nullable=True),
                         Column('check_out', DateTime(), nullable=True)
                         )
            metadata.create_all(self.db)
            
    def create_user_zone(self):
        if not inspect(self.db).has_table("user_zone"):
            print('create user_zone table')
            metadata = MetaData()
            user_zone = Table("user_zone", metadata,
                         Column('user_id', Integer, nullable=True),
                         Column('zone_code', String(15), nullable=True),
                         Column('created_at', DateTime(), default=datetime.now(), nullable=True),
                         Column('updated_at', DateTime(), default=datetime.now(), onupdate=datetime.now(), nullable=True)
                         )
            metadata.create_all(self.db)
    
    def create_user_authorization(self):
        if not inspect(self.db).has_table("user_autho"):
            print('create user_autho table')
            metadata = MetaData()
            autho = Table("user_autho", metadata,
                        Column('user_id', Integer),
                        Column('autho_id', String(80), nullable=False),
                        Column('created_at', DateTime(), default=datetime.now(), nullable=True),
                        Column('updated_at', DateTime(), default=datetime.now(), onupdate=datetime.now(), nullable=True),
                        Column('duration', Integer, nullable=True),
                        Column('role', String(20), nullable=True),
                        Column('expired', Boolean, nullable=True)
                        )
            metadata.create_all(self.db)

    def create_alarm_table(self):
        if not inspect(self.db).has_table("alarm"):
            print('create alarm table')
            metadata = MetaData()
            alarm = Table("alarm", metadata,
                         Column('id', Integer, primary_key=True),
                         Column('report_id', Integer, nullable=True),
                         Column('accidence', Integer, nullable=True),
                         Column('building_id', Integer, nullable=True),
                         Column('field_id', Integer, nullable=True),
                         Column('time', DateTime(), default=datetime.now(), nullable=True),
                         Column('level', Integer, nullable=True),
                         Column('status', Boolean, nullable=True),
                         Column('notification', String(200), nullable=False),
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