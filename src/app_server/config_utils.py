import json
#FILECONFIG = "google_config.json"
GRPCCONFIG='app_service.json'
DBCONFIG='postgressql.json'


def read_app_config():
    with open(GRPCCONFIG,"r") as jsonFile:
        data = json.load(jsonFile)

    return data['app_server_ip'],data['app_port']


def get_video_server_ip():
    with open(GRPCCONFIG,"r") as jsonFile:
        data = json.load(jsonFile)

    return data['video_server_ip'], data['video_server_port']

def get_safety_server_ip():
    with open(GRPCCONFIG,"r") as jsonFile:
        data = json.load(jsonFile)

    return data['safety_server_ip'], data['safety_server_port']

def read_db_config():
    with open(DBCONFIG, "r") as jsonFile:
        data = json.load(jsonFile)

    return data['db_user'], data['db_pass'], data['db_name'], data['server_ip']

def key_duration_config():
    with open(GRPCCONFIG, "r") as jsonFile:
        data = json.load(jsonFile)
    return data['session_key_duration'], data['autho_key_duration']