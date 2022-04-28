# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AutoRegressionTestTool_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
import AutoRegressionTestTool_test
import time
import os
from multiprocessing import Queue
from threading import Thread
from PyQt5.QtGui import *


class Ui_Dialog(object):
    def __init__(self):
        self.sheet_name = ''
        self.cycle_time = 1
        self.msg_queue = Queue()
        self.status_queue = Queue()

    def setupUi(self, Dialog):
        # 自动生成参数
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(1061, 809)
        Dialog.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 110, 81, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(740, 110, 81, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 10, 101, 16))
        self.label_3.setObjectName("label_3")
        self.pushButton_chosefile = QtWidgets.QPushButton(Dialog)
        self.pushButton_chosefile.setGeometry(QtCore.QRect(890, 30, 151, 31))
        self.pushButton_chosefile.setObjectName("pushButton_chosefile")
        self.splitter = QtWidgets.QSplitter(Dialog)
        self.splitter.setGeometry(QtCore.QRect(10, 70, 331, 31))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setHandleWidth(60)
        self.splitter.setObjectName("splitter")
        self.pushButton_starttest = QtWidgets.QPushButton(self.splitter)
        self.pushButton_starttest.setObjectName("pushButton_starttest")
        self.pushButton_stoptest = QtWidgets.QPushButton(self.splitter)
        self.pushButton_stoptest.setObjectName("pushButton_stoptest")
        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setGeometry(QtCore.QRect(10, 30, 661, 31))
        self.lineEdit.setObjectName("lineEdit")
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setGeometry(QtCore.QRect(740, 130, 311, 641))
        self.listWidget.setObjectName("listWidget")
        self.textBrowser = QtWidgets.QTextBrowser(Dialog)
        self.textBrowser.setGeometry(QtCore.QRect(10, 130, 711, 641))
        self.textBrowser.setObjectName("textBrowser")
        self.comboBox = QtWidgets.QComboBox(Dialog)
        self.comboBox.setGeometry(QtCore.QRect(690, 30, 181, 31))
        self.comboBox.setObjectName("comboBox")
        self.radioButton = QtWidgets.QRadioButton(Dialog)
        self.radioButton.setGeometry(QtCore.QRect(710, 80, 89, 16))
        self.radioButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.radioButton.setObjectName("radioButton")
        self.lineEdit_2 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(910, 70, 131, 31))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setGeometry(QtCore.QRect(850, 80, 81, 16))
        self.label_4.setObjectName("label_4")
        self.comboBox.setEnabled(False)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

        # 按键功能
        self.pushButton_chosefile.clicked.connect(self.chose_file)
        self.pushButton_starttest.clicked.connect(self.start_test)
        self.pushButton_stoptest.clicked.connect(self.stop_test)

        # 获取下拉列表活动状态
        self.comboBox.currentIndexChanged[str].connect(self.sheet_value)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "自动测试工具v1.0.0"))
        self.label.setText(_translate("Dialog", "运行记录"))
        self.label_2.setText(_translate("Dialog", "已执行内容"))
        self.label_3.setText(_translate("Dialog", "选择测试用例"))
        self.pushButton_chosefile.setText(_translate("Dialog", "选择测试用例"))
        self.pushButton_starttest.setText(_translate("Dialog", "开始测试"))
        self.pushButton_stoptest.setText(_translate("Dialog", "停止测试"))
        self.radioButton.setText(_translate("Dialog", "重复测试"))
        self.label_4.setText(_translate("Dialog", "重复次数"))

    def chose_file(self):
        title = "选择测试用例表格"  # 对话框标题
        time.sleep(0.1)
        self.pushButton_starttest.setEnabled(False)
        self.pushButton_chosefile.setEnabled(False)
        self.radioButton.setEnabled(False)
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.comboBox.setEnabled(False)
        try:
            file = QtWidgets.QFileDialog.getOpenFileName(caption=title)[0]
            self.lineEdit.setText(file)
            self.comboBox.clear()
            self.comboBox.setEnabled(True)
            sheet_list = list(pd.read_excel(file, sheet_name=None))
            for i in sheet_list:
                self.comboBox.addItem(i)
        except Exception as error:
            print(error)
            pass
        time.sleep(0.1)
        self.pushButton_starttest.setEnabled(True)
        self.pushButton_chosefile.setEnabled(True)
        self.radioButton.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.comboBox.setEnabled(True)

    # 开始标志：UI star里面 发UI_START_FLAG
    # 停止标志：UI star里面 发UI_STOP_FLAG
    # 测试完成标志： 业务里面发 TEST_DENE_FLAG
    def start_test(self):
        # 拆分成两个函数，一个单次 一个循环？
        if self.lineEdit.text() == '':
            pass
        else:
            # 生成log和report文件夹
            try:
                if not os.path.exists(os.path.join("./", 'log')):
                    os.makedirs(os.path.join("./", 'log'))
                else:
                    print('The log directory already exists.')
                if not os.path.exists(os.path.join("./", 'report')):
                    os.makedirs(os.path.join("./", 'report'))
                else:
                    print('The report directory already exists.')
            except Exception as e:
                print(e)

            time.sleep(0.1)
            self.pushButton_starttest.setEnabled(False)
            self.pushButton_chosefile.setEnabled(False)
            self.radioButton.setEnabled(False)
            self.lineEdit.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
            self.comboBox.setEnabled(False)
            start_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
            file = os.path.basename(self.lineEdit.text()).split('.')[0] + start_time
            self.log = open('./log/' + file + '.log', '+a')

            time.sleep(0.1)
            # 启动命令运行log刷新输出界面进程
            self.running_log_thread()
            # 启动测试状态刷新输出界面进程
            self.test_status_thread()
            self.textBrowser.clear()
            self.listWidget.clear()
            self.status_queue.put('UI_START_FLAG')

            # 重复测试部分功能
            if self.radioButton.isChecked():
                if self.lineEdit_2.text() != '':
                    self.cycle_time = int(self.lineEdit_2.text())
                else:
                    self.cycle_time = -1
            else:
                self.cycle_time = 1
            self.test = AutoRegressionTestTool_test.TestPerform(self.lineEdit.text(), self.sheet_name, self.cycle_time, self.msg_queue,self.status_queue)
            self.start_ = Thread(target=self.test.case_run, args=())
            self.start_.start()

    def stop_test(self):
        if self.lineEdit.text() == '':
            pass
        else:
            self.status_queue.put('UI_STOP_FLAG')
            self.test.test_done_flag()
            time.sleep(0.5)
            self.pushButton_starttest.setEnabled(True)
            self.pushButton_chosefile.setEnabled(True)
            self.radioButton.setEnabled(True)
            self.lineEdit.setEnabled(True)
            self.lineEdit_2.setEnabled(True)
            self.comboBox.setEnabled(True)
            self.log.close()
            self.start_.join(0.1)
            time.sleep(0.5)
            # 清空消息队列
            while self.status_queue.qsize() != 0:
                self.status_queue.get()
            while self.msg_queue.qsize() != 0:
                self.msg_queue.get()

    # 获取下拉列表活动状态
    def sheet_value(self, sheet):
        self.sheet_name = sheet

    def running_log_thread(self):
        running_log_thread = Thread(target=self.running_log,args=())
        running_log_thread.start()

    def test_status_thread(self):
        test_status_thread = Thread(target=self.test_status,args=())
        test_status_thread.start()

    def running_log(self):
        while True:
            # 减少资源占用
            time.sleep(0.1)
            queue_log = self.msg_queue.get()
            self.textBrowser.append(queue_log)
            self.textBrowser.moveCursor(self.textBrowser.textCursor().End)
            try:
                self.log.write(queue_log + '\n')
            except ValueError:
                break

    def test_status(self):
        while True:
            time.sleep(0.1)
            queue_status = self.status_queue.get()
            # 测试状态标志
            if queue_status == 'UI_START_FLAG':
                print('UI_START_FLAG')
            elif queue_status == 'UI_STOP_FLAG':
                print('UI_STOP_FLAG')
            # 后面环境因素或者奇怪的跑脚本失败要做新的处理，目前暂时跟测试完成一样处理
            elif queue_status == 'TEST_FAIL_FLAG':
                print('TEST_FAIL_FLAG')
                self.stop_test()
            elif queue_status == 'TEST_FINISH_FLAG':
                print('TEST_FINISH_FLAG')
                self.stop_test()
            else:
                index = self.listWidget.currentRow() + 1
                self.listWidget.addItem(queue_status)
                if 'pass' in queue_status:
                    self.listWidget.item(index).setBackground(QColor('#7FFF11'))
                elif 'fail' in queue_status:
                    self.listWidget.item(index).setBackground(QColor('red'))
                self.listWidget.setCurrentRow(self.listWidget.currentRow()+1)
                # 用来停打印
                try:
                    self.log.write('')
                except ValueError:
                    break
