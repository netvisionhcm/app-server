
from object_tracking import ObjectPools
from ipCamera import CameraPools
from ai_logging import LOG

import pickle
import time
import cv2
import ai_interface_pb2, ai_interface_pb2_grpc
import ipCamera as Camera


class ai_interface(ai_interface_pb2_grpc.AnalyServiceServicer):

    def __init__(self):
        self.INTERVAL = 3
        self.frame = None
        self.area_equation = None
        self.warnings = []
        self.dangers = []
        self.person_time_pools = {}
        LOG.info("interface init.")
    
    def AddCamera(self, camera, context):
        global CameraPools
        LOG.info("Add camera")
        LOG.info("camera_id: {}".format(camera.camera_id))
        LOG.info("location: {}".format(camera.location))
        LOG.info("coordinates: {}".format(camera.coordinates))
        LOG.info("address: {}".format(camera.address))
        LOG.info("port: {}".format(camera.port))
        LOG.info("uri: {}".format(camera.uri))
        Newcamera = Camera.ipCamera(camera.camera_id, 'http', camera.address, camera.port, camera.location, camera.uri)
        Camera.addCameraPools(Newcamera)
        
        if camera.camera_id in CameraPools:
            return ai_interface_pb2.CameraResult(success= True, message='Camera Id: %s was added' % camera.camera_id)
        return ai_interface_pb2.CameraResult(success= False, message='Camera Id: %s was not added' % camera.camera_id)
        
    
    def DelCamera(self, info, context):
        LOG.info("Del camera")
        LOG.info("camera_id: {}".format(info.camera_id))
        Camera.delCamera(info.camera_id)
        return ai_interface_pb2.CameraResult(success= True, message='Camera Id: %s was deleted' % info.camera_id)
        
    
    
    def GetFrames(self, data, context):
        global ObjectPools
        if data.camera_id in list(ObjectPools):
            ObjectPools['lock'].acquire()
            obtracker = ObjectPools[data.camera_id]
            ObjectPools['lock'].release()
            while True:
                if len(obtracker.framePools) > 0:
                    frame_info = obtracker.framePools[0]
                    break
                time.sleep(1)
        else:
            return ai_interface_pb2.ProcessedData(frame=[], persons=[])
            
        self.frame = frame_info['frame']
        persons = frame_info['persons']
        
        # Draw area 
        warnings = data.warning_list
        dangers = data.danger_list
        
        boolWarning = False
        boolDanger = False 
        area_name = ''
        returnAll = []
        for person in persons:
            for warning in warnings:
                #self.drawArea('warning', warning.border)                                
                if self.isWarning(person, warning.name, warning.border, obtracker.area_equation):
                    boolWarning =  True
                    area_name = warning.name
                    break
            

            for danger in dangers:
                #self.drawArea('danger', danger.border)
                if self.isDanger(person, danger.name, danger.border, obtracker.area_equation):
                    boolDanger =  True
                    boolWarning =  False
                    area_name = danger.name
                    break
            

            # Save arlam state by INTERVAL = 2s
            if boolDanger or boolWarning:
                if person['person_id'] in list(self.person_time_pools):
                    ti = time.time()
                    if (ti - self.person_time_pools[person['person_id']] > 2):
                        self.person_time_pools[person['person_id']] = ti
                    else:
                        boolWarning =  False
                        boolDanger =  False
                else:
                    self.person_time_pools[person['person_id']] = time.time()


            returnBbox = ai_interface_pb2.Bbox(xMin= int(person['bbox'][0]), 
                                                yMin=int(person['bbox'][1]), 
                                                xMax=int(person['bbox'][2]),    
                                                yMax=int(person['bbox'][3]))
                                                
            returnPerson = ai_interface_pb2.TrackingData(bbox = returnBbox, 
                                                        person_id = person['person_id'], 
                                                        equiqments = person['equiqments'], 
                                                        time_in = person['time_in'], 
                                                        area_name = area_name,
                                                        warning = boolWarning, 
                                                        danger = boolDanger)

            boolWarning, boolDanger = False, False
            returnAll.append(returnPerson)
            #print(returnPerson)

        #self.saveImage(self.frame, 'helloxxx')
        #print('Save image .......................')
        
        return ai_interface_pb2.ProcessedData(frame=pickle.dumps(self.frame), persons=returnAll)
            
    #def saveImage(self, frame, path):
    #    cv2.imwrite("%s.png" % path, frame)
    '''
    def drawArea(self, kind, areas):
        COLOR = (0, 0, 0)
        if kind == 'warning':
            COLOR = (255, 255, 0)
        if kind == 'danger':
            COLOR = (255, 0, 0)
        for area in areas:
            i = 0
            while i < len(area):
                w0 = area[i]
                if i+1 == len(area):
                    w1 = area[0]
                else:
                    w1 = area[i+1]
                cv2.line(self.frame, pt1=(w0[0], w0[1]), pt2=(w1[0], w1[1]), color=COLOR, thickness=3, lineType=8, shift=0)
                i += 1
    '''

    
    def isDanger(self, person, area_name, border, areaEquation):
        areas = []
        for r in border:
            area = [r.posX, r.posY]
            areas.append(area)

        areaEquation.setAreaname(area_name)
        areaEquation.setDanger(areas)
        
        bbox = person["bbox"]
        point1 = [int(bbox[0]), int(bbox[3])] # xmin, ymax
        point2 = [int(bbox[2]), int(bbox[3])] # xmax, ymax
        
        return not areaEquation.checkDanger([point1, point2])

    
    def isWarning(self, person, area_name, border, areaEquation):
        areas = []
        for r in border:
            area = [r.posX, r.posY]
            areas.append(area)

        areaEquation.setAreaname(area_name)
        areaEquation.setWarning(areas)
        
        bbox = person["bbox"]
        point1 = [int(bbox[0]), int(bbox[3])] # xmin, ymax
        point2 = [int(bbox[2]), int(bbox[3])] # xmax, ymax
        
        return not areaEquation.checkWarning([point1, point2])


    

