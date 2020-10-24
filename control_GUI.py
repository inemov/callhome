# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 15:49:07 2020

@author: Ivan Nemov
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import generic_PID
import face_detection
import set_servo_position
import csv

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.form_widget = FormWidget(self)
        _widget = QtWidgets.QWidget()
        _layout = QtWidgets.QVBoxLayout(_widget)
        _layout.addWidget(self.form_widget)
        self.setCentralWidget(_widget)
        self.setWindowTitle("Camera pan-tilt control")
        self.quit = QtWidgets.QAction("Quit", self)
        self.quit.triggered.connect(self.closeEvent)
        
    def closeEvent(self, event):
        self.form_widget.exit_action_custom()
        event.ignore()
        
class FormWidget(QtWidgets.QWidget):
    
    def __init__(self, parent):
        super(FormWidget, self).__init__(parent)
        self.__controls()
      
        self._pan_signal_message = generic_PID.PID_message()
        self._pan_PID = generic_PID.PID(self._pan_signal_message)
        self._pan_signal_message.update_output_array_signal.connect(self.pan_send_position)
        self._pan_PID.tune_on_reset(TS = self.pan_TS, DIRECTION = self.pan_direction, STRUCTURE = self.pan_structure, FORM = self.pan_form, DRL = self.pan_DRL, PV_RNG = [0,640], OUT_RNG = [-90,90])
        self._pan_PID.tune_on_run(KP = self.pan_KP, TI = self.pan_TI, TD = self.pan_TD, OUT_LIM = self.pan_OUT_LIM)
        
        self._tilt_signal_message = generic_PID.PID_message()
        self._tilt_PID = generic_PID.PID(self._tilt_signal_message)
        self._tilt_signal_message.update_output_array_signal.connect(self.tilt_send_position)
        self._tilt_PID.tune_on_reset(TS = self.tilt_TS, DIRECTION = self.tilt_direction, STRUCTURE = self.tilt_structure, FORM = self.tilt_form, DRL = self.tilt_DRL, PV_RNG = [0,480], OUT_RNG = [-90,90])
        self._tilt_PID.tune_on_run(KP = self.tilt_KP, TI = self.tilt_TI, TD = self.tilt_TD, OUT_LIM = self.tilt_OUT_LIM)
        
        self._servo_message = set_servo_position.servo_message()
        self._servo_message.standby_position_signal.connect(self.standby_position_confirmation)
        self._servo_position = set_servo_position.servo_position(self._servo_message)
        self._servo_position.start()
        
        self._detection_message = face_detection.detection_message()
        self._detection = face_detection.detection(self._detection_message)
        self._detection_message.detected_coordinates_signal.connect(self.update_detected_coordinates)
        self._detection_message.video_frame_signal.connect(self.update_video_frame)
        self._detection.start()
        
        self._pan_PID.start()
        self._tilt_PID.start()
        
        self.__layout()

    def __controls(self):
        
        self.MODE = "IMAN"
        
        self.load_parameters()
        
        # self.pan_KP = 1
        # self.pan_TI = 8
        # self.pan_TD = 0
        # self.pan_OUT_LIM = [-80, 80]
        # self.pan_structure = "I"
        # self.pan_TS = 0.1
        # self.pan_direction = "direct"
        # self.pan_form = "velocity"
        # self.pan_DRL = 0
        
        # self.tilt_KP = 1
        # self.tilt_TI = 8
        # self.tilt_TD = 0
        # self.tilt_OUT_LIM = [-80, 80]
        # self.tilt_structure = "I"
        # self.tilt_TS = 0.1
        # self.tilt_direction = "direct"
        # self.tilt_form = "velocity"
        # self.tilt_DRL = 0
        
        self.menu_bar=QtWidgets.QMenuBar()
        file_menu=self.menu_bar.addMenu("File")
        exit_action=QtWidgets.QAction('Exit',self)
        exit_action.triggered.connect(self.exit_action_custom)
        file_menu.addAction(exit_action)
        
        view_menu=self.menu_bar.addMenu("View")
        show_hide_tuning_action=QtWidgets.QAction('Tuning',self)
        show_hide_tuning_action.triggered.connect(self.hide_show_tuning)
        view_menu.addAction(show_hide_tuning_action)
        show_hide_preview_action=QtWidgets.QAction('Preview',self)
        show_hide_preview_action.triggered.connect(self.hide_show_preview)
        view_menu.addAction(show_hide_preview_action)        
        
        self.ModeControlBox = QtWidgets.QGroupBox(self)
        self.ModeControlBox.setObjectName("ModeControlBox")
        self.ModeControlBox.setFixedWidth(300)
        self.ModeControlBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.ModeControlBox.setTitle("Pan-Tilt control")
        
        self.ManualRadioButton = QtWidgets.QRadioButton(self.ModeControlBox)
        self.ManualRadioButton.setObjectName("ManualRadioButton")
        self.ManualRadioButton.setText("Manual")
        self.ManualRadioButton.setChecked(True)
        self.ManualRadioButton.setDisabled(False)
        self.ManualRadioButton.clicked.connect(self.manual_control)
        
        self.AutoRadioButton = QtWidgets.QRadioButton(self.ModeControlBox)
        self.AutoRadioButton.setObjectName("AutoRadioButton")
        self.AutoRadioButton.setText("Auto")
        self.AutoRadioButton.setChecked(False)
        self.AutoRadioButton.setDisabled(False)
        self.AutoRadioButton.clicked.connect(self.auto_control)
        
        self.ManualControlBox = QtWidgets.QGroupBox(self)
        self.ManualControlBox.setObjectName("ManualControlBox")
        self.ManualControlBox.setFixedWidth(300)
        self.ManualControlBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.ManualControlBox.setTitle("Manual control")
        
        self.UP_CommandButton = QtWidgets.QPushButton(self.ManualControlBox)
        self.UP_CommandButton.setObjectName("UP_CommandButton")
        self.UP_CommandButton.setFixedWidth(80)
        self.UP_CommandButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.UP_CommandButton.setText("UP")
        self.UP_CommandButton.clicked.connect(self.manual_UP)
        self.UP_CommandButton.setEnabled(True)
        
        self.DN_CommandButton = QtWidgets.QPushButton(self.ManualControlBox)
        self.DN_CommandButton.setObjectName("DN_CommandButton")
        self.DN_CommandButton.setFixedWidth(80)
        self.DN_CommandButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.DN_CommandButton.setText("DOWN")
        self.DN_CommandButton.clicked.connect(self.manual_DOWN)
        self.DN_CommandButton.setEnabled(True)
        
        self.LF_CommandButton = QtWidgets.QPushButton(self.ManualControlBox)
        self.LF_CommandButton.setObjectName("LF_CommandButton")
        self.LF_CommandButton.setFixedWidth(80)
        self.LF_CommandButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.LF_CommandButton.setText("LEFT")
        self.LF_CommandButton.clicked.connect(self.manual_LEFT)
        self.LF_CommandButton.setEnabled(True)
        
        self.RT_CommandButton = QtWidgets.QPushButton(self.ManualControlBox)
        self.RT_CommandButton.setObjectName("RT_CommandButton")
        self.RT_CommandButton.setFixedWidth(80)
        self.RT_CommandButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.RT_CommandButton.setText("RIGHT")
        self.RT_CommandButton.clicked.connect(self.manual_RIGHT)
        self.RT_CommandButton.setEnabled(True)
        
        self.TuningBox = QtWidgets.QGroupBox(self)
        self.TuningBox.setObjectName("TuningBox")
        self.TuningBox.setFixedWidth(340)
        self.TuningBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.TuningBox.setTitle("Tuning")
        
        self.Label_pan_KP = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_pan_KP.setFont(font)
        self.Label_pan_KP.setObjectName("Label_pan_KP")
        self.Label_pan_KP.setText("Pan  KP: ")
        
        self.Text_pan_KP = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_pan_KP.setFixedHeight(25)
        self.Text_pan_KP.setText(str(self.pan_KP))
        self.Text_pan_KP.textChanged.connect(self.Text_pan_KP_manual_change)

        self.Label_tilt_KP = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_tilt_KP.setFont(font)
        self.Label_tilt_KP.setObjectName("Label_tilt_KP")
        self.Label_tilt_KP.setText("Tilt  KP: ")
        
        self.Text_tilt_KP = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_tilt_KP.setFixedHeight(25)
        self.Text_tilt_KP.setText(str(self.tilt_KP))
        self.Text_tilt_KP.textChanged.connect(self.Text_tilt_KP_manual_change)
        
        self.Label_pan_TI = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_pan_TI.setFont(font)
        self.Label_pan_TI.setObjectName("Label_pan_TI")
        self.Label_pan_TI.setText("  TI: ")
        
        self.Text_pan_TI = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_pan_TI.setFixedHeight(25)
        self.Text_pan_TI.setText(str(self.pan_TI))
        self.Text_pan_TI.textChanged.connect(self.Text_pan_TI_manual_change)
        
        self.Label_tilt_TI = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_tilt_TI.setFont(font)
        self.Label_tilt_TI.setObjectName("Label_tilt_TI")
        self.Label_tilt_TI.setText("  TI: ")
        
        self.Text_tilt_TI = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_tilt_TI.setFixedHeight(25)
        self.Text_tilt_TI.setText(str(self.tilt_TI))
        self.Text_tilt_TI.textChanged.connect(self.Text_tilt_TI_manual_change)
        
        self.Label_pan_TD = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_pan_TD.setFont(font)
        self.Label_pan_TD.setObjectName("Label_pan_TD")
        self.Label_pan_TD.setText("  TD: ")
        
        self.Text_pan_TD = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_pan_TD.setFixedHeight(25)
        self.Text_pan_TD.setText(str(self.pan_TD))
        self.Text_pan_TD.textChanged.connect(self.Text_pan_TD_manual_change)
        
        self.Label_tilt_TD = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_tilt_TD.setFont(font)
        self.Label_tilt_TD.setObjectName("Label_tilt_TD")
        self.Label_tilt_TD.setText("  TD: ")
        
        self.Text_tilt_TD = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_tilt_TD.setFixedHeight(25)
        self.Text_tilt_TD.setText(str(self.tilt_TD))
        self.Text_tilt_TD.textChanged.connect(self.Text_tilt_TD_manual_change)

        self.PanPIDStructureBox = QtWidgets.QGroupBox(self)
        self.PanPIDStructureBox.setObjectName("PanPIDStructureBox")
        self.PanPIDStructureBox.setFixedWidth(320)
        self.PanPIDStructureBox.setFixedHeight(65)
        self.PanPIDStructureBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.PanPIDStructureBox.setTitle("Pan PID structure:")
        
        self.PanPIDStructureI = QtWidgets.QRadioButton(self.PanPIDStructureBox)
        self.PanPIDStructureI.setObjectName("PanPIDStructureI")
        self.PanPIDStructureI.setText("I")
        self.PanPIDStructureI.setChecked(False)
        self.PanPIDStructureI.setDisabled(False)
        self.PanPIDStructureI.clicked.connect(self.PanPID_structure_selection)
        
        self.PanPIDStructureI_PD = QtWidgets.QRadioButton(self.PanPIDStructureBox)
        self.PanPIDStructureI_PD.setObjectName("PanPIDStructureI_PD")
        self.PanPIDStructureI_PD.setText("I-PD")
        self.PanPIDStructureI_PD.setChecked(False)
        self.PanPIDStructureI_PD.setDisabled(False)
        self.PanPIDStructureI_PD.clicked.connect(self.PanPID_structure_selection)
        
        self.PanPIDStructurePI_D = QtWidgets.QRadioButton(self.PanPIDStructureBox)
        self.PanPIDStructurePI_D.setObjectName("PanPIDStructurePI_D")
        self.PanPIDStructurePI_D.setText("PI-D")
        self.PanPIDStructurePI_D.setChecked(False)
        self.PanPIDStructurePI_D.setDisabled(False)
        self.PanPIDStructurePI_D.clicked.connect(self.PanPID_structure_selection)
        
        self.PanPIDStructurePID = QtWidgets.QRadioButton(self.PanPIDStructureBox)
        self.PanPIDStructurePID.setObjectName("PanPIDStructurePID")
        self.PanPIDStructurePID.setText("PID")
        self.PanPIDStructurePID.setChecked(False)
        self.PanPIDStructurePID.setDisabled(False)
        self.PanPIDStructurePID.clicked.connect(self.PanPID_structure_selection)
        
        self.PanPID_structure_selection()
        
        self.TiltPIDStructureBox = QtWidgets.QGroupBox(self)
        self.TiltPIDStructureBox.setObjectName("TiltPIDStructureBox")
        self.TiltPIDStructureBox.setFixedWidth(320)
        self.TiltPIDStructureBox.setFixedHeight(65)
        self.TiltPIDStructureBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.TiltPIDStructureBox.setTitle("Tilt PID structure:")
        
        self.TiltPIDStructureI = QtWidgets.QRadioButton(self.TiltPIDStructureBox)
        self.TiltPIDStructureI.setObjectName("TiltPIDStructureI")
        self.TiltPIDStructureI.setText("I")
        self.TiltPIDStructureI.setChecked(False)
        self.TiltPIDStructureI.setDisabled(False)
        self.TiltPIDStructureI.clicked.connect(self.TiltPID_structure_selection)
        
        self.TiltPIDStructureI_PD = QtWidgets.QRadioButton(self.TiltPIDStructureBox)
        self.TiltPIDStructureI_PD.setObjectName("TiltPIDStructureI_PD")
        self.TiltPIDStructureI_PD.setText("I-PD")
        self.TiltPIDStructureI_PD.setChecked(False)
        self.TiltPIDStructureI_PD.setDisabled(False)
        self.TiltPIDStructureI_PD.clicked.connect(self.TiltPID_structure_selection)
        
        self.TiltPIDStructurePI_D = QtWidgets.QRadioButton(self.TiltPIDStructureBox)
        self.TiltPIDStructurePI_D.setObjectName("TiltPIDStructurePI_D")
        self.TiltPIDStructurePI_D.setText("PI-D")
        self.TiltPIDStructurePI_D.setChecked(False)
        self.TiltPIDStructurePI_D.setDisabled(False)
        self.TiltPIDStructurePI_D.clicked.connect(self.TiltPID_structure_selection)
        
        self.TiltPIDStructurePID = QtWidgets.QRadioButton(self.TiltPIDStructureBox)
        self.TiltPIDStructurePID.setObjectName("TiltPIDStructurePID")
        self.TiltPIDStructurePID.setText("PID")
        self.TiltPIDStructurePID.setChecked(False)
        self.TiltPIDStructurePID.setDisabled(False)
        self.TiltPIDStructurePID.clicked.connect(self.TiltPID_structure_selection)
        
        self.TiltPID_structure_selection()
        
        self.Label_pan_OUT_MIN = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_pan_OUT_MIN.setFont(font)
        self.Label_pan_OUT_MIN.setObjectName("Label_pan_OUT_MIN")
        self.Label_pan_OUT_MIN.setText("Pan OUT MIN: ")
        
        self.Text_pan_OUT_MIN = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_pan_OUT_MIN.setFixedHeight(25)
        self.Text_pan_OUT_MIN.setText(str(self.pan_OUT_LIM[0]))
        self.Text_pan_OUT_MIN.textChanged.connect(self.Text_pan_OUT_MIN_manual_change)
        
        self.Label_pan_OUT_MAX = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_pan_OUT_MAX.setFont(font)
        self.Label_pan_OUT_MAX.setObjectName("Label_pan_OUT_MAX")
        self.Label_pan_OUT_MAX.setText("  OUT MAX: ")
        
        self.Text_pan_OUT_MAX = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_pan_OUT_MAX.setFixedHeight(25)
        self.Text_pan_OUT_MAX.setText(str(self.pan_OUT_LIM[1]))
        self.Text_pan_OUT_MAX.textChanged.connect(self.Text_pan_OUT_MAX_manual_change)
        
        self.Label_pan_OUT_VAL = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_pan_OUT_VAL.setFont(font)
        self.Label_pan_OUT_VAL.setObjectName("Label_pan_OUT_VAL")
        self.Label_pan_OUT_VAL.setText("  OUT: ")
        
        self.Text_pan_OUT_VAL = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_pan_OUT_VAL.setFixedHeight(25)
        self.Text_pan_OUT_VAL.setText(str(int(self.pan_EXT_FB)))
        
        self.Label_tilt_OUT_MIN = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_tilt_OUT_MIN.setFont(font)
        self.Label_tilt_OUT_MIN.setObjectName("Label_tilt_OUT_MIN")
        self.Label_tilt_OUT_MIN.setText("Tilt OUT MIN: ")
        
        self.Text_tilt_OUT_MIN = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_tilt_OUT_MIN.setFixedHeight(25)
        self.Text_tilt_OUT_MIN.setText(str(self.tilt_OUT_LIM[0]))
        self.Text_tilt_OUT_MIN.textChanged.connect(self.Text_tilt_OUT_MIN_manual_change)
        
        self.Label_tilt_OUT_MAX = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_tilt_OUT_MAX.setFont(font)
        self.Label_tilt_OUT_MAX.setObjectName("Label_tilt_OUT_MAX")
        self.Label_tilt_OUT_MAX.setText("  OUT MAX: ")
        
        self.Text_tilt_OUT_MAX = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_tilt_OUT_MAX.setFixedHeight(25)
        self.Text_tilt_OUT_MAX.setText(str(self.tilt_OUT_LIM[1]))
        self.Text_tilt_OUT_MAX.textChanged.connect(self.Text_tilt_OUT_MAX_manual_change)
        
        self.Label_tilt_OUT_VAL = QtWidgets.QLabel(self.TuningBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.Label_tilt_OUT_VAL.setFont(font)
        self.Label_tilt_OUT_VAL.setObjectName("Label_tilt_OUT_VAL")
        self.Label_tilt_OUT_VAL.setText("  OUT: ")
        
        self.Text_tilt_OUT_VAL = QtWidgets.QLineEdit(self.TuningBox)
        self.Text_tilt_OUT_VAL.setFixedHeight(25)
        self.Text_tilt_OUT_VAL.setText(str(int(self.tilt_EXT_FB)))
        
        self.Apply_Pan_CommandButton = QtWidgets.QPushButton(self.TuningBox)
        self.Apply_Pan_CommandButton.setObjectName("Apply_Pan_CommandButton")
        self.Apply_Pan_CommandButton.setFixedWidth(80)
        self.Apply_Pan_CommandButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Apply_Pan_CommandButton.setText("Apply")
        self.Apply_Pan_CommandButton.clicked.connect(self.apply_pan_tuning)
        self.Apply_Pan_CommandButton.setEnabled(True)
        
        self.Apply_Tilt_CommandButton = QtWidgets.QPushButton(self.TuningBox)
        self.Apply_Tilt_CommandButton.setObjectName("Apply_Tilt_CommandButton")
        self.Apply_Tilt_CommandButton.setFixedWidth(80)
        self.Apply_Tilt_CommandButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Apply_Tilt_CommandButton.setText("Apply")
        self.Apply_Tilt_CommandButton.clicked.connect(self.apply_tilt_tuning)
        self.Apply_Tilt_CommandButton.setEnabled(True)
        
        self.PreviewBox = QtWidgets.QGroupBox(self)
        self.PreviewBox.setObjectName("PreviewBox")
        self.PreviewBox.setFixedWidth(300)
        self.PreviewBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.PreviewBox.setTitle("Preview")
        
        self.VideoFrame=QtWidgets.QLabel(self.PreviewBox)
        self.VideoFrame.setObjectName("VideoFrame")
        
    def __layout(self):

# general window layout
        self.vmainbox=QtWidgets.QVBoxLayout()    
        self.v1groupbox = QtWidgets.QVBoxLayout()
        self.v1groupbox.addWidget(self.ModeControlBox)
        self.v1groupbox.addWidget(self.ManualControlBox)
        self.v1groupbox.addWidget(self.PreviewBox)
        self.v2groupbox = QtWidgets.QVBoxLayout()
        self.v2groupbox.addWidget(self.TuningBox)
        self.hgroupbox = QtWidgets.QHBoxLayout()
        self.hgroupbox.addLayout(self.v1groupbox)
        self.hgroupbox.addLayout(self.v2groupbox)
        
        self.vmainbox.addWidget(self.menu_bar)
        self.vmainbox.addLayout(self.hgroupbox)
        self.setLayout(self.vmainbox)

#top left panel layout (mode selection)
        self.hModeControlBox=QtWidgets.QHBoxLayout()
        self.hModeControlBox.addWidget(self.ManualRadioButton)
        self.hModeControlBox.addWidget(self.AutoRadioButton)
        
#middle left panel layout (manual controll buttons)
        self.h1ManualControlBox=QtWidgets.QHBoxLayout()
        self.h1ManualControlBox.addWidget(self.UP_CommandButton)
        self.h1ManualControlBox.addWidget(self.LF_CommandButton)
        self.h2ManualControlBox=QtWidgets.QHBoxLayout()
        self.h2ManualControlBox.addWidget(self.DN_CommandButton)
        self.h2ManualControlBox.addWidget(self.RT_CommandButton)
        self.vManualControlBox=QtWidgets.QVBoxLayout()
        self.vManualControlBox.addLayout(self.h1ManualControlBox)
        self.vManualControlBox.addLayout(self.h2ManualControlBox)
        
#bottom left panel layoyt (preview)
        self.hPreviewBox=QtWidgets.QHBoxLayout()
        self.hPreviewBox.addWidget(self.VideoFrame)
        
#right panel layout (tuning)
        self.hPanPIDStructureBox=QtWidgets.QHBoxLayout()
        self.hPanPIDStructureBox.addWidget(self.PanPIDStructureI)
        self.hPanPIDStructureBox.addWidget(self.PanPIDStructureI_PD)
        self.hPanPIDStructureBox.addWidget(self.PanPIDStructurePI_D)
        self.hPanPIDStructureBox.addWidget(self.PanPIDStructurePID)
        self.PanPIDStructureBox.setLayout(self.hPanPIDStructureBox)
        
        self.hTiltPIDStructureBox=QtWidgets.QHBoxLayout()
        self.hTiltPIDStructureBox.addWidget(self.TiltPIDStructureI)
        self.hTiltPIDStructureBox.addWidget(self.TiltPIDStructureI_PD)
        self.hTiltPIDStructureBox.addWidget(self.TiltPIDStructurePI_D)
        self.hTiltPIDStructureBox.addWidget(self.TiltPIDStructurePID)
        self.TiltPIDStructureBox.setLayout(self.hTiltPIDStructureBox)

        self.h1TuningBox=QtWidgets.QHBoxLayout()
        self.h1TuningBox.addWidget(self.Label_pan_KP)
        self.h1TuningBox.addWidget(self.Text_pan_KP)
        self.h1TuningBox.addWidget(self.Label_pan_TI)
        self.h1TuningBox.addWidget(self.Text_pan_TI)
        self.h1TuningBox.addWidget(self.Label_pan_TD)
        self.h1TuningBox.addWidget(self.Text_pan_TD)
        self.h1TuningBox.addWidget(self.Apply_Pan_CommandButton)
        self.h2TuningBox=QtWidgets.QHBoxLayout()
        self.h2TuningBox.addWidget(self.Label_tilt_KP)
        self.h2TuningBox.addWidget(self.Text_tilt_KP)
        self.h2TuningBox.addWidget(self.Label_tilt_TI)
        self.h2TuningBox.addWidget(self.Text_tilt_TI)
        self.h2TuningBox.addWidget(self.Label_tilt_TD)
        self.h2TuningBox.addWidget(self.Text_tilt_TD)
        self.h2TuningBox.addWidget(self.Apply_Tilt_CommandButton)
        self.h3TuningBox=QtWidgets.QHBoxLayout()
        self.h3TuningBox.addWidget(self.Label_pan_OUT_MIN)
        self.h3TuningBox.addWidget(self.Text_pan_OUT_MIN)
        self.h3TuningBox.addWidget(self.Label_pan_OUT_MAX)
        self.h3TuningBox.addWidget(self.Text_pan_OUT_MAX)
        self.h3TuningBox.addWidget(self.Label_pan_OUT_VAL)
        self.h3TuningBox.addWidget(self.Text_pan_OUT_VAL)
        self.h4TuningBox=QtWidgets.QHBoxLayout()
        self.h4TuningBox.addWidget(self.Label_tilt_OUT_MIN)
        self.h4TuningBox.addWidget(self.Text_tilt_OUT_MIN)
        self.h4TuningBox.addWidget(self.Label_tilt_OUT_MAX)
        self.h4TuningBox.addWidget(self.Text_tilt_OUT_MAX)
        self.h4TuningBox.addWidget(self.Label_tilt_OUT_VAL)
        self.h4TuningBox.addWidget(self.Text_tilt_OUT_VAL)
        
        self.vTuningBox=QtWidgets.QVBoxLayout()
        self.vTuningBox.addLayout(self.h1TuningBox)
        self.vTuningBox.addLayout(self.h2TuningBox)
        self.vTuningBox.addLayout(self.h3TuningBox)
        self.vTuningBox.addLayout(self.h4TuningBox)
        self.vTuningBox.addWidget(self.PanPIDStructureBox)
        self.vTuningBox.addWidget(self.TiltPIDStructureBox)
        
        self.preview_hidden = False
        self.tuning_hidden = False
        self.hide_show_tuning()
        self.hide_show_preview()
        
#set layouts to groupboxes
        self.ModeControlBox.setLayout(self.hModeControlBox)
        self.ManualControlBox.setLayout(self.vManualControlBox)
        self.PreviewBox.setLayout(self.hPreviewBox)
        self.TuningBox.setLayout(self.vTuningBox)
        
    def manual_control(self):
        self.UP_CommandButton.setEnabled(True)
        self.DN_CommandButton.setEnabled(True)
        self.LF_CommandButton.setEnabled(True)
        self.RT_CommandButton.setEnabled(True)
        self.MODE = "IMAN"
    
    def auto_control(self):
        self.UP_CommandButton.setEnabled(False)
        self.DN_CommandButton.setEnabled(False)
        self.LF_CommandButton.setEnabled(False)
        self.RT_CommandButton.setEnabled(False)
        self.MODE = "AUT"
    
    def manual_UP(self):
        self.pan_EXT_FB, self.tilt_EXT_FB = self._servo_position.get_position()
        self.tilt_send_position(self.tilt_EXT_FB - 5)
        self.update_position_indication()
    
    def manual_DOWN(self):
        self.pan_EXT_FB, self.tilt_EXT_FB = self._servo_position.get_position()
        self.tilt_send_position(self.tilt_EXT_FB + 5)
        self.update_position_indication()
    
    def manual_LEFT(self):
        self.pan_EXT_FB, self.tilt_EXT_FB = self._servo_position.get_position()
        self.pan_send_position(self.pan_EXT_FB - 5)
        self.update_position_indication()
    
    def manual_RIGHT(self):
        self.pan_EXT_FB, self.tilt_EXT_FB = self._servo_position.get_position()
        self.pan_send_position(self.pan_EXT_FB + 5)
        self.update_position_indication()
        
    def update_detected_coordinates(self, position):
        self.pan_PV, self.tilt_PV, self.pan_SP, self.tilt_SP = position
        if self.pan_PV == -888 or self.tilt_PV == -888:
            self.MODE = "IMAN"
        else:
            if self.ManualRadioButton.isChecked():
                self.MODE = "IMAN"
            elif self.AutoRadioButton.isChecked():
                self.MODE = "AUT"
        self.pan_EXT_FB, self.tilt_EXT_FB = self._servo_position.get_position()
        self._pan_PID.update_inputs(self.pan_PV, self.pan_SP, self.pan_EXT_FB, self.pan_EXT_FB, self.MODE)
        self._tilt_PID.update_inputs(self.tilt_PV, self.tilt_SP, self.tilt_EXT_FB, self.tilt_EXT_FB, self.MODE)
        
    def update_position_indication(self):
        self.pan_EXT_FB, self.tilt_EXT_FB = self._servo_position.get_position()
        self.Text_pan_OUT_VAL.setText(str(int(self.pan_EXT_FB)))
        self.Text_tilt_OUT_VAL.setText(str(int(self.tilt_EXT_FB)))
    
    def update_video_frame(self, Q_image):
        convertToQtFormat = QtGui.QPixmap.fromImage(Q_image)
        convertToPixmap = QtGui.QPixmap(convertToQtFormat)
        self.VideoFrame.setPixmap(convertToPixmap.scaled(280, 210))
    
    def pan_send_position(self, position):
        self._servo_position.update_pan_remote_SP(position)
        self.update_position_indication()
    
    def tilt_send_position(self, position):
        self._servo_position.update_tilt_remote_SP(position)
        self.update_position_indication()
        
    def Text_pan_KP_manual_change(self):
        if self.Text_pan_KP.text() != "":
            self.pan_KP = float(str(self.Text_pan_KP.text()))
            
    def Text_tilt_KP_manual_change(self):
        if self.Text_tilt_KP.text() != "":
            self.tilt_KP = float(str(self.Text_tilt_KP.text()))
            
    def Text_pan_TI_manual_change(self):
        if self.Text_pan_TI.text() != "":
            self.pan_TI = float(str(self.Text_pan_TI.text()))
            
    def Text_tilt_TI_manual_change(self):
        if self.Text_tilt_TI.text() != "":
            self.tilt_TI = float(str(self.Text_tilt_TI.text()))
            
    def Text_pan_TD_manual_change(self):
        if self.Text_pan_TD.text() != "":
            self.pan_TD = float(str(self.Text_pan_TD.text()))
    
    def Text_tilt_TD_manual_change(self):
        if self.Text_tilt_TD.text() != "":
            self.tilt_TD = float(str(self.Text_tilt_TD.text()))
            
    def Text_pan_OUT_MIN_manual_change(self):
        if self.Text_pan_OUT_MIN.text() != "":
            self.pan_OUT_LIM[0] = float(str(self.Text_pan_OUT_MIN.text()))
            
    def Text_pan_OUT_MAX_manual_change(self):
        if self.Text_pan_OUT_MAX.text() != "":
            self.pan_OUT_LIM[1] = float(str(self.Text_pan_OUT_MAX.text()))
            
    def Text_tilt_OUT_MIN_manual_change(self):
        if self.Text_tilt_OUT_MIN.text() != "":
            self.tilt_OUT_LIM[0] = float(str(self.Text_tilt_OUT_MIN.text()))
            
    def Text_tilt_OUT_MAX_manual_change(self):
        if self.Text_tilt_OUT_MAX.text() != "":
            self.tilt_OUT_LIM[1] = float(str(self.Text_tilt_OUT_MAX.text()))
            
    def apply_pan_tuning(self):
        self._pan_PID.tune_on_run(KP = self.pan_KP, TI = self.pan_TI, TD = self.pan_TD, OUT_LIM = self.pan_OUT_LIM)
        self.save_parameters()
        
    def apply_tilt_tuning(self):
        self._tilt_PID.tune_on_run(KP = self.tilt_KP, TI = self.tilt_TI, TD = self.tilt_TD, OUT_LIM = self.tilt_OUT_LIM)
        self.save_parameters()
    
    def PanPID_structure_selection(self):
        if not(self.PanPIDStructureI.isChecked() or self.PanPIDStructureI_PD.isChecked() or self.PanPIDStructurePI_D.isChecked() or self.PanPIDStructurePID.isChecked()):
            if self.pan_structure == "I":
                self.PanPIDStructureI_PD.setChecked(False)
                self.PanPIDStructurePI_D.setChecked(False)
                self.PanPIDStructurePID.setChecked(False)
                self.PanPIDStructureI.setChecked(True)
            elif self.pan_structure == "I-PD":
                self.PanPIDStructurePI_D.setChecked(False)
                self.PanPIDStructurePID.setChecked(False)
                self.PanPIDStructureI.setChecked(False)
                self.PanPIDStructureI_PD.setChecked(True)
            elif self.pan_structure == "PI-D":
                self.PanPIDStructurePID.setChecked(False)
                self.PanPIDStructureI.setChecked(False)
                self.PanPIDStructureI_PD.setChecked(False)
                self.PanPIDStructurePI_D.setChecked(True)
            elif self.pan_structure == "PID":
                self.PanPIDStructureI.setChecked(False)
                self.PanPIDStructureI_PD.setChecked(False)
                self.PanPIDStructurePI_D.setChecked(False)
                self.PanPIDStructurePID.setChecked(True)
        
        if self.PanPIDStructureI.isChecked():
            self.pan_structure = "I"
            self.pan_KP = 1
            self.pan_TD = 0
            self.Text_pan_KP.setText(str(self.pan_KP))
            self.Text_pan_TD.setText(str(self.pan_TD))
            self.Text_pan_KP.setReadOnly(True)
            self.Text_pan_TD.setReadOnly(True)
        elif self.PanPIDStructureI_PD.isChecked():
            self.pan_structure = "I-PD"
            self.Text_pan_KP.setReadOnly(False)
            self.Text_pan_TD.setReadOnly(False)
        elif self.PanPIDStructurePI_D.isChecked():
            self.pan_structure = "PI-D"
            self.Text_pan_KP.setReadOnly(False)
            self.Text_pan_TD.setReadOnly(False)
        elif self.PanPIDStructurePID.isChecked():
            self.pan_structure = "PID"
            self.Text_pan_KP.setReadOnly(False)
            self.Text_pan_TD.setReadOnly(False)
            
        self.ManualRadioButton.setChecked(True)
        self.AutoRadioButton.setChecked(False)
        self.manual_control()
        
        try:
            self._pan_PID.tune_on_reset(TS = self.pan_TS, DIRECTION = self.pan_direction, STRUCTURE = self.pan_structure, FORM = self.pan_form, DRL = self.pan_DRL, PV_RNG = [0,640], OUT_RNG = [-90,90])
            self._pan_PID.tune_on_run(KP = self.pan_KP, TI = self.pan_TI, TD = self.pan_TD, OUT_LIM = self.pan_OUT_LIM)
        except:
            return(None)
        
        self.save_parameters()
            
    def TiltPID_structure_selection(self):
        if not(self.TiltPIDStructureI.isChecked() or self.TiltPIDStructureI_PD.isChecked() or self.TiltPIDStructurePI_D.isChecked() or self.TiltPIDStructurePID.isChecked()):
            if self.tilt_structure == "I":
                self.TiltPIDStructureI_PD.setChecked(False)
                self.TiltPIDStructurePI_D.setChecked(False)
                self.TiltPIDStructurePID.setChecked(False)
                self.TiltPIDStructureI.setChecked(True)
            elif self.tilt_structure == "I-PD":
                self.TiltPIDStructurePI_D.setChecked(False)
                self.TiltPIDStructurePID.setChecked(False)
                self.TiltPIDStructureI.setChecked(False)
                self.TiltPIDStructureI_PD.setChecked(True)
            elif self.tilt_structure == "PI-D":
                self.TiltPIDStructurePID.setChecked(False)
                self.TiltPIDStructureI.setChecked(False)
                self.TiltPIDStructureI_PD.setChecked(False)
                self.TiltPIDStructurePI_D.setChecked(True)
            elif self.tilt_structure == "PID":
                self.TiltPIDStructureI.setChecked(False)
                self.TiltPIDStructureI_PD.setChecked(False)
                self.TiltPIDStructurePI_D.setChecked(False)
                self.TiltPIDStructurePID.setChecked(True)
        
        if self.TiltPIDStructureI.isChecked():
            self.tilt_structure = "I"
            self.tilt_KP = 1
            self.tilt_TD = 0
            self.Text_tilt_KP.setText(str(self.tilt_KP))
            self.Text_tilt_TD.setText(str(self.tilt_TD))
            self.Text_tilt_KP.setReadOnly(True)
            self.Text_tilt_TD.setReadOnly(True)
        elif self.TiltPIDStructureI_PD.isChecked():
            self.tilt_structure = "I-PD"
            self.Text_tilt_KP.setReadOnly(False)
            self.Text_tilt_TD.setReadOnly(False)
        elif self.TiltPIDStructurePI_D.isChecked():
            self.tilt_structure = "PI-D"
            self.Text_tilt_KP.setReadOnly(False)
            self.Text_tilt_TD.setReadOnly(False)
        elif self.TiltPIDStructurePID.isChecked():
            self.tilt_structure = "PID"
            self.Text_tilt_KP.setReadOnly(False)
            self.Text_tilt_TD.setReadOnly(False)
            
        self.ManualRadioButton.setChecked(True)
        self.AutoRadioButton.setChecked(False)
        self.manual_control()
        
        try:
            self._tilt_PID.tune_on_reset(TS = self.tilt_TS, DIRECTION = self.tilt_direction, STRUCTURE = self.tilt_structure, FORM = self.tilt_form, DRL = self.tilt_DRL, PV_RNG = [0,480], OUT_RNG = [-90,90])
            self._tilt_PID.tune_on_run(KP = self.tilt_KP, TI = self.tilt_TI, TD = self.tilt_TD, OUT_LIM = self.tilt_OUT_LIM)
        except:
            return(None)
        
        self.save_parameters()
            
    def save_parameters(self):     
        filename = QtCore.QDir.currentPath()+'/config.csv'
        with open(filename, 'w', newline='') as csvfile:
            params_csv = csv.writer(csvfile, dialect='excel')
            params_csv.writerow(['_pan_KP',self.pan_KP])
            params_csv.writerow(['_pan_TI',self.pan_TI])
            params_csv.writerow(['_pan_TD',self.pan_TD])
            params_csv.writerow(['_pan_OUT_LIM',self.pan_OUT_LIM[0],self.pan_OUT_LIM[1]])
            params_csv.writerow(['_pan_TS',self.pan_TS])
            params_csv.writerow(['_pan_structure',self.pan_structure])
            params_csv.writerow(['_pan_direction',self.pan_direction])
            params_csv.writerow(['_pan_form',self.pan_form])
            params_csv.writerow(['_pan_DRL',self.pan_DRL])
            params_csv.writerow(['_tilt_KP',self.tilt_KP])
            params_csv.writerow(['_tilt_TI',self.tilt_TI])
            params_csv.writerow(['_tilt_TD',self.tilt_TD])
            params_csv.writerow(['_tilt_OUT_LIM',self.tilt_OUT_LIM[0],self.tilt_OUT_LIM[1]])
            params_csv.writerow(['_tilt_TS',self.tilt_TS])
            params_csv.writerow(['_tilt_structure',self.tilt_structure])
            params_csv.writerow(['_tilt_direction',self.tilt_direction])
            params_csv.writerow(['_tilt_form',self.tilt_form])
            params_csv.writerow(['_tilt_DRL',self.tilt_DRL])
    
    def load_parameters(self):
        self.pan_EXT_FB = 0
        self.tilt_EXT_FB = 0
        filename = QtCore.QDir.currentPath()+'/config.csv'
        readcsv=csv.reader(open(filename))
        for row in readcsv:
            if row[0] == '_pan_KP':
                self.pan_KP = float(row[1])
            elif row[0] == '_pan_TI':
                self.pan_TI = float(row[1])
            elif row[0] == '_pan_TD':
                self.pan_TD = float(row[1])
            elif row[0] == '_pan_OUT_LIM':
                self.pan_OUT_LIM = [float(row[1]), float(row[2])]
            elif row[0] == '_pan_TS':
                self.pan_TS = float(row[1])
            elif row[0] == '_pan_structure':
                self.pan_structure = str(row[1])
            elif row[0] == '_pan_direction':
                self.pan_direction = str(row[1])
            elif row[0] == '_pan_form':
                self.pan_form = str(row[1])
            elif row[0] == '_pan_DRL':
                self.pan_DRL = float(row[1])
            elif row[0] == '_tilt_KP':
                self.tilt_KP = float(row[1])
            elif row[0] == '_tilt_TI':
                self.tilt_TI = float(row[1])
            elif row[0] == '_tilt_TD':
                self.tilt_TD = float(row[1])
            elif row[0] == '_tilt_OUT_LIM':
                self.tilt_OUT_LIM = [float(row[1]), float(row[2])]
            elif row[0] == '_tilt_TS':
                self.tilt_TS = float(row[1])
            elif row[0] == '_tilt_structure':
                self.tilt_structure = str(row[1])
            elif row[0] == '_tilt_direction':
                self.tilt_direction = str(row[1])
            elif row[0] == '_tilt_form':
                self.tilt_form = str(row[1])
            elif row[0] == '_tilt_DRL':
                self.tilt_DRL = float(row[1])
    
    def hide_show_tuning(self):
        if self.tuning_hidden:
            self.tuning_hidden = False
            self.TuningBox.show()
        else:
            self.tuning_hidden = True
            self.TuningBox.hide()
    
    def hide_show_preview(self):
        if self.preview_hidden:
            self._detection.change_preview(True)
            self.preview_hidden = False
            self.PreviewBox.show()
        else:
            self._detection.change_preview(False)
            self.preview_hidden = True
            self.PreviewBox.hide()
    
    def exit_action_custom(self):
        self._servo_position.destroy()
        self._pan_PID.decommission()
        self._tilt_PID.decommission()
        self._detection.destroy()
        
    def standby_position_confirmation(self, confirmation):
        if confirmation:
            # exit event loop
            QtWidgets.QApplication.quit
            # close applications
            sys.exit()
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()
    
if __name__ == '__main__':
    sys.exit(main())