import subprocess
import logging
import netifaces as ni
import paramiko


my_logger = logging.getLogger('control_log_vm')


def ssh_query(cmd, ip_destination, output=False, user_name='root', password='iprotect'):
    """
    in order to run a ssh command easier
    :param cmd:
    :param ip_destination:
    :param user_name:
    :param password:
    :param output:
    """

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(str(ip_destination), username=user_name, password=password)
    if output:
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            return stdin, stdout, stderr
        except subprocess.CalledProcessError:
            out = False
            return out
    if int(ssh.exec_command(cmd)) == 0:
        return True
    else:
        return False
