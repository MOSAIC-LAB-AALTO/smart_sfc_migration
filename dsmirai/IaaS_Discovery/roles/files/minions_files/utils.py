import subprocess
import logging
import netifaces as ni
import paramiko
import os
from multiprocessing import Process
import iperf_server
import psutil
import time
import json
import random

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


def clean_container_bridge_ovs(container_name, ovs_source, diff=''):
    basic_cmd = "brctl delif br{0}{1} veth{1}Ovs{0}".format(diff, container_name)
    os.system(basic_cmd)

    basic_cmd = "ovs-vsctl del-port {0} vethOvs{1}{2}".format(ovs_source, diff, container_name)
    os.system(basic_cmd)

    basic_cmd = "ip link del dev veth{}Ovs{}".format(container_name, diff)
    os.system(basic_cmd)

    basic_cmd = "ifconfig br{}{} down".format(diff, container_name)
    os.system(basic_cmd)

    basic_cmd = "brctl delbr br{}{}".format(diff, container_name)
    os.system(basic_cmd)


def unattached_process(ip_server, number_of_request):
    p = Process(name='iperf', target=iperf_server.run, args=(ip_server, number_of_request,))
    p.start()
    return 1


def monitor_bandwidth():
    dict_file = {}
    abstracted_time = 0
    with open('/root/PID_test_network.txt', "w") as my_file:
        my_file.write(str(os.getpid()))
        my_file.write('\n')
    while 1:
        result = psutil.net_io_counters(pernic=True)
        temp = {}
        for i in result:
            temp[i] = {'bytes_sent': result[i][0], 'bytes_recv': result[i][1]}
        dict_file[abstracted_time] = temp
        time.sleep(.5)
        abstracted_time += 1
        with open('/root/test_network.txt', "w") as my_file:
            my_file.write(json.dumps(dict_file))
            my_file.write('\n')


def check_cpu_util():
    # check cpu utilization as a percentage
    dict_file = {}
    abstracted_time = 0
    number = random.randint(1, 120)
    with open('/root/PID_test_CPU.txt', "w") as my_file:
        my_file.write(str(os.getpid()))
        my_file.write('\n')
    while 1:
        cpu_utilization = psutil.cpu_percent(interval=1, percpu=True)
        # properly handle cpu utilization percentage returns
        sum_ = 0
        for j in range(len(cpu_utilization)):
            sum_ = sum_ + cpu_utilization[j]
        dict_file[abstracted_time] = sum_
        abstracted_time += 1
        with open('/root/test_CPU_{}.txt'.format(number), "w") as my_file:
            my_file.write(json.dumps(dict_file))
            my_file.write('\n')


def unattached_process_bandwidth():
    p = Process(name='bandwidth', target=monitor_bandwidth)
    # p = Process(name='cpu', target=check_cpu_util)
    p.start()
    return 1
