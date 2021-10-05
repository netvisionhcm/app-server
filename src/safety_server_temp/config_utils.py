import json
#FILECONFIG = "google_config.json"
GRPCCONFIG='app_service.json'

def get_ip_port():
    with open(GRPCCONFIG,"r") as jsonFile:
        data = json.load(jsonFile)

    return data['server_ip'], data['server_port']