
USER_API_STATUS = {
    "SIGN_IN_FAILED" : (0, "Wrong ID"),
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
    "INTERNAL_DB_ERR" : (12, "Something when wrong, try again!")
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

def existing_session(mobile_number):
    query = "\
        with latest_session as \
        (select tb.id as user_id, us.session_id,\
        CASE \
            WHEN us.created_at + interval '1 hour' * us.duration < now()::timestamp  THEN true\
                ELSE false\
            END is_expired\
        from tbuser as tb inner join user_session as us \
            on tb.id = us.user_id\
        where \
            tb.mobile_number = '{}'\
            and (us.expired is NULL\
            or us.expired is false)\
        order by us.created_at desc limit 1)\
        select * from latest_session".format(mobile_number)
    return query

def update_expired(user_id, session_id):
    query = "update user_session set expired=true \
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

def create_session(user_id, session_id, session_duration):
    insert_session = "INSERT INTO user_session(user_id, session_id, created_at, updated_at, duration, expired) \
                                VALUES ({},'{}',now(), now(),{}, false)".format(user_id, session_id, session_duration)
    return insert_session

def session_checkin(session_id):
    query = f"UPDATE user_session SET check_in = now() where session_id = '{session_id}'"
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