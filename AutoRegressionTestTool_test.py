import time
from time import sleep
import pandas as pd
import paramiko
import os


class PyShell(object):
    def __init__(self, queue, **kwargs):
        # self.case = kwargs['case']
        # self.step = kwargs['step']
        self.msg_log = queue
        self.comments = kwargs['comments']
        self.server = kwargs['server']
        self.user = kwargs['user']
        self.password = str(kwargs['password'])
        # self.shell_str = kwargs['shell_str'].split('|')
        self.shell_str_mod = str(kwargs['shell_str_mod'])
        if self.shell_str_mod == '1':
            self.shell_str = kwargs['shell_str'].split('|')
        else:
            self.shell_str = kwargs['shell_str']
        self.shell_str = kwargs['shell_str']
        self.wait_str = kwargs['wait_str'].split('|')
        self.wait_time = kwargs['wait_time']
        self.timeout = kwargs['timeout']
        self.fail_str = kwargs['fail_str'].split('|')
        # transport和channel
        self.transport = ''
        self.channel = ''
        # 链接失败的重试次数
        self.try_times = 3
        self.connet_type = True
        self.connect()

    # 调用该方法连接远程主机
    def connect(self):
        while True:
            # 连接过程中可能会抛出异常，比如网络不通、链接超时
            try:
                self.transport = paramiko.Transport(sock=(self.server, 22))
                self.transport.connect(username=self.user, password=self.password)
                self.channel = self.transport.open_session()
                self.channel.settimeout(self.timeout)
                self.channel.get_pty()
                self.channel.invoke_shell()  # 伪终端方法，命令执行后连接不会重置
                # 如果没有抛出异常说明连接成功，直接返回
                self.msg_log.put('连接%s成功' % self.server)
                # 接收到的网络数据解码为str
                # print(self.channel.recv(65535))
                return
            # 直接返回失败不定位
            except Exception:
                if self.try_times != 0:
                    self.msg_log.put('连接%s失败，正在重新连接' % self.server)
                    self.try_times -= 1
                else:
                    self.msg_log.put('连接服务器失败，请检查用户名密码是否正确，目标服务器是否在线。')
                    self.connet_type = False
                    return self.connet_type
                    # exit(1)     # 直接退出了程序

    # 发送要执行的命令
    def send(self, cmd):
        cmd += '\r'
        result = ''
        # 发送要执行的命令
        self.channel.send(cmd)
        # 回显很长的命令可能执行较久，通过循环分批次取回回显,执行成功返回true,失败返回false
        while True:
            sleep(0.5)
            ret = self.channel.recv(-1).decode('utf-8')
            result += ret
            return result

    # 启动命令下发&回显匹配
    def start_test(self):
        if self.connet_type:
            times = 0
            # 多命令;考虑下面while部分再搞个函数，这部分弄成递归，保证多命令下发时每个命令都有正常回显
            if type(self.shell_str) == list:
                for i in self.shell_str:
                    self.send(i)
                    sleep(0.5)
                result = self.send(self.shell_str)
            # 单命令
            else:
                result = self.send(self.shell_str)
            while times < self.timeout:
                for wait_str in self.wait_str:
                    if wait_str in result:
                        self.msg_log.put(result)
                        return True, self.comments + ' pass'
                for fail_str in self.fail_str:
                    if fail_str in result:
                        self.msg_log.put(result)
                        return False, self.comments + ' fail'
                self.msg_log.put(result)
                wait_time = 0
                while wait_time < self.wait_time:
                    times += 1
                    wait_time += 1
                    sleep(0.9)
                d = '\n'
                result = self.send(d)
                self.msg_log.put(result)
            return False, self.comments + ' timeout'
        else:
            return False, self.comments + ' server is offline'

    # 断开连接
    def close(self):
        try:
            self.channel.close()
            self.transport.close()
        except AttributeError:
            pass


# 测试执行主要逻辑代码
class TestPerform(object):
    def __init__(self, filename,sheet_name,queue1,queue2):
        self.filename = filename
        self.sheet_name = sheet_name
        self.queue_log = queue1
        self.queue_status = queue2
        self.test_data_dict = {}
        self.case_index = []
        self.case_step_dict = {}
        # 获取用例内容
        self.case_read()
        self.case_result = {}
        self.step_result = {}
        self.start_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
        self.file_xlsx = os.path.basename(self.filename).split('.')[0] + self.start_time

    def case_run(self):
        self.queue_log.put('测试用例&路径：' + self.filename)
        self.queue_log.put('测试用例表名：' + self.sheet_name)
        # for循环根据case-step进行类初始化，每次把所有step的ssh都先连接上，再进行操作；
        # 执行测试部分
        for case in self.case_index:
            # case内操作
            class_list = []
            self.queue_log.put('START TESTING CASE: %s , %s' % (case,time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())))
            for step in self.case_step_dict[case]:
                # step的ssh初始化
                step_init = PyShell(self.queue_log,**self.test_data_dict[case][step])  # 传递字典进去
                class_list.append(step_init)
            for i in range(len(self.case_step_dict[case])):
                # 执行step操作
                self.step_result[self.case_step_dict[case][i]] = class_list[i].start_test()
                sleep(0.5)
            # STEP执行完成后断开ssh连接
            for i in range(len(self.case_step_dict[case])):
                class_list[i].close()
            self.queue_log.put('CASE ENDING: %s , %s' % (case,time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())))
            self.case_result[case] = self.step_result
            self.step_result = {}
            sleep(0.5)
        # 输出测试结果
        self.test_result()

    def case_read(self):
        df = pd.read_excel(self.filename,sheet_name=self.sheet_name)  # 读取xlsx中第一个sheet
        for i in df.index.values:   # 获取行号的索引，并对其进行遍历：
            try:
                # 根据i来获取每一行指定的数据 并利用to_dict转成字典
                read_case = df.loc[i,['case', ]].to_list()
                read_step = df.loc[i,['step', ]].to_list()
                content = df.loc[i,['comments', 'server', 'user', 'password', 'shell_str', 'shell_str_mod', 'wait_str', 'wait_time', 'timeout', 'fail_str']].to_dict()
                # case名称做键，step做值，剩下的东西做step里的子键值
                try:
                    self.test_data_dict[read_case[0]][read_step[0]] = content
                except KeyError:
                    self.test_data_dict[read_case[0]] = {read_step[0]: content}
                # 按表格顺序获取case,去掉重复case,作为case索引 case_index
                if read_case[0] not in self.case_index:
                    self.case_index.append(read_case[0])
                # step字典,case_step_dict
                try:
                    self.case_step_dict[read_case[0]].append(read_step[0])
                except KeyError:
                    self.case_step_dict[read_case[0]] = [read_step[0]]
            except KeyError as KeyError_msg:
                self.queue_log.put('用例表格内容有误，请检查！')
                self.queue_log.put(KeyError_msg)

    # 输出测试结果为表格
    def test_result(self):
        test_case = []
        test_step = []
        test_result = []
        test_comments = []
        for k in self.case_result.keys():
            for j in self.case_result[k].keys():
                self.queue_log.put(
                    f'TEST CASE {k} : STEP {j} RESULT {self.case_result[k][j][0]}, TEST COMMENTS : {self.case_result[k][j][1]}')
                test_case.append(k)
                test_step.append(j)
                if self.case_result[k][j][0]:
                    test_result.append('pass')
                else:
                    test_result.append('fail')
                test_comments.append(self.case_result[k][j][1])
        df = pd.DataFrame({'test_case': test_case, 'test_step': test_step, 'test_result': test_result,
                           'test_comments': test_comments})
        df.to_excel(self.file_xlsx + '.xlsx')


# 把这堆的位置搞好就可以了
# if __name__ == '__main__':
#     # app = QApplication(sys.argv)
#     # MainWindow = QMainWindow()
#     # window = AutoRegressionTestTool_ui.Ui_Dialog()
#     # window.setupUi(MainWindow)
#     # MainWindow.show()
#     # sys.exit(app.exec_())
#     # k = Entrance(r'C:\Users\DELL\Desktop\测试交付\实验室CPU状态.xlsx')
#     # k.entrance()
#
#     # 这部分可以放到主函数声明
#     queue_log = Queue()  # 创建log队列
#     queue_status = Queue()  # 测试状态队列
#     log_queue = ResultPush(queue_log)   # 实例化LOG上传消息队列，用于传入函数调用
#     status_queue = ResultPush(queue_status)   # 实例化测试状态队列，用于传入函数调用
#
#     # 这部分在GUI点击里面增加
#     file_name = r'C:\Users\DELL\Desktop\测试交付\demo测试用用例￥.xlsx'
#     datetime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
#     file = os.path.basename(file_name).split('.')[0] + datetime
#
#     # 这部分也可以在GUI点击里面增加
#     # 实例化打印和写log类
#     log = Logging(file + '.log',queue_log,queue_status)
#     # 写log方法做一个进程
#     log_thread = Thread(target=log.log_print, args=())
#     log_thread.start()
#     # 写status做一个进程
#     status_thread = Thread(target=log.status, args=())
#     status_thread.start()
#     # 实例化测试用例
#     auto_test = TestPerform(file_name,log_queue,status_queue)
#     # 执行测试用例
#     auto_test.case_run()
#     # 测试完成后，关闭log
#     log.file_log.close()

