import threading

import time
import cv2
import json
import image_actions as vImage
import numpy as np


from image_actions import SCREENSHOTS, PERSON
from flask import Response, request, jsonify
from flask import Flask
from flask import render_template
from flask import send_file
from postgres_query import Postgres_Query

from ai_bridge import AI_Bridge

from camera_query import Camera_Query
from area_query import Area_Query
from moving_query import Moving_Query

from user_management.user_query import User_Query

from safety_gear_query import Safety_Gears_Query


RESTAPI_PORT = 13344

safety = Flask(__name__)

safety.config["DEBUG"] = True

lock = threading.Lock()

## QUERY dict for all sql table ###


def generate(cameraId, scale):
    # grab global references to the output frame and lock variables
    global lock
    while True:
        # wait until the lock is acquired
        with lock:
            time.sleep(1/24)
            frame = AIbridge.get_video_frame(cameraId, scale)
            if len(frame) == 0:
                frame = np.zeros((scale[0], scale[1], 3), np.uint8)

            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
            # yield the output frame in the byte format
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                  bytearray(encodedImage) + b'\r\n')


@safety.route('/')
def index():

    camera_list = QUERY['camera'].get_camera_list()
    safety_gears_list = ['belt', 'helmet', 'vest', 'shose']

    return render_template(
        'zone_config.html',
        title="Zone Configuration",
        nav_dash="active",
        camera_list=camera_list,
        safety_gears_list=safety_gears_list,
        status=True
    )


@safety.route('/zone_config')
def zone_config():

    camera_list = QUERY['camera'].get_camera_list()

    safety_gears_list = ['belt', 'helmet', 'vest', 'shose']

    return render_template(
        'zone_config.html',
        title="Zone Configuration",
        nav_dash="active",
        camera_list=camera_list,
        safety_gears_list=safety_gears_list,
        status=True
    )


@safety.route('/ajax_get_safety_gears', methods=['POST'])
def ajax_get_safety_gears():
    camera_id = request.json['CameraId']
    print('Get safety gears required by zone: ', camera_id)
    #safety_gears = QUERY['safety_gear'].get_safety_gear(camera_id)

    safety_gears = ['belt', 'helmet', 'vest', 'shose']

    return jsonify({"status": True, "results": safety_gears})


@safety.route('/ajax_get_zone_permitted', methods=['POST'])
def ajax_get_zone_permitted():
    person_name = request.json['PersonName']
    print('Get zones permitted for person: ', person_name)


    zones_permitted = ['Zone1', 'Zone2', 'Zone3', 'Zone4']

    return jsonify({"status": True, "results": zones_permitted})


@safety.route("/video_feed/<camera_id>")
def video_feed(camera_id):
    # return the response generated along with the specific media
    # type (mime type)
    scale = AIbridge.get_video_size(camera_id)
    return Response(generate(camera_id, scale),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@safety.route("/video_scale/<camera_id>")
def video_scale(camera_id):
    # return the response generated along with the specific media
    # type (mime type)
    #cameraId = path
    scale = (64, 48)
    return Response(generate(camera_id, scale),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


def getXYinDict(indict, key):
    poss = []
    inlist = indict[key]
    for ss in inlist:
        xpos = int(ss['XPos'])
        ypos = int(ss['YPos'])
        poss.append([xpos, ypos])
    return poss


@safety.route("/ajax_set_area_pools", methods=['POST'])
def apply_danger_pools():
    camera_id = request.json['CameraId']
    names = request.json['Names']
    warnings = request.json['Warnings']
    dangers = request.json['Dangers']

    print(names)
    print(warnings)
    print(dangers)

    success, results = QUERY['area'].add_area(camera_id, json.dumps(
        names), json.dumps(warnings), json.dumps(dangers))
    # print(success)
    print('Add areas for tracking: %s' % results)
    if success == False:
        success, results = QUERY['area'].edit_area(camera_id, json.dumps(
            names), json.dumps(warnings), json.dumps(dangers))

    if success:
        AIbridge.make_area_pools(camera_id, names, warnings, dangers)

    return jsonify({"status": success, "results": results})


# camera functions
@safety.route('/camera_list')
def camera_list():

    camera_list = QUERY['camera'].get_camera_list()
    print(camera_list)

    return render_template(
        'camera_list.html',
        title="Camera List",
        nav_camera_list="active",
        nav_camera="menu-open",
        camera_list=camera_list,
        status=True
    )


@safety.route('/camera_add')
def camera_add():
    return render_template(
        'camera_add.html',
        title="Camera Add",
        nav_camera_add="active",
        nav_camera="menu-open"
    )


@safety.route('/tracking_info')
def tracking_info():

    moving_logs = QUERY['moving'].get_moving_logs('ALL')
    # print(moving_logs)

    return render_template(
        'tracking_info.html',
        title="All Tracking Infomations",
        nav_tracking_info="active",
        nav_logs="menu-open",
        moving_logs=moving_logs,
        status=True
    )


@safety.route('/danger_info')
def danger_info():

    moving_logs = QUERY['moving'].get_moving_logs('danger')
    # print(moving_logs)

    return render_template(
        'danger_info.html',
        title="Danger Tracking Infomations",
        nav_danger_info="active",
        nav_logs="menu-open",
        moving_logs=moving_logs,
        status=True
    )


@safety.route('/warning_info')
def warning_info():

    moving_logs = QUERY['moving'].get_moving_logs('warning')
    # print(moving_logs)

    return render_template(
        'warning_info.html',
        title="Warning Tracking Infomations",
        nav_warning_info="active",
        nav_logs="menu-open",
        moving_logs=moving_logs,
        status=True
    )


@safety.route('/camera_edit/<cameraid>')
def camera_edit(cameraid):

    ret = QUERY['camera'].get_camera(cameraid)

    camera_location = ret[1]
    camera_coordinate = ret[2]
    camera_address = ret[3]
    camera_port = ret[4]
    camera_uri = ret[5]
    (w, h) = AIbridge.get_video_size(cameraid)

    item = {}
    item["camera_id"] = cameraid
    item["location"] = camera_location
    item["coordinate"] = camera_coordinate
    item["address"] = camera_address
    item["port"] = camera_port
    item["uri"] = camera_uri
    item["height"] = h
    item["width"] = w

    safety_gears_list = ['belt', 'helmet', 'vest', 'shose']
    


    return render_template(
        'camera_edit.html',
        title="Camera Edit",
        nav_camera_list="active",
        nav_camera="menu-open",
        object=item,
        safety_gears_list=safety_gears_list,
        # width=w,
        # height=h,
        status=True
    )


@safety.route('/camera_view/<cameraid>')
def camera_view(cameraid):

    ret = QUERY['camera'].get_camera(cameraid)

    camera_location = ret[1]
    camera_coordinate = ret[2]
    camera_address = ret[3]
    camera_port = ret[4]
    camera_uri = ret[5]

    item = {}
    item["camera_id"] = cameraid
    item["location"] = camera_location
    item["coordinate"] = camera_coordinate
    item["address"] = camera_address
    item["port"] = camera_port
    item["uri"] = camera_uri

    return render_template(
        'camera_view.html',
        title="Camera View",
        nav_camera_list="active",
        nav_camera="menu-open",
        object=item,
        width=1280,
        height=720,
        status=True
    )


@safety.route('/camera_edit/screenshots/<camera_id>')
def load_screenshot(camera_id):
    # return the response generated along with the specific media
    # type (mime type)
    print('get image of ' + camera_id)
    try:
        return send_file(SCREENSHOTS + camera_id + '.png', mimetype='image/gif')
    except Exception as e:
        print("Unknown error")
        print(e)
        print("Send blank image repalced")
        return send_file(SCREENSHOTS + 'no-screenshot.png', mimetype='image/gif')


@safety.route('/ajax_del_camera', methods=['POST'])
def ajax_del_camera():
    camera_name_list = request.json['data']
    print(camera_name_list)
    for camera in camera_name_list:
        success, results = AIbridge.del_camera(camera)
        print(success)
        print(results)

    return jsonify({"status": success, "results": results})


@safety.route('/ajax_edit_camera', methods=['POST'])
def ajax_edit_camera():
    camera_id = request.json['camera_id']
    camera_location = request.json['camera_location']
    camera_coordinate = request.json['camera_coordindate']
    camera_address = request.json['camera_address']
    camera_port = request.json['camera_port']
    camera_uri = request.json['camera_uri']

    success, results = QUERY['camera'].edit_camera(camera_id, camera_location,
                                                   camera_coordinate, camera_address, camera_port, camera_uri)

    return jsonify({"status": success, "results": results})


@safety.route('/ajax_add_camera', methods=['POST'])
def ajax_add_camera():
    camera_id = request.json['camera_id']
    camera_location = request.json['camera_location']
    camera_coordinate = request.json['camera_coordinate']
    camera_address = request.json['camera_address']
    camera_port = request.json['camera_port']
    camera_uri = request.json['camera_uri']

    success, results = AIbridge.add_camera(
        camera_id, camera_location, camera_coordinate, camera_address, camera_port, camera_uri)

    print('Add camera:', success, results)

    return jsonify({"status": success, "results": results})


@safety.route('/ajax_get_log', methods=['POST'])
def ajax_get_log():
    return jsonify({"status": True, "results": ''})


def safetyrun(host, port, reloader):
    try:
        safety.run(debug=True, host=host,
                   port=RESTAPI_PORT, use_reloader=reloader)
    except (KeyboardInterrupt, SystemExit):
        print('Stop server')


@safety.route('/ajax_del_log', methods=['POST'])
def ajax_del_log():
    time_list = request.json['data']
    print(time_list)
    for time in time_list:
        success, results = QUERY['moving'].del_moving_log(time)
        print(success)
    if success:
        vImage.delImage(PERSON + time)

    return jsonify({"status": success, "results": results})


@safety.route('/ajax_get_area_pools', methods=['POST'])
def ajax_get_area_pools():
    camera_id = request.json['data']
    print("get areas by zone name: ", camera_id)
    areas = QUERY['area'].get_area_tracking(camera_id)

    item = {}
    item["names"] = areas[0]
    item["warns"] = areas[1]
    item["dangers"] = areas[2]

    return jsonify({"status": True, "results": item})


# region user sign in up

@safety.route("/user/certification", methods=['POST'])
def certification():
    app_mobile_num = request.json['mobile_number']
    print('vbwss Received certificate message from mobile_number: ', app_mobile_num)
    dbreturn = userQuery.register_session(app_mobile_num)
    return jsonify(dbreturn)

@safety.route("/user/certification", methods=['GET'])
def validate():
    session_id = request.args.get('sid')
    print('validate for : ', session_id)
    dbreturn = userQuery.validate_session(session_id)
    return jsonify(dbreturn)


@safety.route("/user/signup", methods=['POST'])
def user_signing_up():
    mobile = request.json['mobile_number']
    name = request.json['user_name']
    passw = request.json['password']
    dbreturn = userQuery.sign_up(name, passw, mobile)
    return jsonify(dbreturn)

@safety.route("/user/signin", methods=['POST'])
def user_signing_in():
    name = request.json['user_name']
    passw = request.json['password']
    # dob = request.json['dob']

    #
    dbreturn = userQuery.sign_in(name, passw)

    # sign_up(data)
    return jsonify(dbreturn)

# endregion


if __name__ == "__main__":
    global QUERY, userQuery
    QUERY = {}
    sql_conn = Postgres_Query().get_db_connection()

    ### init query dict ###
    QUERY['camera'] = Camera_Query(sql_conn)
    QUERY['area'] = Area_Query(sql_conn)
    QUERY['moving'] = Moving_Query(sql_conn)
    userQuery = User_Query(sql_conn)
    QUERY['safety_gear'] = Safety_Gears_Query(sql_conn)
    #QUERY['user'] = User_Query(sql_conn)

    # AIbridge = AI_Bridge(QUERY)

    # start flask server
    print('Server started on {0}'.format(RESTAPI_PORT))
    safetyrun('0.0.0.0', RESTAPI_PORT, True)
