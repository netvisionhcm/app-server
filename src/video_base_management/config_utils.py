import json
#FILECONFIG = "google_config.json"
DBCONFIG = 'postgressql.json'

GRPCCONFIG = 'grpc_service.json'


def read_grpc_config():
    with open(GRPCCONFIG, "r") as jsonFile:
        data = json.load(jsonFile)

    return data['server_ip'], data['ai_port']


def read_db_config():
    with open(DBCONFIG, "r") as jsonFile:
        data = json.load(jsonFile)

    return data['db_user'], data['db_pass'], data['db_name'], data['server_ip']

def key_duration_config():
    with open(GRPCCONFIG, "r") as jsonFile:
        data = json.load(jsonFile)
    return data['session_key_duration'], data['autho_key_duration']
