from PyQt5 import uic
import serial
from datetime import date, datetime, time, timedelta
from PyQt5.QtGui import QColor, QBrush, QStandardItem, QStandardItemModel,QTextDocument, QFont, QTextCursor, QTextLength
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrintDialog,QPrinter
from PyQt5.QtWidgets import QApplication, QMessageBox, QLineEdit, QTableView, QDialog, QDesktopWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QDateTime, Qt, QAbstractTableModel, QUrl, QTimer
import hashlib
import shutil
from time import sleep
from functools import partial
import threading
from pydal import DAL, Field
from easygui import msgbox
import math
import subprocess
import requests
import tempfile
import win32api
import win32print
import queue
from win32com.client.gencache import EnsureDispatch
from win32com.client import constants
import wmi
import openpyxl
from openpyxl.styles import PatternFill
import sys
import calendar
import re
import webbrowser
import numpy as np
import pandas as pd
import logging
from win32printing import Printer
import os
import json
#from tinytuya import OutletDevice
#from scapy.all import ARP, Ether, srp
import keyboard
import win32ui

class MySignal(QObject):
    sig_sec = pyqtSignal(str)
    card_data = pyqtSignal(str)
    sig_sec2 = pyqtSignal(str)
    sig2 = pyqtSignal(str)
    sig_min = pyqtSignal(str)
    sig_tenmin = pyqtSignal(str)
    http_error = pyqtSignal(str)
    update_display = pyqtSignal(str)
    sig_scan = pyqtSignal(str)
    sig_scan_complete = pyqtSignal(str)
    add_new_record = pyqtSignal(list)
    sig_close = pyqtSignal(str)
    save_to_db = pyqtSignal(str)
    sig_locked = pyqtSignal(list)
    update_GUI = pyqtSignal(str)
    update_time_ = pyqtSignal(str)
    #sig_toggle = pyqtSignal(list)
    sig_temp = pyqtSignal(list)
    sig_disp = pyqtSignal(list)
    sig_TV = pyqtSignal(str)
    username__ = pyqtSignal(str)
    close_comm = pyqtSignal(str)
    send_html_queue = pyqtSignal(str)
    sig_delivery = pyqtSignal(list)
    sig_delivery_print = pyqtSignal(str)
    update_active_rooms = pyqtSignal(list)
    update_active_rooms2 = pyqtSignal(list)
    update_inactive_rooms = pyqtSignal(list)
    comm_update = pyqtSignal(list)
    connectivity_status = pyqtSignal(bool)
    check_out = pyqtSignal(list)
    