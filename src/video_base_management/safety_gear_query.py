import logging

from config_utils import *
from sqlalchemy import *
from postgres_query import sql_query_action


logger = logging.getLogger()


class Safety_Gears_Query(object):
    def __init__(self, postgres_db_conn):
        self.conn = postgres_db_conn

    def add_safety_gear(self, camera_id, gears):
        query = "INSERT INTO safety_gears VALUES ('{}','{}')".format(
            camera_id, gears)
        return sql_query_action(self.conn, query, camera_id)

    def get_safety_gear(self, camera_id):
        table = 'safety_gears'
        query_result = self.conn.execute(
            "SELECT * FROM {} WHERE camera_id='{}'".format(table, camera_id)
        ).fetchall()

        return query_result[0]

    def edit_safety_gear(self, camera_id, new_gears):
        query = "UPDATE safety_gears \
                 SET gears='{}'\
                 WHERE camera_id='{}'".format(camera_id, new_gears)

        return sql_query_action(self.conn, query, camera_id)

    def delete_safety_gear(self, camera_id):
        query = "DELETE FROM {} \
                 WHERE camera_id='{}'".format("safety_gears", camera_id)
        return sql_query_action(self.conn, query, camera_id)
