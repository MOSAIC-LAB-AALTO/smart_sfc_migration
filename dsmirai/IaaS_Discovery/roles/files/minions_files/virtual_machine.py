import subprocess
import logging
import netifaces as ni
import paramiko
import linux_container as lxc_driver


my_logger = logging.getLogger('control_log_vm')


# Getting the Disk of the VM
def get_vm_disk():
    try:
        cmd = 'df -H /'
        result = subprocess.check_output(cmd, shell=True)
        my_info = result.decode().split('\n')
        vm_status = my_info[1].split()[0:6]
        for i in range(1,  int(len(vm_status[0])+1)):
            if vm_status[3][i-1] == 'M':
                res = vm_status[3].split('M')
                return res[0]
            elif vm_status[3][i-1] == 'G':
                res = vm_status[3].split('G')
                first_number = float(res[0].replace(',', '.'))
                second_number = float(1000.0)
                answer = (first_number * second_number)
                return answer
    except Exception as exception:
        my_logger.critical('ERROR: get_vm_disk():' + str(exception) + '\n')
        print("unable to get disk information from our VM")


# Getting the Memory of the VM
def get_vm_mem():
    try:
        cmd = 'vmstat -s'
        result = subprocess.check_output(cmd, shell=True)
        my_info = result.decode().split('\n')
        free_memory = my_info[0].split()[0:3]
        return int(int(free_memory[0])/1024)
    except Exception as exception:
        my_logger.critical('ERROR: get_vm_mem():' + str(exception) + '\n')
        print("unable to get memory information from our VM ")


# Getting the CPU of the VM
def get_vm_cpu():
    try:
        cmd = 'nproc'
        result = subprocess.check_output(cmd, shell=True)
        return int(result)
    except Exception as exception:
        my_logger.critical('ERROR: get_vm_cpu():' + str(exception) + '\n')
        print("unable to get cpu information from our VM")


# Getting the IP address of the VM
def get_ip():
    ip_list = ni.interfaces()
    # TODO: to be changed to enp in the FRD instances
    indices = [s for i, s in enumerate(ip_list) if 'enp' in s]
    return ni.ifaddresses(str(indices[0]))[ni.AF_INET][0]['addr']


# Get a folder size
def get_size_folder(container_name, path='/checkpoint/3'):
    cmd = 'du -sh /var/lib/lxc/{}{}'.format(container_name, path)
    print('The path to size: {}'.format(cmd))
    result = subprocess.check_output(cmd, shell=True)
    my_info = result.decode().split('\t')
    if my_info[0][-1] == 'M':
        return my_info[0].split('M')[0]
    return my_info[0].split('G')[0]


# Setting default output bridge
def default_bridge():

    subprocess.Popen(['brctl', 'addbr', 'brOut'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    basi_cmd = 'ifconfig brOut 192.168.0.2 netmask 255.255.255.0 up'
    subprocess.check_output(basi_cmd, shell=True)
    basi_cmd = 'iptables -t nat -A POSTROUTING --out-interface {} -j MASQUERADE'.format(get_ip())
    subprocess.check_output(basi_cmd, shell=True)
    basi_cmd = 'iptables -A FORWARD --in-interface brOut -j ACCEPT'
    subprocess.check_output(basi_cmd, shell=True)


# host available resources computation
def resource_availability():

    nb_container = lxc_driver.list_containers()
    print(nb_container)
    vm_cpu = get_vm_cpu()
    vm_ram = get_vm_mem()
    vm_disk = get_vm_disk()

    for i in range(len(nb_container)):
        # TODO: later to be changed by a list that contains all the VNFs present in the node
        if nb_container[i] != 'nginxBKserver' and nb_container[i] != 'nginxBKclient' and nb_container[i] != 'lxc-ovs' \
                and nb_container[i] != 'empty':
            cpu = lxc_driver.get_cpu(nb_container[i])
            ram = lxc_driver.get_mem(nb_container[i])
            disk = lxc_driver.get_size(nb_container[i])
            vm_cpu = int(vm_cpu) - int(cpu)
            vm_ram = int(vm_ram) - int(ram)
            vm_disk = float(vm_disk) - float(disk)

    return vm_cpu, vm_ram, vm_disk
