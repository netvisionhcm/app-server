### image actions ###
import cv2

from os import remove

SCREENSHOTS = 'static/screenshots/'
PERSON = 'static/person_capture/'


def saveImage(frame, path):
    cv2.imwrite("%s.png" % path, frame)


def delImage(path):
    remove("%s.png" % path)


def getImage(camera_id):
    frame = cv2.imread(SCREENSHOTS + "%s.png" % camera_id)
    return frame


def getImage_person(time_in):
    frame = cv2.imread(PERSON + "%s.png" % time_in)
    return frame
