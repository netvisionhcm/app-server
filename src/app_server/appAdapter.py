from flask import Response, request, jsonify
from flask import Flask
from flask import send_file
import requests, json

from config_utils import get_video_server_ip, get_safety_server_ip
from postgres_query import Postgres_Query
from user_management.user_query import User_Query
from user_management.alarm_query import Alarm_Query
from werkzeug.utils import secure_filename
import os
import base64
EMPTY_CODE = 204

RESTAPI_PORT = 30001


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi'}

app = Flask(__name__)

app.config["DEBUG"] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SERVER_IP, SERVER_PORT =  get_video_server_ip()
SAFETY_SERVER_IP, SAFETY_SERVER_PORT =  get_safety_server_ip()


@app.route("/user/create_session", methods=['POST'])
def certification():
    # print('####', request)
    app_mobile_num = request.json['mobile_number']
    print('app server Received certificate message from mobile_number: ', app_mobile_num)
    
    # response = requests.post(f"http://{SERVER_IP}:{SERVER_PORT}/user/certification", json=request.json)
    print('App server Received certificate message from mobile_number: ', app_mobile_num)
    dbreturn = userQuery.register_session(app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

@app.route("/user/create_session", methods=['GET'])
def validate():
    session_id = request.args.get('sid')
    if 'zone_code' in request.args:
        zone_code = request.args.get('zone_code')
    else:
        zone_code = None
        
    if not zone_code:
        zone_code = None
    print('validate for : ', session_id)
    dbreturn = userQuery.validate_session(session_id, zone_code)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

@app.route("/user/add_zone", methods=['POST'])
def add_zone():
    user_id = request.json['user_id']
    zone_code = request.json['zone_code']
    dbreturn = userQuery.add_user_zone(user_id, zone_code)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

@app.route("/user/get_certificate", methods=['POST'])
def get_certification():
    app_mobile_num = request.json['mobile_number']
    dbreturn = userQuery.set_cer_number(app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

@app.route("/user/verify_certificate", methods=['POST'])
def verify_certificate():
    app_mobile_num = request.json['mobile_number']
    cer_number = request.json['certificate_number']
    dbreturn = userQuery.verify_cer_number(app_mobile_num, cer_number)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

@app.route("/user/signup", methods=['POST'])
def user_signing_up():
    mobile = request.json['mobile_number']
    name = request.json['user_name']
    passw = request.json['password']
    
    if mobile is None or name is None or passw is None:
        return Response(response={'success': False}, status=200, mimetype="application/json")

    # response = requests.post(f"http://{SERVER_IP}:{SERVER_PORT}/user/signup", json=request.json)
    dbreturn = userQuery.sign_up(name, passw, mobile)
    #
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")


@app.route("/user/signin", methods=['POST'])
def user_sign_in():
    invalid_params = 'user_name' not in request.json or 'password' not in request.json
    if invalid_params:
        return Response(response=json.dumps({'success': False, 'message':'Invalid parameters'}), status=200, mimetype="application/json")
    name = request.json['user_name']
    passw = request.json['password']
    
    # response = requests.post(f"http://{SERVER_IP}:{SERVER_PORT}/user/signin", json=request.json)
    dbreturn = userQuery.sign_in(name, passw)
    #
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")



@app.route("/connection/heartbeat", methods=['POST'])
def connection_heartbeat():
    app_mobile_num = request.json['mobile_number']
    app_user_name = request.json['name']
    app_user_time = request.json['time']

    # run_heartbeat_func()
    # send_warning_on_message()
    # send_warning_off_message()
    # disconnect_message()
    print('Received sign in message from mobile_number: ', app_mobile_num)

    return jsonify({"success": True, "message": 'message for heartbeat'})


@app.route("/report/accident", methods=['POST'])
def accident_report():
    app_mobile_num = request.json['mobile_number']
    app_user_name = request.json['name']
    app_user_accident = request.json['accident_type']
    app_user_time = request.json['time']

    # run_heartbeat_func()
    # send_warning_on_message()
    # send_warning_off_message()
    # disconnect_message()
    # send_accident_message()
    print('Received accident message from mobile_number: ', app_mobile_num)

    return ('', EMPTY_CODE)


@app.route("/request/location", methods=['POST'])
def request_location():
    app_mobile_num = request.json['mobile_number']
    app_user_name = request.json['name']
    app_user_time = request.json['time']

    # get_location()

    print('Received request location from mobile_number: ', app_mobile_num)

    return jsonify({"success": True, "location": {'camera': '', 'zone': '', 'coordinate': [0, 0]}})


# api to Safety server UNE
@app.route("/spatial_info", methods=['POST'])
def spatial_info():
    try:
        request_spatial_info = request.json['requestSpatialInfo']
    except Exception as ex:
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    response = requests.post(f"http://{SAFETY_SERVER_IP}:{SAFETY_SERVER_PORT}/spatial_info", json=request.json)
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=response, status=200, mimetype="application/json")


# mobile app call to make an alarm report
@app.route("/user_report", methods=['POST'])
def user_report():
    # input json like:
    # {
    #     'reportManualAlarm': {
    #     'reporterID': string,
    #     'accident_type': {
    # 	       'fire': boolean
    #     },
    #     'fieldID': number | null,
    #     'buildingID': number | null,
    #     'notifications': string | null      // report message(optional)
    #     }
    # }

    try:
        reportManualAlarm = request.json['reportManualAlarm']    
    except Exception as ex:
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    response = requests.post(f"http://{SAFETY_SERVER_IP}:{SAFETY_SERVER_PORT}/user_report", json=request.json)
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    
    ## TODO: queue the message reponse from safety server to push to mobile
    
    return Response(response=response, status=200, mimetype="application/json")


@app.route("/location_info", methods=['POST'])
def location_info():
    try:
        requestUserPosition = request.json['requestUserPosition']
        id = requestUserPosition["id"]
    except Exception as ex:
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    response = requests.post(f"http://{SAFETY_SERVER_IP}:{SAFETY_SERVER_PORT}/location_info", json=request.json)
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=response, status=200, mimetype="application/json")

# for safety server to call and send alarm info
@app.route("/alarm_info", methods=['POST'])
def alarm_info():
#     {
#     'accident_type': {
# 	'fire': boolean
#     },
#     // The disaster location is indicated by the building ID or field ID, and either must not be null.
#     'buildingID': number | null,  // can’t know if it’s null.
#     'fieldID': number | null,      // can’t know if it’s null.
#     'time': string,                   // YYYY-MM-DD hh:mm:ss
#     'status': boolean,              // true : disaster occurrence, false : disaster release
#     'level': number,                // 1 : Attention, 2 : Warning1, 3 : Warning2, 4 : Serious
#     'notifications': string         // disaster message
# }

    try:
        accident_type = request.json['accident_type']
        isFire = accident_type['fire']
        buildingID = request.json['buildingID']
        fieldID = request.json['fieldID']
        time = request.json['time']
        status = request.json['status']
        level = request.json['level']
        notifications = request.json['notifications']
    except Exception as ex:
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")
    
    ##TODO queue the messessage here to send to app

    return Response(response=json.dumps({'success': True, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

# mobile request repeatedly to get the info
@app.route("/retrieve_alarm", methods=['POST'])
def alarm_info_retrieve():
    try:
        number = request.json['number']
    except Exception as ex:
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    dbreturn = alarmQuery.get_latest_alarm(number)
    print('dbreturn ', dbreturn)
    #
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

# mobile request repeatedly to get the info
@app.route("/heartbeat", methods=['GET'])
def heartbeat():
    if request and request.json and 'alarm_ids' in request.json:
        holding_ids = request.json['alarm_ids'] # mobile sending holding ids
    else:
        holding_ids = None
    # try:
    #     holding_ids = request.json['alarm_ids'] # mobile sending holding ids
    #     print(f'holding ids {holding_ids} having type {type(holding_ids)}')
    # except Exception as ex:
    #     return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    dbreturn = alarmQuery.get_latest_and_check_stop(holding_ids)
    print('dbreturn ', dbreturn)
    #
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")


@app.route("/stop_alarm", methods=['POST'])
def stop_alarm():
    try:
        id = request.json['alarm_id']
    except Exception as ex:
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    dbreturn = alarmQuery.stop_alarm(id)
    print('dbreturn ', dbreturn)
    #
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           

@app.route("/report_alarm", methods=['POST'])
def alarm_info_add():
    try:                   
        print(request.form)
        reportjson = request.form #json.loads(request.form['data'])
        if 'user_id' in reportjson:
            user_id = int(reportjson['user_id'])
            print(f'user id {user_id}')
        else:
            user_id = None
        accident = int(reportjson['accidence'])   # 1, 2, 4, 8, 16, 32
        buildingID = int(reportjson['building_id'])
        fieldID = int(reportjson['field_id'])
        time = reportjson['time']
        level = int(reportjson['level'])
        notifications = reportjson['notifications']
        print('go here 1')
        if user_id is not None and 'filecount' in reportjson:
            filecount = int(reportjson['filecount'])
            media_names = json.loads(reportjson['media_file'])
            for i in range(filecount):
                print('go here 2')
                uploaded_file = reportjson[f'file{i}']
                print('go here 3')
                filename = media_names[f'file{i}']
                print(uploaded_file)
                print(filename)
                # if uploaded_file is None or uploaded_file.filename == '':
                #     continue
                # if not allowed_file(filename):
                #     continue
                
                # filename = secure_filename(uploaded_file.filename)
                if not os.path.exists(os.path.join(UPLOAD_FOLDER, str(user_id))):
                    os.makedirs(os.path.join(UPLOAD_FOLDER, str(user_id)))
                fullfilepath = os.path.join(UPLOAD_FOLDER, str(user_id), filename)
                with open(fullfilepath, "wb") as fh:
                    fh.write(base64.b64decode(uploaded_file))
                print(fullfilepath)
                
                # uploaded_file.save(fullfilepath)
        
    except Exception as ex:
        print(ex)
        return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

    dbreturn = alarmQuery.add_alarm(user_id, accident, buildingID, fieldID, time, level, notifications)
    #
    #print('Received signing_up message from mobile_number: ', app_mobile_num)
    return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

# @app.route("/report_alarm", methods=['POST'])
# def alarm_info_add():
#     try:                   
#         print(request.form)
#         reportjson = request.form #json.loads(request.form['data'])
#         if 'user_id' in reportjson:
#             user_id = reportjson['user_id']
#             print(f'user id {user_id}')
#         else:
#             user_id = None
#         accident = reportjson['accidence']   # 1, 2, 4, 8, 16, 32
#         buildingID = reportjson['building_id']
#         fieldID = reportjson['field_id']
#         time = reportjson['time']
#         level = reportjson['level']
#         notifications = reportjson['notifications']
        
#         if user_id is not None and 'filecount' in reportjson:
#             filecount = reportjson['filecount']
#             for i in range(1, filecount + 1):
#                 uploaded_file = request.files[f'file{i}']
#                 if uploaded_file is None or uploaded_file.filename == '':
#                     continue
#                 if not allowed_file(uploaded_file.filename):
#                     continue
                
#                 filename = secure_filename(uploaded_file.filename)
#                 if not os.path.exists(os.path.join(UPLOAD_FOLDER, str(user_id))):
#                     os.makedirs(os.path.join(UPLOAD_FOLDER, str(user_id)))
#                 fullfilepath = os.path.join(UPLOAD_FOLDER, str(user_id), filename)
#                 print(fullfilepath)
                
#                 uploaded_file.save(fullfilepath)
        
#     except Exception as ex:
#         print(ex)
#         return Response(response=json.dumps({'success': False, 'message' : 'wrong parameters'}), status=200, mimetype="application/json")

#     dbreturn = alarmQuery.add_alarm(user_id, accident, buildingID, fieldID, time, level, notifications)
#     #
#     #print('Received signing_up message from mobile_number: ', app_mobile_num)
#     return Response(response=json.dumps(dbreturn), status=200, mimetype="application/json")

@app.route("/send_files", methods=['POST'])       #test only     
def test_api():
    print('Received request')
    print(request)                         
    uploaded_file = request.files['file1']
    filename = secure_filename(uploaded_file.filename)
    uploaded_file.save(os.path.join(UPLOAD_FOLDER, filename))
    uploaded_file2 = request.files['file2']
    filename2 = secure_filename(uploaded_file2.filename)
    uploaded_file2.save(os.path.join(UPLOAD_FOLDER, filename2))
    
    data = (request.form['data'])
    print('data received is :', data, type(data))
    print(json.loads(data))
    return 'success'
    


if __name__ == "__main__":
    global userQuery, alarmQuery
    sql_conn = Postgres_Query().get_db_connection()
    userQuery = User_Query(sql_conn)
    alarmQuery = Alarm_Query(sql_conn)

    # start flask server
    print('Server started on {0}'.format(RESTAPI_PORT))
    app.run(debug=True, host='0.0.0.0', port=RESTAPI_PORT, use_reloader=True)
