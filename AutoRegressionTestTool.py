import faulthandler
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui import AutoRegressionTestTool_ui


def main():
    faulthandler.enable()
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    main_ui = AutoRegressionTestTool_ui.Ui_Dialog()
    main_ui.setupUi(MainWindow)
    MainWindow.show()
    app.exec_()

'''
todo:
1.main拆成两个，一个ssh库，一个测试执行库
2.UI拆成两个，一个是ssh库的UI，一个是测试执行库的UI
3.新增个log库，用于记录日志和生成报告，日志文件大于100M时自动备份
4.库的文件夹名称要更新一下
'''

if __name__ == '__main__':
    main()

