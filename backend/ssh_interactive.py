from  django.contrib.auth import authenticate
from backend import paramiko_ssh
from web import models

#这个类主要处理用户和堡垒机进行交互的内容，并调用远程登录paramiko_ssh.py中的ssh_connect函数进行远程连接。
class SshHandler(object):

    #这个类包含了ArgvHandler类的一个实例，可以从中获取用户输入的参数信息。
    #把models文件的内容赋给SshHandler的models属性。
    def __init__(self,argv_handler_instance):
        self.argv_handler_instance = argv_handler_instance
        self.models = models

    #登录认证程序
    def auth(self):
        count = 0
        while count < 3:
            username = input("堡垒机账号:").strip()
            password = input("Password:").strip()
            #还是用django自带的认证模块。
            user = authenticate(username=username,password=password)
            if user:
                #把认证成功的用户保存到当前对象中。
                self.user = user
                return True
            else:
                count +=1

    #堡垒机启动时交互脚本,输入堡垒机账户和密码才能登录堡垒机。
    def interactive(self):
        #self.auth()返回True，表示用户认证成功，接着执行下边的操作。
        if self.auth():
            print("Ready to print all the authorized hosts...to this user ...")
            while True:
                #user是UserProfile的一个对象，代表一个堡垒机账户，通过它能取得所有和这个账户相关的远程主机组
                host_group_list = self.user.host_groups.all()
                for index,host_group_obj in enumerate(host_group_list):
                    print("%s.\t%s[%s]"%(index,host_group_obj.name, host_group_obj.host_to_remote_users.count()))
                #未分组的主机直接和堡垒机用户相关联的。调用QuerySet的count方法，统计和这个用户相关的主机有多少个。
                print("z.\t未分组主机[%s]" % (self.user.host_to_remote_users.count()))

                choice = input("请选择主机组>>:").strip()
                if choice.isdigit():
                    choice = int(choice)
                    selected_host_group = host_group_list[choice]
                elif choice == 'z':
                    selected_host_group = self.user

                #让用户选择主机。
                while True:
                    #HostGroup表和UserProfile表中都有host_to_remote_users这个字段，所以这里可以这么写。
                    for index,host_to_user_obj in enumerate(selected_host_group.host_to_remote_users.all()):
                        print("%s.\t%s" % (index, host_to_user_obj))

                    choice = input("请选择主机>>:").strip()
                    if choice.isdigit():
                        choice = int(choice)
                        selected_host_to_user_obj = selected_host_group.host_to_remote_users.all()[choice]
                        print("going to logon  %s" % selected_host_to_user_obj )
                        #确定用户选择了哪个主机，调用paramiko_ssh进行进一步操作
                        # 把当前SshHandler对象传进去，这里包含着堡垒机用户的信息；还有用户选择的主机
                        paramiko_ssh.ssh_connect(self, selected_host_to_user_obj )

                    #从主机选择界面回退到主机组选择界面。
                    if choice == "b":
                        break