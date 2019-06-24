
# 解析用户输入的参数,并调用相应的功能
class ArgvHandler(object):
    def __init__(self ,sys_args):
        self.sys_args = sys_args

    # 打印帮助信息，不管是提醒用户输入，还是用户输入错误的指示信息都是在这个函数里边处理的。
    def help_msg(self ,error_msg=''):
        msgs = """
            %s
            run    启动用户交互程序
            """ % error_msg
        exit()

    # 根据用户参数，调用对应的方法
    def call(self):
        if len(self.sys_args) == 1:
            self.help_msg()
        # 用户要调用的方法名肯定是argv[1]，后边跟着的是参数。这是语法规则。
        if hasattr(self ,self.sys_args[1]):
            func = getattr(self ,self.sys_args[1])
            func()
        else:
            self.help_msg("没有方法:%s "% self.sys_args[1])


    def run(self):
        # 创建一个SshHandler对象，调用它的interactive方法。
        from  backend.ssh_interactive import SshHandler
        obj = SshHandler(self)
        obj.interactive()

