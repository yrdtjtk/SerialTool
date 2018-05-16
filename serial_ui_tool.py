#-*- coding:utf-8 -*-
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from ui_serial_tool import Ui_Form

import time
import datetime

import serial
import serial.tools.list_ports

import threading

import func
from res import images_qr

def getProgVer():
    return 'V1.002'

def getNowStr(isCompact=True, isMill=False):
    now = datetime.datetime.now()
    if isCompact:
        if isMill:
            s_datatime = now.strftime('%Y%m%d%H%M%S%f')
        else:
            s_datatime = now.strftime('%Y%m%d%H%M%S')
    else:
        if isMill:
            s_datatime = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        else:
            s_datatime = now.strftime('%Y-%m-%d %H:%M:%S')
    return s_datatime

def getTxt(txtName):
    table = {'openPort':'Open(&O)', 'closePort':'Close(&C)'}
    return table[txtName]

def createSerial(portName):
    ser = serial.Serial()
    ser.port = portName
    ser.baudrate = 57600
    ser.timeout = 2
    ser.parity = 'N'
    ser.stopbits = 1

    return ser

def portRecvProc(ser, sig):
    while True:
        if ser.isOpen():
            num = ser.inWaiting()
            if num > 0:
                b = ser.read(num)
                sig.emit(b)
        time.sleep(0.01)

class MainWindow(QtWidgets.QWidget):

    sig_portRecv = QtCore.pyqtSignal(bytes, name='refresh_UI_Recv_Signal')

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle('Serial Tool - ' + getProgVer())

        self.sig_portRecv.connect(self.refresh_UI_Recv)

        for port in serial.tools.list_ports.comports():
            self.ui.cob_Com.addItem(port[0])
        self.ser = createSerial(self.ui.cob_Com.currentText())
        self.ui.pb_OpenOrClose.setText(getTxt('openPort'))
        # self.ui.lbl_Com.setPixmap(QtGui.QPixmap("ico/off.png"))
        self.ui.lbl_Com.setPixmap(QtGui.QPixmap(":/ico/off.png"))
        self.ui.te_Recv.setReadOnly(True)
        self.ui.lbl_Status.setText('')

        self.timerStatus = QTimer(self)
        self.timerStatus.timeout.connect(self.timerStatusProc)

        self.ui.pb_OpenOrClose.clicked.connect(self.on_pb_OpenOrClose_Clicked)
        self.ui.pb_Send.clicked.connect(self.on_pb_Send_Clicked)
        self.ui.pb_MakeStation.clicked.connect(self.on_pb_MakeStation_Clicked)
        self.ui.pb_ClearRecv.clicked.connect(self.on_pb_ClearRecv_Clicked)

        self.ui.sp_CircleT.setRange(1, 20)
        self.ui.sp_CircleT.setToolTip('CircleT')
        self.ui.sp_Station.setRange(1, 63)
        self.ui.sp_Station.setToolTip('Station')

        QtWidgets.QWidget.setTabOrder(self.ui.cob_Com, self.ui.pb_OpenOrClose)
        QtWidgets.QWidget.setTabOrder(self.ui.pb_OpenOrClose, self.ui.chk_HexRecv)
        QtWidgets.QWidget.setTabOrder(self.ui.chk_HexRecv, self.ui.pb_ClearRecv)
        QtWidgets.QWidget.setTabOrder(self.ui.pb_ClearRecv, self.ui.sp_CircleT)
        QtWidgets.QWidget.setTabOrder(self.ui.sp_CircleT, self.ui.cob_UpDown)
        QtWidgets.QWidget.setTabOrder(self.ui.cob_UpDown, self.ui.sp_Station)
        QtWidgets.QWidget.setTabOrder(self.ui.sp_Station, self.ui.pb_MakeStation)
        QtWidgets.QWidget.setTabOrder(self.ui.pb_MakeStation, self.ui.chk_HexSend)
        QtWidgets.QWidget.setTabOrder(self.ui.chk_HexSend, self.ui.pb_Send)
        QtWidgets.QWidget.setTabOrder(self.ui.pb_Send, self.ui.cob_Com)

        self.show()

    def on_pb_OpenOrClose_Clicked(self):
        if not self.ser.isOpen():
            self.ser = createSerial(self.ui.cob_Com.currentText())
            try:
                self.ser.open()
            except Exception as e:
                print(e)
                self.ui.lbl_Status.setText(str(e))
                self.timerStatus.start(3000)
            if self.ser.isOpen():
                self.ui.pb_OpenOrClose.setText(getTxt('closePort'))
                self.ui.lbl_Com.setPixmap(QtGui.QPixmap(":/ico/on.png"))
                t = threading.Thread(target=portRecvProc, args = (self.ser, self.sig_portRecv))
                t.start()
        else:
            self.ser.close()
            self.ui.pb_OpenOrClose.setText(getTxt('openPort'))
            self.ui.lbl_Com.setPixmap(QtGui.QPixmap(":/ico/off.png"))

    def refresh_UI_Recv(self, b):
        if self.ui.chk_HexRecv.isChecked():
            s1 = func.buf2hexstr(b)
            s2 = '[<font color="red">' + getNowStr(False, True) + '</font>] %04u: ' % len(b)
            s = s2 + s1
            self.ui.te_Recv.append(s) #换行追加
        else:
            s = bytes.decode(b, 'utf-8', errors='ignore')
            self.ui.te_Recv.moveCursor(QtGui.QTextCursor.End);
            self.ui.te_Recv.insertPlainText(s)


    def on_pb_Send_Clicked(self):
        if self.ser.isOpen():
            txt = self.ui.te_Send.toPlainText()
            print('txt = ' + txt)
            if self.ui.chk_HexSend.isChecked():
                b = func.hexstr2buf(txt)
            else:
                b = bytes(txt, 'utf-8')
            self.ser.write(b)

    def on_pb_MakeStation_Clicked(self):
        s_cmd = '12'

        s_datatime = getNowStr()

        s_gps = '00'*12
        print(self.ui.sp_Station.cursor())
        s_station = '%02X' % self.ui.sp_Station.value() # '01'
        s_direction = '%02X' % self.ui.cob_UpDown.currentIndex() # '00'
        s_circleT = '%02X' % self.ui.sp_CircleT.value() # '01'

        s = s_cmd + s_datatime + s_gps + s_station + s_direction + s_circleT

        b = func.hexstr2buf(s)
        length = len(b)
        s_len = '%04X' % length
        s_crc = '%04X' % func.crc(b)

        s_all = s_len + s + s_crc
        self.ui.te_Send.setText(s_all)

        self.ui.chk_HexSend.setChecked(True)
        self.on_pb_Send_Clicked()

    def on_pb_ClearRecv_Clicked(self):
        self.ui.te_Recv.setText('')

    def timerStatusProc(self):
        self.ui.lbl_Status.setText('')

    # def eventFilter(self, obj, ev):
    #     print('eventFilter')

    def keyPressEvent(self, ev):
        print('keyPressEvent, ev = ' + str(ev.modifiers()) + ', ' + hex(ev.key()))
        if ev.key() == Qt.Key_Return:
            print('Enter Key')
            if ev.modifiers() == Qt.ControlModifier:
                print('Ctrl Key')
                if QtWidgets.QWidget.focusWidget(self) == self.ui.te_Send:
                    self.on_pb_Send_Clicked()
            else:
                curWidg = QtWidgets.QWidget.focusWidget(self)
                if curWidg == self.ui.sp_CircleT \
                        or curWidg == self.ui.sp_Station \
                        or curWidg == self.ui.cob_UpDown:
                    self.on_pb_MakeStation_Clicked()


    def closeEvent(self, ev):
        if self.ser.isOpen():
            self.ser.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = MainWindow()
    sys.exit(app.exec_())
