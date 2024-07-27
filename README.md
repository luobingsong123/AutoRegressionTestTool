# AutoRegressionTestTool
运行说明：
1.新建python 3.x版本工程
2.把所有.py文件添加到工程
3.安装好用到的库
4.运行AutoRegressionTestTool.py可看到操作界面
其他内容：
1.打包成.exe参考命令：pyinstaller -F AutoRegressionTestTool.py --noconsole
2.如果有调试问题的疑难杂症可以把所有异常处理都打印出来，目前出现的异常部分都是不执行任何操作
目前测试能运行用力的对应库版本清单：
Package         Version
--------------- -----------
bcrypt          4.2.0
cffi            1.16.0
cryptography    43.0.0
et-xmlfile      1.1.0
numpy           2.0.1
openpyxl        3.1.5
pandas          2.2.2
paramiko        3.4.0
pip             23.2.1
pycparser       2.22
PyNaCl          1.5.0
PyQt5           5.15.11
PyQt5-Qt5       5.15.2
PyQt5_sip       12.15.0
python-dateutil 2.9.0.post0
pytz            2024.1
six             1.16.0
tzdata          2024.1


