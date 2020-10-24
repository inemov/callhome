# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 20:57:16 2020

@author: Ivan Nemov
"""

import time
from PyQt5 import QtCore
from threading import Thread

class PID_message(QtCore.QObject):
    update_output_array_signal = QtCore.pyqtSignal(float)               #send message with PID out

class PID(Thread):
    def __init__(self, _signal_message):
        Thread.__init__(self)
        self._signal_message = _signal_message
        self.commissioned = True
        
    def decommission(self):
        self.commissioned = False
   
    def tune_on_run(self, KP = -1, TI = -1, TD = -1, OUT_LIM = [-888,-888]):
        
        if KP == -1:
            try:
                if self.KP == None:
                    self.KP = 1
            except:
                self.KP = 1
        else:
            self.KP = KP
            
        if TI == -1:
            try:
                if self.TI == None:
                    self.TI = 100
            except:
                self.TI = 100
        else:
            self.TI = TI
            
        if TD == -1:
            try:
                if self.TD == None:
                    self.TD = 0
            except:
                self.TD = 0
        else:
            self.TD = TD
            
        if OUT_LIM == [-888,-888]:
            try:
                if self.OUT_LIM == None:
                    self.OUT_LIM = [0, 100]
            except:
                self.OUT_LIM = [0, 100]
        else:
            self.OUT_LIM = OUT_LIM
        
    def tune_on_reset(self, TS = -1, DIRECTION = "", STRUCTURE = "", FORM = "", DRL = -1, PV_RNG = [-888,-888], OUT_RNG = [-888,-888]):
        
        if TS == -1:
            try:
                if self.TS == None:
                    self.TS = 1
            except:
                self.TS = 1
        else:
            self.TS = TS
        
        if DIRECTION == "" or (DIRECTION != "reverse" and DIRECTION != "direct"):
            try:
                if self.DIRECTION == None:
                    self.DIRECTION = "reverse"
            except:
                self.DIRECTION = "reverse"
        else:
            self.DIRECTION = DIRECTION
        
        if STRUCTURE == "" or (STRUCTURE != "I" and STRUCTURE != "I-PD" and STRUCTURE != "PI-D" and STRUCTURE != "PID"):
            try:
                if self.STRUCTURE == None:
                    self.STRUCTURE = "PI-D"
            except:
                self.STRUCTURE = "PI-D"
        else:
            self.STRUCTURE = STRUCTURE
        
        if FORM == "" or (FORM != "velocity" and FORM != "position"):
            try:
                if self.FORM == None:
                    self.FORM = "velocity"
            except:
                self.FORM = "velocity"
        else:
            self.FORM = FORM
            
        if DRL == -1:
            try:
                if self.DRL == None:
                    self.DRL = 0
            except:
                self.DRL = 0
        else:
            self.DRL = DRL
        
        if PV_RNG == [-888,-888]:
            try:
                if self.PV_RNG == None:
                    self.PV_RNG = [0, 100]
            except:
                self.PV_RNG = [0, 100]
        else:
            self.PV_RNG = PV_RNG
            
        if OUT_RNG == [-888,-888]:
            try:
                if self.OUT_RNG == None:
                    self.OUT_RNG = [0, 100]
            except:
                self.OUT_RNG = [0, 100]
        else:
            self.OUT_RNG = OUT_RNG
            
        self.reset_PID()
    
    def update_inputs(self, IN = 0, SP = 0, EXT_FB = 0, MAN_OUT = 0, MODE = ""):
        self.IN = IN
        self.SP = SP
        self.EXT_FB = EXT_FB
        self.MAN_OUT = MAN_OUT
        if MODE == "" or (MODE != "IMAN" and MODE == "MAN" and MODE == "AUT"): # and MODE == "CAS"):
            try:
                if self.MODE == None:
                    self.MODE = "MAN"
            except:
                self.MODE = "MAN"
        else:
            self.MODE = MODE
        
    def update_output(self):
        self._signal_message.update_output_array_signal.emit(self.OUT)
        
    def reset_PID(self):
        self.P_ERROR = 0
        self.I_ERROR = 0
        self.D_ERROR = 0
        self.DPV = 0
        self.DDPV = 0
        self.MODE = "IMAN"
    
    def run(self):
        while self.commissioned:
            
            time_start = time.time()
            
            if self.MODE == "IMAN":
                
                try:
                    IN = (self.IN - self.PV_RNG[0]) * 100 / (self.PV_RNG[1] - self.PV_RNG[0])
                    SP = (self.SP - self.PV_RNG[0]) * 100 / (self.PV_RNG[1] - self.PV_RNG[0])
                except:
                    IN = 0
                    SP = 0
                if self.STRUCTURE == "PID":
                    self.D_ERROR = ((IN - SP) - self.I_ERROR) - self.P_ERROR
                    self.P_ERROR = (IN - SP) - self.I_ERROR
            
                if self.STRUCTURE == "PI-D":
                    self.D_ERROR = (IN - self.DPV) - self.DDPV
                    self.P_ERROR = (IN - SP) - self.I_ERROR
                
                if self.STRUCTURE == "I-PD":
                    self.D_ERROR = (IN - self.DPV) - self.P_ERROR
                    self.P_ERROR = IN - self.DPV
                    
                if self.STRUCTURE == "I":
                    self.D_ERROR = 0
                    self.P_ERROR = 0
                
                self.I_ERROR = IN - SP
                self.DDPV = IN - self.DPV
                self.DPV = IN
                
                try:
                    self.OUT = max(min(self.EXT_FB, self.OUT_LIM[1]), self.OUT_LIM[0])
                except:
                    self.EXT_FB = self.OUT_LIM[0]
                    self.OUT = max(min(self.EXT_FB, self.OUT_LIM[1]), self.OUT_LIM[0])
                
                if (time.time() - time_start) < self.TS:
                    time.sleep(self.TS - (time.time() - time_start))
                
            elif self.MODE == "MAN":
                
                IN = (self.IN - self.PV_RNG[0]) * 100 / (self.PV_RNG[1] - self.PV_RNG[0])
                SP = (self.SP - self.PV_RNG[0]) * 100 / (self.PV_RNG[1] - self.PV_RNG[0])
            
                if self.STRUCTURE == "PID":
                    self.D_ERROR = ((IN - SP) - self.I_ERROR) - self.P_ERROR
                    self.P_ERROR = (IN - SP) - self.I_ERROR
            
                if self.STRUCTURE == "PI-D":
                    self.D_ERROR = (IN - self.DPV) - self.DDPV
                    self.P_ERROR = (IN - SP) - self.I_ERROR
                
                if self.STRUCTURE == "I-PD":
                    self.D_ERROR = (IN - self.DPV) - self.P_ERROR
                    self.P_ERROR = IN - self.DPV
                
                if self.STRUCTURE == "I":
                    self.D_ERROR = 0
                    self.P_ERROR = 0
                
                self.I_ERROR = IN - SP
                self.DDPV = IN - self.DPV
                self.DPV = IN
                
                try:
                    self.OUT = max(min(self.MAN_OUT, self.OUT_LIM[1]), self.OUT_LIM[0])
                except:
                    self.MAN_OUT = self.OUT_LIM[0]
                    self.OUT = max(min(self.MAN_OUT, self.OUT_LIM[1]), self.OUT_LIM[0])
                
                if (time.time() - time_start) < self.TS:
                    time.sleep(self.TS - (time.time() - time_start))
                
                self.update_output()
                
            elif self.MODE == "AUT":
                IN = (self.IN - self.PV_RNG[0]) * 100 / (self.PV_RNG[1] - self.PV_RNG[0])
                SP = (self.SP - self.PV_RNG[0]) * 100 / (self.PV_RNG[1] - self.PV_RNG[0])
            
                if self.STRUCTURE == "PID":
                    self.D_ERROR = ((IN - SP) - self.I_ERROR) - self.P_ERROR
                    self.P_ERROR = (IN - SP) - self.I_ERROR
            
                if self.STRUCTURE == "PI-D":
                    self.D_ERROR = (IN - self.DPV) - self.DDPV
                    self.P_ERROR = (IN - SP) - self.I_ERROR
                
                if self.STRUCTURE == "I-PD":
                    self.D_ERROR = (IN - self.DPV) - self.P_ERROR
                    self.P_ERROR = IN - self.DPV
                
                if self.STRUCTURE == "I":
                    self.D_ERROR = 0
                    self.P_ERROR = 0
                
                self.I_ERROR = IN - SP
                self.DDPV = IN - self.DPV
                self.DPV = IN

                if self.DIRECTION == "reverse":
                    sign = -1
                elif self.DIRECTION == "direct":
                    sign = 1
            
                OUT = (self.OUT - self.OUT_RNG[0]) * 100 / (self.OUT_RNG[1] - self.OUT_RNG[0])
                EXT_FB = (self.EXT_FB - self.OUT_RNG[0]) * 100 / (self.OUT_RNG[1] - self.OUT_RNG[0])
                DOUT = sign * self.KP * (self.P_ERROR + (self.TS / self.TI) * self.I_ERROR + (self.TD / self.TS) * self.D_ERROR) + self.DRL * (self.TS / self.TI) * (EXT_FB - OUT)

                if self.FORM == "velocity":
                    OUT = OUT + DOUT
                elif self.FORM == "position":
                    OUT = EXT_FB + DOUT
                
                self.OUT = max(min(self.OUT_RNG[0] + OUT * (self.OUT_RNG[1] - self.OUT_RNG[0]) / 100, self.OUT_LIM[1]), self.OUT_LIM[0])

                if (time.time() - time_start) < self.TS:
                    time.sleep(self.TS - (time.time() - time_start))
                
                self.update_output()
                
            # elif self.MODE == "CAS":
            #     if (time.time() - time_start) < self.TS:
            #           time.sleep(self.TS - (time.time() - time_start))
                
            #     self.update_output()
            