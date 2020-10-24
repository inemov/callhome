# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 18:29:17 2020

@author: Ivan Nemov
"""


import cv2
import time
import numpy as np
from PyQt5 import QtCore, QtGui
from threading import Thread
from picamera.array import PiRGBArray
from picamera import PiCamera

class detection_message(QtCore.QObject):
    detected_coordinates_signal = QtCore.pyqtSignal(list)                 #update coordinates of detedcted person
    video_frame_signal = QtCore.pyqtSignal(QtGui.QImage)

class detection(Thread):
    def __init__(self, _signal_message):
        Thread.__init__(self)
        self._signal_message = _signal_message
        self.destroyed = False
        self.preview_enabled = True
    
    def destroy(self):
        self.destroyed = True
        
    def change_preview(self, enabled):
        self.preview_enabled = enabled
    
    def run(self):
        
        camera = PiCamera()
        w = 640
        h = 480
        camera.resolution = (w, h)
        camera.framerate = 32
        camera.vflip = True
        
        cap = PiRGBArray(camera, size=(w, h))
        time.sleep(0.1)
        
        detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        detect_object = False
        
        for frame in camera.capture_continuous(cap, format='bgr', use_video_port = True):
            # sample rate
            time.sleep(0.005)
    
            # Capture frame-by-frame
            image = frame.array

            if detect_object == False:
                try:
                    # detect people in the image
                    rectangles_w_h, levels, weights = detector.detectMultiScale3(image, scaleFactor=1.05, minNeighbors=9, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE, outputRejectLevels=True)
                    
                    # distance to centers
                    centers = np.array([pow((pow((x+0.5*(width-w)),2)+pow((y+0.5*(hight-h)),2)),0.5) for (x, y, width, hight) in rectangles_w_h], dtype=np.int16)
                    
                    # pick people closest to image center
                    if centers.size != 0:
                        if weights[np.argmin(centers)] > 6:
                            roi = tuple(rectangles_w_h[np.argmin(centers),:])
                        else:
                            roi = ()
                    else:
                        roi = ()
                    
                    # initialize tracking
                    if roi != ():
                        tracker = None
                        tracker = cv2.TrackerCSRT_create()
                        successTracking = tracker.init(image, roi)
                        if successTracking:
                            detect_object = True
                    else:
                        successTracking = False
                except:
                    roi = ()
                    successTracking = False
                    detect_object = False
                
                # set timer to re-run detection
                time_of_detection = time.time()
            
            # track detected object
            if detect_object and successTracking:
                successTracking, roi = tracker.update(image)
                roi=tuple(roi)
                if successTracking == False:
                    detect_object = False
                    roi = ()
            else:
                detect_object = False
                roi = ()
            
            # re-run detection on timeout
            if (time.time() - time_of_detection) > 30:
                detect_object = False
            
            # estimate center of detection and mark-up iage
            if roi != ():
                x_avg_np = int(roi[0]+0.5*roi[2])
                y_avg_np = int(roi[1]+0.5*roi[3])
                if self.preview_enabled:
                    cv2.circle(image, (x_avg_np, y_avg_np), 80, (0, 255, 0), 1)
            else:
                x_avg_np = -888
                y_avg_np = -888
            
            # clear the stream in preparation for the next frame
            cap.truncate(0)
            
            # send coordinates
            self._signal_message.detected_coordinates_signal.emit([x_avg_np, y_avg_np, 0.5*w, 0.5*h])

            # Send the resulting frame to main thread
            if self.preview_enabled:
                Q_Image = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                self._signal_message.video_frame_signal.emit(Q_Image)
            
            # exit loop when destroyed by main programm
            if self.destroyed:
                break
            
        # When everything done, release the camera and clear objects
        camera.close()
        detector = None
        tracker = None