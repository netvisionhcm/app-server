
from concurrent import futures
from ai_interface import ai_interface
from config_utils import *


import ai_interface_pb2, ai_interface_pb2_grpc

import time
import grpc

from ai_logging import Logging

LOG = Logging().getLogger()

server_ip, grpc_port = read_grpc_config()


_ONE_DAY_IN_SECONDS = 0

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ai_interface_pb2_grpc.add_AnalyServiceServicer_to_server(ai_interface(), server)
    server.add_insecure_port('[::]:%s' % grpc_port)
    server.start()
    LOG.info('Server started at %s:%s' % (server_ip, grpc_port))
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()