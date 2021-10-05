
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt

from threading import Thread, Lock
from collections import deque

from deep_sort import preprocessing
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from deep_sort.detection import Detection as ddet

from yolov4_detection import ObjectDetectionEngine

from datetime import datetime

import areaEquation as Area

from ai_logging import LOG

max_cosine_distance = 0.5
nms_max_overlap = 0.3
nn_budget = None

METRIC = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
TRACKER = Tracker(METRIC)

# Object pool for each video line
ObjectPools={'lock': Lock(), 'cam000xxx' : None}

class ObjectTracking(Thread):
    def __init__(self, camera_id, stream):
        Thread.__init__(self)
        self.QUELENG = 3
        self.isrun = False
        self.camera_id = camera_id
        self.stream = stream
        self.origin_framePools = deque(maxlen=self.QUELENG)
        self.framePools = deque(maxlen=self.QUELENG)
        self.object_detection_engine = ObjectDetectionEngine()
        
        ### area equaqion init ###
        self.area_equation = Area.areaEquation(self.camera_id, '', [], [])
        
    def run(self):
        # by default VideoCapture returns float instead of int
        
        #LOG.info(self.stream)
        #width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        #LOG.info(width)
        #height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
        #LOG.info(height)
        #fps = int(self.stream.get(cv2.CAP_PROP_FPS))
        #LOG.info(fps)
        

        ### use for output avi video file ###
        #codec = cv2.VideoWriter_fourcc(*'MJPG')
        #out = cv2.VideoWriter('video_out.avi', codec, fps, (width, height))

        
        self.isrun = True

        th = Thread(target=lambda: self.get_frame_thread())
        th.start()
        while len(self.origin_framePools) == 0:
            time.sleep(0.1)
        

        while self.isrun:
            (return_value, frame) = self.origin_framePools[0]
            #return_value, frame = self.stream.read()
            #LOG.info(return_value)
            if return_value:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #image = Image.fromarray(frame)
            else:
                LOG.info('Video has ended or failed, try a different video format!')
                break
            #execute object detect
            start_time = time.time()
            results = self.object_detection_engine.perform_detection(frame)
            
            
            label_list = []
            my_rects = []
            my_labels = []
            
            for item in results:
                xmin = item[0]
                ymin = item[1]
                xmax = item[2]
                ymax = item[3]
                label = item[4]

                feature_w = abs(xmin-xmax)
                feature_h = abs(ymin-ymax)
                my_rects.append([xmin, ymin, feature_w, feature_h])
                my_labels.append(label)

            result_data = []
            detections = [Detection(bbox, 1.0, None,label) for bbox, label in zip(my_rects, my_labels)]
            
            #initialize color map
            cmap = plt.get_cmap('tab20b')
            colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]
        
            boxes = np.array([d.tlwh for d in detections])
            scores = np.array([d.confidence for d in detections])
            indices = preprocessing.non_max_suppression(boxes, nms_max_overlap, scores)
            detections = [detections[i] for i in indices]

            TRACKER.predict()
            TRACKER.update(detections)

            deleted_id = []
            for track in TRACKER.deleted_tracks:
                deleted_id.append(track.track_id)
            
            persons = []
            for track in TRACKER.tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue
                bbox = track.to_tlbr()
                class_name = 'person'
                result_data.append((bbox[0],bbox[1],bbox[2],bbox[3],int(track.track_id),track.label,deleted_id))    
                
                # draw bbox on screen
                color = colors[int(track.track_id) % len(colors)]
                color = [i * 255 for i in color]
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color, 2)
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1]-30)), (int(bbox[0])+(len(class_name)+len(str(track.track_id)))*17, int(bbox[1])), color, -1)
                cv2.putText(frame, class_name + "-" + str(track.track_id),(int(bbox[0]), int(bbox[1]-10)),0, 0.75, (255,255,255),2)
                
                '''
                # if enable info flag then LOG.info details about each track
                # checking area for warning and danger
                #LOG.info(len(bbox))
                #LOG.info("Tracker ID: {}, Class: {},  BBox Coords (xmin, ymin, xmax, ymax): {}".format(str(track.track_id), class_name, (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))))
                ### bbox === [xmin, ymin, xmax, ymax]  ###
                #point1 = [int(bbox[0]), int(bbox[1])] # xmin, ymin
                #point2 = [int(bbox[2]), int(bbox[1])] # xmax, ymin
                #point1 = [int(bbox[0]), int(bbox[3])] # xmin, ymax
                #point2 = [int(bbox[2]), int(bbox[3])] # xmax, ymax
                '''

                person = {}
                person["person_id"] = track.track_id
                person["bbox"] = bbox
                person["time_in"] = str(datetime.now())
                person["equiqments"] = []
                persons.append(person)

                        
  
            # calculate frames per second of running detections
            fps = 1.0 / (time.time() - start_time)
            cv2.putText(frame, "FPS: %.2f" % fps, (8, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (100, 255, 0), 3, cv2.LINE_AA)
            #LOG.info("CameraID: %s, FPS: %.2f" % (self.camera_id, fps))

            result = np.asarray(frame)
            result = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            #LOG.info(type(result))
            frame_info = {}
            frame_info['frame'] = result
            frame_info['persons'] = persons
            #LOG.info(frame_info)
            self.framePools.append(frame_info)
            
            #out.write(result)
            
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        th.join()

    def get_frame_thread(self):
        while self.isrun:
            return_value, frame = self.stream.read()
            self.origin_framePools.append((return_value, frame))
            time.sleep(1/33)

    def stop(self):
        self.isrun = False
        
        