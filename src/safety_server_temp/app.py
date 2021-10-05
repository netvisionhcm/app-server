from flask import Response, request, jsonify
from flask import Flask
from flask import send_file
import requests, json
from config_utils import get_ip_port


app = Flask(__name__)

app.config["DEBUG"] = True

SERVER_IP, SERVER_PORT =  get_ip_port()


@app.route("/spatial_info", methods=['POST'])
def spatial_info():
    request_spatial_info = request.json['requestSpatialInfo']
    print('Safety server a request spatial info')
    response = {
        "buildingGroups" : {
            "id": 0,
            "name": "Vinhome center park",
            "buildings": [
                {
                    "id": 0,
                    "name": "Landmark",
                    "fields": [
                        {
                            "id": 0,
                            "floorIndex": 0,
                            "name": "lobby"
                        },
                        {
                            "id": 1,
                            "floorIndex": 1,
                            "name": "Level 1"
                        }
                    ]
                },
                {
                    "id": 1,
                    "name": "Citizen Block",
                    "fields": [
                        {
                            "id": 2,
                            "floorIndex": 0,
                            "name": "Level 2"
                        },
                        {
                            "id": 3,
                            "floorIndex": 1,
                            "name": "Level 3"
                        }
                    ]
                }
            ]
        },
        "outdoorFields" :  [
            {
                "id": 0,
                "floorIndex": 0,
                "name": "lobby"
            },
            {
                "id": 1,
                "floorIndex": 1,
                "name": "Level 1"
            }
        ]}
    return jsonify(response)

@app.route("/user_report", methods=['POST'])
def user_report():
    reportManualAlarm = request.json['reportManualAlarm']
    print('Safety server receive a report alarm')
    response = {
        "reportManualAlarm": {
            "reportAlarm": {
                "accident_type": {
                "fire": True
                },
                "fieldID": None,
                "buildingID": 1,
                "notifications": "1-1동 화재발생!!!"
            }
        }
    }

    return jsonify(response)

@app.route("/location_info", methods=['POST'])
def location_info():
    
    # params got from app server
    requestUserPosition = request.json['requestUserPosition']
    id = requestUserPosition["id"]
    
    response = {
        "id": "id01",
        "x": 41.40338,
        "y":  2.17403,
        "fieldID": "Basement landmark" 
    }


    return jsonify(response)

# app server call to login/out event
@app.route("/log_event", methods=['POST'])
def log_event():
    
    # params got from app server
    loginEvent = request.json['loginEvent']
    id = loginEvent['id']
    login = loginEvent['login']

    return Response(response=json.dumps({'success': True, 'message' : 'Log in/out event done'}), status=200, mimetype="application/json")


if __name__ == "__main__":

    # start flask server
    print('Server started on {0}'.format(SERVER_PORT))
    app.run(debug=True, host=SERVER_IP, port=SERVER_PORT, use_reloader=True)
