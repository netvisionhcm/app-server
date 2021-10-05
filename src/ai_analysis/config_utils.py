import json
#FILECONFIG = "google_config.json"
GRPCCONFIG='grpc_service.json'


def read_grpc_config():
    with open(GRPCCONFIG,"r") as jsonFile:
        data = json.load(jsonFile)

    return data['server_ip'],data['ai_port']