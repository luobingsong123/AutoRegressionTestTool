import sys
from PyQt5.QtWidgets import *
from ui import AutoRegressionTestTool_ui

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    window = AutoRegressionTestTool_ui.Ui_Dialog()
    window.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
