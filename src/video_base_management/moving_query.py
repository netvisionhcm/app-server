import logging

from config_utils import *
from sqlalchemy import *
from postgres_query import sql_query_action


logger = logging.getLogger()


class Moving_Query(object):
    def __init__(self, postgres_db_conn):
        self.conn = postgres_db_conn

    def add_moving_log(self, camera_id, zone_name, in_time, person_id, pos, state):
        query = "INSERT INTO movinglogs VALUES ('{}','{}','{}','{}','{}','{}')".format(in_time,
                                                                                       camera_id, zone_name, person_id, pos, state)
        return sql_query_action(self.conn, query, in_time)

    def get_moving_logs(self, state):
        table = 'movinglogs'
        try:
            if state == 'ALL':
                query_result = self.conn.execute(
                    "SELECT * FROM {}".format(table)
                ).fetchall()
            else:
                query_result = self.conn.execute(
                    "SELECT * FROM {} \
                     WHERE state='{}'".format(table, state)
                ).fetchall()
            return query_result
        except Exception as e:
            # print(e)
            return []

    def del_moving_log(self, time):
        query = "DELETE FROM {} \
                 WHERE time='{}'".format("movinglogs", time)
        return sql_query_action(self.conn, query, time)
