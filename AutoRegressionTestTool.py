import faulthandler
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui import AutoRegressionTestTool_ui
import traceback


def main():
    faulthandler.enable()
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    main_ui = AutoRegressionTestTool_ui.Ui_Dialog()
    main_ui.setupUi(MainWindow)
    MainWindow.show()
    app.exec_()


'''
先在UI加个失败停止/报告生成选项
todo:
1.main拆成两个，一个ssh库，一个测试执行库
2.UI拆成两个，一个是ssh库的UI，一个是测试执行库的UI
3.新增个log库，用于记录日志和生成报告，日志文件大于100M时自动备份,LOG也放在ui这边记录。
4.库的文件夹名称要更新一下
5.加个打开日志路径/报告路径的按钮
'''

if __name__ == '__main__':
    try:
        main()
    except Exception:
        print("出现未知错误：", traceback.format_exc())
        input("请复制内容或截图保存通知开发人员！"
              "按任意键退出...")
        sys.exit(1)

