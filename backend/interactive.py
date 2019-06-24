import socket
import sys
import time
from paramiko.py3compat import u
import tty
import termios


# windows does not have termios...
# try:
#     import termios
#     import tty
#     has_termios = True
# except ImportError:
#     has_termios = False


# def interactive_shell(chan):
#     if has_termios:
#         posix_shell(chan)
#     else:
#         return False


def interactive_shell(chan):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)
        cmd = []
        # f = open('ssh_test.log','w')
        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = u(chan.recv(1024))
                    if len(x) == 0:
                        sys.stdout.write('\r\n*** EOF\r\n')
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                if x == '\r':
                    print('input>', ''.join(cmd))
                    # log = "%s   %s\n" %(time.strftime("%Y-%m-%d %X", time.gmtime()), ''.join(cmd))
                    # 记录下用户在远程主机上进行的操作。
                    chan.models.AuditLog.objects.create(
                        user=chan.crazyeye_account,
                        log_type=1,
                        host_to_remote_user=chan.host_to_user_obj,
                        content=''.join(cmd)
                    )
                    # f.write(log)
                    cmd = []
                else:
                    cmd.append(x)
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
