
USER_API_STATUS = {
    "SIGN_IN_FAILED" : (0, "Wrong ID or password"),
    "INVALID_NAME_PWD" : (1, "Either user name or password is not correct"),
    "SIGN_IN_DONE" : (2, "Sign in is done"),
    "SIGN_UP_DONE" : (3, "Sign up is done"),
    "USER_NAME_TAKEN" : (4, "User name is already taken"),
    "MOBILE_TAKEN" : (5, "Mobile number has been taken"),
    
    "CREATE_SESSION_FAIL" : (6, "Session is failed created"),
    "CREATE_SESSION_DONE" : (7, "Session is done created"),
    
    "SIGN_UP_FAILED" : (8, "Sign up is failed"),
    "VALIDATE_DONE" : (9, "Validate session done"),
    "VALIDATE_FAILED" : (10, "Validate session failed"),
    "USER_EXIST" : (11, "User already exists"),
    "INTERNAL_DB_ERR" : (12, "Something when wrong, try again!"),
    
    "CER_ISSUE_DONE" :  (15, "Certificate number issued successfully"),
    "CER_ISSUE_FAILED" :  (16, "Certificate number issued failed"),
    "CER_VERIFY_DONE" :  (17, "Certificate number verified successfully"),
    "CER_VERIFY_FAILED" :  (18, "Certificate number verified failed"),
    "CREATE_USER_ZONE_DONE" :  (19, "Create user and zone done")
}

ALARM_API_STATUS = {
    "ADD_DONE" : (13, "Add alarm ok"),
    "GET_DONE" : (14, "Get alarm ok"),
    "STOP_DONE" : (19, "Stop alarm done")
}


# class StatusMess(IntEnum):
#     UNKNOWN_ID=0,
#     WRONG_PASS=1,
#     LOGIN_SUC=2,
#     SIGNUP_SUC=3,
#     DUP_ID=4,
#     DUP_PHONE=5

ENCRYPT_KEY = "netv2021"
SESSION_DURATION = 9 # in hours
AUTHO_DURATION = 9 # in hours
DEFAULT_ROLE = 'worker'


# USER RELATED API

def existing_session(mobile_number):
    query = "\
        with latest_session as \
        (select tb.id as user_id, us.session_id,\
        CASE \
            WHEN us.created_at + interval '1 hour' * us.duration < now()::timestamp  THEN true\
                ELSE false\
            END is_expired\
        from tbuser as tb inner join working_session as us \
            on tb.id = us.user_id\
        where \
            tb.mobile_number = '{}'\
            and (us.expired is NULL\
            or us.expired is false)\
        order by us.created_at desc limit 1)\
        select * from latest_session".format(mobile_number)
    return query

def update_expired(user_id, session_id):
    query = "update working_session set expired=true \
            where user_id = {} \
            and session_id = '{}'".format(user_id, session_id)
    return query

def get_user(mobile_number):
    return f"select id from tbuser where mobile_number='{mobile_number}'"

def get_user_by_mobile(mobile_number):
    return f"select * from tbuser where mobile_number='{mobile_number}'"

def get_user_name(user_name):
    return f"select * from tbuser where user_name='{user_name}'"

def create_user(mobile_number):
    query = "INSERT INTO tbuser (mobile_number) VALUES ('{}')".format(mobile_number)
    return query

def insert_user_zone(user_id, zone_code):
    query = "INSERT INTO user_zone (user_id, zone_code, created_at, updated_at) VALUES ('{}', '{}', now(), now())".format(user_id, zone_code)
    return query

def create_session(user_id, session_id, session_duration):
    insert_session = "INSERT INTO working_session(user_id, session_id, created_at, updated_at, duration, expired) \
                                VALUES ({},'{}',now(), now(),{}, false)".format(user_id, session_id, session_duration)
    return insert_session

def session_checkin(session_id, zone_code):
    if zone_code is None:
        query = "UPDATE working_session SET check_in = now() where session_id = '{}'".format(session_id)
    else:
        query = "UPDATE working_session SET check_in = now(), zone_code = '{}' where session_id = '{}'".format(zone_code, session_id)
    print(query)
    return query

def update_username_pass(user_name, hashed_pass, mobile_number):
    query = f"UPDATE tbuser SET user_name = '{user_name}', password = '{hashed_pass}' where mobile_number = '{mobile_number}';"
    return query

def get_user_by_username_password(user_name, hased_pass):
    query = "Select * from tbuser where user_name = '{}' and password = '{}'".format(user_name, hased_pass)
    return query

def update_autho_expired(user_id):
    query = "UPDATE public.user_autho \
	        SET expired=true where user_id = {}".format(user_id)
    return query

def insert_authorization(user_id, autho_id, duration):
    query = "INSERT INTO user_autho(user_id, autho_id, created_at, updated_at, duration, expired) \
                                VALUES ({},'{}',now(), now(),{}, false)".format(user_id, autho_id, duration)
    return query

# ALARM RELATED API
def create_alarm(user_id, accidence, buildingId, filedId, time, level, notification):
    if user_id:
        query = "INSERT INTO alarm(report_id, accidence, building_id, field_id, time, level, status, notification) \
                                    VALUES ({}, {}, {}, {}, '{}', {}, true, '{}')"\
                                    .format(user_id, accidence, buildingId, filedId, time, level, notification)
    else:
         query = "INSERT INTO alarm(accidence, building_id, field_id, time, level, status, notification) \
                                    VALUES ({}, {}, {}, '{}', {}, {}, true, '{}')"\
                                    .format(accidence, buildingId, filedId, time, level, notification)
    print(query)
    return query

def select_alarm(user_id, accidence, buildingId, filedId, time, level, notification):
    if user_id:
        query = "SELECT * from alarm where report_id = {} \
                                            and accidence = {} \
                                            and building_id = {} \
                                            and field_id = {} \
                                            and time = '{}' \
                                            and level = {} \
                                            and status =  true;" \
                                    .format(user_id, accidence, buildingId, filedId, time, level, notification)
    else:
        query = "SELECT * from alarm where  accidence = {} \
                                            and building_id = {} \
                                            and field_id = {} \
                                            and time = '{}' \
                                            and level = {} \
                                            and status =  true;" \
                                    .format(accidence, buildingId, filedId, time, level, notification)
    print(query)
    return query

def stop_alarm(alarm_id):
    query = "Update alarm set status = false where id = {}".format(alarm_id)
    return query

def select_alarm_limit(number):
    query = "SELECT * FROM alarm order by time desc limit {}".format(number)
    return query

def select_latest_and_stopped_alarm(holding_ids):
    if holding_ids is not None:
        maxid = max(holding_ids)
        print(f'maxid is {maxid}')
        ids = ','.join(str(id) for id in holding_ids)
        print(f'ids is {ids}')
        query = "SELECT * FROM alarm where (id > {} or id in ({})) and status = true order by id;".format(maxid, ids)
        print(f'query of select max ids is: {query}')
        return query
    else:
        query = "SELECT * FROM alarm where status = true order by id;"
        return query
        



def failed_return(api_status, message=''):
    code, m = api_status

    if message == '':
        message = m

    return {
        'success' : False,
        'code' : code,
        'message' : message
    }

def success_return(api_status, data, message=''):
    code, m = api_status
        
    if message == '':
        message = m

    return {
        'success' : True,
        'code' : code,
        'message' : message,
        'data' : data
    }