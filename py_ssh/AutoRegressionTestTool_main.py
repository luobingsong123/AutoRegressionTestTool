import os
from subprocess import call
from time import sleep,localtime,strftime
import paramiko


class PyShell(object):
    def __init__(self, queue, **kwargs):
        # self.case = kwargs['用例名']
        # self.step = kwargs['步骤']
        self.msg_log = queue
        self.comments = str(kwargs['说明'])
        self.server = kwargs['服务器']
        self.user = str(kwargs['用户名'])
        self.password = str(kwargs['密码'])
        self.shell_str = [(kwargs['发送命令'])]
        self.wait_str = str(kwargs['等待回显']).split('|')
        self.wait_time = kwargs['刷新间隔']
        self.timeout = kwargs['超时时间']
        self.fail_str = str(kwargs['失败回显']).split('|')
        # transport和channel
        self.transport = ''
        self.channel = ''
        # 链接失败的重试次数
        self.try_times = 1
        self.connet_type = True

    # 连接远程主机
    def connect(self):
        while True:
            # 连接过程中可能会抛出异常，比如网络不通、链接超时
            if self.server == 'cmd':
                self.msg_log.put('执行本地cmd命令\n')
                return
            try:
                self.transport = paramiko.Transport(sock=(self.server, 22))
                self.transport.connect(username=self.user, password=self.password)
                self.channel = self.transport.open_session()
                self.channel.settimeout(self.timeout)
                self.channel.get_pty()
                self.channel.invoke_shell()  # 伪终端方法，命令执行后连接不会重置
                # 如果没有抛出异常说明连接成功，直接返回
                self.msg_log.put('连接%s成功\n' % self.server)
                sleep(0.1)
                # 接收到的网络数据解码为str
                return
            # 直接返回失败不定位
            except Exception:
                if self.try_times != 0:
                    self.msg_log.put('连接%s失败，正在重新连接\n' % self.server)
                    self.try_times -= 1
                else:
                    self.msg_log.put('连接服务器失败，请检查用户名密码是否正确，目标服务器是否在线。\n')
                    self.connet_type = False
                    return self.connet_type
                    # exit(1)     # 直接退出了程序

    # 发送要执行的命令
    def send(self, cmd):
        if 'CTRL+C' in cmd:
            cmd = '\x03'
        result = ''
        # 发送要执行的命令
        self.channel.send(cmd)
        # 回显很长的命令可能执行较久，通过循环分批次取回回显,执行成功返回true,失败返回false
        while True:
            sleep(0.01)
            recv_cache = self.channel.recv(-1)
            try:
                ret = recv_cache.decode('utf-8')
            except UnicodeDecodeError:
                ret = str(recv_cache)
            result += ret
            return result.replace('\r\n', '\n')

    # 启动命令下发&回显匹配 // 执行windows本地bat脚本
    def start_test(self):
        # 已经连上服务器标志
        try:
            if self.connet_type:
                times = 0
                result = ''
                # 发送命令
                if self.server == 'cmd':
                    # 执行本地标志
                    # 执行之后返回ture
                    # 默认pass
                    # 文件不存在则返回fail
                    # 执行脚本后等待 wait_time
                    # bat脚本名和路径都放到命令里
                    try:
                        call(self.shell_str)
                        self.msg_log.put(self.shell_str)
                        return True, self.comments + ' pass'
                    except FileNotFoundError as error:
                        print(error)
                        self.msg_log.put(error)
                        return False, self.comments + ' fail'
                else:
                    for i in self.shell_str:
                        result = self.send(i+'\n')
                        self.msg_log.put(result)
                    # 判断回显
                    while times < self.timeout:
                        for wait_str in self.wait_str:
                            if wait_str in result:
                                return True, self.comments + ' pass'
                        for fail_str in self.fail_str:
                            if fail_str in result:
                                return False, self.comments + ' fail'
                        wait_time = 0
                        while wait_time < self.wait_time:
                            times += 1
                            wait_time += 1
                            sleep(0.9)
                        result = self.send('')
                        self.msg_log.put(result)
                    return False, self.comments + ' timeout'
            else:
                return False, self.comments + ' server is offline'
        except OSError as error:
            print(error)
            self.msg_log.put('OSError: Socket is closed\n')
            self.msg_log.put('连接已断开\n')
            return False, self.comments + ' OSError: Socket is closed'

    # 断开连接
    def close(self):
        try:
            # print('channel 连接断开')
            self.channel.close()
        except AttributeError as error:
            print(error)


# 测试执行主要逻辑代码
class TestPerform(object):
    def __init__(self, filename, sheet_name, retest_time, queue1, queue2, delay_time,test_data_dict,case_index,case_step_dict):
        self.filename = filename
        self.sheet_name = sheet_name
        self.ret = retest_time
        self.retest_time = retest_time
        self.queue_log = queue1
        self.queue_status = queue2
        self.test_data_dict = test_data_dict
        self.case_index = case_index
        self.case_step_dict = case_step_dict
        # 获取用例内容 改到UI那边线程获取了，后面报告也直接走UI那边落
        # self.case_read()
        self.case_result = {}
        self.step_result = {}
        self.delay_time = delay_time

    def case_run(self):
        try:
            self.queue_log.put('测试用例&路径：' + self.filename + '\n')
            self.queue_log.put('测试用例表名：' + self.sheet_name + '\n')
            # self.queue_log.put('重复测试次数：' + str(self.retest_time))
            # for循环根据case-step进行类初始化，每次把所有step的ssh都先连接上，再进行操作；
            # 后续改进增加连接复用，多step后台识别
            # 执行测试部分
            if self.delay_time != 0:
                self.queue_log.put('延时开始测试,现在不开始测试，' + str(self.delay_time) + '分钟后开始测试' + '\n')
                self.queue_log.put(strftime("当前时间：%Y-%m-%d %H:%M:%S\n", localtime()))
                sleep(self.delay_time * 60)
            while self.retest_time != 0:
                self.start_time = strftime("%Y%m%d %H：%M：%S", localtime())
                self.queue_status.put('------------------------------------------------------------')
                self.queue_status.put('-------------------重复执行测试分隔线-------------------')
                self.queue_status.put('开测时间:' + self.start_time + '  第' + str(self.ret - self.retest_time) + '次测试')
                for case in self.case_index:
                    # case内操作
                    self.queue_status.put('----------------------测试用例分隔线---------------------')
                    self.queue_status.put('当前用例:' + str(case) + '\n开始时间:' + self.start_time)
                    self.class_list = {0:[]}
                    self.report_xlsx = os.path.basename(self.filename).split('.')[0] + self.start_time
                    self.queue_log.put('开始测试用例: %s , %s\n' % (case, self.start_time))
                    step_no = 0
                    # 加一步连接复用
                    for step in self.case_step_dict[case]:
                        self.queue_status.put(step + '   ' + str(self.test_data_dict[case][step]['说明']) + '   ' + 'running')
                        # step的ssh初始化
                        # 判断一下step里面的连接复用标志，如果大于1则复用，否则不复用
                        # print(self.test_data_dict[case][step])
                        step_connect_reuse = self.test_data_dict[case][step]['连接复用']
                        if step_connect_reuse == 0 or step_connect_reuse == 'Non':
                            self.step_init = PyShell(self.queue_log, **self.test_data_dict[case][step])  # 如果是连服务器，则传递字典进去
                            self.class_list[0].append(self.step_init)
                            self.step_init.connect()
                            # step执行,执行完后返回结果
                            self.step_result[self.case_step_dict[case][step_no]] = self.step_init.start_test()
                        else:
                            # 如果连接存在，则不用再连接
                            # 如果连接不存在，则先连接，再跑用例命令
                            if step_connect_reuse not in self.class_list.keys():
                                self.step_init = PyShell(self.queue_log, **self.test_data_dict[case][step])
                                self.class_list[step_connect_reuse]=self.step_init
                                self.step_init.connect()
                                self.step_result[self.case_step_dict[case][step_no]] = self.step_init.start_test()
                            else:
                                # 如果连接存在，则不用再连接,执行属性数据初始化
                                # 2024.8.15 不记得这块有什么用了o。O
                                # self.class_list[step_connect_reuse].__init__(self,self.queue_log, **self.test_data_dict[case][step])
                                self.class_list[step_connect_reuse].comments = self.test_data_dict[case][step]['说明']
                                self.class_list[step_connect_reuse].server = self.test_data_dict[case][step]['服务器']
                                self.class_list[step_connect_reuse].user = self.test_data_dict[case][step]['用户名']
                                self.class_list[step_connect_reuse].password = str(self.test_data_dict[case][step]['密码'])
                                self.class_list[step_connect_reuse].shell_str = [(self.test_data_dict[case][step]['发送命令'])]
                                self.class_list[step_connect_reuse].wait_str = self.test_data_dict[case][step]['等待回显'].split('|')
                                self.class_list[step_connect_reuse].wait_time = self.test_data_dict[case][step]['刷新间隔']
                                self.class_list[step_connect_reuse].timeout = self.test_data_dict[case][step]['超时时间']
                                self.class_list[step_connect_reuse].fail_str = self.test_data_dict[case][step]['失败回显'].split('|')
                                sleep(0.5)
                                # step执行,执行完后返回结果
                                self.step_result[self.case_step_dict[case][step_no]] = self.class_list[step_connect_reuse].start_test()
                        result = self.step_result.get(self.case_step_dict[case][step_no])
                        if result is not None and result[0]:
                            self.queue_status.put(step + '   ' + str(self.test_data_dict[case][step]['说明']) + '   ' + 'pass')
                        else:
                            self.queue_status.put(step + '   ' + str(self.test_data_dict[case][step]['说明']) + '   ' + 'fail')
                        step_no += 1
                    # STEP执行完成后断开ssh连接
                    # print('case:',self.class_list)
                    self.close_all_ssh()
                    self.case_done_flag()
                    self.end_time = strftime("%Y%m%d %H：%M：%S", localtime())
                    self.queue_log.put('当前用例执行完成: %s , %s\n' % (case, self.end_time))
                    self.case_result[case] = self.step_result
                    self.step_result = {}
                    sleep(1)
                # self.test_result()
                self.retest_time -= 1
            self.test_done_flag()
        except ValueError as error:
            print(error)
            pass

    # 输出测试结果


    def test_done_flag(self):
        # 用例执行完成标志
        self.queue_status.put('TEST_FINISH_FLAG')
        # 关闭所有ssh连接

    def case_done_flag(self):
        # 用例执行完成标志
        self.queue_status.put('CASE_FINISH_FLAG')

    def close_all_ssh(self):
        try:
            for keys in self.class_list.keys():
                if keys == 0:
                    for i in range(len(self.class_list[keys])):
                        # print(self.class_list[keys][i])
                        self.class_list[keys][i].close()
                else:
                    self.class_list[keys].close()
            self.step_init.close()
        except Exception as error:
            print('close_all_ssh:',error)
            pass