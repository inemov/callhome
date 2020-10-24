# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 17:57:23 2020

@author: Ivan Nemov
"""
import pantilthat as pth
import time
from threading import Thread
from PyQt5 import QtCore

class servo_message(QtCore.QObject):
    standby_position_signal = QtCore.pyqtSignal(bool)   

class servo_position(Thread):
    
    def __init__(self, _signal_message):
        Thread.__init__(self)
        self._signal_message = _signal_message
        self.destroyed = False
        try:
            pth.servo_enable(1, True)
            pth.servo_enable(2, True)
        except:
            print("Error")
        
        self.set_standby_position(0, 0)
    
    def destroy(self):
        self.destroyed = True
        
    def get_position(self):
        try:
            return([pth.get_pan(), pth.get_tilt()])
        except:
            print("Error")
    
    def update_pan_remote_SP(self, position):
        self.pan_SP = max(min(position,90),-90)
        
    def update_tilt_remote_SP(self, position):
        self.tilt_SP = max(min(position,90),-90)
    
    def run(self):
        pan_EXT_FB, tilt_EXT_FB = self.get_position()
        self.update_pan_remote_SP(pan_EXT_FB)
        self.update_tilt_remote_SP(tilt_EXT_FB)
        while self.destroyed == False:
            time.sleep(0.02)
            pan_PV, tilt_PV = self.get_position()
            if abs(pan_PV-self.pan_SP)>=1:
                try:
                    pth.pan(self.pan_SP)
                except:
                    print("Error")
            if abs(tilt_PV-self.tilt_SP)>=1:
                try:
                    pth.tilt(self.tilt_SP)
                except:
                    print("Error")
        
        self.set_standby_position(0, 45)
        
        try:
            pth.servo_enable(1, False)
            pth.servo_enable(2, False)
        except:
            print("Error")
        
        self._signal_message.standby_position_signal.emit(True)
        
    def set_standby_position(self, pan_standby, tilt_standby):
        pan_PV, tilt_PV = self.get_position()
        while abs(pan_PV-pan_standby)>=1 or abs(tilt_PV-tilt_standby)>=1:
            pan_PV, tilt_PV = self.get_position()
            if pan_PV-pan_standby != 0:
                pan_SP = pan_PV - abs(pan_PV-pan_standby)/(pan_PV-pan_standby)
            else:
                pan_SP = pan_standby
            if tilt_PV-tilt_standby != 0:
                tilt_SP = tilt_PV - abs(tilt_PV-tilt_standby)/(tilt_PV-tilt_standby)
            else:
                tilt_SP = tilt_standby
                
            time.sleep(0.02)
            
            try:
                pth.pan(pan_SP)
                pth.tilt(tilt_SP)
            except:
                print("Error")