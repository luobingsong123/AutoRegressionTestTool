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


if __name__ == '__main__':
    main()
