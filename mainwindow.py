#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import uic
import serial
from datetime import date, datetime, time, timedelta
from PyQt5.QtGui import QColor, QBrush, QStandardItem, QStandardItemModel,QTextDocument, QFont, QTextCursor, QTextLength
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrintDialog,QPrinter
from PyQt5.QtWidgets import QMessageBox, QLineEdit, QTableView, QDialog, QDesktopWidget, QVBoxLayout, QTableWidget, QListWidgetItem,  QLabel, QTableWidgetItem, QPushButton, QFileDialog, QHeaderView, QApplication, QGroupBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QDateTime, Qt, QAbstractTableModel, QUrl, QTimer
import hashlib
import shutil
from time import sleep
from functools import partial
import threading
from pydal import DAL, Field
from easygui import msgbox
from my_signal import MySignal
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
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo
import win32com.client as win32
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from collections import defaultdict

from reportlab.lib.styles import getSampleStyleSheet


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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
import keyboard
import win32ui
import asyncio
from concurrent.futures import ThreadPoolExecutor

#from HASS_devices import HomeAssistantSwitchSummary



queue_db = []
queue_db_update = []
relative_path = os.getcwd()#path.abspath(path.join(getcwd(),'../'))


#create a folder "logs" under Resource if not exist
if not os.path.exists('Resource/logs'):
    os.makedirs('Resource/logs')


cur_d8 = datetime.now().strftime('%Y%m%d_%H%M.log')
logging.basicConfig(filename=f'Resource/logs/{cur_d8}', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)



global_RM_count = 96
global_record = {}
test_global = '1'
db = DAL('sqlite://WJV_DB4.db',folder = 'DB',migrate=False)
db.define_table('WJV_db',  Field('Ticket_ID',unique=True) ,Field('RFID_',type='string', default=None),Field('Room_Type',type='string'),Field('extra_heads',type='integer'),
            Field('Room_Merchandise','json'), Field('Room_Meals','json'),Field('Status_','string'),Field('Extended_','boolean'), Field('Check_In',type ='datetime'),
            Field('Check_Out',type ='datetime'), Field('Room_Number',type='string'),Field('Cashier_',type='string'),Field('Total_Price',type='string'),Field('Mer_Price',type='string'),
            Field('RM_Price',type='string'),Field('Price_',type='string'), Field('uploaded_to_cloud', 'boolean', default=False))
db.define_table('Room_rates_db',  Field('Rate_ID',unique=True) ,Field('Rate_Name',type='string'),Field('Price_',type='integer'),Field('Price_add',type='integer'),Field('Head_price',type='integer'))
db.define_table('Merchandise_rates_db',  Field('Merchandise_ID',unique=True) ,Field('Merchandise_Name',type='string'),Field('Price_',type='integer'),Field('Quantity_',type='integer'),
                Field('Min_',type='integer'),Field('Type_','string'), Field('Count_',type='integer', default=0))
db.define_table('Meals_rates_db',  Field('Meals_ID',unique=True) ,Field('Meals_Name',type='string'),Field('Price_',type='string'),Field('Quantity_',type='integer'),
                Field('Min_',type='integer'))
db.define_table('WJV_users',  Field('User_',type='string') ,Field('Password_',type='string'))
db.define_table('InvTrckng_by_date',  Field('Date01',type='date'))
db.define_table('Inventory_tracking',  Field('Merchandise_ID','reference Merchandise_rates_db') ,Field('Ref_Date',type='date'),Field('SI_',type='integer'),
                Field('DI_',type='integer'),Field('PI_',type='integer'))

db.define_table('Track_delivery',  Field('Merchandise_ID') ,Field('Merchandise_Name'),Field('Delivery_date',type='date'),
                Field('Quantity',type='integer'), Field('price',type='float'))
db.define_table('RFID',  Field('Room_Num') ,Field('ID_',type='string'))
class ConfigChecker:
    def __init__(self):
        self.config_info = {}

    def check_config(self):
        with open("Resource/config.json", 'r') as json_file:
            self.config_info = json.load(json_file)



class Key_Thread(QThread):
    key_pressed = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Key_Thread, self).__init__(parent)
        self.signal = MySignal()
        self.code_ = []
        self.code_ts = []
        self.reg_list = [1234098712, 3210291395, 3210661411, 1234567890]
        self.running = True  # Add running flag

    def run(self):
        def on_press(event):
            if not self.running:  # Check if thread should stop
                return  # Exit if the flag is False

            if event.event_type == "down":
                #print(self.code_)
                key = f"{event.name}"
                if key.isdigit():
                    self.code_.append(key)
                    self.code_ts.append(datetime.now())
                else:
                    self.code_ = []
                    self.code_ts = []

                if len(self.code_) >= 10:
                    self.code_ = self.code_[-10:]
                    self.code_ts = self.code_ts[-10:]
                    code_ = self.combine_list_to_int(self.code_)
                    code_ = str(code_).zfill(10)
                    print(code_, 'rfid code')
                    time_diff = (datetime.now() - self.code_ts[0]).total_seconds()
                    if time_diff < 0.5:
                        self.signal.card_data.emit(code_)
                        self.code_ = []
                        self.code_ts = []

        keyboard.hook(on_press)

        while self.running:  # Keep the loop running as long as the flag is True
            keyboard.wait()

    def combine_list_to_int(self, lst):
        combined_int = int(''.join(map(str, lst)))
        return combined_int

    def stop(self):
        print ('stoping thread')
        try:
            self.running = False  # Set running flag to False to stop the thread
            keyboard.unhook_all()  # Unhook all keyboard listeners if needed
        except Exception as e:
            print ('thread stop error', e)

class SimpleThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.queue = queue.Queue()

    def run(self):
        while True:
            host = self.queue.get()
            try:
                #url_mgs = "https://galesquio.pythonanywhere.com/WJV_INN/default/%s/?total_sale=%s&total_guess=%s&total_room=%s&room_sales=%s&occupied_rooms=%s&date_=%s&wjv_branch=%s"%(web_page,str(_total_amount),str(total_guess_),str(total_used_room),str(room_sales_),str(occupied_rooms_),str(dt2_str),self.config_info['BRANCH'])
                result = requests.get(str(host))#url = urlopen(str(host))
                data_ = str(str(host.split("?")[1]).split("&")[:5])
                #logging.info(data_)
            except Exception as e:
                pass#print (e, 'error')
            self.queue.task_done()



( Ui_aboutDialog, QaboutDialog ) = uic.loadUiType( 'about.ui' )
class aboutDialog ( QaboutDialog ):
    """MainWindow inherits QDialog"""
    def __init__ ( self,version_,parent=None):
        super(aboutDialog, self).__init__(parent)
        self.ui = Ui_aboutDialog()
        self.ui.setupUi( self )
        self.ui.version_.setText(version_)

    def __del__ ( self ):
        self.ui = None



(Ui_DeliveryPreview, QDialog) = uic.loadUiType('deliveryPreview.ui')
class DeliveryPreview( QDialog ):
    def __init__ ( self,merchandise_list2,parent=None):
        super(DeliveryPreview, self).__init__(parent)
        self.ui = Ui_DeliveryPreview()
        self.signal2 = MySignal()
        self.ui.setupUi( self )
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.ui.date_selected.setText(str(merchandise_list2[1]))
        self.post_data2(merchandise_list2[0])
        self.ui.print_delivery.clicked.connect(self.print_info)

    def __del__ (self):
        self.ui = None

    def print_info(self):
        self.signal2.sig_delivery_print.emit('print')
        self.close()

    def post_data2(self,overall_list):
        row_count = len(overall_list)
        model = QStandardItemModel(row_count + 1, 5)  # Add one more row for the grand total
        headers = ['id #', 'Merchandise/Menu Name', 'Delivered QTY', 'Raw Price', 'Total Price']
        model.setHorizontalHeaderLabels(headers)

        total_price_sum = 0  # Variable to store the sum of total prices

        for row in range(row_count):
            for column in range(5):
                if column == 4:  # Calculate total price if it's the fifth column
                    delivered_qty = overall_list[row][2]
                    raw_price = overall_list[row][3]
                    if delivered_qty is not None and raw_price is not None:
                        total_price = delivered_qty * raw_price
                        total_price_sum += total_price  # Add to the sum
                        item = QStandardItem(str(total_price))
                    else:
                        item = QStandardItem("N/A")
                else:
                    item = QStandardItem(str(overall_list[row][column]))
                item.setTextAlignment(Qt.AlignCenter)
                if column < 3:
                    item.setFlags(Qt.ItemIsEnabled)
                model.setItem(row, column, item)

        # Add the grand total row
        grand_total_item = QStandardItem(str(total_price_sum))
        grand_total_item.setTextAlignment(Qt.AlignCenter)
        grand_total_item.setFlags(Qt.ItemIsEnabled)  # Disable editing
        grand_total_font = QFont("Calibri", 12, QFont.Bold)  # Increase font size and make it bold
        grand_total_item.setFont(grand_total_font)
        grand_total_item.setForeground(QBrush(QColor("red")))  # Set text color to red
        model.setItem(row_count, 4, grand_total_item)

        self.ui.tableView_deliveryPreview.setModel(model)
        font = QFont("Calibri", 11)
        self.ui.tableView_deliveryPreview.setFont(font)
        self.ui.tableView_deliveryPreview.resizeColumnsToContents()
        self.ui.tableView_deliveryPreview.horizontalHeader().setStretchLastSection(True)
        self.ui.tableView_deliveryPreview.horizontalHeader().setStyleSheet("QHeaderView { font-size: 8pt;font:bold }")
        self.ui.tableView_deliveryPreview.setSortingEnabled(True)
        self.ui.tableView_deliveryPreview.setAlternatingRowColors(True)
        self.ui.tableView_deliveryPreview.setStyleSheet("alternate-background-color: rgb(231, 231, 231) ;background-color: white;")
        #set table read only
        self.ui.tableView_deliveryPreview.setEditTriggers(QTableView.NoEditTriggers)  # Optional for added safety

#        self.ui.tableView_deliveryPreview.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def close_program (self):
        self.close()



(Ui_Delivery, QDialog) = uic.loadUiType('delivery.ui')
class Delivery(QDialog):
    def __init__(self, merchandise_list, parent=None):
        super(Delivery, self).__init__(parent)
        self.ui = Ui_Delivery()
        self.ui.setupUi(self)
        self.ui.save_delivery_info.clicked.connect(self.capture_tableview)
        self.signal2 = MySignal()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setModal(True)

        self.all_data = merchandise_list
        self.filtered_data_by_type = self.all_data  # New: track filtered data by type

        self.init_filter_combo()
        self.display_data(self.all_data)

        self.ui.keywordsearch.textChanged.connect(self.filter_by_keyword)  # New: connect search box

    def __del__(self):
        self.ui = None

    def capture_tableview(self):
        model = self.ui.tableView_delivery.model()
        data = []
        for row in range(model.rowCount()):
            data.append([])
            for column in range(model.columnCount()):
                index = model.index(row, column)
                data[row].append(str(model.data(index)))

        new_list = []
        items_with_zero_price = []

        for line in data:
            if int(line[4]) > 0:
                if float(line[-1]) == 0:
                    items_with_zero_price.append(line[1])
                line.pop(1)
                new_list.append(line)

        if items_with_zero_price:
            item_names = ', '.join(items_with_zero_price)
            message = f"The following items have a price of zero:\n{item_names}.\nAre you sure you want to proceed?"
            reply = QMessageBox.question(self, 'Confirm Proceed', message,
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            else:
                self.signal2.sig_delivery.emit(new_list)
                self.close()
        else:
            self.signal2.sig_delivery.emit(new_list)
            self.close()

    def init_filter_combo(self):
        self.ui.comboBox_filter.clear()
        self.ui.comboBox_filter.addItem("All")
        types = set()
        for row in self.all_data:
            types.add(str(row[1]))
        for t in sorted(types):
            self.ui.comboBox_filter.addItem(t)
        self.ui.comboBox_filter.currentIndexChanged.connect(self.filter_data)

    def display_data(self, data):
        row_count = len(data)
        model = QStandardItemModel(row_count, 6)
        header__ = ['id #', 'Type', 'Merchandise/Menu Name', 'Current QTY', 'Delivered QTY', 'Raw Price']
        model.setHorizontalHeaderLabels(header__)
        for row in range(row_count):
            for column in range(6):
                item = QStandardItem(str(data[row][column]))
                item.setTextAlignment(Qt.AlignCenter)
                if column < 3:
                    item.setFlags(Qt.ItemIsEnabled)
                model.setItem(row, column, item)

        self.ui.tableView_delivery.setModel(model)
        font = QFont("Calibri", 11)
        self.ui.tableView_delivery.setFont(font)
        self.ui.tableView_delivery.resizeColumnsToContents()
        self.ui.tableView_delivery.horizontalHeader().setStretchLastSection(True)
        self.ui.tableView_delivery.horizontalHeader().setStyleSheet("QHeaderView { font-size: 8pt;font:bold }")
        self.ui.tableView_delivery.setSortingEnabled(True)
        self.ui.tableView_delivery.setAlternatingRowColors(True)
        self.ui.tableView_delivery.setStyleSheet(
            "alternate-background-color: rgb(231, 231, 231); background-color: white;")

    def filter_data(self):
        selected = self.ui.comboBox_filter.currentText()
        if selected == "All":
            self.filtered_data_by_type = self.all_data
        else:
            self.filtered_data_by_type = [row for row in self.all_data if str(row[1]) == selected]
        self.filter_by_keyword()  # Apply keyword filter after type filter

    def filter_by_keyword(self):
        keyword = self.ui.keywordsearch.text().lower().strip()
        if not keyword:
            self.display_data(self.filtered_data_by_type)
            return

        filtered = []
        for row in self.filtered_data_by_type:
            if any(keyword in str(cell).lower() for cell in row):
                filtered.append(row)

        self.display_data(filtered)

    def close_program(self):
        self.close()


class CommandRunner(QThread):
    
    def __init__(self, command):
        super().__init__()
        self.signal2 = MySignal()
        self.command = command

    def run(self):
        sleep(2)
        process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            self.signal2.sig_scan.emit(line)
        process.wait()
        return_code = process.returncode
        self.signal2.sig_scan_complete.emit(f"Completed")


(Ui_DialogWindow2, QDialog) = uic.loadUiType('login.ui')
class Login( QDialog ):
    def __init__ ( self,parent=None):
        super(Login, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.ui = Ui_DialogWindow2()
        self.ui.setupUi( self )
        self.signal2 = MySignal()
        self.setWindowTitle('Credentials')

        #self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.ui.login_button.clicked.connect(self.handleLogin)
        self.ui.close_.clicked.connect(self.close_program)
        self.ui.user_.setFocusPolicy(Qt.StrongFocus)
        self.ui.user_.setFocus()
        self.ui.pass_.setEchoMode(QLineEdit.Password)
        self.ui.pass_.returnPressed.connect(self.handleLogin)
    def __del__ (self):
        self.ui = None


    def close_program (self):
        #self.signal2.sig2.emit("ok")
        self.close()


    def closeEvent(self, event):
        #self.signal2.sig2.emit("ok")
        self.close()


    def handleLogin(self):
        global db
        user_name = self.ui.user_.text()
        user_pass = self.ui.pass_.text()
        query = (db.WJV_users.User_ == user_name)
        rows = db(query).select()
        if rows:
            for row in rows:
                if row.Password_ != user_pass:
                    QMessageBox.warning(
                        self, 'Error', 'Bad user or password')
                    self.signal2.username__.emit('')
                else:
                    self.logged = user_name
                    self.username_ = user_name
                    self.accept()
                    self.signal2.username__.emit(user_name)
                    log__ = 'user log as %s'%self.username_
                    #logging.info(log__)

        else:
            QMessageBox.warning(
                self, 'Error', 'Bad user or password')

class timer_thread(QThread):
    def __init__(self):
        super(timer_thread, self).__init__()
        self.signal = MySignal()
        self.counter_sec = 0
        self.counter_tenmin = 0
        self._running = True

    def __del__(self):
        self.wait()

    def run(self):
        while self._running:
            sleep(1)
            self.counter_sec += 1
            self.signal.sig_sec.emit("ok")
            self.signal.sig_sec2.emit("ok")
            if self.counter_sec >= 30:
                self.signal.sig_min.emit('ok')
                self.counter_sec = 0
            if self.counter_tenmin >= 1200:
                self.signal.sig_tenmin.emit('ok')
                self.counter_tenmin = 0

    def stop(self):
        print ('stoping thread - timer_thread')
        self._running = False

class update_min(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.current_time = ''
        self.signal = MySignal()

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            sleep(1)
            self.signal.sig_TV.emit("ok")


( Ui_MainWindow2, QMainWindow2 ) = uic.loadUiType( 'TV_display.ui' )
class MainWindow2 (QMainWindow2):
    """MainWindow inherits QMainWindow"""
    def __init__ (self, parent=None):
        QMainWindow2.__init__(self, parent)
        self.ui = Ui_MainWindow2()
        self.signal = MySignal()
        self.ui.setupUi(self)
        self.myThread = update_min()
        self.myThread.start()
        self.myThread.signal.sig_TV.connect(self.iterate_info)
        config_checker = ConfigChecker()
        config_checker.check_config()
        self.config_info = config_checker.config_info
        self.room_max = int(self.config_info['ROOM_MAX']) + 1
        self.clear_max_room()
        self.iterate_info()
        

    def __del__ (self):
        self.ui = None

    def clear_max_room (self):
        for x in range(self.room_max,96):
            eval("self.ui.groupBoxRM_%s.setHidden(True)"%x)

    def close_window (self):
        self.close()
    def iterate_info(self):
        global global_record
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        for x in range(1,self.room_max):
            try:
                rm_name = 'ROOM_%s'%x
                if rm_name in test_global:
                    rm_time = test_global[rm_name][0]
                    rm_type_hr = int(test_global[rm_name][2].split(' ')[1])
                    rm_delta = rm_time + timedelta(hours=rm_type_hr)
                    time_delta = (rm_delta - now).total_seconds()
                    m, s = divmod(time_delta, 60)
                    h, m = divmod(m, 60)
                    new_time = '%02d:%02d:%02d'%(h,m,s)
                    if test_global[rm_name][-3]:
                        eval("self.ui.label%s.setText('EXTEND')"%(x))
                        eval('self.ui.box%s.setStyleSheet("background-color: rgb(0, 170, 255);")'%x)
                    else:
                        if time_delta < 0:
                            eval('self.ui.box%s.setStyleSheet("background-color: rgb(255, 0, 0);")'%x)
                            eval("self.ui.label%s.setText('OVER')"%(x))
                        else:
                            eval("self.ui.label%s.setText('%s')"%(x,new_time))
                            eval('self.ui.box%s.setStyleSheet("background-color: rgb(0, 255, 0);")'%x)
                else:
                    eval("self.ui.label%s.setText('')"%x)
                    eval('self.ui.box%s.setStyleSheet("")'%x)
            except:
                pass


class MyTableModel(QAbstractTableModel):
    def __init__(self, parent, mylist,  *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.mylist = mylist
    def rowCount(self, parent):
        return len(self.mylist)
    def columnCount(self, parent):
        return len(self.mylist[0])
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]
    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.mylist = sorted(self.mylist, key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.mylist.reverse()
        self.emit(SIGNAL("layoutChanged()"))


class MonthlyPreview(QDialog):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create a table widget to display the data
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['TRANSACTION DATE', 'ITEM NAME', 'QTY', 'PRICE', 'TOTAL'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        monthly_data, total_amount, self.start_date, self.end_date, self.branch_ = self.data
        
        # Set the row count
        self.table.setRowCount(len(monthly_data) + 1)  # Add one for the total row
        
        for row_idx, row in enumerate(monthly_data):
            for col_idx, item in enumerate(row):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))
        
        # Add the total amount row
        total_row_idx = len(monthly_data)
        self.table.setItem(total_row_idx, 0, QTableWidgetItem("TOTAL AMOUNT RECEIVED:"))
        self.table.setItem(total_row_idx, 4, QTableWidgetItem(f"{total_amount:.2f}"))  # Assuming TOTAL is in the last column

        # Format the total row (optional)
        for col_idx in range(1, 4):  # Clear the other cells in the total row
            self.table.setItem(total_row_idx, col_idx, QTableWidgetItem(""))

        # Add total amount received label
        total_label = QLabel(f'TOTAL AMOUNT: {total_amount:.2f}')
        layout.addWidget(self.table)
        layout.addWidget(total_label)
        
        # Add export button
        self.export_button = QPushButton('Export to PDF')
        self.export_button.clicked.connect(self.export_to_pdf)
        layout.addWidget(self.export_button)

        self.setLayout(layout)


    
    def export_to_pdf(self):
        """Exports the DataFrame to a PDF file using ReportLab."""

        df = pd.DataFrame(self.data[0], columns=["DATE", "ITEM NAME", "QTY", "PRICE", "TOTAL"])
        
        # Calculate the grand total for the "TOTAL" column
        grand_total = df["TOTAL"].sum()

        # Create a list to hold the table data, including the header
        table_data = [df.columns.to_list()]  # Add column headers here
        table_data.extend(df.values.tolist())  # Add the actual data rows

        # Add the grand total row at the bottom
        table_data.append(["Grand Total", "", "", "", f"Php {grand_total:,.2f}"])

        # Create a Table object with header row styling
        table = Table(table_data, style=[
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),             # Header text alignment
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),   # Header font
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),            # Header vertical alignment
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),  # Grid lines
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),    # Table border
            ('BACKGROUND', (-1, -1), (-1, -1), colors.lightgrey),  # Grand total background
            ('ALIGN', (-1, -1), (-1, -1), 'CENTER'),         # Grand total alignment
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),  # Grand total font
        ])

        # Create a PDF document with appropriate page size and title
        pdf = SimpleDocTemplate("report.pdf", pagesize=letter, title="Dataframe as PDF")

        # Build the PDF document with the title and table
        elements = []


        subtitle = f'Branch: {self.branch_}'
        subtitle_style = getSampleStyleSheet()['Heading2']
        subtitle_style.alignment = 1  # Left alignment (0: left, 1: center, 2: right)
        subtitle_style.fontSize = 12  # Set custom font size for the subtitle (e.g., 14 points)
        subtitle_paragraph = Paragraph(subtitle, subtitle_style)  # Convert subtitle string to a Paragraph (flowable)
        elements.append(subtitle_paragraph)

        title = f'Date coverage: {self.start_date} - {self.end_date}'
        title_style = getSampleStyleSheet()['Title']
        title_style.alignment = 1  # Left alignment (0: left, 1: center, 2: right)
        title_style.fontSize = 10  # Set custom font size (e.g., 18 points)
        title_paragraph = Paragraph(title, title_style)  # Convert title string to a Paragraph (flowable)
        elements.append(title_paragraph)

        # Subtitle below the title with left alignment


        # Add space between the subtitle and the table using Spacer
        elements.append(Spacer(1, 2))  # Spacer(width, height), height is in points (1 inch = 72 points)

        # Add the table
        elements.append(table)

        # Build the PDF document
        pdf.build(elements)

        # Open the generated PDF file after saving
        os.startfile("report.pdf")



( Ui_MainWindow, QMainWindow ) = uic.loadUiType( 'mainwindow.ui' )
class MainWindow ( QMainWindow ):
    """MainWindow inherits QMainWindow"""
    def __init__ ( self, user_name,parent = None ):
        QMainWindow.__init__( self, parent )
        global global_RM_count, queue_db, queue_db_update
        self.signal = MySignal()
        self.ui = Ui_MainWindow()
        self.ui.setupUi( self )
        self.load_room_mapping()
        self.update_titles()
        self.config_info = self.read_config()
        self.skip_rooms = self.config_info['SKIPPED_ROOMS']
        # Populate the combobox room_list based on room_mapping.json
        self.ui.room_list.clear()
        self.ui.comboBox_roomNumber.clear()
        for room_key, room_data in self.room_mapping.items():
            self.ui.room_list.addItem(f"{room_data[0]}")
            self.ui.comboBox_roomNumber.addItem(f"{room_data[0]}")


        self.active_rooms_ = []
        self.locked_rooms = []
        self.unavailable_rooms = []
        self.ha_enable_flag = False
        try:
            if self.config_info['HASS_FLAG'] == True:
                from HASS_devices import HomeAssistantSwitchSummary
                self.ha_enable_flag = True
                hass_api = self.config_info['HASS_API']
                hass_ip = self.config_info['HASS_IP']
                # Replace with your Home Assistant details
                HOME_ASSISTANT_URL = hass_ip
                API_TOKEN = hass_api
                self.ha_summary = HomeAssistantSwitchSummary(HOME_ASSISTANT_URL, API_TOKEN)
                self.ha_summary.signal.update_active_rooms.connect(self.update_room_status)
                self.ha_summary.signal.update_inactive_rooms.connect(self.inactive_room_status)
                monitoring_thread = self.ha_summary.start_monitoring()
        except Exception as e:
            print (e)
        self.queue_checkin = {}
        room_max = int(self.config_info['ROOM_MAX']) + 1
        self.limit_list = []
        self.counter_disp = 0
        #self.aut0_timer = 5
        self.ui.tabWidget.setCurrentIndex(0)
        for x in range(room_max, global_RM_count+1):
            self.limit_list.append(x)
        #self.ui.comboBox_type.currentIndexChanged.connect(self.update_qty_wristband)
        self.ui.comboBox_typeB.currentIndexChanged.connect(self.selection_settings)
        self.ui.actionLogout_2.triggered.connect(self.logout_)
        self.ui.clear_db.clicked.connect(self.clear_database)
        self.ui.actionRefresh.triggered.connect(self.update_DB_GUI)
        #self.ui.actionTV_Display.triggered.connect(self.view_tv)
        self.ui.actionAbout.triggered.connect(self.about_)
        self.ui.actionExit.triggered.connect(self.close_allWindow)
        self.ui.actionAbout_2.triggered.connect(self.about_2)
        self.ui.generate.clicked.connect(self.generate_report)
        self.ui.print__.clicked.connect(self.handlePrint)
        self.ui.view_excel_inventory.clicked.connect(self.to_excel)
        self.disable_max_room()
        self.settings_flag = False
        self.ui.preview__.clicked.connect(self.handlePreview)
        self.ui.create_user.clicked.connect(self.create_user_pass)
        self.ui.update_mer_db_.clicked.connect(self.update_mer_db)
        self.ui.printall.clicked.connect(self.print_all_pending)
        self.ui.update_db__.clicked.connect(self.update_db_merchandise)
        self.ui.update_db_rfid.clicked.connect(self.update_db_rfid)
        self.ui.update_db__3.clicked.connect(self.update_db_roomrates)
        self.ui.view_all.clicked.connect(self.view_room_details)
        self.ui.comboBox_merchandise.currentIndexChanged.connect(self.update_mer_info)
        self.ui.comboBox_roomNumber.currentIndexChanged.connect(self.update_rfid_info)
        #self.ui.comboBox_roomrate_update.currentIndexChanged.connect(self.update_roomrates_info)
        self.historical_time = datetime.now()
        self.ui.room_list.currentIndexChanged.connect(self.update_roomrates_info)
        self.username = user_name
        self.ui.pushButton_settings.clicked.connect(self.selection_settings4)
        self.ui.pushButton_home.clicked.connect(self.selection_settings1)
        self.ui.pushButton_cashier.clicked.connect(self.selection_settings2)
        self.ui.pushButton_merchandise.clicked.connect(self.selection_settings3)
        self.ui.tabWidget.setTabEnabled(4,False) #disable settings by default
        self.ui.view_.clicked.connect(self.view_inventory__)
        self.signal.send_html_queue.connect(self.try_send_url)
        self.hardware_status = False
        self.line_ctr = 0
        self.ui.pushButton_settings.setEnabled(False)
        self.ui.label_20.setEnabled(False)
        self.ui.add_free_item.clicked.connect(self.add_free_item)
        self.ui.remove_free_item.clicked.connect(self.remove_free_item)
        self.ui.update_merchandise_btn.clicked.connect(self.update_delivery_info)
        self.ui.preview_delivery.clicked.connect(self.preview_delivery_details)
        self.ui.preview_delivery_2.clicked.connect(self.preview_monthly_details)
        #self.ui.print_delivery.clicked.connect(self.preview_delivery_details)

        #self.ui.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
        self.toggle_bit = True
        self.indicator_flag = False
        self.msg_notavailable = set()
        self.db_result = {}
        self.db_result_keys = []
        self.header = ['Room #','TicketID', 'Room Type','Serial#', 'CheckIn', 'CheckOut','Hours','+Head', 'Cashier', 'Total Price','Mechandise']
        self.header2 = ['Platform','Booking #', 'Room#','Guest Name', 'Amount', '# of Days','CheckIn', 'CheckOut','Hours','+Head','Total Price', 'Mechandise']
        query = (db.WJV_db.Status_ == "Open")
        rows = db(query).select()
        for row in rows:
            self.db_result_keys.append(int(row.Room_Number.split('_')[1]))
            self.db_result.update({row.Room_Number:[row.Check_In,row.Room_Merchandise,row.Room_Type,
                row.RM_Price, row.Ticket_ID, row.Cashier_, row.Extended_, self.config_info['BRANCH'], row.extra_heads]})

        self.update_GUI()
        self.thread = SimpleThread()
        self.thread.start()

        self.timer_ = timer_thread()
        self.timer_.start()
        self.timer_.signal.sig_sec.connect(self.update_GUI)
        self.timer_.signal.sig_min.connect(self.remove_duplicates)
        self.timer_.signal.sig_tenmin.connect(self.update_web_info)
        #self.timer_.signal.sig_sec2.connect(self.update_timer2)
        self.auto_Inv_tracking()
        self.recover = {}
        for idx in range(1,global_RM_count+2):
            eval('self.ui.room_%s_button.clicked.connect(partial(self.button_clicked, %s))'%(idx,idx))
            self.recover.update({idx:10})
        self.enable_admin_buttons()
        self.data_uploader = DataUploader(self.config_info)
        self.data_uploader.signal.connectivity_status.connect(self.update_connectivity_status)
        self.data_uploader.start()
        
        self.key_thread_ = Key_Thread()
        self.key_thread_.start()
        self.key_thread_.signal.card_data.connect(self.open_dialog_window)
        # Define the COM port and baud rate
        self.com_port = self.config_info['DISPLAYPort']  # Change this to your COM port (e.g., 'COM3' on Windows)
        self.baud_rate = 9600   # Make sure it matches the Arduino's baud rate
        try:
            self.ser = serial.Serial(self.com_port, self.baud_rate)
        except Exception as e:
            pass#print(f"An error occurred: {e} ")

    def update_web_info(self):
        #print ('update web info called - common')
        self.data_uploader.upload_data_to_cloud()

    def update_connectivity_status(self, status):
        color = "rgb(0, 255, 0)" if status else "rgb(255, 0, 0)"
        self.ui.box_connectivity.setStyleSheet(
            f"""
            color: #333;
            border: 2px solid #555;
            border-radius: 2px;
            padding: 5px;
            background-color: {color};
            """
        )

    def update_lock_status(self, locked_rooms):
        for locked_room in locked_rooms:
            new_idx = int(locked_room.split(' ')[1])
            if not locked_room.capitalize() in self.locked_rooms:
                self.locked_rooms.append(locked_room.capitalize())
            exec('self.ui.stat%s.setStyleSheet("color: #333; border: 2px solid #555; border-radius: 12px; padding: 5px; background-color: rgb(253, 0, 0);")'%str(new_idx))

    def inactive_room_status(self, inactive_rooms):
        pass
        #self.locked_rooms = inactive_rooms
        #print (self.locked_rooms, 'signal connect to locked rooms')

    def display_message(self,msg_):
        try:
            msg_ = msg_[:4]
            if msg_:
                message = "|".join(msg_) + "\n"# str(msg_[0])+"|test|new|one" + "\n"
                self.ser.write(message.encode())
        except serial.SerialException:
            pass
            #print(f"Failed to open {self.com_port}. Make sure the port is available and the device is connected.")
            #self.ser = serial.Serial(self.com_port, self.baud_rate)

        except Exception as e:
            pass#print(f"An error occurred: {e} ")

    def remove_duplicates(self):
        # Use a query to get records with "Status_" of "Open" and group them by "Room_number"
        query = (db.WJV_db.Status_ == "Open")
        rows = db(query).select(db.WJV_db.Room_Number, db.WJV_db.id, orderby=db.WJV_db.id)

        # Create a dictionary to store the results
        room_id_map = {}

        # Populate the dictionary
        for row in rows:
            room_number = row.Room_Number
            room_id = row.id
            if room_number not in room_id_map:
                room_id_map[room_number] = []
            room_id_map[room_number].append(room_id)

        # Print the dictionary where room numbers map to sorted room IDs
        #print(room_id_map)
        for room_number, id_list in room_id_map.items():
            if len(id_list) > 1:
                # If there's more than one value, remove the smallest one
                id_list.remove(min(id_list))
                for id_ in id_list:
                    deleted_rows = db(db.WJV_db.id == id_).delete()
                    db.commit()
                    #if deleted_rows:
                        #logging.info(f'Duplicates found. removing id: {id_}')

                
    def load_room_mapping(self):
        # Read room_mapping.json and save it to self.room_mapping
        with open('Resource/room_mapping.json') as f:
            self.room_mapping = json.load(f)
        #print (self.room_mapping, 'room mapping')

    def update_titles(self):
        for room_key, room_data in self.room_mapping.items():
            #print (room_key, room_data, 'room data')
            room_num = int(room_key.split('_')[1])
            group_box_name = f"groupBox_room{room_num}"
            group_box = self.findChild(QGroupBox, group_box_name)
            if group_box:
                # Use the first element of room_data for the title
                group_box.setTitle(room_data[0])

    def open_dialog_window(self, card_code):
        active_window = QApplication.activeWindow()
        if active_window == self:
            #print(f"{self.windowTitle()} is currently active.")
            query = (db.WJV_db.RFID_ == card_code) & (db.WJV_db.Status_ == "Open")
            rows = db(query).select()
            for row in rows:
                room_number = (int(row.Room_Number.split('_')[1]))
                #print (card_code,room_number)
                self.button_clicked(room_number)
                break

    def read_config(self):
        with open("Resource/config.json", 'r') as json_file:
            config_info = json.load(json_file)
        return config_info

    def active_room_list(self,pass_arg):
        self.active_rooms_ = pass_arg
        #print (self.active_rooms_, 'active rooms')

    def string_to_time(self,time_str):
        # Parse the string using strptime
        dt = datetime.strptime(time_str.strip().lower(), "%I%p")
        return dt.time()

    def get_time_group_and_startB(self, delta_hr):
        current_time = datetime.now()

        shifts__ = self.config_info["COTTAGE_Start_time"]
        #print(shifts__, 'shifts')

        try:
            shifts = {
                'Morning': self.string_to_time(shifts__[0]),     # 8AM
                'Afternoon': self.string_to_time(shifts__[1]),   # 2PM
                'Evening': self.string_to_time(shifts__[2]),     # 8PM
            }
        except Exception as e:
            #print(e, 'error in get_time_group_and_start')
            shifts = {
                'Morning': time(8, 0),
                'Afternoon': time(14, 0),
                'Evening': time(20, 0),
            }

        candidates = []

        for name, start_t in shifts.items():
            start_dt = datetime.combine(current_time.date(), start_t)
            end_dt = start_dt + timedelta(hours=delta_hr)

            # Handle overnight shift (e.g., 8PM - 6AM)
            if end_dt.date() != start_dt.date():
                if current_time >= start_dt:
                    pass  # tonight 8PM to tomorrow
                else:
                    start_dt -= timedelta(days=1)
                    end_dt = start_dt + timedelta(hours=delta_hr)

            if start_dt <= current_time < end_dt:
                candidates.append((start_dt, name))

        if candidates:
            start_dt, name = max(candidates)
            #print(f"Current time {current_time.strftime('%I:%M %p')} is within {name} shift window. Start time: {start_dt}")
            return name, start_dt

        # No active shift — return None for both
        #print(f"No active shift at {current_time.strftime('%I:%M %p')}.")
        return None, None


    def update_room_status(self, room_info_all):
        #print ('update room status called')
        for room_info in room_info_all:
            #print (room_info[0] , self.locked_rooms, room_info, '<######')
            if room_info[0] in self.locked_rooms:
                room_info[1] = 'LOCKED'
            #self.config_info = self.read_config()
            rm_number, stat_ = room_info
            new_idx = int(rm_number.split(' ')[1])

            if stat_ == 'OFF':
                if rm_number in self.unavailable_rooms:
                    self.unavailable_rooms.remove(rm_number)
                #if not rm_number in self.active_rooms_:
                #    self.active_rooms_.append(rm_number)
                #if rm_number in self.active_rooms_:
                #    self.active_rooms_.remove(rm_number)
                self.check_in_stat = []
                query = (db.WJV_db.Status_ == "Open")
                rows = db(query).select()
                for row in rows:
                    self.check_in_stat.append(int(row.Room_Number.split('_')[1]))
                self.recover[int(new_idx)] = 10
                #if rm_number in self.locked_rooms:
                #    self.locked_rooms.remove(rm_number.capitalize())
                exec('self.ui.room_%s_button.setEnabled(True)'%str(new_idx))
                exec('self.ui.stat%s.setStyleSheet("color: #333; border: 2px solid #555; border-radius: 12px; padding: 5px; background-color: rgb(255, 255, 255);")'%str(new_idx))
            elif stat_ == 'UNAVAILABLE':
                if not rm_number in self.unavailable_rooms:
                    self.unavailable_rooms.append(rm_number)
                #elf.recover[int(new_idx)] = 10
                #self.locked_rooms.append(rm_number.capitalize())
                exec('self.ui.stat%s.setStyleSheet("color: #333; border: 2px solid #555; border-radius: 12px; padding: 5px; background-color: rgb(255, 255, 180);")'%str(new_idx))
            elif stat_ == 'ON':
                #print(QApplication.activeWindow(),"active window")

                if rm_number in self.unavailable_rooms:
                    self.unavailable_rooms.remove(rm_number)
                #if rm_number in self.locked_rooms:
                #    self.locked_rooms.remove(rm_number.capitalize())
                if not rm_number in self.active_rooms_:
                    self.active_rooms_.append(rm_number)
                try:
                    #print (rm_number,self.locked_rooms, 'check if in locked rooms')
                    if not rm_number in self.locked_rooms:
                        room_x = 'ROOM_%s'%rm_number.split(' ')[1]
                        query = (db.WJV_db.Status_ == 'Open')
                        rows = db(query).select()
                        machine_list = []
                        for row in rows:
                            machine_list.append(row.Room_Number)
                        #print (machine_list, 'occupied rooms')
                        if not room_x in machine_list:
                            #query to db, get the room number last close status

                            last_closed_record = db((db.WJV_db.Room_Number == room_x) & 
                                                    (db.WJV_db.Status_ == 'Close')).select(
                                                    db.WJV_db.Check_Out,
                                                    orderby=~db.WJV_db.Check_Out, limitby=(0, 1)).first()

                            # Check if a record was found
                            try:
                                check_out_datetime = last_closed_record.Check_Out
                                current_datetime = datetime.now()
                                time_difference = (current_datetime - check_out_datetime).total_seconds()
                            except:
                                time_difference = 301


                            print (rm_number, '<------------------------------------')
                            rm_num = rm_number.split(' ')[1]
                            rm_num_mapping = self.room_mapping[f"ROOM_{str(rm_num).zfill(2)}"][0]

                            if time_difference > 300:
                                cur_datetime = datetime.now()
                                ticket_id = cur_datetime.strftime("%m%d%y_%I%M%S")
                                ticket_id = room_x + "_"+ ticket_id
                                rm_num = rm_number.split(' ')[1]
                                room_hour_ = self.room_mapping[f"ROOM_{str(rm_num).zfill(2)}"][1]
                                rm_num_mapping = self.room_mapping[f"ROOM_{str(rm_num).zfill(2)}"][0]
                                type__ = "R_0%s_%s"%((str(rm_num).zfill(2)), room_hour_)
                                query = (db.Room_rates_db.Rate_ID.contains(type__))
                                rows = db(query).select()
                                standard_room_rate = rows[0].Rate_Name + " Php " + str(rows[0].Price_)
                                cur_datetime = datetime.now()

                                query_rfid = (db.RFID.Room_Num == room_x)
                                rows_rfid = db(query_rfid).select()
                                group_ = None
                                if "COTTAGE" in standard_room_rate:
                                    group_, cur_datetime = self.get_time_group_and_startB(room_hour_)
                                    if group_:
                                        details_ = [ticket_id, standard_room_rate, 0, {}, {}, 'Open', False, cur_datetime, None,room_x , 'system', 0, 0, 0, None, None, rows_rfid[0].ID_]
                                        self.add_new_db(details_)
                                    else:
                                        if rm_num not in self.msg_notavailable:
                                            QMessageBox.warning(self, "Warning", f"""{rm_num_mapping} is not available yet.\nAuto check-in is disabled. \nPlease make sure that {rm_num_mapping} is turned off and try again later.""", QMessageBox.Ok, QMessageBox.Ok)
                                            self.msg_notavailable.add(rm_num)
                                else:
                                    details_ = [ticket_id, standard_room_rate, 0, {}, {}, 'Open', False, cur_datetime, None,room_x , 'system', 0, 0, 0, None, None, rows_rfid[0].ID_]
                                    self.add_new_db(details_)
                            else:
                                try:
                                    if rm_num not in self.msg_notavailable:
                                        QMessageBox.warning(self, "Warning", f"""{rm_num_mapping} is not available yet.\nAuto check-in is disabled.\nPlease make sure that {rm_num_mapping} is turned off and try again later.""", QMessageBox.Ok, QMessageBox.Ok)
                                        self.msg_notavailable.add(rm_num)
                                except:
                                    if rm_num not in self.msg_notavailable:
                                        QMessageBox.warning(self, "Warning", f"""{rm_num_mapping} is not available yet.\nAuto check-in is disabled.\nPlease make sure that {rm_num_mapping} is turned off and try again later.""", QMessageBox.Ok, QMessageBox.Ok)
                                        self.msg_notavailable.add(rm_num)

                except Exception as e:
                    db.rollback()
                    print (e)
                exec('self.ui.stat%s.setStyleSheet("color: #333; border: 2px solid #555; border-radius: 12px; padding: 5px; background-color: rgb(50, 194, 25);")'%str(new_idx))
            else:
                #pass
                exec('self.ui.stat%s.setStyleSheet("color: #333; border: 2px solid #555; border-radius: 12px; padding: 5px; background-color: rgb(255, 255, 180);")'%str(new_idx))
        self.update_DB_GUI()
        #print (self.unavailable_rooms)
                


    def print_message2(self, msg__):
        font = {
            "height": 11,
        }
        font2 = {
            "height": 16,
        }

        font3 = {
            'height': 12,
            'italic':1,
        }



        max_ = len(msg__)
        with Printer(linegap=1) as printer:
            for idx, x in enumerate(msg__):
                if idx==0:
                    printer.text(x.strip(), font_config=font2)
                else:
                    printer.text(x.strip(), font_config=font)

    def print_billing(self,filename, printer_name = None):
        try:
            if printer_name == 'thermal':
                win32print.SetDefaultPrinter(self.config_info['THERMAL'])
                printer_name = win32print.GetDefaultPrinter()
                stat__ = self.check_printer(printer_name)
                if stat__:
                    out = '/d:"%s"' % (printer_name)
                    with open(filename) as f:
                        contents = f.readlines()
                    self.print_message2(contents)
                else:
                    QMessageBox.warning(self, 'Error', 'Printer not available')
        except:
            QMessageBox.warning(self, 'Error', 'Unable to print')


    def format_table(self, data):
        # Adjust column widths as needed
        column_widths = [13, 5, 7, 7]   # Example column widths
        table_string = ""
        
        for row in data:
            formatted_row = ""
            for i, item in enumerate(row):
                formatted_row += str(item).ljust(column_widths[i])
            table_string += formatted_row.strip() + "\n"
        print (table_string)
        return table_string

    def print_table(self, table_string, printer_name="XP-581"):
        # Open a handle to the printer
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            # Start a print job
            hjob = win32print.StartDocPrinter(hprinter, 1, ("Table Print", None, "RAW"))
            try:
                # Start a page
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, table_string.encode())
                win32print.EndPagePrinter(hprinter)
            finally:
                win32print.EndDocPrinter(hjob)
        finally:
            win32print.ClosePrinter(hprinter)


    def print_billing2B(self,data, printer_name = None):
        try:
            if printer_name == 'thermal':
                win32print.SetDefaultPrinter(self.config_info['THERMAL'])
                printer_name_actual = win32print.GetDefaultPrinter()
                stat__ = self.check_printer(printer_name_actual)
                #print (data)
                if stat__:
                    out = '/d:"%s"' % (printer_name_actual)
                    table_string = self.format_table(data)
                    self.print_table(table_string,printer_name_actual)
                    #self.print_message3(contents)
        except:
            pass



    def check_printer(self,printer_name):
        c = wmi.WMI ()
        for p in c.Win32_Printer():
            if p.caption == printer_name:
                #print 'equal', p.WorkOffline
                if p.WorkOffline:
                    status_ = False
                else:
                    status_ = True
        return status_

    def preview_delivery_details(self):
        global relative_path
        #self.update_web_info()
        # temp_var = self.ui.dateTimeEdit.date() 
        # selected_date = temp_var.toPyDate()
        selected_date = self.ui.calendarWidget_2.selectedDate().toPyDate()
        print (selected_date)
        query = (db.Track_delivery.Delivery_date == selected_date)
        rows = db(query).select()
        merchandise_list_2 = []
        if rows:
            for idx, row in enumerate(rows):
                merchandise_list_2.append([row.Merchandise_ID,row.Merchandise_Name,row.Quantity, row.price]) 
        try:
            self.ui.delivery_msg.setText('')
            self.deliveryPreview_dialog = DeliveryPreview([merchandise_list_2,selected_date])
            self.deliveryPreview_dialog.setWindowTitle( 'Preview Delivery Window' )
            self.deliveryPreview_dialog.show()
            self.deliveryPreview_dialog.signal2.sig_delivery_print.connect(self.print_delivery_details)
        except:
            pass   

    def preview_monthly_details(self):
        global relative_path
        # temp_var = self.ui.dateTimeEdit.date()  # Assume you're using a date picker for selecting month
        # selected_date = temp_var.toPyDate()
        selected_date = self.ui.calendarWidget_2.selectedDate().toPyDate()

        # Get the first and last day of the month
        first_day_of_month = selected_date.replace(day=1)
        last_day_of_month = (first_day_of_month + pd.DateOffset(months=1)).replace(day=1) - pd.DateOffset(days=1)

        # Query for transactions within the selected month
        query = (db.Track_delivery.Delivery_date >= first_day_of_month) & (db.Track_delivery.Delivery_date <= last_day_of_month)
        rows = db(query).select()

        # Prepare data for the dialog
        monthly_data = []
        total_amount = 0.0
        if rows:
            for row in rows:
                total = row.Quantity * row.price  # Calculate total
                total_amount += total
                monthly_data.append([
                    row.Delivery_date.strftime("%b-%d-%Y"),  # Format the date
                    row.Merchandise_Name,
                    row.Quantity,
                    row.price,
                    total
                ])
        
        # Create and display the dialog
        try:
            self.ui.delivery_msg.setText('')
            self.monthlyPreview_dialog = MonthlyPreview([monthly_data, total_amount, first_day_of_month.strftime("%B %d"), last_day_of_month.strftime("%B %d"), self.config_info['BRANCH']])
            self.monthlyPreview_dialog.setWindowTitle('Preview Monthly Transactions')
            #set window size
            self.monthlyPreview_dialog.resize(800, 400)
            self.monthlyPreview_dialog.show()
        except Exception as e:
            print(f"Error displaying monthly preview: {e}")


    def print_delivery_details(self):
        global relative_path
        #temp_var = self.ui.dateTimeEdit.date() 
        #selected_date = temp_var.toPyDate()
        #get the selected date from a qcalendarwidget
        selected_date = self.ui.calendarWidget_2.selectedDate().toPyDate()
        query = (db.Track_delivery.Delivery_date == selected_date)
        rows = db(query).select()
        pending_print = ''
        grand_total = 0
        data = [] 
        if rows:
            for idx, row in enumerate(rows):
                if idx == 0:
                    data.append(['BRANCH:',self.config_info['BRANCH'], ' ', ' '])
                    data.append(['Date:',row.Delivery_date.strftime("%b-%d-%Y"),' ',' '])
                    data.append(['DAILY','','',''])
                    data.append(['-------------','-----','-------','-------'])
                    data.append(['Item Name', 'Qty', 'Price', 'Total' ])
                    data.append(['-------------','-----','-------','-------'])
                    # msg_ = 'DATE: %s\n\n' % row.Delivery_date
                    # pending_print += msg_
                try:
                    total_ = row.Quantity * row.price
                    grand_total += total_
                except:
                    total_ = 0
                # Adjust column widths to ensure the total length is 25 characters
                name_ = (row.Merchandise_Name[:10] if len(row.Merchandise_Name) > 10 else row.Merchandise_Name.ljust(10))
                qty_ = str(row.Quantity).ljust(3)
                price_ = str(round(row.price,2)).ljust(5)
                total_str = str(round(total_,2)).ljust(6)
                data.append([name_, qty_, price_, total_str])
        data.append(['TOTAL','','',grand_total])
        data.append(['','','',''])
        data.append(['','','',''])
        self.print_billing2B(data,"thermal")


    def is_non_zero_number(self,s):
        try:
            # Try to convert the string to a float
            num = float(s)
            # Check if the number is not zero
            return num != 0
        except ValueError:
            # If a ValueError is raised, the string is not a number
            return False

    def save_delivery_db(self,for_saving):
        save_flag = True
        self.update_web_info()
        #print (for_saving)
        if len(for_saving):
            updates_ = ''
            for items in for_saving:
                if int(items[3]) > 0:
                        msg_ = '%s:%s - %s %s\n'%(items[0],items[1],items[2],items[3])
                        updates_+=(msg_)
                        new_qty = int(items[2]) + int(items[3])
                        db(db.Merchandise_rates_db.id==int(items[0])).update(Quantity_=new_qty)

                        qty__ = 0
                        myqueryA = (db.Track_delivery.Merchandise_ID ==  items[0]) & (db.Track_delivery.Delivery_date == datetime.now().date())
                        data_rowA = db(myqueryA).select()
                        if data_rowA:
                            for row_ in data_rowA:
                                qty__+=row_.Quantity
                        #print (items, '#############')
                        db.Track_delivery.insert(Merchandise_ID=items[0],Merchandise_Name=items[1],
                            Delivery_date = datetime.now().date(),Quantity = int(items[3]), price = float(items[4]))
                        qty__+=int(items[3])


                        myquery = (db.Inventory_tracking.Merchandise_ID ==  int(items[0])) & (db.Inventory_tracking.Ref_Date == datetime.now().date())
                        data_row = db(myquery).select()
                        current_inventory = qty__
                        db(db.Inventory_tracking.id==data_row[0].id).update(DI_= current_inventory)
                        
                else:
                    save_flag = False
                    self.ui.delivery_msg.setText('Error on saving data. Check the details please.\n Quantity and Price should be greater than zero.')
            if save_flag:
                db.commit()

                data = [['BRANCH:',self.config_info['BRANCH'],'',''],['Date:',datetime.now().strftime("%b-%d-%Y %H:%M"),'',''],['/ transaction','','','']]
                grand_total = 0
                total_qty = 0
                if for_saving:
                    for idx, row in enumerate(for_saving):
                        if idx == 0:
                            data.append(['-------------','-----','-------','-------'])
                            data.append(['Item Name', 'Qty', 'Price', 'Total' ])
                            data.append(['-------------','-----','-------','-------'])
                            # msg_ = 'DATE: %s\n\n' % row.Delivery_date
                            # pending_print += msg_
                        try:
                            total_ = float(row[3]) * float(row[4])
                            total_qty += float(row[3])
                            grand_total += total_
                        except:
                            total_ = 0
                        # Adjust column widths to ensure the total length is 25 characters
                        name_ = (row[1][:10] if len(row[1]) > 10 else row[1].ljust(10))
                        qty_ = str(row[3]).ljust(3)
                        price_ = str(round(float(row[4]),2)).ljust(5)
                        total_str = str(round(total_,2)).ljust(6)
                        data.append([name_, qty_, price_, total_str])
                data.append(['-------------','-----','-------','-------'])
                data.append(['TOTAL_AMOUNT','','',round(grand_total,2)]) #grand_total])
                data.append(['TOTAL_QTY','','',round(total_qty,2)]) #grand_total])
                data.append(['-------------','-----','-------','-------'])
                data.append(['','','',''])
                data.append(['','','',''])
                self.print_billing2B(data,"thermal")


                self.ui.delivery_msg.setText('Selected Item/s successfully save to DB.')
                #QMessageBox.information(self, "Message", "Successfully Save to DB.")
                logging.info(updates_)
            else:
                db.rollback()
            #logging.info(updates_)

    def about_2(self):
        try:
            self.about_dialog = aboutDialog(self.config_info['VERSION'])
            self.about_dialog.setWindowTitle( 'About' )
            self.about_dialog.show()
        except:
            pass
    def about_(self):
        try:
            pdf_file_path = ('Resource/UserManual.pdf')
            subprocess.Popen(['start', pdf_file_path], shell=True)
        except:
            QMessageBox.critical(self, "Message", "User Manual not found.")


    def view_room_details(self):
        myquery = (db.Room_rates_db.id != None)
        items = ["Room Name - Hour span > [Amount, +Hour, +Head]\n"]
        max__ = int(self.config_info['ROOM_MAX'])

        # Fetch and store data in a list
        data_list = []
        for row in db(myquery).select():
            data_01 = row.Rate_ID.split('_')
            rec_ = int(data_01[1])
            if rec_ <= max__:
                data_list.append(row)

        # Sort the data by Hour span and then Room number
        sorted_data = sorted(data_list, key=lambda x: (int(x.Rate_ID.split('_')[2]), int(x.Rate_ID.split('_')[1])))

        # Build the items list with the sorted data
        for row in sorted_data:
            data_01 = row.Rate_ID.split('_')
            room_number = int(data_01[1])
            room_name = self.room_mapping.get(f"ROOM_{str(room_number).zfill(2)}", f"ROOM_{room_number}")[0]
            info_ = "%s - %s Hours > [%s, %s, %s]\n" % (room_name, data_01[2], row.Price_, row.Price_add, row.Head_price)
            items.append(info_)


        
        with open('room_rates.txt', 'w') as file_handler:
            for item in items:
                file_handler.write("{}".format(item))
        txt_file_path = 'room_rates.txt'
        os.startfile('room_rates.txt')
        #f = open('room_rates.txt', 'w')
        #simplejson.dump(items, f)
        #f.close()

    def clear_database(self):
        question01 = "Are you sure you want to clear the merchandise database?"
        reply = QMessageBox.question(self, 'Message', question01, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:


                current_date2 = datetime.now().date()
                myquery = (db.Merchandise_rates_db.id != None)
                for row in db(myquery).select():
                    db(db.Merchandise_rates_db.id==row.id).update(Quantity_=0)


                current_date2 = datetime.now().max
                current_date = datetime.now().date()
                query = (db.Inventory_tracking.Ref_Date >= current_date ) & (db.Inventory_tracking.Ref_Date <= current_date2)
                rows = db(query).select()
                if rows:
                    for row in rows:
                        db(db.Inventory_tracking.id == row.id).update(SI_ = 0, DI_ = 0, PI_=0)
                db.commit()
                self.update_mer_info()
                self.update_rfid_info()
                #logging.info('Merchandise DB cleared')
            except Exception as e:
                print (e,'#####')
        else:
            pass#event.ignore()

    def disable_max_room(self):
        room_max = int(self.config_info['ROOM_MAX'])+1
        
        for x in range(room_max, global_RM_count+1):
            eval('self.ui.groupBox_room%s.setDisabled(True)'%x)
        for x in self.skip_rooms:
            eval('self.ui.groupBox_room%s.setDisabled(True)'%x)

    def to_excel(self):
        try:
            filename = 'inventory.csv'
            os.startfile(filename)
        except Exception as e:
            print ('error opening file', e)


    def enable_admin_buttons(self):
        if self.username == 'admin':
            self.ui.tabWidget.setTabEnabled(4,True)
            self.ui.pushButton_settings.setEnabled(True)
            self.ui.label_20.setEnabled(True)
        else:
            self.ui.tabWidget.setTabEnabled(4,False)
            self.ui.pushButton_settings.setEnabled(False)
            self.ui.label_20.setEnabled(False)


    def create_user_pass(self):
        global db
        user_name = self.ui.user_1.text()
        pass_1 = self.ui.pass_1.text()
        pass_2 = self.ui.pass_2.text()
        if pass_1 == pass_2:
            try:
                db.WJV_users.insert(User_=user_name,Password_=pass_1)
                db.commit()
                QMessageBox.information(self, "Message", "Successfully Created a USER/PASSWORD")
                self.ui.pass_1.clear()
                self.ui.pass_2.clear()
                self.ui.user_1.clear()
            except:
                print ('error creating user')

        else:
            QMessageBox.critical(self, "Message", "Password does not match")

    def try_send_url(self,msg_url):
        queue.put(msg_url)


    def update_delivery_info(self):
        try:
            #self.update_web_info()
            query2_ = (db.Merchandise_rates_db.Type_ != 'WRISTBAND')
            rows = db(query2_).select()
            merchandise_list_ = []
            for row in rows:
                merchandise_list_.append([row.id,row.Type_,row.Merchandise_Name,row.Quantity_,0,0])
            self.delivery_dialog = Delivery(merchandise_list_)
            self.delivery_dialog.setWindowTitle( 'Delivery Window' )
            self.delivery_dialog.show()
            self.delivery_dialog.signal2.sig_delivery.connect(self.save_delivery_db)
        except:
            pass

    def print_all_pending(self):
        #logging.info('Printing all temporary receipt')
        QMessageBox.information(self, "Message", "Printing all temporary receipt")
        query = (db.WJV_db.Status_ == 'Open')
        rows = db(query).select()
        cur_time = datetime.now()
        pending_print = 'DATE: %s\n-----------------------------\n'%cur_time.strftime('%b-%d-%Y %H:%M %p')
        ctr__ = 0
        if rows:
            for row in rows:
                ctr__+=1
                #self.ui.payment_amount
                
                rows_record = row
                if not 'TENANT' in rows_record.Room_Type:
                    msg_2 = ''
                    serial_id = rows_record.id
                    serial_search = '%s*'%rows_record.Ticket_ID
                    room_hr_details = int(rows_record.Room_Type.split(" ")[1])
                    room_type_details = str(rows_record.Room_Type.split(" ")[0])
                    room_type_cost = float(rows_record.Room_Type.split(" ")[-1])
                    payment_amount = 'Php %.2f'%room_type_cost



                    query2A = (db.WJV_db.Ticket_ID == serial_search)
                    rows2A = db(query2A).select()
                    paid_amount = 0
                    if rows2A:
                        paid_amount = rows2A[0].Total_Price

                    cust_details = rows_record.Price_
                    if cust_details:
                        temp_data__ = rows_record.Price_.split(',')
                        data__ = "\nPlatform: %s\nName: %s\nRef#: %s\nNo of Guest: %s\n"%(temp_data__[2],temp_data__[3],temp_data__[1],temp_data__[-1])
                    else:
                        data__ = ''
                    expected_out = rows_record.Check_In + timedelta(hours=room_hr_details)
                    room_rate_ = float(rows_record.Room_Type.split(" ")[-1])
                    running_time = (cur_time - rows_record.Check_In).total_seconds()
                    hours, remainder = divmod(running_time,60*60)
                    minutes, seconds = divmod(remainder,60)
                    self.time_diff = round(((cur_time - expected_out).total_seconds()/3600.00),2)
                    frac, whole = math.modf(self.time_diff)
                    if room_type_details == 'TENANT':
                        if whole >= 72.0:
                            extra_charge = .05
                        else:
                            extra_charge = 0
                    else:
                        extra_charge = max(0, whole) + (1 if max(0,frac) > 0.167 else 0) #0.167 -> 10 minutes
                    mer_list = ''
                    mer_list2 = ''
                    test = ''
                    mer_cost = 0
                    if rows_record.Room_Merchandise:
                        free_ctr = 0
                        counter_ = 2
                        for item_name, qty_ in rows_record.Room_Merchandise.items():
                            free_ = ''
                            if 'Php 0' in item_name:
                                free_ = ' FREE'
                                free_ctr +=int(qty_)
                            mer_list = mer_list + '\n  >%s %s pc/s - [ %s ]'%(free_, qty_,item_name)
                            mer_list2 = mer_list2 + '\n  >%s pc/s\n   [%s]'%(qty_,item_name.split(':')[1].strip())
                            item_cost =  int(qty_) * int(item_name.split(" ")[-1])
                            mer_cost += item_cost
                            try:
                                temp001 = rows_record.Price_.split(',')[0]
                                temp002 = rows_record.Price_.split(',')[-1]
                                if temp001 != '':
                                    counter_ = int(temp001) * int(temp002)
                            except:
                                pass


                    else:
                        mer_list2 = mer_list = ''
                    room_name_ = str(rows_record.Room_Type.split("Php")[0]).strip()
                    room_hour_ = str(rows_record.Room_Type.split(" ")[1]).strip()
                    rm_num_ = rows_record.Room_Number.split('_')[1]
                    room_name = rows_record.Room_Number
                    specific_room = "RR_0%s_%s"%(str(rm_num_).zfill(2),room_hour_)


                    if 'Custom' in room_name_:
                        add_head_ =  int(self.config_info['BOOKING+HD'])
                        extra_hour = int(self.config_info['BOOKING+HR'])
                    elif 'TENANT' in room_name_:
                        specific_room = "MR_0%s_%s"%(str(rm_num_).zfill(2),room_hour_)
                        query = (db.Room_rates_db.Rate_Name == room_name_ and db.Room_rates_db.Rate_ID.contains(specific_room))
                        rows = db(query).select()
                        if rows:
                            extra_hour = int(rows[0].Price_)
                            add_head_ = 0

                        else:
                            add_head_ =  0
                            extra_hour = 0
                    else:
                        query = (db.Room_rates_db.Rate_Name == room_name_ and db.Room_rates_db.Rate_ID.contains(specific_room))
                        rows = db(query).select()
                        if room_name == 'ROOM_97':
                            add_head_ = 0
                            extra_hour = 0
                        else:
                            add_head_ = rows[0].Head_price
                            extra_hour = int(rows[0].Price_add)
                    ext_head = rows_record.extra_heads*add_head_
                    total_price = room_rate_ + extra_charge*extra_hour + mer_cost + ext_head
                    checkIN_time = rows_record.Check_In
                    checkOUT_time = expected_out
                    computed_ext_charge = extra_charge*extra_hour
                    computed_ext_heads = rows_record.extra_heads
                    if room_name == 'ROOM_97':
                        room_name = 'WALKIN CUSTOMER'
                        checkIN_time = 'NA'
                        checkOUT_time = 'NA'
                        hours = 0
                        minutes = 0
                        room_rate_ = '(Walk-in)'
                        computed_ext_charge = '-'
                        extra_charge = 0
                        ext_head = '-'
                        computed_ext_heads = '-'
                        total_price = mer_cost
                    balance_ = total_price - float(paid_amount)
                    msg_2 = '''#%s
%s
%s
CheckIn : %s
CheckOut: %s
Excess Hour: Php %s
Addl Head  : Php %s
Merchandise: Php %s%s
Total BILL : Php %s
Downpayment: Php %.2f
Balance Amt: Php %.2f
'''%(str(serial_id).zfill(10),room_name,rows_record.Room_Type,checkIN_time.strftime("%b%d %H:%M"),checkOUT_time.strftime("%b%d %H:%M"),
                    computed_ext_charge, ext_head ,
                    mer_cost,mer_list2,"%0.2f"%total_price,float(paid_amount),balance_)
                    pending_print+= msg_2 + '\n-----------------------------\n'
            open ('Resource/billing_all.txt', "w").write (pending_print)
            try:
                self.win_print('Resource/billing_all.txt',"thermal")
            except Exception as e:
                QMessageBox.critical(self, "Message", str(e))


    def print_message(self, msg__):
        font = {
            "height": 11,
        }
        font2 = {
            "height": 16,
        }

        font3 = {
            'height': 12,
            'italic':1,
        }



        max_ = len(msg__)
        with Printer(linegap=1) as printer:
            for idx, x in enumerate(msg__):
                if '#' in x:
                    printer.text(x.strip(), font_config=font2)
                #elif idx == 1:
                #    printer.text(x.strip(), font_config=font3)
                else:
                    printer.text(x.strip(), font_config=font)

    def win_print(self,filename, printer_name = None):
        try:
            if printer_name == 'thermal':
                win32print.SetDefaultPrinter(self.config_info['THERMAL'])
                printer_name = win32print.GetDefaultPrinter()
                out = '/d:"%s"' % (printer_name)
                with open(filename) as f:
                    contents = f.readlines()
                self.print_message(contents)
        except Exception as e:
            QMessageBox.warning(self, 'Error', 'Unable to print')
            print (e)
    def view_inventory__(self):
        query2_ = (db.Merchandise_rates_db.id > 0)
        #self.update_web_info()
        rows = db(query2_).select()
        merchandise_list_ = {}
        for row in rows:
            merchandise_list_.update({row.id: row.Merchandise_Name})

        current_date2 = datetime.now().max
        current_date = datetime.now().date()
        offset_days = current_date - timedelta(days=11)

        query = (db.Inventory_tracking.Ref_Date >= offset_days) & (db.Inventory_tracking.Ref_Date <= current_date2)
        rows = db(query).select(orderby=db.Inventory_tracking.Merchandise_ID)
        all_list = []

        if rows:
            for row in rows:
                formatted_date = row.Ref_Date.strftime('%b %d')
                if current_date == row.Ref_Date:
                    myquery = (db.Merchandise_rates_db.id == int(row.Merchandise_ID))
                    query2_ = db(myquery).select()
                    all_list.append([merchandise_list_[row.Merchandise_ID], 'Actual', formatted_date, query2_[0].Quantity_])
                else:
                    all_list.append([merchandise_list_[row.Merchandise_ID], 'Actual', formatted_date, row.SI_])
                all_list.append([merchandise_list_[row.Merchandise_ID], 'Sold', formatted_date, row.PI_])
                all_list.append([merchandise_list_[row.Merchandise_ID], 'Delivery', formatted_date, row.DI_])

        test = pd.DataFrame(all_list, columns=['Merchandise', 'Category', 'Date', 'Value'])

        # Create a pivot table with a MultiIndex for columns
        newdata = pd.pivot_table(
            test,
            index='Merchandise',
            columns=['Date', 'Category'],
            values='Value',
            aggfunc='sum',
            fill_value=0
        )

        # Reset index to convert it back to a DataFrame
        newdata_reset = newdata.reset_index()
        newdata_reset.columns = [' - '.join(map(str, col)) if isinstance(col, tuple) else col for col in newdata_reset.columns]

        #get all item name in Merchandise_rates_db when the merchandise is not equal to "MERCHANDISE"
        query2_ = (db.Merchandise_rates_db.Type_ == "MERCHANDISE")
        rows = db(query2_).select()
        merchandise_list_2 = []
        for row in rows:
            merchandise_list_2.append(row.Merchandise_Name)

        #iterate rows of newdata_reset and remain the row if it is in the merchandise_list_2
        newdata_reset = newdata_reset[newdata_reset['Merchandise - '].isin(merchandise_list_2)]
        # Sort the DataFrame by the first column
        # Load data into QTableWidget
        self.load_data(newdata_reset)

    def load_data(self, dataframe):
        # Sort columns by date (ignoring the first column "Merchandise -")
        sorted_columns = [dataframe.columns[0]] + sorted(dataframe.columns[1:], key=lambda x: pd.to_datetime(x.split(" - ")[0], format='%b %d', errors='coerce'))
        dataframe = dataframe[sorted_columns]

        # Set row and column counts based on DataFrame
        self.ui.tableWidget.setRowCount(dataframe.shape[0])
        self.ui.tableWidget.setColumnCount(dataframe.shape[1])

        # Set column headers
        self.ui.tableWidget.setHorizontalHeaderLabels([str(col) for col in dataframe.columns])

        # Populate QTableWidget with data
        for row in range(dataframe.shape[0]):
            for col in range(dataframe.shape[1]):
                item = QTableWidgetItem(str(dataframe.iloc[row, col]))
                
                # Check if the column header contains "Actual"
                if "Actual" in dataframe.columns[col]:
                    font = item.font()
                    font.setBold(True)  # Set the font to bold
                    item.setFont(font)
                    item.setForeground(QColor(0, 0, 255))
                self.ui.tableWidget.setItem(row, col, item)

        # Get unique dates from the column headers (excluding the first column)
        unique_dates = {col[1] for col in dataframe.columns[1:]}
        # Apply alternating colors to entire columns based on the date
        for idx, date in enumerate(sorted(unique_dates)):
            color = QColor(240, 240, 240) if idx % 2 == 0 else QColor(255, 255, 255)  # Light gray for even, white for odd

            for col in range(1, dataframe.shape[1]):  # Start from 1 to skip 'Merchandise'
                header_item = self.ui.tableWidget.horizontalHeaderItem(col)
                if header_item and header_item.text() == date:
                    for row in range(dataframe.shape[0]):
                        item = self.ui.tableWidget.item(row, col)
                        if item:
                            item.setBackground(color)

        # Optional: Apply alternating row background color manually (optional if using setAlternatingRowColors)
        for row in range(dataframe.shape[0]):
            if row % 2 == 0:
                for col in range(dataframe.shape[1]):
                    item = self.ui.tableWidget.item(row, col)
                    if item:
                        item.setBackground(QColor(240, 240, 240))  # Light gray for alternate rows



    def auto_Inv_tracking(self):
        current_date = datetime.now().date()
        yesterday = current_date - timedelta(days = 1)
        query = (db.InvTrckng_by_date.Date01 == current_date)
        rows = db(query).select()
        if not rows:
            query2_ = (db.Merchandise_rates_db.id > 0)
            rows = db(query2_).select()
            try:
                for row in rows:
                    db.Inventory_tracking.insert(Merchandise_ID=row.id,Ref_Date=current_date,SI_=row.Quantity_,DI_=0,PI_=0)
                db.InvTrckng_by_date.insert(Date01=current_date)
                db.commit()
                #logging.info('Auto tracking executed')
            except Exception as e:
                db.rollback()
                print (e)



    def update_mer_info(self):
        try:
            myquery = (db.Merchandise_rates_db.id == int(str(self.ui.comboBox_merchandise.currentText()).split(" : ")[0][2:]))
            query2_ = db(myquery).select()
            self.ui.stock__.setText(str(query2_[0].Quantity_))
            self.ui.price__.setText(str(query2_[0].Price_))
        except:
            pass

    def update_rfid_info(self):
        print ('updating rfid')
        try:
            query_str = str(self.ui.comboBox_roomNumber.currentText())
            # Compare against the first element of the mapping
            selected_room = next((int(key.split('_')[1]) for key, value in self.room_mapping.items() if value[0] == query_str), None)
            query_str = "ROOM_%s"%str(selected_room)
            myquery = (db.RFID.Room_Num == query_str)
            query2_ = db(myquery).select()
            print (str(query2_[0].ID_))
            self.ui.rfid_.setText(str(query2_[0].ID_))
        except Exception as e:
            print (e)

            



    def update_mer_db(self):
        #check if comboBox_type is equal to 'WRISTBAND'

        if self.ui.comboBox_type.currentText() == 'WRISTBAND':
            current_date = datetime.now().date()
            data_field = [self.ui.mer_name_ent.text(),self.ui.mer_price_ent.text(), self.ui.mer_qty_ent.text(), 0]
            checking_ = self.check_entries(data_field)
            if checking_:
                name_text = data_field[0]

                # Split into prefix (non-digits) and numeric part (digits)
                match = re.match(r"([^0-9]+)(\d+)", name_text)
                
                if match:
                    prefix, num_str = match.groups()
                    num = int(num_str)
                    count = int(data_field[2])

                    for i in range(count):
                        new_number = num + i
                        new_name = f"{prefix}{new_number}"
                        ticket_id = f"MC{datetime.now():%Y%m%d_%H%M%S}_{i}"
                        try:
                            db.Merchandise_rates_db.insert(
                                Merchandise_ID=ticket_id,
                                Merchandise_Name=new_name,
                                Price_=self.ui.mer_price_ent.text(),
                                Quantity_=1,
                                Min_=0,
                                Type_=self.ui.comboBox_type.currentText()
                            )
                        except Exception as e:
                            print(e)

                    db.commit()
                    QMessageBox.information(self, "Message", f"Successfully added items for: \n{name_text}")
                else:
                    QMessageBox.warning(self, "Warning", "Invalid name format. Expected a prefix (any non-number characters) followed by numbers (like BC-10).")
        else:
            current_date = datetime.now().date()
            data_field = [self.ui.mer_name_ent.text(),self.ui.mer_price_ent.text(), self.ui.mer_qty_ent.text(), 0]
            checking_ = self.check_entries(data_field)
            ticket_id = 'MC' + datetime.now().strftime("%Y%m%d_%H%M%S")
            if checking_:
                try:
                    db.Merchandise_rates_db.insert(Merchandise_ID=ticket_id,Merchandise_Name=self.ui.mer_name_ent.text(),Price_=self.ui.mer_price_ent.text(),
                                Quantity_=self.ui.mer_qty_ent.text(),Min_=0, Type_ = self.ui.comboBox_type.currentText())

                    db.commit()
                    myquery = (db.Merchandise_rates_db.Merchandise_ID == ticket_id)
                    query2_ = db(myquery).select()
                    db.Inventory_tracking.insert(Merchandise_ID=query2_[0].id,Ref_Date=current_date,SI_=query2_[0].Quantity_,DI_=0,PI_=0)
                    db.commit()
                    QMessageBox.information(self, "Message", "Successfulyy added in item: \n%s"%self.ui.mer_name_ent.text())
                except Exception as e:
                    print (e)


            self.selection_settings()
        self.ui.mer_name_ent.clear()
        self.ui.mer_price_ent.clear()


    def update_roomrates_info(self):
        
        if self.flag_roomrates_info:# and self.settings_flag:
            try:
                query_str = str(self.ui.room_list.currentText())
                selected_room = next((int(key.split('_')[1]) for key, value in self.room_mapping.items() if value[0] == query_str), None)
                print (selected_room, 'selected room############')

                # Format the room number to include leading zeros (3 digits)
                room_number_str = str(selected_room).zfill(3)

                # Build the pattern to match (e.g., 'RR_001_')
                pattern = f"{room_number_str}_"
                if 'COTTAGE' in query_str:
                    records = db(db.Room_rates_db.Rate_ID.like(f"C%_{pattern}%")).select()
                else:
                    # Records not starting with "C"
                    records = db(~db.Room_rates_db.Rate_ID.like(f"C%") & db.Room_rates_db.Rate_ID.like(f"%_{pattern}%")).select()

                self.ui.tableWidget_roomrates.setRowCount(0)
                self.ui.tableWidget_roomrates.setColumnCount(5)
                self.ui.tableWidget_roomrates.setHorizontalHeaderLabels(["Rate ID", "Rate Name", "Price", "Price Add", "Head Price"])

                # Populate QTableWidget with records
                for row_index, record in enumerate(records):
                    self.ui.tableWidget_roomrates.insertRow(row_index)
                    # Set column 0 and 1 as read-only
                    item_rate_id = QTableWidgetItem(record.Rate_ID)
                    item_rate_id.setFlags(item_rate_id.flags() & ~Qt.ItemIsEditable)
                    self.ui.tableWidget_roomrates.setItem(row_index, 0, item_rate_id)

                    item_rate_name = QTableWidgetItem(record.Rate_Name)
                    item_rate_name.setFlags(item_rate_name.flags() & ~Qt.ItemIsEditable)
                    self.ui.tableWidget_roomrates.setItem(row_index, 1, item_rate_name)

                    # Set other columns as editable
                    self.ui.tableWidget_roomrates.setItem(row_index, 2, QTableWidgetItem(str(record.Price_)))
                    self.ui.tableWidget_roomrates.setItem(row_index, 3, QTableWidgetItem(str(record.Price_add)))
                    self.ui.tableWidget_roomrates.setItem(row_index, 4, QTableWidgetItem(str(record.Head_price)))

                # Apply alternating row colors
                self.ui.tableWidget_roomrates.setAlternatingRowColors(True)
                self.ui.tableWidget_roomrates.setStyleSheet("alternate-background-color: rgb(240, 240, 240); background-color: white;")

                # Adjust column widths
                self.ui.tableWidget_roomrates.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Set column 1 to auto stretch
                self.ui.tableWidget_roomrates.setColumnWidth(2, 80)  # Set smaller width for column 2
                self.ui.tableWidget_roomrates.setColumnWidth(3, 80)  # Set smaller width for column 3
                self.ui.tableWidget_roomrates.setColumnWidth(4, 80)  # Set smaller width for column 4

                # room_numbers = [
                #     int(key.split("_")[1])  # Extract the number from "ROOM_xx"
                #     for key, value in self.room_mapping.items()
                #     if "COTTAGE" in value[0]  # Check if "COTTAGE" is in the room name
                # ]
                # specific_room = "R_0%s_%s"%((str(selected_room).zfill(2)),str(self.ui.comboBox_roomrate_update.currentText()).split(' ')[0])
                # print (specific_room, 'specific room############')
                # myquery = db.Room_rates_db.Rate_ID.contains(specific_room)

                # #myquery = (db.Room_rates_db.Rate_ID == str(self.ui.comboBox_roomrate_update.currentText()))
                # query3_ = db(myquery).select()
                # print (query3_[0].Rate_Name, 'room rates')
                # self.ui.price_rr1.setText(str(query3_[0].Price_))
                # self.ui.rr_hour.setText(str(query3_[0].Price_add))
                # self.ui.rr_head.setText(str(query3_[0].Head_price))
                #commit change
                db.commit()
            except Exception as e:
                print (e, 'xxxxxxxxxxx')

    def check_entries(self, data_field):
        try:
            if str(data_field[2]).isdigit() and str(data_field[3]).isdigit():
                if str(data_field[1]).isdigit():
                    if len(data_field[0]) > 3:
                        return True
                    else:
                        QMessageBox.critical(self, "Message", "Name is too short")
                        return False
                else:
                    QMessageBox.critical(self, "Message", "PRICE should be a number")
                    return False
            else:
                QMessageBox.critical(self, "Message", "QTY and MIN should be a number")
                return False
        except Exception as e:
            print (e)
            return False


    def update_db_merchandise(self):
        try:
            _price = int(self.ui.price__.text())
            _stock = int(self.ui.stock__.text())
            _qty = int(self.ui.add_stocks.value())
            id_2 = int(str(self.ui.comboBox_merchandise.currentText()).split(" : ")[0][2:])
            mer_name_ = str(self.ui.comboBox_merchandise.currentText()).split(" : ")[1]

            db(db.Merchandise_rates_db.Merchandise_Name==mer_name_).update(Price_=_price, Quantity_=_stock+_qty)
            if _qty > 0:
                myquery = (db.Inventory_tracking.Merchandise_ID ==  id_2) & (db.Inventory_tracking.Ref_Date == datetime.now().date())
                data_row = db(myquery).select()
                current_inventory = data_row[0].DI_ + _qty
                db(db.Inventory_tracking.id==data_row[0].id).update(DI_= current_inventory)
            db.commit()
            data_file = [mer_name_,_stock,_price, _qty]
            #logging.info(data_file)
            QMessageBox.information(self, "Message", "Successfully updated the %s details"%mer_name_)
        except Exception as e:
            print (e)


        self.selection_settings()
        #self.generate_mer_report()

    def update_db_rfid(self):
        print ('updating rfid')
        try:
            _rfid = self.ui.rfid_.text()

            query_str = str(self.ui.comboBox_roomNumber.currentText())
            selected_room = next((int(key.split('_')[1]) for key, value in self.room_mapping.items() if value[0] == query_str), None)
            query_str = "ROOM_%s"%str(selected_room)

            db(db.RFID.Room_Num==query_str).update(ID_=_rfid)
            db.commit()
            QMessageBox.information(self, "Message", "Successfully updated the %s details"%query_str)
        except Exception as e:
            print (e)


        self.selection_settings()

    def update_db_roomrates(self):
        try:
            row_count = self.ui.tableWidget_roomrates.rowCount()
            for row in range(row_count):
                rate_id_item = self.ui.tableWidget_roomrates.item(row, 0)
                price_item = self.ui.tableWidget_roomrates.item(row, 2)
                price_add_item = self.ui.tableWidget_roomrates.item(row, 3)
                head_price_item = self.ui.tableWidget_roomrates.item(row, 4)

                if not rate_id_item:
                    continue  # Skip if no Rate_ID

                rate_id = rate_id_item.text()
                price = int(price_item.text()) if price_item and price_item.text().isdigit() else 0
                price_add = int(price_add_item.text()) if price_add_item and price_add_item.text().isdigit() else 0
                head_price = int(head_price_item.text()) if head_price_item and head_price_item.text().isdigit() else 0

                # Update database
                db(db.Room_rates_db.Rate_ID == rate_id).update(
                    Price_ = price,
                    Price_add = price_add,
                    Head_price = head_price
                )

            db.commit()
            QMessageBox.information(self, "Message", "Successfully updated the room rates")
        except:
            QMessageBox.critical(self, "Message", "Error updating room rates")
       
    def add_free_item(self):
        temp_ = (self.ui.mInput.currentItem().text())
        id_, name_ = temp_.split(' : ')
        new_name = name_+'*'
        id_ = int(id_.replace('ID',''))
        db(db.Merchandise_rates_db.id == id_).update(Merchandise_Name=new_name)
        db.commit()
        self.ui.mOuput.addItem(self.ui.mInput.takeItem(self.ui.mInput.currentRow()))
        self.selection_settings()
    def remove_free_item(self):
        temp_ = (self.ui.mOuput.currentItem().text())
        id_, name_ = temp_.split(' : ')
        new_name = name_.replace('*','')
        id_ = int(id_.replace('ID',''))
        db(db.Merchandise_rates_db.id == id_).update(Merchandise_Name=new_name)
        db.commit()
        self.ui.mInput.addItem(self.ui.mOuput.takeItem(self.ui.mOuput.currentRow()))
        self.selection_settings()

    # def update_qty_wristband(self):
    #     selection_type_ = self.ui.comboBox_type.currentText()
    #     if selection_type_ == 'WRISTBAND':
    #         self.ui.mer_qty_ent.setEnabled(False)
    #         self.ui.mer_qty_ent.setText('1')
    #     else:
    #         self.ui.mer_qty_ent.setEnabled(True)
    #         self.ui.mer_qty_ent.clear()

    def selection_settings(self):
        try:
            self.ui.mInput.clear()
            self.ui.mOuput.clear()
            self.ui.comboBox_merchandise.clear()
            self.ui.comboBox_roomNumber.clear()
            self.flag_roomrates_info = True
            selection_type = self.ui.comboBox_typeB.currentText()
            myquery = (db.Merchandise_rates_db.id != None) & (db.Merchandise_rates_db.Type_ == selection_type)
            items = []
            items2 = []
            items2_free = []
            for row in db(myquery).select():
                new_name = "ID%s : %s"%(row.id,row.Merchandise_Name)
                items.append(new_name)
                if '*' in row.Merchandise_Name:
                    items2_free.append(new_name)
                else:
                    items2.append(new_name)
            for text in items:
                self.ui.comboBox_merchandise.addItem(text)
            #add room number and rfid

            self.ui.comboBox_roomNumber.clear()
            for room_key, room_data in self.room_mapping.items():
                self.ui.comboBox_roomNumber.addItem(f"{room_data[0]}")

            #entries = ['one','two', 'three']
            self.ui.mInput.addItems(items2)
            self.ui.mOuput.addItems(items2_free)
            self.update_roomrates_info()
        except:
            pass


    def selection_settings1(self):
        #logging.info('Tab Selection - Home')
        self.settings_flag = False
        self.ui.tabWidget.setCurrentIndex(0)

    def selection_settings2(self):
        self.ui.tabWidget.setCurrentIndex(1)
        self.settings_flag = False
        #logging.info('Tab Selection - Reports')

    def selection_settings3(self):
        self.ui.tabWidget.setCurrentIndex(2)
        self.settings_flag = False
        #logging.info('Tab Selection - Inventory')

    def selection_settings4(self):
        self.ui.tabWidget.setCurrentIndex(4)
        self.settings_flag = True
        #logging.info('Tab Selection - Settings')
        self.selection_settings()

    def handlePrint(self):
        #logging.info("Printing Report")
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1)
            printer_list = []
            for printer_ in printers:
                printer_list.append(printer_[1].split(',')[0])
            #print printer_list, 'printer list'
            big_printer = self.config_info['PRINTER']
            if big_printer in printer_list:
                win32print.SetDefaultPrinter(big_printer)
                dialog = QPrintDialog()
                if dialog.exec_() == QDialog.Accepted:
                    self.handlePaintRequest(dialog.printer())
            else:
                QMessageBox.critical(self, "Information", "%s Printer not found.\n Can't preview document."%big_printer)
        except Exception as e:
            print (e, 'error')


    def handlePreview(self):
        try:
            win32print.SetDefaultPrinter('Microsoft Print to PDF')
            dialog = QPrintPreviewDialog()
            dialog.paintRequested.connect(self.handlePaintRequest)
            dialog.exec_()
        except:
            QMessageBox.critical(self, "Information", 'Printer not found for document preview.')

    def handlePaintRequest(self, printer):
        printer.setOrientation(QPrinter.Landscape)
        printer.setPaperSize(QPrinter.Legal)
        printer.setFullPage(True)
        printer.setPageMargins(5, 8, 5, 8, QPrinter.Millimeter)
        document = QTextDocument()
        cursor = QTextCursor(document)
        model = self.ui.tableView.model()

        table = cursor.insertTable(
            model.rowCount() + 2, model.columnCount())
        header_ = self.header
        sub_total = ['TOTAL', '', '', '', '', '', '', '', '', 0.0, '']
        col__ = 9
        if self.ui.booking_box.isChecked():
            header_ = self.header2
            sub_total = ['TOTAL', '', '', '', '', '', '', '', '', '', 0.0]
            col__ = 10
        for idx, head_name in enumerate(header_):
            cursor.insertHtml("<b>%s</b>" % head_name)
            cursor.movePosition(QTextCursor.NextCell)
        for row in range(model.rowCount()):
            for column in range(table.columns()):
                if column == col__:
                    sub_price = float(model.item(row, column).text().split(" ")[1])
                    sub_total[col__] += sub_price
                # cursor.insertText(model.item(row, column).text())
                if (row % 2) == 0:
                    cursor.insertHtml('<font color="black">%s</font>' % model.item(row, column).text())
                else:
                    cursor.insertHtml('<font color="MidnightBlue">%s</font>' % model.item(row, column).text())
                cursor.movePosition(QTextCursor.NextCell)
        for idx, sub_tt in enumerate(sub_total):
            if idx == col__:
                cursor.insertHtml('<b>Php %.2f</b>' % sub_tt)
            else:
                cursor.insertHtml('<b>%s</b>' % sub_tt)
            cursor.movePosition(QTextCursor.NextCell)

        # Set the width of the second column to 200, and let the rest autoresize
        tableFormat = table.format()
        columnConstraints = [QTextLength(QTextLength.FixedLength, 52)] * table.columns()

        # Define the custom widths for specific columns
        if not self.ui.booking_box.isChecked():
            custom_widths = {1: 140, 2: 140, 4: 115, 5: 115,8:65 ,9: 70, col__ + 1: 320}
        else:
            custom_widths = {0: 80, 1: 82, 2: 60, 3: 120, 4: 60, 5: 72,6:115 ,7: 115, 10:70, 11:320}
        # Set custom widths for specific columns
        for column, width in custom_widths.items():
            columnConstraints[column] = QTextLength(QTextLength.FixedLength, width)

        tableFormat.setColumnWidthConstraints(columnConstraints)
        table.setFormat(tableFormat)

        document.print_(printer)






    def generate_report(self):
        #logging.info("Generate Daily Report")
        selected_date =  self.ui.calendarWidget.selectedDate().toPyDate()
        current_date_min = datetime.combine(selected_date, time.min)
        current_date_max = datetime.combine(selected_date, time.max)
        booking_flag = False
        if self.ui.booking_box.isChecked():
            #print 'checked'
            selected_date = selected_date.replace(day=1)
            year_ = int(selected_date.strftime('%Y'))
            month_ = int(selected_date.strftime('%m'))
            current_date_min = datetime.combine(selected_date, time.min)
            res = calendar.monthrange(year_, month_)[1]
            selected_date_end = selected_date.replace(day=int(res))
            current_date_max = datetime.combine(selected_date_end, time.max)
            booking_flag = True
            query = (db.WJV_db.Check_In <= current_date_max) & (db.WJV_db.Check_In >= current_date_min) &\
                 (db.WJV_db.Price_ != None)
        else:
            #print 'not checked'
            query = ((db.WJV_db.Check_Out <= current_date_max) & (db.WJV_db.Check_Out >= current_date_min)&\
                 (db.WJV_db.Price_ == None))# |\
                #((db.WJV_db.Check_In <= current_date_max) & (db.WJV_db.Check_In >= current_date_min) & (db.WJV_db.Room_Type.contains('Custom')))
        rows = db(query).select()
        overall_list = []
        running_total = 0.0
        running_booking = 0.0
        row_cnt = 0
        if rows:
            for row in rows:
                row_cnt+=1
                rm_number__ = row.Room_Number.split('_')
                rm_number__2 = 'ROOM_%02d'%(int(rm_number__[1]))
                merc_ = str(row.Room_Merchandise)
                new_merc = merc_[1:-1].split(',')
                try:
                    total_hrs = (row.Check_Out - row.Check_In).total_seconds()/60/60
                except:
                    total_hrs = 0

                items__ = ''
                for itm in new_merc:
                    data_ = itm.split('-')
                    try:
                        itm_name = data_[0].split(':')[1].strip()
                        cost = data_[1].split(':')[1].strip()
                        items__+= '%s: %s pc/s, '%(itm_name,cost)
                    except:
                        pass
                booking_amount_all = row.Room_Type.split(' ')
                booking_amount = float(booking_amount_all[-1])
                booking_detail = (booking_amount_all[0])
                if booking_detail == 'Custom':
                    running_booking+=booking_amount
                running_total += float(row.Total_Price)
                booking_info = row.Price_
                #print booking_info, 'booking info'
                if booking_info:
                    booking_info = booking_info.split(',')
                    booking_num = booking_info[1]
                    booking_name = booking_info[-2]
                    numberof_guest = booking_info[0]
                    numberof_days = booking_info[-1]
                    platform_ = booking_info[2]
                if booking_flag:
                    new_room_name = self.room_mapping[f'ROOM_{str(rm_number__[1]).zfill(2)}'][0]
                    overall_list.append([platform_,booking_num, new_room_name,booking_name,booking_amount,numberof_days,row.Check_In,row.Check_Out,' %.2f hr'%total_hrs,row.extra_heads,'Php %.2f'%float(row.Total_Price),items__.rstrip(', ')])
                else: 
                    new_room_name = self.room_mapping[rm_number__2][0]
                    overall_list.append([new_room_name,row.Ticket_ID,row.Room_Type,row.id,row.Check_In,row.Check_Out,' %.2f hr'%total_hrs,row.extra_heads, row.Cashier_,'Php %.2f'%float(row.Total_Price),items__.rstrip(', ')])
        #overall_list.append(['TOTAL','','','','','','','','',running_total,''])
        self.ui.grand_total.setText('Php %.2f'%running_total)
        #self.ui.booking_total.setText('Php %.2f'%running_booking)
        balance__ = running_total - running_booking
        #self.ui.balance_total.setText('Php %.2f'%balance__)
        table_model = MyTableModel(self, overall_list)
        self.table = QTableView(self)
        if not booking_flag:
            model =  QStandardItemModel(row_cnt, 11, self.table)
            header__ = ['Room num','TicketID', 'Room Type','Serial#', 'CheckIn', 'CheckOut','Hours','+Head', 'Cashier', 'Total Price','Mechandise']
            col_len = 11
        else:
            model =  QStandardItemModel(row_cnt, 12, self.table)
            header__ = ['Platform','Booking #', 'Room#','Guest Name', 'Amount', '# of Days','CheckIn', 'CheckOut','Hours','+Head','Total Price', 'Mechandise']
            col_len = 12
        model.setHorizontalHeaderLabels(header__)
        for row in range(row_cnt):
            for column in range(col_len):
                #print overall_list[row][column]
                item = QStandardItem(('%s') %overall_list[row][column])
                item.setTextAlignment(Qt.AlignCenter)
                model.setItem(row, column, item)
        self.ui.tableView.setModel(model)
        font = QFont("Calibri", 11)
        self.ui.tableView.setFont(font)
        #self.ui.tableView.resizeRowsToContents()
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.horizontalHeader().setStretchLastSection(True)
        self.ui.tableView.horizontalHeader().setStyleSheet("QHeaderView { font-size: 8pt;font:bold }");
        # enable sorting
        self.ui.tableView.setSortingEnabled(True)
        self.ui.tableView.sortByColumn(1,Qt.AscendingOrder)
        self.ui.tableView.setAlternatingRowColors(True)
        self.ui.tableView.setStyleSheet("alternate-background-color: rgb(231, 231, 231) ;background-color: white;");


    def close_allWindow (self):
        try:
            
            #self.tv_viewer.close()

            self.key_thread_.stop()
            self.key_thread_.wait()  # This ensures that the thread fully terminates before continuing
            self.timer_.stop()
            self.timer_.wait()
            if self.ha_enable_flag:
                self.ha_summary.stop_monitoring()
                self.ha_summary.wait()
            self.close()

        except Exception as e:
            print (e)


    def logout_(self):
        self.login = Login()
        self.login.show()
        self.login.signal2.sig2.connect(self.close_allWindow)
        self.login.signal2.username__.connect(self.update_username)
        

    def update_username(self,username_return):
        self.username = username_return
        #logging.info(self.username)
        self.enable_admin_buttons()

    def closeEvent(self, event):
        try:
            self.timer_.stop()
            self.key_thread_.stop()
            if self.ha_enable_flag:
                self.ha_summary.stop_monitoring()
            self.close()

        except Exception as e:
            print (e, 'closeevent')

    def parse_html_request(self):
        try:
            dt = date.today()
            dt2 = datetime.combine(dt, datetime.min.time())
            dt2_str = datetime.now().strftime("%m%d%Y%H%M%S")
            query = ( db.WJV_db.Check_Out >= dt2)
            rows = db(query).select()
            _total_amount = 0
            room_sales_ = []
            max_counter = global_RM_count + 2
            for cnt_ in range(max_counter):
                room_sales_.append(0)
            total_used_room = 0
            total_guess_ = 0
            for row in rows:
                _total_amount += float(row.Total_Price)
                room_index = int(row.Room_Number.split("_")[1])-1
                temp_room = room_sales_[room_index]
                room_sales_[room_index] = row.Total_Price + temp_room
                total_used_room +=1
                total_guess_ = total_guess_ + int(row.extra_heads)
            total_guess_ = total_guess_ + (total_used_room*2)
            room_sales_.insert(0,0)
            room_sales_ = str(room_sales_)

            query = ( db.WJV_db.Status_ == "Open")
            rows = db(query).select()
            occupied_rooms_ = []
            for row in rows:
                occupied_rooms_.append(int(row.Room_Number.split("_")[1]))
            occupied_rooms_ = str(occupied_rooms_).replace(' ','')
            web_page = self.config_info['WEB_PAGE']
            prefix_ = ''
            if self.hardware_status:
                prefix_ = '-'
            branch_stat = self.config_info['BRANCH'] + prefix_
            url_mgs = "https://galesquio.pythonanywhere.com/WJV_INN/default/%s/?total_sale=%s&total_guess=%s&total_room=%s&room_sales=%s&occupied_rooms=%s&date_=%s&wjv_branch=%s"%(web_page,str(_total_amount),str(total_guess_),str(total_used_room),str(room_sales_),str(occupied_rooms_),str(dt2_str),branch_stat)
            self.signal.send_html_queue.emit(url_mgs)
        except Exception as e:
            print (e)

    def update_DB_GUI(self):
        #print ('upate DB GUI called')
        global global_record
        #self.update_web_info()
        self.db_result = {}
        self.db_result_keys = []
        query = (db.WJV_db.Status_ == "Open")
        rows = db(query).select()
        for row in rows:
            self.db_result_keys.append(int(row.Room_Number.split('_')[1]))
            self.db_result.update({row.Room_Number:[row.Check_In,row.Room_Merchandise,row.Room_Type,
                row.RM_Price, row.Ticket_ID, row.Cashier_, row.Extended_, self.config_info['BRANCH'], row.extra_heads]})
        global_record = self.db_result
        #print ('upate DB GUI called')
        #url_message = self.parse_html_request()

    def get_room_number(self,room_name):
        return int(room_name.split(' ')[-1])  # Split by space and take the last part as the numeric value

    def update_GUI(self):
        global test_global
        sorted_room_list = sorted(self.active_rooms_, key=self.get_room_number)
        
        #update my time in this format hh:mm:ss
        self.ui.time_.setText(datetime.now().strftime("%H:%M:%S"))

        cur_time__ = datetime.now()
        active_window = QApplication.activeWindow()
        #print (str(active_window), 'active window')
        if active_window:
            window_title = active_window.windowTitle()
        else:
            window_title = ""
        if window_title != "TRANSACTIONS":
            if self.counter_disp >= 7:
                self.display_message(["   Welcome to WJV   "," "*20,cur_time__.strftime("%b-%d  %H:%M:%S %p ")," "*20])
            else:
                if self.counter_disp == 3:
                    self.display_message(["WJV INN","Cashier Display",f"Version: {self.config_info['VERSION']}","  -JD Software-  "])
                self.counter_disp+=1
        time_diff = (cur_time__ - self.historical_time).total_seconds()
        msg_ = "Changing date and time is a company violation.\n You will receive a penalty for this."
        msg_2 = 'CV: %s - %s'%(self.historical_time, cur_time__)
        #if time_diff >= 10:
            #logging.info(msg_2)
        #elif time_diff <= -10:
            #logging.info(msg_2)
        self.historical_time = datetime.now()
        current_time = datetime.now().strftime("%H:%M:%S")
        #print (current_time,self.active_rooms_)
        if self.historical_time.hour == 0 and self.historical_time.minute == 0 and self.historical_time.second in (1,30):
            self.auto_Inv_tracking()

        occupied_cnt = 0
        for cnt_ in range(global_RM_count+1):
            room_name = 'ROOM_%s'%str(cnt_+1)
            #print (cnt_, room_name)
            room_name2 = room_name.lower()
            room_name2A = room_name.lower().replace("_", " ").capitalize()
            try:
                #print (room_name2A, '-----')
                #if f"Room {cnt_+1}" in self.active_rooms_:
                    #print ('-----')
                eval('self.ui.%s_status.setStyleSheet("background-color: rgb(255, 0, 0);")'%room_name2)
                db_items = self.db_result[room_name]
                currentDT = datetime.now()
                time_delta = currentDT - db_items[0]
                time_delta_secs = time_delta.total_seconds()
                time_ref = int(db_items[2].split(" ")[1].split("-")[0])*60*60
                time_ref_min = time_ref - (60*10)
                time_delta_str = str(time_delta).split(".")[0].zfill(8)
                if room_name != 'ROOM_97': eval("self.ui.%s_time.setText(time_delta_str)"%room_name2)
                eval("self.ui.%s_rate.setText('%s')"%(room_name2,db_items[2])) if room_name != 'ROOM_97' else eval("self.ui.%s_rate.setText('WALK-IN')"%room_name2)
                eval("self.ui.%s_button.setText('Update')"%room_name2)
                if room_name != 'ROOM_97': occupied_cnt+=1
                if db_items[-3]:
                    eval('self.ui.%s_status.setStyleSheet("background-color: rgb(0, 170, 255);")'%room_name2)
                else:
                    if time_delta_secs > time_ref:
                        eval('self.ui.%s_status.setStyleSheet("background-color: rgb(255, 0, 0);")'%room_name2)
                    elif time_delta_secs > time_ref_min:
                        eval('self.ui.%s_status.setStyleSheet("background-color: rgb(255, 170, 255);")'%room_name2)
                    else:
                        if db_items[-4] == 'system':
                            eval('self.ui.%s_status.setStyleSheet("background-color: rgb(178, 255, 102);")'%room_name2)
                        else:
                            eval('self.ui.%s_status.setStyleSheet("background-color: rgb(0, 255, 0);")'%room_name2)
                        if 'TENANT' in db_items[2]:
                            eval('self.ui.%s_status.setStyleSheet("background-color: rgb(251, 248, 145);")'%room_name2)
            except Exception as e:
                eval("self.ui.%s_rate.setText('%s')"%(room_name2,""))
                eval('self.ui.%s_status.setStyleSheet("")'%room_name2)
                eval("self.ui.%s_time.setText('')"%room_name2)
                eval("self.ui.%s_rate.setText('')"%room_name2)
                if room_name != 'ROOM_97':
                    eval("self.ui.%s_button.setText('Check-in')"%room_name2)
                else:
                    eval("self.ui.%s_button.setText('Sell Item')"%room_name2)
        room_max = int(self.config_info['ROOM_MAX'])
        skipped_rooms_count  = len(self.config_info['SKIPPED_ROOMS'])
        self.ui.occupied_.setText(str(occupied_cnt))
        self.ui.vacant_.setText(str(room_max-occupied_cnt-skipped_rooms_count))
        test_global = self.db_result

    def button_clicked(self, num):
        num = int(num)
        #print (self.active_rooms_, 'active rooms')
        #logging.info('Dialog App Open for Room %s'%num)

        # Get the current stylesheet
        #current_stylesheet = self.ui.box2.styleSheet()
        try:
            box_name = f"stat{num}"
            current_stylesheet = eval(f"self.ui.{box_name}.styleSheet()")
            #print(current_stylesheet)

            # Extract the RGB color using a regex
            color_match = re.search(r'rgb\((\d+), (\d+), (\d+)\)', current_stylesheet)
            #print(color_match)

            hass_flag_ = False
            if color_match:
                # Strip any extra whitespace and convert to integers
                r, g, b = map(int, color_match.groups())
                
                # Compare with the target color
                if (r, g, b) == (50, 194, 25):
                    hass_flag_ = True

            #print("hass_flag_:", hass_flag_)
        except:
            hass_flag_ = False

        self.dlg = MyAppDialog([num,hass_flag_,self.username,self.indicator_flag,False,self.unavailable_rooms])
        self.dlg.setWindowTitle( 'TRANSACTIONS' )
        self.dlg.show()
        self.dlg.signal.sig_disp.connect(self.display_message)
        self.dlg.signal.update_display.connect(self.update_DB_GUI)
        self.dlg.signal.sig_close.connect(self.close_program)
        self.dlg.signal.add_new_record.connect(self.add_new_db)
        self.dlg.signal.check_out.connect(self.check_out_db)
        msg_ = ["Good day!","Welcome to WJV",f"Vacant Room: {num}",datetime.now().strftime('%b-%d-%Y %H:%M %p')]
        self.display_message(msg_)
        
    def check_out_db(self, details_):
        try:
            db(db.WJV_db.Ticket_ID == details_[0]).update(Check_Out=details_[8],Status_=details_[5], Total_Price = details_[11])
            db.commit()
        except Exception as e:
            print (e)
        

    def insert_db_details_(self, room_number):
        try:
            #print ('add new db details', room_number, self.queue_checkin)
            #print (room_number, self.queue_checkin)
            details_ = self.queue_checkin[int(room_number)]
            #print (details_)
            db.WJV_db.insert(Ticket_ID=details_[0], Room_Type=details_[1], extra_heads=details_[2],
                                    Room_Merchandise=details_[3], Room_Meals=details_[4], Status_=details_[5],
                                    Extended_=details_[6], Check_In=details_[7], Check_Out=details_[8],
                                    Room_Number=details_[9], Cashier_=details_[10], Total_Price=details_[11],
                                    Mer_Price=details_[12], RM_Price=details_[13], Price_=details_[14], RFID_= details_[16])
            db.commit()
            if self.ha_enable_flag:
                self.ha_summary.signal.save_to_db.disconnect(self.insert_db_details_)
                self.ha_summary.signal.http_error.disconnect(self.http_error_msg)
            self.msg_notavailable.discard(str(room_number))
            self.queue_checkin.pop(int(room_number))
        except Exception as e:
            print (e, 'error 002')

    def http_error_msg(self, msg):
        try:
            QMessageBox.critical(self, "Message", msg)
            if self.ha_enable_flag:
                self.ha_summary.signal.save_to_db.disconnect(self.insert_db_details_)
                self.ha_summary.signal.http_error.disconnect(self.http_error_msg)
        except:
            pass
        

    def add_new_db(self, details_):
        #print ('new details' , details_)
        query = (db.WJV_db.Status_ == 'Open')
        rows = db(query).select()
        machine_list = []
        for row in rows:
            machine_list.append(row.Room_Number)
        if not details_[9] in machine_list:
            room_name = details_[9].replace('_',' ')
            result = True
            if not room_name in self.unavailable_rooms:
                if self.ha_enable_flag:
                    result = self.ha_summary.threaded_device_control(self.ha_summary.turn_on_device,'switch.%s'%(room_name.split(' ')[1]))
                    self.ha_summary.signal.save_to_db.connect(self.insert_db_details_)
                    self.ha_summary.signal.http_error.connect(self.http_error_msg)
            if result:
                self.db_result_keys.append(int(room_name.split(' ')[1]))
                self.queue_checkin.update({int(room_name.split(' ')[1]):details_})
                if not self.ha_enable_flag:
                    self.insert_db_details_(room_name.split(' ')[1])
            else:
                print ('Device not found')
            self.close_program()
        else:
            QMessageBox.warning(
                    self, 'Error', 'Existing Room transaction')

    def close_program (self):
        try:
            self.dlg.close()
        except:
            pass
    def __del__ ( self ):
        self.ui = None


( Ui_DialogWindow, QDialog ) = uic.loadUiType( 'dialogwindow.ui' )
class MyAppDialog ( QDialog ):
    """MainWindow inherits QDialog"""
    def __init__ ( self, pass_data,parent=None):
        super(MyAppDialog, self).__init__(parent)
        self.ui = Ui_DialogWindow()
        self.ui.setupUi( self )
        self.load_room_mapping()
        config_checker = ConfigChecker()
        config_checker.check_config()
        self.second_dialog = None
        self.config_info = config_checker.config_info
        self.signal = MySignal()
        self.room_counter = 0
        #print (pass_data, 'pass data')
        data = pass_data[0]
        hw_status = pass_data[1]
        self.username__ = pass_data[2]
        self.ind_flag = pass_data[3]
        self.locked_rm = pass_data[-1]
        #print (self.locked_rm)
        self.rm_num = data
        self.setModal(True)
        self.ui.password_.clear()
        #print (self.rm_num , self.locked_rm, '<---')
        if 'Room %s'%self.rm_num in self.locked_rm:
            self.ui.password_.setEnabled(True)
        if self.rm_num == (int(self.config_info['ROOM_MAX'])+1):
            self.ui.groupBox_4.setEnabled(False)
        else:
            self.ui.groupBox_4.setEnabled(True)
        self.ui.booking_group.setEnabled(False)
        self.update_combobox_type()
        self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
        self.ui.extra_button.clicked.connect(self.update_heads)
        self.ui.merchandise_button.clicked.connect(self.update_merchandise)
        self.ui.merchandise_button_2.clicked.connect(self.update_merchandise_2)
        self.ui.room_rate_button.clicked.connect(self.add_checkin_info)
        self.ui.partial_payment.clicked.connect(self.process_partial_pay)
        self.ui.extend_button.clicked.connect(self.update_room_ext)
        self.ui.checkout_.clicked.connect(self.checkout_guest__confirm)
        self.ui.checkout_enable.clicked.connect(self.update_checkout_button)
        self.ui.merchandise_combobox.currentIndexChanged.connect(self.update_stock_info)
        self.ui.room_rates_comboBox.currentIndexChanged.connect(self.activate_booking)
        self.ui.merchandise_combobox_2.currentIndexChanged.connect(self.update_stock_info2)
        self.ui.filter_edit.textChanged.connect(self.clear_item_qty)
        #connect filter_edit if enter pressed
        self.ui.filter_edit.setFocusPolicy(Qt.StrongFocus)
        self.ui.filter_edit.setFocus()
        self.ui.filter_edit.returnPressed.connect(self.filter_combobox)
        self.ui.platform_comboBox.currentIndexChanged.connect(self.check_monthlies)
        self.global_msg = ''
        if hw_status:
            self.ui.transfer_button.setEnabled(False)
            self.ui.checkout_.setEnabled(False)
            self.ui.checkout_.setStyleSheet("color: rgb(255, 0, 0);")
        else:
            self.ui.transfer_button.setEnabled(True)
            self.ui.checkout_.setEnabled(True)
            self.ui.checkout_.setStyleSheet("color: rgb(0, 0, 0);")
        self.update_stock_info()
        self.update_stock_info2()
        self.ui.dateselection.setDateTime(datetime.now())
        self.ui.dateselection.setEnabled(False)
        self.send_data_back()
    
    def update_checkout_button(self):
        #get the text of password_checkout
        logging.info('trying to bypass checkout by - %s' % self.username__)
        password_checkout = self.ui.password_checkout.text()
        #check if the password_checkout is equal to "qwe123"
        if password_checkout == "1234":
            #set the checkout button to enabled
            self.ui.checkout_.setEnabled(True)
            self.ui.checkout_.setStyleSheet("color: rgb(0, 0, 0);")
            logging.info('successfully bypassed checkout')
        else:
            #pop up message box
            QMessageBox.critical(self, "Message", "Invalid Password")
            logging.info('failed wrong password - %s'%password_checkout)

    def update_combobox_type(self):
        #clear combobox merchandise_combobox_type
        self.ui.merchandise_combobox_type.clear()
        #query the type_ of merchandise and populate it to combobox
        query = (db.Merchandise_rates_db.id != None)
        rows = db(query).select(db.Merchandise_rates_db.Type_, distinct=True)
        #populate the combobox with the type_ of merchandise
        for row in rows:
            #print (row, '----')
            self.ui.merchandise_combobox_type.addItem(row.Type_)
                #query the merchandise and populate it to combobox and let the selection of combobox_type as filter
        self.update_combobox_()


        self.ui.merchandise_combobox_type.currentIndexChanged.connect(self.update_combobox_)

    def load_room_mapping(self):
        # Read room_mapping.json from parent folder "Resource" and save it to self.room_mapping
        with open('Resource/room_mapping.json') as f:
            self.room_mapping = json.load(f)    

    def clear_item_qty(self):
        self.ui.mcd_qty.setValue(0)

    def send_data_back(self):
        self.accept()
        QTimer.singleShot(200, lambda: self.signal.sig_disp.emit(self.message_))

    def process_partial_pay(self):
        query = (db.WJV_db.id == self.serial_ID)
        rows = db(query).select()
        if rows:
            cur_datetime = datetime.now()
            orig_info = rows[0]
            new_name = '%s*'%orig_info.Ticket_ID
            amount__ = self.ui.payment_amount.text().split(' ')[-1]
            partial_cost = "Partial PAYMENT %s"%int(float(amount__))
            try:
                db.WJV_db.insert(Ticket_ID=new_name,Room_Type=partial_cost,extra_heads=0,Room_Merchandise={},Room_Meals={},Status_ ='Close',
                                        Extended_=None,Check_In=orig_info.Check_In,Check_Out=cur_datetime,Room_Number =orig_info.Room_Number, Cashier_ = orig_info.Cashier_,
                                        Total_Price = amount__, Mer_Price =0, RM_Price = 0, Price_=None)
                db.commit()
                self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
                QMessageBox.information(self, "Message", "Successfully Process Partial Payment")
            except:
                db.rollback()

    def check_monthlies(self):
        selection_ = str(self.ui.platform_comboBox.currentText())
        if selection_ == 'GIFTCHECK':
            self.ui.label_9.setText("Number of Hours")
            self.ui.booking_amount.setText("0")
            self.ui.booking_amount.setEnabled(False)
            self.ui.guest_count.setEnabled(True)
            self.ui.booking_days.setEnabled(True)
        elif selection_ == 'MONTHLIES':
            self.ui.label_9.setText("Number of Days")
            self.ui.booking_days.setValue(30)
            self.ui.guest_count.setValue(1)
            self.ui.guest_count.setEnabled(False)
            self.ui.booking_days.setEnabled(False)
            self.ui.dateselection.setEnabled(True)
            #self.ui.booking_reference.setEnabled(False)
            specific_room = "MR_0%s_720"%(str(self.rm_num).zfill(2))
            myquery = (db.Room_rates_db.Rate_ID.contains(specific_room))
            dataB = db(myquery).select()
            if dataB:
                price__ = str(dataB[0].Price_)
                self.ui.booking_amount.setText(price__)
            self.ui.booking_amount.setEnabled(False)
        else:
            self.ui.label_9.setText("Number of Days")
            self.ui.booking_amount.setEnabled(True)
            self.ui.booking_amount.setText('')
            self.ui.booking_days.setValue(1)
            self.ui.guest_count.setEnabled(True)
            self.ui.booking_days.setEnabled(True)
            self.ui.dateselection.setEnabled(False)
            #self.ui.booking_reference.setEnabled(True)

    def update_stock_info2(self):
        new_merchandise = str(self.ui.merchandise_combobox_2.currentText())

        try:
            id_2 = int(new_merchandise.split(':')[0][2:])
            myquery = (db.Merchandise_rates_db.id == id_2)
            query2_ = db(myquery).select()
            __stock = 'Stock/s: %s'%(query2_[0].Quantity_)
            self.ui.stocks_count_2.setText(__stock)
        except Exception as e:
            pass#print (e)

    def update_stock_info(self):
        new_merchandise = str(self.ui.merchandise_combobox.currentText())
        selection_type = str(self.ui.merchandise_combobox_type.currentText())
        try:
            id_2 = int(new_merchandise.split(':')[0][2:])
            myquery = (db.Merchandise_rates_db.id == id_2)
            query2_ = db(myquery).select()
            __stock = 'Stock/s: %s'%(query2_[0].Quantity_)
            self.ui.stocks_count.setText(__stock)
        except Exception as e:
            pass#print (e)

    def check_printer(self,printer_name):
        c = wmi.WMI ()
        for p in c.Win32_Printer():
            if p.caption == printer_name:
                #print 'equal', p.WorkOffline
                if p.WorkOffline:
                    status_ = False
                else:
                    status_ = True
        return status_

    def generate_passkey(self,chosen_number):
        current_hour = datetime.now().hour
        current_minutes = datetime.now().minute
        interval_identifier = current_minutes // 30
        interval_key = hashlib.sha256(str(interval_identifier).encode()).hexdigest()[:4]
        hash_key = hashlib.sha256(b'secret_key').hexdigest()[:2]
        passkey = (current_hour * chosen_number) + interval_identifier + int(interval_key, 16) + int(hash_key, 16)
        passkey = passkey % 1000000
        passkey_str = str(passkey).zfill(6)
        return passkey_str

    def checkout_guest__confirm(self):
        try:
            pass_flag = True
            if True:
                if self.ui.checkBox_print.isChecked():
                    win32print.SetDefaultPrinter(self.config_info['THERMAL'])
                    printer_name = win32print.GetDefaultPrinter()
                    printer_stat = self.check_printer(printer_name)
                    if printer_stat:
                        try:
                            response = QMessageBox.question(self, 'Continue?',
                                    'Confirm - CheckOut Guest?', QMessageBox.Yes, QMessageBox.No)
                            if response == QMessageBox.Yes:
                                self.checkout_guest_()
                            else:
                                pass
                        except Exception as e:
                            print (e)
                    else:
                        msg_ = "No %s printer found"%printer_name
                        QMessageBox.critical(self, "Information", msg_)
                else:
                    try:
                        response = QMessageBox.question(self, 'Continue?',
                                'Confirm - CheckOut Guess?', QMessageBox.Yes, QMessageBox.No)
                        if response == QMessageBox.Yes:
                            self.checkout_guest_()
                        else:
                            pass
                    except Exception as e:
                        print (e)
            else:
                QMessageBox.critical(self, "Information", 'Please turn off breaker first!')
        except Exception as e:
            QMessageBox.critical(self, "Information", 'Cant find printer!\nPlease check printer settings.')
            print (e)

    def print_message(self, msg__):
        font = {
            "height": 11,
        }
        font2 = {
            "height": 16,
        }

        font3 = {
            'height': 12,
            'italic':1,
        }
        max_ = len(msg__)
        with Printer(linegap=1) as printer:
            for idx, x in enumerate(msg__):
                if '#' in x:
                    printer.text(x.strip(), font_config=font2)
                else:
                    printer.text(x.strip(), font_config=font)


    def win_print(self,filename, printer_name = None):
        try:
            if printer_name == 'thermal':
                win32print.SetDefaultPrinter(self.config_info['THERMAL'])
                printer_name = win32print.GetDefaultPrinter()
                out = '/d:"%s"' % (printer_name)
                with open(filename) as f:
                    contents = f.readlines()
                self.print_message(contents)
        except:
            QMessageBox.warning(self, 'Error', 'Unable to print')

    def print_billing(self):
        open ("Resource/billing.txt", "w").write (self.global_msg)
        if self.ui.checkBox_print.isChecked():
            self.win_print("Resource/billing.txt","thermal")
        else:
            pass

    def checkout_guest_(self):
        #logging.info('Checkout Guest')
        try:
            self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
            self.signal.check_out.emit([self.db_records_.Ticket_ID,'','','','','Close','','',datetime.now(),'','',self.total_price,'','','',self.rm_num])
            #self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
            self.signal.update_display.emit("ok")
            self.signal.sig_close.emit("done")
            self.print_billing()

        except Exception as e:
            print (e)

    def enable_free_meal(self, flag):
        if flag:
            self.ui.label_3.setEnabled(True)
            self.ui.merchandise_combobox_2.setEnabled(True)
            self.ui.mcd_qty_2.setEnabled(True)
            self.ui.merchandise_button_2.setEnabled(True)
        else:
            self.ui.label_3.setEnabled(False)
            self.ui.merchandise_combobox_2.setEnabled(False)
            self.ui.mcd_qty_2.setEnabled(False)
            self.ui.merchandise_button_2.setEnabled(False)


    def string_to_time(self,time_str):
        # Parse the string using strptime
        dt = datetime.strptime(time_str.strip().lower(), "%I%p")
        print (dt.time())
        return dt.time()

    def get_time_group_and_start(self, delta_hr):
        current_time = datetime.now()

        shifts__ = self.config_info["COTTAGE_Start_time"]
        print(shifts__, 'shifts')

        try:
            shifts = {
                'Morning': self.string_to_time(shifts__[0]),     # 8AM
                'Afternoon': self.string_to_time(shifts__[1]),   # 2PM
                'Evening': self.string_to_time(shifts__[2]),     # 8PM
            }
        except Exception as e:
            print(e, 'error in get_time_group_and_start')
            shifts = {
                'Morning': time(8, 0),
                'Afternoon': time(14, 0),
                'Evening': time(20, 0),
            }

        candidates = []

        for name, start_t in shifts.items():
            start_dt = datetime.combine(current_time.date(), start_t)
            end_dt = start_dt + timedelta(hours=delta_hr)

            # Handle overnight shift (e.g., 8PM - 6AM)
            if end_dt.date() != start_dt.date():
                if current_time >= start_dt:
                    pass  # tonight 8PM to tomorrow
                else:
                    start_dt -= timedelta(days=1)
                    end_dt = start_dt + timedelta(hours=delta_hr)

            if start_dt <= current_time < end_dt:
                candidates.append((start_dt, name))

        if candidates:
            start_dt, name = max(candidates)
            print(f"Current time {current_time.strftime('%I:%M %p')} is within {name} shift window. Start time: {start_dt}")
            return name, start_dt

        # No active shift — return None for both
        print(f"No active shift at {current_time.strftime('%I:%M %p')}.")
        return None, None

    def add_checkin_info(self):
        #self.active_rooms_
        pass_flag = True
        rm_num = 'Room %s'%self.rm_num
        #print (rm_num , self.locked_rm, 'locked rooms')
        if rm_num in self.locked_rm:
        #if self.tuya_flag==False:
            pass_ = self.ui.password_.text()
            #key_ = self.generate_passkey(self.rm_num)
            #print (key_)
            if pass_ != "1234":
                pass_flag = False
                QMessageBox.critical(self, "Information", 'Please type 1234 to proceed!')
        if pass_flag:
            valid_flag = True
            cur_datetime = datetime.now()
            room_x = "ROOM_%s"%self.rm_num
            query = (db.RFID.Room_Num == room_x)
            rows_rf = db(query).select()
            card_detail = rows_rf[0].ID_
            ticket_id = cur_datetime.strftime("%m%d%y_%I%M%S")
            ticket_id = room_x + "_"+ ticket_id
            
            guest_ = None
            t_price = 0
            if self.rm_num == 97:
                room_type_ = 'WALKIN 0 Hrs Php 0'
            else:
                if len(card_detail) < 10 and self.ui.platform_comboBox.currentText() != 'MONTHLIES':
                    valid_flag = False
                    QMessageBox.critical(self, "Information", 'Please scan the RFID card!')
                room_type_ = str(self.ui.room_rates_comboBox.currentText())
                if room_type_ == 'Custom Check-in':
                    correct_value = ['3','12','24']
                    if self.ui.booking_reference.text() == '' or self.ui.booking_amount.text() == '':
                        valid_flag = False
                    if self.ui.platform_comboBox.currentText() == 'GIFTCHECK':
                        if not self.ui.booking_days.text() in correct_value:
                            valid_flag = False
                    try:
                        if self.ui.platform_comboBox.currentText() == 'MONTHLIES':
                            room_type_ = "TENANT %s Hrs Php %s"%(int(self.ui.booking_days.text())*24, str(self.ui.booking_amount.text()))
                            cur_datetime = self.ui.dateselection.dateTime().toPyDateTime()
                        else:
                            if self.ui.platform_comboBox.currentText() == 'GIFTCHECK':
                                room_type_ = "Custom %s Hrs Php %s"%(int(self.ui.booking_days.text()), str(self.ui.booking_amount.text()))
                            else:    
                                room_type_ = "Custom %s Hrs Php %s"%(int(self.ui.booking_days.text())*24, str(self.ui.booking_amount.text()))
                        guest_ = '%s,%s,%s,%s,%s'%(self.ui.guest_count.text(),self.ui.booking_reference.text(),str(self.ui.platform_comboBox.currentText()),self.ui.guest_name.text(),self.ui.booking_days.text())
                        t_price = float(self.ui.booking_amount.text())
                    except:
                        valid_flag = False

            try:
                if valid_flag == True:
                    #check room type if contains "Cottage"
                    if 'COTTAGE' in room_type_:
                        delta_hr = room_type_.split(' ')[-1].split('Hrs')[0]
                        delta_hr = int(delta_hr)
                        group_, start_ = self.get_time_group_and_start(delta_hr)
                        print ("Group:", group_, "Start:", start_)
                        cur_datetime = start_
                    self.signal.add_new_record.emit([ticket_id,room_type_,0,{},{},'Open',False,cur_datetime,None,room_x, self.username__,t_price, 0, 0, guest_,None ,card_detail])
                    self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
                    msg_new = self.message_
                    #print (self.message_)
                    if msg_new:
                        msg_new.pop(-2)
                        msg_new.insert(0,'Thank you!')
                        msg_new[3] = f"Exp Out: {self.message_[-1]}"
                    self.signal.sig_disp.emit(msg_new)
                    self.signal.update_display.emit("ok")
            except Exception as e:
                db.rollback()
                #print (e, 'error checkin')

    def update_room_ext(self):
        try:
            db(db.WJV_db.Ticket_ID == self.db_records_.Ticket_ID).update(Extended_=True)
            db.commit()
            #self.signal.update_display.emit("ok")
            self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
            self.signal.update_display.emit("ok")
        except Exception as e:
            print (e)
            db.rollback()

    def update_heads(self):
        if int(self.ui.extra_qty.text()) > 0:
            try:
                head_count = self.db_records_.extra_heads
                db(db.WJV_db.Ticket_ID == self.db_records_.Ticket_ID).update(extra_heads=head_count+int(self.ui.extra_qty.text()))
                db.commit()
                self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
            except Exception as e:
                db.rollback()





    def update_merchandise(self):
        if int(self.ui.mcd_qty.text()) > 0:
            new_merchandise = str(self.ui.merchandise_combobox.currentText())
            stock_update_ = int(self.ui.stocks_count.text().split(' ')[1])
            info_basic = '%s - %s'%(new_merchandise,stock_update_)
            #logging.info(info_basic)
            add_flag = True
            selection_type = str(self.ui.merchandise_combobox_type.currentText())
            if stock_update_ <=0:
                question01 = "Zero stocks.\n Would like to add the item?"
                reply = QMessageBox.question(self, 'Message', question01, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    add_flag = False
            if add_flag:
                if self.rm_num == 97:
                    room_name = "ROOM_%s"%self.rm_num
                    query = (db.WJV_db.Room_Number == room_name) & (db.WJV_db.Status_ == 'Open')
                    rows = db(query).select()

                    cur_datetime = datetime.now()
                    room_x = "ROOM_%s"%self.rm_num
                    ticket_id = cur_datetime.strftime("%m%d%y_%I%M%S")
                    ticket_id = room_x + "_"+ ticket_id
                    room_type_ = 'WALKIN 0 Hrs Php 0'
                    if not rows:
                        try:
                            id_2 = int(new_merchandise.split(':')[0][2:])
                            _qty = int(self.ui.mcd_qty.text())
                            merchandise_list = {}
                            merchandise_list[new_merchandise] = _qty
                            db.WJV_db.insert(Ticket_ID=ticket_id,Room_Type=room_type_,extra_heads=0,Room_Merchandise=merchandise_list,Room_Meals={},Status_ ='Open',
                            Extended_=False,Check_In=cur_datetime,Check_Out=None,Room_Number =room_x, Cashier_ = self.username__, Total_Price = 0, Mer_Price =0, RM_Price = 0)
                            myquery = (db.Inventory_tracking.Merchandise_ID ==  id_2) & (db.Inventory_tracking.Ref_Date == datetime.now().date())
                            data_row = db(myquery).select()
                            current_inventory = data_row[0].PI_ + _qty
                            db(db.Inventory_tracking.id==data_row[0].id).update(PI_= current_inventory)
                            myquery = (db.Merchandise_rates_db.id == id_2)
                            query2_ = db(myquery).select()
                            __stock = int(query2_[0].Quantity_)
                            check_quantity = (__stock - _qty)
                            if (check_quantity <=0):
                                check_quantity = 0
                            db(db.Merchandise_rates_db.id==id_2).update(Quantity_=__stock - _qty)
                            db.commit()
                            self.signal.update_display.emit("ok")
                            self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
                        except Exception as e:
                            db.rollback()
                            print (e, 'error1')
                    else:
                        merchandise_list = self.db_records_.Room_Merchandise
                        id_2 = int(new_merchandise.split(':')[0][2:])
                        _qty = int(self.ui.mcd_qty.text())
                        last_count = 0



                        try:
                            try:
                                merchandise_list[new_merchandise] += int(self.ui.mcd_qty.text())
                            except:
                                merchandise_list[new_merchandise] = int(self.ui.mcd_qty.text())
                            db(db.WJV_db.Ticket_ID == self.db_records_.Ticket_ID).update(Room_Merchandise=merchandise_list)
                            myquery = (db.Inventory_tracking.Merchandise_ID ==  id_2) & (db.Inventory_tracking.Ref_Date == datetime.now().date())
                            data_row = db(myquery).select()
                            current_inventory = data_row[0].PI_ + _qty
                            db(db.Inventory_tracking.id==data_row[0].id).update(PI_= current_inventory)

                            myquery = (db.Merchandise_rates_db.id == id_2)
                            query2_ = db(myquery).select()
                            __stock = int(query2_[0].Quantity_)
                            check_quantity = (__stock - _qty)
                            if (check_quantity <=0):
                                check_quantity = 0
                            db(db.Merchandise_rates_db.id==id_2).update(Quantity_=check_quantity)
                            db.commit()
                            self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
                        except Exception as e:
                            print (e)
                            db.rollback()

                else:
                    merchandise_list = self.db_records_.Room_Merchandise

                    id_2 = int(new_merchandise.split(':')[0][2:])
                    _qty = int(self.ui.mcd_qty.text())
                    last_count = 0

                    try:
                        try:
                            merchandise_list[new_merchandise] += _qty
                        except:
                            merchandise_list[new_merchandise] = _qty
                        db(db.WJV_db.Ticket_ID == self.db_records_.Ticket_ID).update(Room_Merchandise=merchandise_list)
                        myquery = (db.Inventory_tracking.Merchandise_ID ==  id_2) & (db.Inventory_tracking.Ref_Date == datetime.now().date())
                        data_row = db(myquery).select()
                        current_inventory = data_row[0].PI_ + _qty
                        db(db.Inventory_tracking.id==data_row[0].id).update(PI_= current_inventory)
                        myquery = (db.Merchandise_rates_db.id == id_2)
                        query2_ = db(myquery).select()
                        __stock = int(query2_[0].Quantity_)
                        check_quantity = (__stock - _qty)
                        if (check_quantity <=0):
                            check_quantity = 0
                        db(db.Merchandise_rates_db.id==id_2).update(Quantity_=check_quantity)
                        db.commit()
                        self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
                    except Exception as e:
                        print (e)
                        db.rollback()



    def update_merchandise_2(self):
        if int(self.ui.mcd_qty_2.text()) > 0:
            new_merchandise = str(self.ui.merchandise_combobox_2.currentText())
            stock_update_ = int(self.ui.stocks_count_2.text().split(' ')[1])
            add_flag = True
            if stock_update_ <=0:
                question01 = "Zero stocks.\n Would like to add the item?"
                reply = QMessageBox.question(self, 'Message', question01, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    add_flag = False
            if add_flag:
                merchandise_list = self.db_records_.Room_Merchandise
                try:
                    merchandise_list[new_merchandise] += int(self.ui.mcd_qty_2.text())
                except:
                    merchandise_list[new_merchandise] = int(self.ui.mcd_qty_2.text())
                try:
                    db(db.WJV_db.Ticket_ID == self.db_records_.Ticket_ID).update(Room_Merchandise=merchandise_list)

                    id_2 = int(new_merchandise.split(':')[0][2:])
                    _qty = int(self.ui.mcd_qty_2.text())
                    myquery = (db.Inventory_tracking.Merchandise_ID ==  id_2) & (db.Inventory_tracking.Ref_Date == datetime.now().date())
                    data_row = db(myquery).select()
                    current_inventory = data_row[0].PI_ + _qty
                    db(db.Inventory_tracking.id==data_row[0].id).update(PI_= current_inventory)

                    myquery = (db.Merchandise_rates_db.id == id_2)
                    query2_ = db(myquery).select()
                    __stock = int(query2_[0].Quantity_)
                    check_quantity = (__stock - _qty)
                    if (check_quantity <=0):
                        check_quantity = 0
                    db(db.Merchandise_rates_db.id==id_2).update(Quantity_=check_quantity)
                    db.commit()
                    self.db_records_, self.total_price, self.serial_ID, self.message_ = self.update_GUI_info()
                except Exception as e:
                    print (e)
                    db.rollback()







    def update_GUI_info(self):
        #print (self.locked_rooms)
        try:

            room_name = "ROOM_%s"%self.rm_num
            query = (db.WJV_db.Room_Number == room_name) & (db.WJV_db.Status_ == 'Open')
            rows = db(query).select()
            cur_time = datetime.now()
            self.update_combobox2_()
            self.update_combobox_()
            temp_rm = 'Room %s'%self.rm_num
            # if temp_rm in self.locked_rm:
            #     self.ui.password_.setEnabled(True)

                
            
            if rows:
                self.ui.password_.setEnabled(False)
                self.ui.room_rate_button.setEnabled(False)
                self.ui.partial_payment.setEnabled(True)
                self.ui.room_rates_comboBox.setEnabled(False)
                self.ui.time_coverage.setText('-')
                #self.ui.time_coverage.setEnabled(False)
                rows_record = rows[0]
                if rows_record.Extended_: self.ui.extend_button.setEnabled(False)
                serial_id = rows_record.id
                serial_search = '%s*'%rows_record.Ticket_ID
                room_hr_details = int(rows_record.Room_Type.split(" ")[1])
                room_type_details = str(rows_record.Room_Type.split(" ")[0])
                room_type_cost = float(rows_record.Room_Type.split(" ")[-1])
                temp_price = float(rows_record.Total_Price)
                payment_amount = 'Php %.2f'%room_type_cost
                not_reg_flag = False
                if room_type_details != 'REGULAR' and room_type_details != 'COTTAGE':
                    serial_search ='%s'%rows_record.Ticket_ID
                    not_reg_flag = True

                query2A = (db.WJV_db.Ticket_ID == serial_search)
                rows2A = db(query2A).select()
                paid_amount = 0
                if rows2A:
                    paid_amount = float(rows2A[0].Room_Type.split(" ")[-1])
                    self.ui.partial_payment.setEnabled(False)
                    self.ui.payment_amount.setText('')
                else:
                    self.ui.payment_amount.setText(payment_amount)


                flag_bal = False
                cust_details = rows_record.Price_
                if cust_details:
                    temp_data__ = rows_record.Price_.split(',')
                    data__ = "\nPlatform: %s\nName: %s\nRef#: %s\nNo of Days: %s\n"%(temp_data__[2],temp_data__[3],temp_data__[1],temp_data__[-1])
                    self.ui.partial_payment.setEnabled(False)
                    self.ui.payment_amount.setText('')
                    flag_bal = True
                else:
                    data__ = ''
                flagc = False
                if room_hr_details == 24 and room_type_details != 'Custom':
                    self.enable_free_meal(True)
                    flagc = True
                elif room_type_details == 'Custom' and room_type_cost!=0:
                    self.enable_free_meal(True)
                    flagc = True
                else:
                    self.enable_free_meal(False)
                expected_out = rows_record.Check_In + timedelta(hours=room_hr_details)
                room_rate_ = float(rows_record.Room_Type.split(" ")[-1])
                running_time = (cur_time - rows_record.Check_In).total_seconds()
                hours, remainder = divmod(running_time,60*60)
                minutes, seconds = divmod(remainder,60)
                self.time_diff = round(((cur_time - expected_out).total_seconds()/3600.00),2)
                frac, whole = math.modf(self.time_diff)
                if room_type_details == 'TENANT':
                    if whole >= 72.0:
                        extra_charge = .05
                    else:
                        extra_charge = 0
                else:
                    extra_charge = max(0, whole) + (1 if max(0,frac) > 0.167 else 0) #0.167 -> 10 minutes
                mer_list = ''
                mer_list2 = ''
                test = ''
                mer_cost = 0
                if rows[0].Room_Merchandise:
                    free_ctr = 0
                    counter_ = 2
                    for item_name, qty_ in rows_record.Room_Merchandise.items():
                        free_ = ''
                        if 'Php 0' in item_name:
                            free_ = ' FREE'
                            free_ctr +=int(qty_)
                        mer_list = mer_list + '  >%s %s pc/s - [ %s ]\n'%(free_, qty_,item_name)
                        mer_list2 = mer_list2 + '  >%s pc/s\n   [%s]\n'%(qty_,item_name.split(':')[1].strip())
                        item_cost =  int(qty_) * int(item_name.split(" ")[-1])
                        mer_cost += item_cost
                        try:
                            temp001 = rows[0].Price_.split(',')[0]
                            temp002 = rows[0].Price_.split(',')[-1]
                            if temp001 != '':
                                counter_ = int(temp001) * int(temp002)
                        except:
                            pass
                        if free_ctr<counter_ and flagc ==True:
                            self.enable_free_meal(True)
                        else:
                            self.enable_free_meal(False)

                else:
                    mer_list2 = mer_list = ' ( NO ITEM )'
                room_name_ = str(rows_record.Room_Type.split("Php")[0]).strip()
                room_hour_ = str(rows_record.Room_Type.split(" ")[1]).strip()
                specific_room = "RR_0%s_%s"%(str(self.rm_num).zfill(2),room_hour_)

                cottage_room_numbers = [
                    int(key.split("_")[1])  # Extract the number from "ROOM_xx"
                    for key, value in self.room_mapping.items()
                    if "COTTAGE" in value[0]  # Check if "COTTAGE" is in the room name
                ]

                if 'Custom' in room_name_:
                    add_head_ =  int(self.config_info['BOOKING+HD'])
                    extra_hour = int(self.config_info['BOOKING+HR'])
                elif 'TENANT' in room_name_:
                    specific_room = "MR_0%s_%s"%(str(self.rm_num).zfill(2),room_hour_)
                    query = (db.Room_rates_db.Rate_Name == room_name_ and db.Room_rates_db.Rate_ID.contains(specific_room))
                    rows = db(query).select()
                    if rows:
                        extra_hour = rows[0].Price_
                        add_head_ = 0

                    else:
                        add_head_ =  0
                        extra_hour = 0
                elif int(self.rm_num) in cottage_room_numbers:
                    specific_room = "CR_0%s_%s"%(str(self.rm_num).zfill(2),room_hour_)
                    query = (db.Room_rates_db.Rate_Name == room_name_ and db.Room_rates_db.Rate_ID.contains(specific_room))
                    rows = db(query).select()
                    if rows:
                        add_head_ = rows[0].Head_price
                        extra_hour = rows[0].Price_add
                else:
                    query = (db.Room_rates_db.Rate_Name == room_name_ and db.Room_rates_db.Rate_ID.contains(specific_room))
                    rows = db(query).select()
                    if room_name == 'ROOM_97':
                        add_head_ = 0
                        extra_hour = 0
                    else:
                        add_head_ = rows[0].Head_price
                        extra_hour = rows[0].Price_add
                ext_head = rows_record.extra_heads*add_head_
                total_price = room_rate_ + extra_charge*extra_hour + mer_cost + ext_head
                checkIN_time = rows_record.Check_In
                checkOUT_time = expected_out
                computed_ext_charge = extra_charge*extra_hour
                computed_ext_heads = rows_record.extra_heads
                room_num__ = room_name.split('_')[-1].zfill(2)
                room_name_ = self.room_mapping[f'ROOM_{room_num__}'][0]
                if room_name == 'ROOM_97':
                    room_name = 'WALKIN CUSTOMER'
                    checkIN_time = 'NA'
                    checkOUT_time = 'NA'
                    hours = 0
                    minutes = 0
                    room_rate_ = '(Walk-in)'
                    computed_ext_charge = '-'
                    extra_charge = 0
                    ext_head = '-'
                    computed_ext_heads = '-'
                    total_price = mer_cost
                balance_ = total_price - float(paid_amount)
                msg_ = '''Serial #: %s
WJV INN
%s
%s
%s
CheckIn Time:\t\t%s
Expected Time Out:\t%s
Total Hours: %s Hours and %s Minutes

BILLING STATEMENT:
Room Rate: Php %s
Excess Charge: Php %s (%s hr or pct)
Additional Head: Php %s (%s person/s)
Total Merchandise: Php %s
%s

TOTAL BILL : Php %s
Downpayment: Php %.2f
Balance Amt: Php %.2f
Thank You !'''%(str(serial_id).zfill(10),room_name_,cur_time.strftime('%b-%d-%Y %H:%M %p'),data__,checkIN_time,checkOUT_time,int(hours), int(minutes),room_rate_,
                    computed_ext_charge,extra_charge, ext_head , rows_record.extra_heads,
                    mer_cost,mer_list,"%0.2f"%total_price,float(paid_amount),balance_)
                msg_2 = '''#%s
WJV INN
%s
%s

CheckIn Time:
 >%s
Expected Time Out:
 >%s
Total Hours:
 >%s Hrs, %s Min

BILLING STATEMENT:
Room Rate: Php %s
Excess Charge:
 >Php %s (%s hr or pct)
Additional Head:
 >Php %s (%s person/s)
Total Merchandise:
 >Php %s
%s

TOTAL BILL : Php %s
Downpayment: Php %.2f
Balance Amt: Php %.2f
Thank You !
---------------------------

---- Internal use only ----
GATE PASS
#%s
%s
%s
 >%s Hrs, %s Min
Thank You!
--
--
--'''%(str(serial_id).zfill(10),room_name_,cur_time.strftime('%b-%d-%Y %H:%M %p'),checkIN_time,checkOUT_time,int(hours), int(minutes),room_rate_,
                    computed_ext_charge,extra_charge, ext_head , rows_record.extra_heads,
                    mer_cost,mer_list2,"%0.2f"%total_price,float(paid_amount),balance_,str(serial_id).zfill(10),cur_time.strftime('%b-%d-%Y %H:%M %p'),room_name,int(hours), int(minutes))

                ticket = rows_record
                if not_reg_flag==True and temp_price!=total_price:
                    db(db.WJV_db.id==serial_id).update(Total_Price= total_price)
                    db.commit()
                try:
                    message_ = [f"{room_name} - ( {room_hr_details}HRS )",checkIN_time.strftime('IN:  %b-%d %H:%M %p'),checkOUT_time.strftime('OUT: %b-%d %H:%M %p'),f"hrs: {hours} min: {minutes}",checkOUT_time.strftime('%H:%M %p')]
                except:
                    message_ = []
            else:
                msg_ = '\n\n\n\n\n\t\tGOOD DAY!\n\t\tWelcome to WJV INN'
                msg_2 = ''
                total_price = 0
                ticket = None
                self.ui.partial_payment.setEnabled(False)
                serial_id = 0
                balance_ = 0
                self.ui.payment_amount.setText('')
                message_ = []
            self.global_msg = msg_2
            self.ui.summary_.setText(msg_)
            
            bal__ = '%.2f'%balance_
            self.ui.balance_amt.setText(bal__)
            
            return [ticket, balance_ ,serial_id, message_]
        except Exception as e:
            print (e)

    def activate_booking(self):
        rates_selection = str(self.ui.room_rates_comboBox.currentText())
        if rates_selection == 'Custom Check-in':
            self.ui.booking_group.setEnabled(True)
            self.ui.time_coverage.setText('-')
        else:
            self.ui.booking_group.setEnabled(False)
            if "COTTAGE" in rates_selection:
                #get the time in the rates_selection
                time_ = rates_selection.split(" ")[1]
                time_ = int(time_)
                group_, start_ = self.get_time_group_and_start(time_)
                group_time = "%s - [%s - %s]"%(group_, start_.strftime('%I%p'), (start_+timedelta(hours=time_)).strftime('%I%p'))
                self.ui.time_coverage.setText(group_time)


    def update_combobox_(self):
        self.ui.merchandise_combobox.clear()
        selection_type = self.ui.merchandise_combobox_type.currentText()
        if selection_type == "WRISTBAND":
            self.ui.mcd_qty.setEnabled(False)
            self.ui.mcd_qty.setValue(1)
            myquery = (db.Merchandise_rates_db.Quantity_ > 0) & (db.Merchandise_rates_db.Type_ == selection_type)
        else:
            self.ui.mcd_qty.setEnabled(True)
            self.ui.mcd_qty.setValue(0)
            myquery = (db.Merchandise_rates_db.Type_ == selection_type)
        self.items_ = []
        
        for row in db(myquery).select():
            new_name = "ID%s : %s - Php %s" % (row.id, row.Merchandise_Name, row.Price_)
            self.items_.append(new_name)
            

        #check the 

        for text in self.items_:
            self.ui.merchandise_combobox.addItem(text)

        # Clear the room rates combobox and populate it with sorted values
        self.ui.room_rates_comboBox.clear()
        room_numbers = [
            int(key.split("_")[1])  # Extract the number from "ROOM_xx"
            for key, value in self.room_mapping.items()
            if "COTTAGE" in value[0]  # Check if "COTTAGE" is in the room name
        ]
        if int(self.rm_num) in room_numbers:
            specific_room = "CR_0%s" % (str(self.rm_num).zfill(2))
        else:
            specific_room = "RR_0%s" % (str(self.rm_num).zfill(2))
        myquery = (db.Room_rates_db.Rate_ID.contains(specific_room))
        items = []
        
        dataB = db(myquery).select()
        if dataB:
            for row in dataB:
                new_name = "%s Php %s" % (row.Rate_Name, row.Price_)
                items.append(new_name)
            
            # Add the custom check-in option
            items.append("Custom Check-in")

            # Sort the items based on the number of hours in the string
            def get_hours(item):
                parts = item.split()
                if len(parts) > 2 and parts[1].isdigit():  # Check if it's in the format "X Hrs"
                    return int(parts[1])  # Return the number of hours as an integer
                return float('inf')  # Place "Custom Check-in" at the end

            sorted_items = sorted(items, key=get_hours)

            # Add sorted items to the combobox
            for text in sorted_items:
                self.ui.room_rates_comboBox.addItem(text)
        rates_selection = str(self.ui.room_rates_comboBox.currentText())
        if "COTTAGE" in rates_selection:
            #get the time in the rates_selection
            time_ = rates_selection.split(" ")[1]
            time_ = int(time_)
            group_, start_ = self.get_time_group_and_start(time_)
            group_time = "%s - [%s - %s]"%(group_, start_.strftime('%I%p'), (start_+timedelta(hours=time_)).strftime('%I%p'))
            self.ui.time_coverage.setText(group_time)

            #print(sorted_items)

    def filter_combobox(self):
        filter_text = self.ui.filter_edit.text().lower()  # Get the filter text in lowercase
        for index in range(self.ui.merchandise_combobox.count()):
            item_text = self.ui.merchandise_combobox.itemText(index).lower()
            self.ui.merchandise_combobox.setItemData(index, item_text)  # Ensure original item text is preserved
            
            if filter_text in item_text:
                self.ui.merchandise_combobox.showPopup()
            else:
                self.ui.merchandise_combobox.hidePopup()  # Hide the dropdown if no match

        # Re-add all items to show them based on the filter
        self.ui.merchandise_combobox.clear()
        for item in self.items_:
            if filter_text in item.lower():
                self.ui.merchandise_combobox.addItem(item)

    def update_combobox2_(self):
        self.ui.merchandise_combobox_2.clear()
        myquery = (db.Merchandise_rates_db.Merchandise_Name.contains('*'))
        items = []
        
        dataA = db(myquery).select()
        if dataA:
            for row in dataA:
                new_name = "ID%s : %s - Php 0"%(row.id, row.Merchandise_Name)
                items.append(new_name)
            for text in items:
                self.ui.merchandise_combobox_2.addItem(text)

    def __del__ ( self ):
        self.ui = None



class DataUploader(QThread):
    def __init__(self, config_info):
        super().__init__()
        self.config_info = config_info
        self.signal = MySignal()
        self.executor = ThreadPoolExecutor(max_workers=5)  # Allow up to 5 concurrent requests

    def upload_data_to_cloud(self):
        try:
            print(f"Uploading data to cloud at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            one_month_ago = datetime.now() - timedelta(days=7)
            query = ((db.WJV_db.uploaded_to_cloud == False) | (db.WJV_db.uploaded_to_cloud == None)) & (db.WJV_db.Check_In >= one_month_ago)
            rows = db(query).select()
            url = 'https://webdashboard.pythonanywhere.com/testapp/default/save_info'
            headers = {"Content-Type": "application/json"}
            print (url, headers)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Schedule all requests concurrently
            tasks = [loop.run_in_executor(self.executor, self.send_request, url, headers, row) for row in rows]
            loop.run_until_complete(asyncio.gather(*tasks))

        except Exception as e:
            print("Error:", e)
            self.signal.connectivity_status.emit(False)

    def send_request(self, url, headers, row):
        """Send a request in a separate thread to avoid blocking the UI."""
        try:
            data = {
                'PC_Name': str(self.config_info['BRANCH']),
                'Ticket_ID': str(row.Ticket_ID),
                'Room_Type': str(row.Room_Type),
                'extra_heads': int(row.extra_heads),
                'Room_Merchandise': json.dumps(row.Room_Merchandise),
                'Room_Meals': json.dumps(row.Room_Meals),
                'Status_': str(row.Status_),
                'Extended_': bool(row.Extended_),
                'Check_In': row.Check_In.strftime('%Y-%m-%d %H:%M:%S') if row.Check_In else None,
                'Check_Out': row.Check_Out.strftime('%Y-%m-%d %H:%M:%S') if row.Check_Out else None,
                'Room_Number': str(row.Room_Number),
                'Cashier_': str(row.Cashier_),
                'Total_Price': str(row.Total_Price),
                'Mer_Price': str(row.Mer_Price),
                'RM_Price': str(row.RM_Price),
                'Price_': str(row.Price_) if row.Price_ is not None else '0'
            }
            response = requests.post(url, headers=headers, json=data)
            json_response = response.json()

            # Update only if Check_Out is not None
            if data['Check_Out']:
                row.update_record(uploaded_to_cloud=True)
                db.commit()
            self.signal.connectivity_status.emit(True)
        except requests.exceptions.JSONDecodeError:
            print("Error: Response is not in JSON format.")
        except Exception as e:
            print("Request failed:", e)
            self.signal.connectivity_status.emit(False)

    def run(self):
        while True:
            self.upload_data_to_cloud()
            sleep(900)