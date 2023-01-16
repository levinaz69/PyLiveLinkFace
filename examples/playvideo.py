import socket
import time
import random
import csv
import sys
import numpy as np
import datetime

from timecode import Timecode
from pylivelinkface import PyLiveLinkFace, FaceBlendShape

import os
import cv2

trackPath = "H:/UnrealProjects/LiveLinkData/livelink/20230112_MySlate_15"
trackName = "MySlate_15_KiP"
videoName = trackName + ".mov"
takeName = trackName + "_cal.csv"

SHOW_VIDEO = True
DEFAULT_FPS = 60

UDP_IP = "127.0.0.1"
UDP_PORT = 11111

py_face = PyLiveLinkFace()
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    s.connect((UDP_IP, UDP_PORT))
        
    filename = trackPath + os.sep + takeName
    # filename = sys.argv[1]
    data = []
    timecodes = []
    with open(filename) as fcsv:
        reader = csv.reader(fcsv)
        try:
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                datarow = np.array(row[2:], dtype=np.float32) if len(row[2:]) == 61 else np.zeros(61, dtype=np.float32)
                tcstr = row[0].split('.')
                tc = (Timecode(DEFAULT_FPS, tcstr[0]), int(tcstr[1])/1000) 
                data.append(datarow)
                timecodes.append(tc)
            data = np.array([*data], dtype=np.float32)
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))

    data_frame_count = data.shape[0]-1

    trackbarName = 'trackbar'
    winName = "LLPlayer"
    currentFrame = 0.0

    def onTrackbarChange(current_frame):
        currentFrame = current_frame

    if SHOW_VIDEO == True:
        cap = cv2.VideoCapture(trackPath + os.sep + videoName)
        video_frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        # fps = cap.get(cv2.CAP_PROP_FPS)
        cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)
    else:
        video_frame_count = data_frame_count
    fps = DEFAULT_FPS

    cv2.namedWindow(winName)
    cv2.createTrackbar(trackbarName, winName, 0, int(video_frame_count), onTrackbarChange)

    # Wait start 
    if cv2.waitKey(0) == 27:
        exit()

    elapse = 1.0
    timer = time.time()
    start_tc = timecodes[0][0]
    data_idx = 0
    frame = 0
    while True:
        cur_tc = start_tc + frame

        while data_idx < len(data):
            if timecodes[data_idx][0] < cur_tc:
                tc = timecodes[data_idx]
                for i in range(data.shape[1]):
                    py_face.set_blendshape(i, data[data_idx][i])
                s.sendall(py_face.encode(tc[0], tc[1]))
                data_idx += 1
            else:
                break
        else:
            break


        if SHOW_VIDEO == True:
            _, image = cap.read()
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            image = cv2.resize(image, (image.shape[1]//2, image.shape[0]//2))
            cv2.imshow(winName, image)

        cv2.setTrackbarPos(trackbarName, winName, frame)

        now = time.time()
        elapse = now - timer
        timer = now

        wait = max(1.0/fps - elapse, 0)
        playfps = 1.0/(wait + elapse)
        print('elapse: {} playfps: {} wait: {}'.format(str(elapse), str(playfps), str(wait)))

        key = cv2.waitKey(max(round(wait * 1000), 1))
        if key == 27:   # ESC
            break
        elif key == 32:    # SPACE
            while (key2:=cv2.waitKey(0)) != 27:
                if key2 == 32:
                    break
            else:
                break

        frame += 1

        if frame == video_frame_count: break
        
        # if frame == data.shape[0]-1: break
        # if frame == data.shape[0]-1: frame = 0

    if SHOW_VIDEO == True:
        cap.release()
    cv2.destroyAllWindows()

except KeyboardInterrupt:
    pass
        
finally: 
    s.close()

