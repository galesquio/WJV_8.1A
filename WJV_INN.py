import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QAction, QWidget, QLabel, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
import subprocess
from easygui import msgbox
from os import path, getcwd
from mainwindow import Login, MySignal
from sys import exit
username = ''
import os
from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS
import json
#pip install pyqt5 easygui pywin32 pyqtwebengine pydal win32printing  wmi openpyxl numpy pandas keyboard pyserial reportlab requests pyqt5designer pyinstaller
class SingleInstance:   
    def __init__(self):
        self.mutexname = "WJVINN_{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}"
        self.mutex = CreateMutex(None, False, self.mutexname)
        self.lasterror = GetLastError()
    def already_running(self):
        return (self.lasterror == ERROR_ALREADY_EXISTS)
    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)

def update_username(username_return):
    global username
    username = username_return



if __name__ == '__main__':
    myapp = SingleInstance()
    if myapp.already_running():
        msg_ = 'Another instance of the application is already running.\nApplication will now close.'
        msgbox(msg_, 'APPLICATION ERROR')
        exit(0)
    else:
        app = QApplication(sys.argv)
        signal = MySignal()
        login = Login()
        login.setWindowTitle('Credentials')
        login.setWindowIcon(QIcon('icon.ico'))
        login.signal2.username__.connect(update_username)
        if login.exec_() == QDialog.Accepted:
            from mainwindow import MainWindow
            app.setApplicationName('WJV INN')
            w = MainWindow(username)
            w.setWindowIcon(QIcon('icon.ico'))
            version_ = ''
            try:
                with open("Resource/config.json", 'r') as json_file:
                    config_info = json.load(json_file)
            except:
                pass
            version_ = config_info['VERSION']
            w.setWindowTitle('WJV INN - v%s' % version_)
            w.showMaximized()
            sys.exit(app.exec_())

# Tabunok
# API Key=r83un4qsg559japhuymj
# Secret=2558c292c02b4e279aa291f2834e7970
# DeviceID=eb190b07ede84534f7q4fn
# Region=us


#JY
# API Key=9deegtvu9nm3gvtpcrt7
# Secret=2fa627bb76674cafa4120f76bea668c3
# DeviceID=ebd29e98f76f58532ez7ef
# Region=us