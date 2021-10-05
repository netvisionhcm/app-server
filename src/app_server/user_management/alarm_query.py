from datetime import datetime
from io import SEEK_CUR
import logging

from flask import request

from config_utils import *
from sqlalchemy import *
from psycopg2.errors import UniqueViolation

import urllib.parse as urlparse

from key_processing.aescbc import AESCBC
logger = logging.getLogger()

from user_management.helper import *

class Alarm_Query(object):
    def __init__(self, postgres_db_conn):
        self.conn = postgres_db_conn

    def add_alarm(self, user_id, fire, buildingId, filedId, time, level, notification):
        try:
            self.conn.execute(create_alarm(user_id, fire, buildingId, filedId, time, level, notification))
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))
        just_added_alarm = self.conn.execute(select_alarm(user_id, fire, buildingId, filedId, time, level, notification)).fetchone()
        
        if just_added_alarm:
            id, report_id, accidence, building_id, field_id, time, level, status, notification = just_added_alarm
            data = {
                 'id': id,
                 'report_id': report_id,
                 'accidence': accidence,
                 'building_id': building_id,
                 'field_id': field_id,
                 'time': str(time),
                 'level': level,
                 'status': status,
                 'notification': notification
            }
            return success_return(ALARM_API_STATUS['ADD_DONE'], data)
        return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], "cannot add alarm")
    
    def stop_alarm(self, alarm_id):
        try:
            self.conn.execute(stop_alarm(alarm_id))
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))
        # print(request.host_url)
        return success_return(ALARM_API_STATUS['STOP_DONE'], {})
    
    def get_latest_alarm(self, number):
        try:
            alarms = self.conn.execute(select_alarm_limit(number)).fetchall()
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))
        data = []
        for al in alarms:
            print(al)
            _, _, _, _, _, _, _, _, _, notification = al
            print('not ', notification)
            data.append(notification)
            
        return success_return(ALARM_API_STATUS['GET_DONE'], data)
    
    def get_latest_and_check_stop(self, holding_ids):
        try:
            alarms = self.conn.execute(select_latest_and_stopped_alarm(holding_ids)).fetchall()
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))
        data = []
        for al in alarms:
            id, report_id, accidence, building_id, field_id, time, level, status, notification = al
            al_json = {
                 'id': id,
                 'report_id': report_id,
                 'accidence': accidence,
                 'building_id': building_id,
                 'field_id': field_id,
                 'time': str(time),
                 'level': level,
                 'status': status,
                 'notification': notification
            }
            data.append(al_json)
        return success_return(ALARM_API_STATUS['GET_DONE'], data)
