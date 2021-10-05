"""Access IP Camera in Python OpenCV"""
import cv2
import requests
import threading 

from os import remove
from object_tracking import ObjectTracking, ObjectPools
from ai_logging import LOG

# Camera pool for each input ip_camera
CameraPools={'lock': threading.Lock(), 'cam000xxx' : None}

class ipCamera(object):
    def __init__(self, cameraID, protocol, host, port, localtion, uri):
        self.cameraID = cameraID
        self.protocol = protocol
        self.host = host
        self.port = port
        self.localtion = localtion
        if uri:
            self.uri = uri
        else:
            self.uri = 'videofeed?username=&password'
    
    def getVideoStream(self):
        link = "%s://%s:%s/" % (self.protocol, self.host, self.port)
        print(link)
        try:
            request = requests.get(link, verify=False, timeout=3)
            if request.status_code == 200:
                link = link + self.uri
                print(link)
                self.stream = cv2.VideoCapture(link)
                #print(self.stream)
                return self.stream
            else:
                LOG.warning("Cannot connect to %s://%s:%s" % (self.protocol, self.host, self.port))
                self.stream = None
                return None
        except:
            LOG.warning("Cannot connect to %s://%s:%s" % (self.protocol, self.host, self.port))
            self.stream = None
            return None

        
    def getProto(self):
        return self.protocol
        
    def getHost(self):
        return self.host
        
    def getPort(self):
        return self.port

        
def addCameraPools(cam):
    global CameraPools
    CameraPools['lock'].acquire()
    CameraPools[cam.cameraID] = cam
    CameraPools['lock'].release()
    cameraHandle()
    
    return True
    
def getCameraPools(cam):
    global CameraPools
    return CameraPools
    
def delCamera(cam_id):
    global CameraPools
    CameraPools['lock'].acquire()
    if cam_id in list(CameraPools):
        del CameraPools[cam_id]
    CameraPools['lock'].release()
    cameraHandle()
    return
    
def cameraHandle():
    global CameraPools, ObjectPools

    # add new object tracking for new camera
    for key in list(CameraPools):
        print(CameraPools)
        if key in ObjectPools or key == 'lock' or key == 'cam000xxx':
            continue
        else:
            #ip_camera Object
            print("ip_camera Object")
            camera = CameraPools[key]
            camera.getVideoStream()
            if camera.stream == None:
                print("This camera is invalid, remove its")
                CameraPools['lock'].acquire()
                del CameraPools[key]
                CameraPools['lock'].release()
                #if len(CameraPools) == 2:
                #    break
                
            else:
                print("start tracking")
                objectTrack = ObjectTracking(camera.cameraID, camera.stream)
                objectTrack.isDaemon = True
                objectTrack.start()
                print("start tracking start done")
                
                #add object tracking to pools
                ObjectPools['lock'].acquire()
                ObjectPools[camera.cameraID] = objectTrack
                ObjectPools['lock'].release()
            
    # del object tracking for removed camera
    for key in list(ObjectPools):
        if key in CameraPools or key == 'lock' or key == 'cam000xxx':
            continue
        else:
            ObjectPools[key].stop() 
            ("This camera is removed, so remove object also.")
            del ObjectPools[key]
    return
    
def loadCameraList(camera_list):
    print(camera_list)
    for camera in camera_list:
        exist = False
        for key in list(ObjectPools):
            if key == camera[0]:
                exist = True
                break
        if exist == False:
            camera_id = camera[0]
            host = camera[3]
            port = camera[4]
            location = camera[1]
            uri = camera[5]
            Newcamera = ipCamera(camera_id, 'http', 
                                        host, port, location, uri)
            addCameraPools(Newcamera)
    return camera_list
