import base64
from binascii import hexlify
import getpass
import os
import select
import socket
import sys
import time
import traceback
from paramiko.py3compat import input

import paramiko
try:
    import interactive
except ImportError:
    from . import interactive


def manual_auth(t,hostname,username, password):
    default_auth = 'p'
    #auth = input('Auth by (p)assword, (r)sa key, or (d)ss key? [%s] ' % default_auth)
    # if len(auth) == 0:
    #     auth = default_auth
    auth = default_auth
    if auth == 'r':
        default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
        path = input('RSA key [%s]: ' % default_path)
        if len(path) == 0:
            path = default_path
        try:
            key = paramiko.RSAKey.from_private_key_file(path)
        except paramiko.PasswordRequiredException:
            password = getpass.getpass('RSA key password: ')
            key = paramiko.RSAKey.from_private_key_file(path, password)
        t.auth_publickey(username, key)
    elif auth == 'd':
        default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_dsa')
        path = input('DSS key [%s]: ' % default_path)
        if len(path) == 0:
            path = default_path
        try:
            key = paramiko.DSSKey.from_private_key_file(path)
        except paramiko.PasswordRequiredException:
            password = getpass.getpass('DSS key password: ')
            key = paramiko.DSSKey.from_private_key_file(path, password)
        t.auth_publickey(username, key)
    else:
        #pw = getpass.getpass('Password for %s@%s: ' % (username, hostname))
        t.auth_password(username, password)

#创建ssh连接的socket，并进行连接。
def ssh_connect(ssh_handler_instance,host_to_user_obj):
    #从传进来的对象中拿到ip地址和port（外键引用Host表）；拿到username和password（外键引用RemoteUser表）
    hostname = host_to_user_obj.host.ip_addr
    port = host_to_user_obj.host.port
    username = host_to_user_obj.remote_user.username
    password = host_to_user_obj.remote_user.password

    #创建连接的套接字。如果出错，返回异常。
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
    except Exception as e:
        print('*** Connect failed: ' + str(e))
        traceback.print_exc()
        sys.exit(1)

    try:
        t = paramiko.Transport(sock)
        try:
            t.start_client()
        except paramiko.SSHException:
            print('*** SSH negotiation failed.')
            sys.exit(1)
        # 把.ssh/known_hosts文件中的对应关系保存到字典结构中。
        try:
            keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                print('*** Unable to open host keys file')
                keys = {}

        # check server's host key -- this is important.
        key = t.get_remote_server_key()
        if hostname not in keys:
            print('*** WARNING: Unknown host key!')
        elif key.get_name() not in keys[hostname]:
            print('*** WARNING: Unknown host key!')
        elif keys[hostname][key.get_name()] != key:
            print('*** WARNING: Host key has changed!!!')
            sys.exit(1)
        else:
            print('*** Host key OK.')

        # 远程主机用户、密码认证，如果不成功，退出。
        if not t.is_authenticated():
            manual_auth(t,hostname,username, password)
        if not t.is_authenticated():
            print('*** Authentication failed. :(')
            t.close()
            sys.exit(1)
        # 远程主机账户、密码认证成功后，给ssh连接打开一个session，获得一个终端，开启一个shell。
        chan = t.open_session()
        chan.get_pty()
        chan.invoke_shell()

        # 把登录堡垒机的用户赋给chan。还要把models文件赋给chan，以及登录的主机和账户，
        # 用来审计，保存登录时信息，留作备份。
        chan.crazyeye_account = ssh_handler_instance.user
        chan.host_to_user_obj = host_to_user_obj
        chan.models = ssh_handler_instance.models

        print('*** Here we go!\n')
        ssh_handler_instance.models.AuditLog.objects.create(
            user = ssh_handler_instance.user ,
            log_type = 0 ,
            host_to_remote_user = host_to_user_obj,
            content = "***user login***"
        )
        # 调用interactive.py中的interactive_shell，在linux或者windows中使用不同的方法实际去连接远程
        interactive.interactive_shell(chan)
        chan.close()
        t.close()
        # 记录下用户退出时候的信息。
        ssh_handler_instance.models.AuditLog.objects.create(
            user=ssh_handler_instance.user,
            log_type=2,
            host_to_remote_user=host_to_user_obj,
            content="***user logout***"
        )

    except Exception as e:
        print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
        traceback.print_exc()
        try:
            t.close()
        except:
            pass
        sys.exit(1)


