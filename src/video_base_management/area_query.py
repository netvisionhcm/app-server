import logging

from config_utils import *
from sqlalchemy import *
from postgres_query import sql_query_action


logger = logging.getLogger()


class Area_Query(object):
    def __init__(self, postgres_db_conn):
        self.conn = postgres_db_conn

    def add_area(self, camera_id, zone_name, warning, danger):
        query = "INSERT INTO areas VALUES ('{}','{}','{}','{}')".format(camera_id,
                                                                        zone_name, warning, danger)

        return sql_query_action(self.conn, query, camera_id)

    def get_area(self, camera_id):
        table = 'areas'
        try:
            query_result = self.conn.execute(
                "SELECT * FROM {} WHERE camera_id='{}'".format(
                    table, camera_id)
            ).fetchall()
            return query_result[0]
        except Exception as e:
            print(e)
            return []

    def edit_area(self, camera_id, zone_name, warning_area, danger_area):
        query = "UPDATE areas \
                  SET names='{}', warning='{}', danger='{}'\
                  WHERE camera_id='{}'".format(zone_name, warning_area, danger_area, camera_id)

        return sql_query_action(self.conn, query, camera_id)

    def delete_area(self, camera_id):
        query = "DELETE FROM {} \
                 WHERE camera_id='{}'".format("areas", camera_id)
        return sql_query_action(self.conn, query, camera_id)

    def get_area_tracking(self, camera_id):
        result = self.get_area(camera_id)
        if len(result) == 0:
            return [], [], []
        area_name = json.loads(result[1])
        warning = json.loads(result[2])
        danger = json.loads(result[3])
        return area_name, warning, danger

