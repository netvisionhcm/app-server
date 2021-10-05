import cv2
import time
import signal
from ai_logging import Logging
from object_tracking import ObjectTracking

LOG = Logging().getLogger()

VC = cv2.VideoCapture('video.avi')

def handler(signum, frame):
    objectTrack.stop()
    exit(1)
    
signal.signal(signal.SIGINT, handler)


if __name__ == '__main__':
    global objectTrack
    print("tracking init")
    objectTrack = ObjectTracking('cam_test', VC)
    objectTrack.isDaemon = True
    objectTrack.start()
    print("thread ...")
    
    while True:
        time.sleep(0.5)
        
    
    
