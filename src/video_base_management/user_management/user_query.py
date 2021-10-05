from datetime import datetime
from io import SEEK_CUR
import logging

from flask import request

from config_utils import *
from sqlalchemy import *
from psycopg2.errors import UniqueViolation
import hashlib

import urllib.parse as urlparse

from key_processing.aescbc import AESCBC
logger = logging.getLogger()

from user_management.helper import *
from config_utils import key_duration_config

class User_Query(object):
    def __init__(self, postgres_db_conn):
        self.conn = postgres_db_conn
        self.aes = AESCBC()
        self.session_duration, self.autho_duration = key_duration_config()

    def register_session(self, mobile_number):
        session = self.conn.execute(existing_session(mobile_number)).fetchone()
        if session is not None:
            user_id, session_id, expired = session
            if not expired:
                data = {
                    'session_id' : session_id,
                    'activation_link' : f'{request.base_url}?sid={session_id}' 
                }
                return success_return(USER_API_STATUS['CREATE_SESSION_DONE'], data)
            else:
                self.conn.execute(update_expired(user_id, session_id))
        
        user = self.conn.execute(get_user(mobile_number)).fetchone()

        if user is None:
            try:
                self.conn.execute(create_user(mobile_number))
            except Exception as ex:
                from pprint import pprint
                pprint(vars(ex))
   
                # return False, 1 if type(ex.orig) == UniqueViolation else 0
                return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))
            # get ID again due to create_user cannot return newly created one
            id, = self.conn.execute(get_user(mobile_number)).fetchone()
        else:
            id, = user
       
        timestr = str(datetime.now())
        session_str = f'{id}|{timestr}'
        print('## SESSION STR is ', session_str, len(session_str))
        session_id = self.aes.encrypt(session_str, ENCRYPT_KEY)
        print('## session string after hashed ', session_id )
        try:
            self.conn.execute(create_session(id, session_id, self.session_duration))
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))
        print(request.host_url)
        data = {
            'session_id' : session_id,
            'activation_link' : f'{request.base_url}?sid={session_id}' 
        }
        return success_return(USER_API_STATUS['CREATE_SESSION_DONE'], data)


    def validate_session(self, session_id):
        try:
            # original_session = urlparse.unquote_plus(session_id)
            # print("original ", original_session)
            self.conn.execute(session_checkin(session_id))
        except Exception as ex:
            return failed_return(USER_API_STATUS["VALIDATE_FAILED"], str(ex))
        return success_return(USER_API_STATUS["VALIDATE_DONE"], {})


    def sign_up(self, user_name, password, mobile_number):
        user = self.conn.execute(get_user_by_mobile(mobile_number)).fetchone()
        mobile_exist = user is not None
        if mobile_exist:
            _, db_user_name, _, _ = user
            if db_user_name is not None and db_user_name != user_name:
                return failed_return(USER_API_STATUS["MOBILE_TAKEN"])
            if db_user_name is not None and db_user_name == user_name:
                return failed_return(USER_API_STATUS["USER_EXIST"])
        
        user =  self.conn.execute(get_user_name(user_name)).fetchone()

        if user is not None:
            print('got user ', user)
            return failed_return(USER_API_STATUS["USER_NAME_TAKEN"])
        else:
            try:
                self.conn.execute(create_user(mobile_number))
            except Exception as ex:
                from pprint import pprint
                pprint(vars(ex))
                print(f'type(ex.orig) {type(ex.orig)}')

        hashed_pass = hashlib.md5(password.encode('utf-8')).hexdigest()

        try:
            self.conn.execute(update_username_pass(user_name, hashed_pass, mobile_number))
        except Exception as ex:
            print(ex)
            return failed_return(USER_API_STATUS["SIGN_UP_FAILED"], str(ex))
        data = {
            'user_name' : user_name,
        }
        return success_return(USER_API_STATUS["SIGN_UP_DONE"], data)

    def sign_in(self, user_name, password):
        hashed_pass = hashlib.md5(password.encode('utf-8')).hexdigest()
        try:
            dbresult = self.conn.execute(get_user_by_username_password(user_name, hashed_pass)).fetchone()
        except Exception as ex:
            from pprint import pprint
            pprint(vars(ex))
            return failed_return(USER_API_STATUS["SIGN_IN_FAILED"])

        if dbresult is None:
            return failed_return(USER_API_STATUS["SIGN_IN_FAILED"])
        try:
            user_id, _, _, _ = dbresult
            self.conn.execute(update_autho_expired(user_id))
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'])
        
        timestr = str(datetime.now())
        autho_str = f'{user_id}|{timestr}|{DEFAULT_ROLE}'
        print('## SESSION STR is ', autho_str, len(autho_str))
        autho_id = self.aes.encrypt(autho_str, ENCRYPT_KEY)
        print('## session string after hashed ', autho_id )
        
        try:
            self.conn.execute(insert_authorization(user_id, autho_id, self.autho_duration))
        except Exception as ex:
            return failed_return(USER_API_STATUS['INTERNAL_DB_ERR'], str(ex))

        data = {
            'autho_id' : autho_id
        }
        
        return success_return(USER_API_STATUS["SIGN_IN_DONE"], data)
