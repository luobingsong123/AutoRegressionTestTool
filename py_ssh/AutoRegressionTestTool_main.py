import os
import time
from subprocess import call
from time import sleep

import pandas as pd
import paramiko



class PyShell(object):
    def __init__(self, queue, **kwargs):
        # self.case = kwargs['用例名']
        # self.step = kwargs['步骤']
        self.msg_log = queue
        self.comments = kwargs['说明']
        self.server = kwargs['服务器']
        self.user = kwargs['用户名']
        self.password = str(kwargs['密码'])
        self.shell_str_mod = str(kwargs['发送模式'])
        if self.shell_str_mod == '1':
            self.shell_str = kwargs['发送命令'].split('|')
        else:
            self.shell_str = [(kwargs['发送命令'])]
        self.wait_str = kwargs['等待回显'].split('|')
        self.wait_time = kwargs['刷新间隔']
        self.timeout = kwargs['超时时间']
        self.fail_str = kwargs['失败回显'].split('|')
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
                time.sleep(0.1)
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
        cmd += ''
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
        try:
            # print('transport 连接断开')
            self.transport.close()
        except AttributeError as error:
            print(error)


# 测试执行主要逻辑代码
class TestPerform(object):
    def __init__(self, filename, sheet_name, retest_time, queue1, queue2, delay_time):
        self.filename = filename
        self.sheet_name = sheet_name
        self.ret = retest_time
        self.retest_time = retest_time
        self.queue_log = queue1
        self.queue_status = queue2
        self.test_data_dict = {}
        self.case_index = []
        self.case_step_dict = {}
        # 获取用例内容
        self.case_read()
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
                self.queue_log.put(
                    '延时开始测试,现在不开始测试，' + str(self.delay_time) + '分钟后开始测试' + '\n')
                self.queue_log.put(time.strftime("当前时间：%Y-%m-%d %H:%M:%S\n", time.localtime()))
                sleep(self.delay_time * 60)
            while self.retest_time != 0:
                self.start_time = time.strftime("%Y%m%d %H：%M：%S", time.localtime())
                self.queue_status.put('开测时间:' + self.start_time + '  第' + str(self.ret - self.retest_time) + '次测试')
                for case in self.case_index:
                    # case内操作
                    class_list = {0:[]}
                    self.report_xlsx = os.path.basename(self.filename).split('.')[0] + self.start_time
                    self.queue_log.put(
                        '开始测试用例: %s , %s\n' % (case, self.start_time))
                    step_no = 0
                    # 加一步连接复用
                    for step in self.case_step_dict[case]:
                        # step的ssh初始化
                        # 判断一下step里面的连接复用标志，如果大于1则复用，否则不复用
                        # print(self.test_data_dict[case][step])
                        step_connect_reuse = self.test_data_dict[case][step]['连接复用']
                        if step_connect_reuse == 0:
                            step_init = PyShell(self.queue_log, **self.test_data_dict[case][step])  # 如果是连服务器，则传递字典进去
                            class_list[0].append(step_init)
                            step_init.connect()
                            # step执行,执行完后返回结果
                            self.step_result[self.case_step_dict[case][step_no]] = step_init.start_test()
                        else:
                            # 如果连接存在，则不用再连接
                            # 如果连接不存在，则先连接，再跑用例命令
                            if step_connect_reuse not in class_list.keys():
                                step_init = PyShell(self.queue_log, **self.test_data_dict[case][step])
                                class_list[step_connect_reuse]=step_init
                                step_init.connect()
                                self.step_result[self.case_step_dict[case][step_no]] = step_init.start_test()
                            else:
                                # 如果连接存在，则不用再连接,执行属性数据初始化
                                # class_list[step_connect_reuse].__init__(self,self.queue_log, **self.test_data_dict[case][step])
                                class_list[step_connect_reuse].comments = self.test_data_dict[case][step]['说明']
                                class_list[step_connect_reuse].server = self.test_data_dict[case][step]['服务器']
                                class_list[step_connect_reuse].user = self.test_data_dict[case][step]['用户名']
                                class_list[step_connect_reuse].password = str(self.test_data_dict[case][step]['密码'])
                                class_list[step_connect_reuse].shell_str_mod = str(self.test_data_dict[case][step]['发送模式'])
                                if class_list[step_connect_reuse].shell_str_mod == '1':
                                    class_list[step_connect_reuse].shell_str = self.test_data_dict[case][step]['发送命令'].split('|')
                                else:
                                    class_list[step_connect_reuse].shell_str = [(self.test_data_dict[case][step]['发送命令'])]
                                class_list[step_connect_reuse].wait_str = self.test_data_dict[case][step]['等待回显'].split('|')
                                class_list[step_connect_reuse].wait_time = self.test_data_dict[case][step]['刷新间隔']
                                class_list[step_connect_reuse].timeout = self.test_data_dict[case][step]['超时时间']
                                class_list[step_connect_reuse].fail_str = self.test_data_dict[case][step]['失败回显'].split('|')
                                time.sleep(0.5)
                                # step执行,执行完后返回结果
                                self.step_result[self.case_step_dict[case][step_no]] = class_list[step_connect_reuse].start_test()
                        sleep(0.2)
                        result = self.step_result.get(self.case_step_dict[case][step_no])
                        if result is not None and result[0]:
                            self.queue_status.put(str(case) + '   ' + self.case_step_dict[case][step_no] + '   ' + 'pass')
                        else:
                            self.queue_status.put(str(case) + '   ' + self.case_step_dict[case][step_no] + '   ' + 'fail')
                        step_no += 1
                        # # 增加用例间间隔，为清输出窗口留出时间
                        # self.test_clear_flag()
                        # sleep(2)
                    # STEP执行完成后断开ssh连接
                    # print('case:',class_list)
                    for keys in class_list.keys():
                        if keys == 0:
                            for i in range(len(class_list[keys])):
                                # print(class_list[keys][i])
                                class_list[keys][i].close()
                        else:
                            class_list[keys].close()
                    self.end_time = time.strftime("%Y%m%d %H：%M：%S", time.localtime())
                    self.queue_log.put('当前用例执行完成: %s , %s\n' % (case, self.end_time))
                    self.case_result[case] = self.step_result
                    self.step_result = {}
                    sleep(0.1)
                self.test_result()
                self.retest_time -= 1
                sleep(1)
            self.test_done_flag()
            sleep(1)
        except ValueError as error:
            print(error)
            pass

    def case_read(self):
        """
        读取用例内容  用例名  用例步骤  用例内容
        """
        try:
            df = pd.read_excel(self.filename, sheet_name=self.sheet_name)
        except ValueError as error:
            self.queue_log.put('用例表格异常，请检查！\n')
            self.queue_log.put(error)
            self.queue_status.put('TEST_FAIL_FLAG')
            return
        for i in df.index.values:  # 获取行号的索引，并对其进行遍历：   # 用例步骤有重复内容的话会有异常，但目前没有出现报错
            try:
                # 根据i来获取每一行指定的数据 并利用to_dict转成字典
                read_case = df.loc[i, ['用例名', ]].to_list()
                read_step = df.loc[i, ['步骤', ]].to_list()
                content = df.loc[
                    i, ['说明', '服务器', '用户名', '密码', '发送命令', '发送模式', '等待回显', '刷新间隔',
                        '超时时间', '失败回显', '连接复用']].to_dict()
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
                self.queue_log.put('用例表格内容有误，请检查！\n')
                self.queue_log.put(KeyError_msg)
                self.queue_status.put('TEST_FAIL_FLAG')
                break
        # 创建一个带表头的全局xlsx
        # self.df = pd.DataFrame({'test_case', 'test_step', 'test_result','test_comments'})
        # 还要一个计数，行的计数,从1开始，不算表头
        # self.df_row = 1

    # 输出测试结果
    def test_result(self):
        """
        :return: 生成测试报告
        """
        test_case = []
        test_case_result = {}
        test_step = []
        test_result = []
        test_comments = []
        test_pass = 0
        test_fail = 0
        for k in self.case_result.keys():
            for j in self.case_result[k].keys():
                test_case.append(k)
                test_step.append(j)
                if self.case_result[k][j][0]:
                    test_result.append('pass')
                    test_case_result[k] = True
                else:
                    test_result.append('fail')
                    test_case_result[k] = False
                test_comments.append(self.case_result[k][j][1])
            if test_case_result[k]:
                test_pass += 1
            else:
                test_fail += 1
        df = pd.DataFrame({'test_case': test_case, 'test_step': test_step, 'test_result': test_result,
                           'test_comments': test_comments})
        # 报告格式&着色相关
        # df_style = df.style.applymap(lambda x: 'background-color:green' if test_result == 'pass' else 'background-color:red', subset=['test_result'])
        # writer = pd.ExcelWriter('./report/' + self.report_xlsx + '.xlsx',)
        # df_style.to_excel(writer,sheet_name='Sheet1', index=False)
        # writer.save()
        df.to_excel('./report/' + self.report_xlsx + '.xlsx',index=False)
        # 输出html格式报告
        f = open('./report/' + self.report_xlsx + '.html', 'a')
        message = """
        <html>
        <head></head>
        <body>
        <p> </p>
        <p>测试用例&路径：%s</p>
        <p>测试用例表：%s</p>
        <p> </p>
        <p> </p>
        <p>测试开始时间：%s</p>
        <p>测试结束时间：%s</p>
        <p> </p>
        <p> </p>
        <p>执行测试用例数：%s</p>
        <p>测试通过用例数：%s</p>
        <p>测试不通过用例数：%s</p>
        <p> </p>
        <p> </p>
        <p>测试用例执行状态：</p>
        </body>
        </html>
        """ % (self.filename, self.sheet_name,self.start_time,self.end_time,len(self.case_result.keys()),test_pass,test_fail)
        f.write(message)
        f.write(df.to_html())
        f.close()

    def test_done_flag(self):
        # 用例执行完成标志
        self.queue_status.put('TEST_FINISH_FLAG')

    def test_clear_flag(self):
        # 用例执行完成标志
        self.queue_log.put('CLEAR_FLAG\n')
