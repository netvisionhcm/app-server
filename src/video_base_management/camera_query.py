import logging

from config_utils import *
from sqlalchemy import *
from postgres_query import sql_query_action


logger = logging.getLogger()


class Camera_Query(object):
    def __init__(self, postgres_db_conn):
        self.conn = postgres_db_conn

    def add_camera(self, camera_id, location, coordinate, address, port, uri):
        query = "INSERT INTO cameras VALUES ('{}','{}','{}','{}','{}','{}')".format(camera_id,
                                                                                    location, coordinate, address, port, uri)
        return sql_query_action(self.conn, query, camera_id)

    def get_camera(self, camera_id):
        table = 'cameras'
        query_result = self.conn.execute(
            "SELECT * FROM {} WHERE camera_id='{}'".format(table, camera_id)
        ).fetchall()

        return query_result[0]

    def get_camera_list(self):
        try:
            query_result = self.conn.execute(
                "SELECT * FROM cameras"
            ).fetchall()
        except Exception as e:
            return []

        return query_result

    def edit_camera(self, camera_id, location, coordinate, address, port, uri):
        query = "UPDATE cameras \
                  SET location='{}',coordinate='{}',address='{}',port='{}',uri='{}'\
                  WHERE camera_id='{}'".format(camera_id, location, coordinate, address, port, uri)

        return sql_query_action(self.conn, query, camera_id)

    def delete_camera(self, camera_id):
        query = "DELETE FROM {} \
                 WHERE camera_id='{}'".format("cameras", camera_id)
        return sql_query_action(self.conn, query, camera_id)
