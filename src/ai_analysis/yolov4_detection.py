# example usage: python yolo_video.py -i video.mp4 -o video_out.avi
import argparse
import glob
import time
import logging
import cv2
import numpy as np
import threading

from pathlib import Path
from ai_logging import LOG


class ObjectDetectionEngine(object):
    def __init__(self):
        self.height = 720
        self.width = 1280
        self.confidence = 0.5
        self.threshold = 0.4
        self.weights = glob.glob("yolo/*.weights")[0]
        self.labels = glob.glob("yolo/*.txt")[0]
        self.cfg = glob.glob("yolo/*.cfg")[0]
        self.num_net = 10
        self.net_dict = {}
        self.lock = threading.Lock()

        LOG.info("Using {} weights ,{} configs and {} labels.".format(
            self.weights, self.cfg, self.labels))

        self.class_names = list()
        with open(self.labels, "r") as f:
            self.class_names = [cname.strip() for cname in f.readlines()]

        self.COLORS = np.random.randint(0, 255, size=(len(self.class_names), 3), dtype="uint8")

        for i in range(self.num_net):
            start_time = time.time()
            #net = cv2.dnn.readNetFromCaffe('ssd/MobileNetSSD_deploy.prototxt', 'ssd/MobileNetSSD_deploy.caffemodel')
            net = cv2.dnn.readNetFromDarknet(self.cfg, self.weights)
            #net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            #net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)


            layer = net.getLayerNames()
            layer = [layer[i[0] - 1] for i in net.getUnconnectedOutLayers()]
            self.net_dict[i] = {'net':net,'layer':layer,'status':1}
            #print('Creation time:',time.time()-start_time)
            
        #self.writer = None
    def get_available_net(self):
        for i in range(self.num_net):
            ret_dict = self.net_dict[i]
            if ret_dict['status'] == 1: 
                self.net_dict[i]['status'] = 0
                return ret_dict['net'],ret_dict['layer'],i

        return None, None    
    
    
    def perform_detection(self,frm):
        (H, W) = frm.shape[:2]
        blob = cv2.dnn.blobFromImage(frm, 1/255.0, (416, 416),
                                     swapRB=True, crop=False)
        self.lock.acquire()
        net,layer,idx = self.get_available_net()
        self.lock.release()
        net.setInput(blob)
        #start_time = time.time()
        layerOutputs = net.forward(layer)
        #end_time = time.time()

        boxes = []
        classIds = []
        confidences = []
        results = []
        for output in layerOutputs:
            
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                if confidence > self.confidence:
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width/2))
                    y = int(centerY - (height/2))

                    boxes.append([x, y, int(width), int(height)])
                    classIds.append(classID)
                    confidences.append(float(confidence))

        idxs = cv2.dnn.NMSBoxes(
            boxes, confidences, self.confidence, self.threshold)

        if len(idxs) > 0:
            for i in idxs.flatten():
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])

                #color = [int(c) for c in self.COLORS[classIds[i]]]
                #cv2.rectangle(frm, (x, y), (x + w, y + h), color, 2)
                label = self.class_names[classIds[i]]
                #if label not in self.object_db:
                #    continue
                
                results.append((x,y,x + w,y + h,label))
                '''
                text = "{}: {:.4f}".format(
                    self.class_names[classIds[i]], confidences[i])
                cv2.putText(frm, text, (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                fps_label = "FPS: %.2f" % (1 / (end_time - start_time))
                cv2.putText(frm, fps_label, (0, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)   
                '''            

        self.lock.acquire()
        self.net_dict[idx]['status'] = 1
        self.lock.release()
        
        return results
                            
        
