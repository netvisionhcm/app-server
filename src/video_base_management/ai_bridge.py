from __future__ import print_function
from config_utils import read_grpc_config
from postgres_query import Postgres_Query
from os import remove
from threading import Thread 
from collections import deque
from image_actions import SCREENSHOTS, PERSON

import image_actions as vImage
import numpy as np
import time
import pickle
import grpc
import cv2
import json
import ai_interface_pb2
import ai_interface_pb2_grpc


grpc_server, grpc_port = read_grpc_config()

class AI_Bridge(object):
    def __init__(self, QUERY):

        self.sql_query = QUERY
        self.channel = grpc.insecure_channel(
            '%s:%s' % (grpc_server, grpc_port))
        self.stub = ai_interface_pb2_grpc.AnalyServiceStub(self.channel)

        self.area_pools = {}
        self.frame_pools = {}
        self.grpc_pools = {}
        # ['camera_id'] = [thread, isRunning, interval]
        self.video_thread_pools = {}

        self.camera_init()

    def start_video_thread(self, camera_id):

        if camera_id in list(self.video_thread_pools):
            pass
        else:
            th = Thread(target=lambda: self.frame_actions(camera_id))
            isRunning = True
            interval = 1/24
            self.video_thread_pools[camera_id] = [th, isRunning, interval]
            th.start()

    def stop_video_thread(self, camera_id):
        if camera_id in list(self.video_thread_pools):
            isRunning = False
            self.video_thread_pools[camera_id][1] = isRunning
            th = self.video_thread_pools[camera_id][0]
            th.join()
            del self.video_thread_pools[camera_id]

    def add_grpc_connection(self, ai_analysis_server, grpc_server, grpc_port):
        if ai_analysis_server in list(self.grpc_pools):
            pass
        else:
            channel = grpc.insecure_channel('%s:%s' % (grpc_server, grpc_port))
            stub = ai_interface_pb2_grpc.AnalyServiceStub(channel)
            self.grpc_pools[ai_analysis_server] = stub

    def get_frame(self, camera_id):
        if camera_id in list(self.frame_pools):
            while len(self.frame_pools[camera_id]) == 0:
                time.sleep(0.1)
            return self.frame_pools[camera_id][0]
        else:
            return []

    def get_video_frame(self, camera_id, scale):
        frame = self.get_frame(camera_id)
        if len(frame) == 0:
            return []
        if len(scale) > 1:
            frame = cv2.resize(frame, scale)
        return frame

    def get_video_size(self, camera_id):
        frame = self.get_frame(camera_id)
        if len(frame) == 0:
            return (0, 0)

        (H, W) = frame.shape[:2]
        return (W, H)

    def add_camera(self, camera_id, location, coordinates, address, port, uri):
        respone = self.stub.AddCamera(ai_interface_pb2.CameraInfo(camera_id=camera_id,
                                                                  location=location,
                                                                  coordinates=coordinates,
                                                                  address=address,
                                                                  port=port,
                                                                  uri=uri))

        print(respone.success)
        if respone.success:
            self.frame_pools[camera_id] = deque(maxlen=3)
            self.start_video_thread(camera_id)

            success, results = self.sql_query['camera'].add_camera(camera_id, location, coordinates,
                                                         address, port, uri)
            print('Add camera: %s' % results)

            # SAVE screenshot for camera_id
            scale = ()
            frame = self.get_video_frame(camera_id, scale)
            vImage.saveImage(frame, SCREENSHOTS + camera_id)
            return success, results
        return False, 'Cannot add camera'

    def del_camera(self, camera_id):
        respone = self.stub.DelCamera(
            ai_interface_pb2.CameraId(camera_id=camera_id))
        print(respone)
        if respone.success:
            self.stop_video_thread(camera_id)
            success, results = self.sql_query['camera'].delete_camera(camera_id)

            # DELETE screenshot for camera_id
            vImage.delImage(SCREENSHOTS + camera_id)

        return success, results

    def frame_actions(self, camera_id):
        # Save camera screenshot
        while True:
            isRunning = self.video_thread_pools[camera_id][1]
            interval = self.video_thread_pools[camera_id][2]
            if not isRunning:
                break
            time.sleep(interval)

            warning_list, danger_list = [], []
            if camera_id in list(self.area_pools):
                warning_list = self.area_pools[camera_id][0]
                danger_list = self.area_pools[camera_id][1]

            respone = self.stub.GetFrames(ai_interface_pb2.PreProcessingData(camera_id=camera_id,
                                                                             warning_list=warning_list,
                                                                             danger_list=danger_list))

            # print(respone.persons)
            frame = pickle.loads(respone.frame)

            frame = self.draw_areas_frame(frame, warning_list, danger_list)

            persons = respone.persons
            for person in persons:
                # print(person.warning)
                # print(person.danger)
                frame = self.alarm_actions(frame, camera_id, person)

            self.frame_pools[camera_id].append(frame)

    def make_area_pools(self, camera_id, names, warnings, dangers):
        w, d = 0, 0
        wlist, dlist = [], []
        for name in names:
            if w < len(warnings):
                bw = []
                for warn in warnings[w]:
                    c = ai_interface_pb2.Coordinate(posX=warn[0], posY=warn[1])
                    bw.append(c)
                if len(bw) > 0:
                    a = ai_interface_pb2.Area(name=name, border=bw)
                    wlist.append(a)
                w += 1
                continue

            if d < len(dangers):
                bd = []
                for danger in dangers[d]:
                    c = ai_interface_pb2.Coordinate(
                        posX=danger[0], posY=danger[1])
                    bd.append(c)
                if len(bd) > 0:
                    a = ai_interface_pb2.Area(name=name, border=bd)
                    dlist.append(a)
                d += 1
                continue
        self.area_pools[camera_id] = [wlist, dlist]

    def draw_areas_frame(self, frame, warnings, dangers):
        for ww in warnings:
            for i in range(len(ww.border)):
                w0 = ww.border[i]
                if i+1 == len(ww.border):
                    w1 = ww.border[0]
                else:
                    w1 = ww.border[i+1]
                cv2.line(frame, pt1=(w0.posX, w0.posY), pt2=(w1.posX, w1.posY), color=(
                    0, 255, 255), thickness=3, lineType=8, shift=0)

        for dd in dangers:
            for i in range(len(dd.border)):
                d0 = dd.border[i]
                if i+1 == len(dd.border):
                    d1 = dd.border[0]
                else:
                    d1 = dd.border[i+1]
                cv2.line(frame, pt1=(d0.posX, d0.posY), pt2=(d1.posX, d1.posY), color=(
                    0, 0, 255), thickness=3, lineType=8, shift=0)
        return frame

    def alarm_actions(self, frame, camera_id, person):
        intbbox = [person.bbox.xMin, person.bbox.yMin,
                   person.bbox.xMax, person.bbox.yMax]
        if person.warning:
            cv2.putText(frame, "Warning", (256, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 0), 3, cv2.LINE_AA)
            self.sql_query['moving'].add_moving_log(
                camera_id, person.area_name, person.time_in, person.person_id, json.dumps(intbbox), "warning")
            vImage.saveImage(frame, PERSON + person.time_in)
        if person.danger:
            cv2.putText(frame, "Danger", (256, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 3, cv2.LINE_AA)
            self.sql_query['moving'].add_moving_log(
                camera_id, person.area_name, person.time_in, person.person_id, json.dumps(intbbox), "danger")
            vImage.saveImage(frame, PERSON + person.time_in)

        return frame

    def camera_init(self):
        # init by load list camera from database
        print('Waiting for load camera list...')
        camera_list = self.sql_query['camera'].get_camera_list()
        self.load_camera_list(camera_list)
        print('Load camera done.')

        # init areas tracking from db
        print('Waiting for init areas...')
        for camera in camera_list:
            camera_id = camera[0]
            # get areas tracking from db
            names, warns, dangers = self.sql_query['area'].get_area_tracking(camera_id)
            # make areas pools
            self.make_area_pools(camera_id, names, warns, dangers)
        print('Init done.')

    def load_camera_list(self, camera_list):
        for camera in camera_list:
            camera_id = camera[0]
            host = camera[3]
            port = camera[4]
            location = camera[1]
            coordinates = camera[2]
            uri = camera[5]
            print('Load camera %s' % camera_id)
            self.add_camera(camera_id, location, coordinates,
                            host, str(port), uri)


'''    
if __name__ == "__main__":   
    AI = ai_bridge()
    AI.add_camera('cam001', 'vn', '0,0', '113.173.15.32', '16677', 'videofeed')
    print('add done')
    
    AI.del_camera('cam001')
    print('del done')
'''
