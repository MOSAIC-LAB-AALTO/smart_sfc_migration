import subprocess
import lxc
import logging
import time


my_logger = logging.getLogger('control_log_lxc')


# more efficient information about container's CPU
def get_cpu(container_name):
    try:
        cmd = 'cat /var/lib/lxc/{}/config'.format(container_name)
        result = subprocess.check_output(cmd, shell=True)
        result = result.decode().split('\n')
        for line in result:
            if "lxc.cgroup.cpuset.cpus" in line:
                my_info = line.split(' = ')
                if all(item in my_info[1] for item in [',', '-']):
                    temp = my_info[1].split(",")
                    if '-' in temp[0]:
                        number_cpu = temp[0].split("-")
                    else:
                        number_cpu = temp[1].split("-")
                    number_cpu_2 = str((int(number_cpu[1]) - int(number_cpu[0])) + 2)
                    return int(number_cpu_2)
                elif '-' in my_info[1]:
                    number_cpu = my_info[1].split('-')
                    number_cpu_2 = str((int(number_cpu[1]) - int(number_cpu[0])) + 1)
                    return int(number_cpu_2)

                elif ',' in my_info[1]:
                    temp = my_info[1].split(",")
                    i = 0
                    while i < len(temp):
                        i += 1
                    return i
                else:
                    return 1

        return 1
    except Exception as exception:
        my_logger.critical('ERROR: get_cpu():' + str(exception) + '\n')
        print("unable to get cpu information from our linux container")


# more efficient information about container's Memory
def get_mem(container_name):
    try:
        print("Getting Memory information")
        cmd = 'cat /var/lib/lxc/{}/config'.format(container_name)
        result = subprocess.check_output(cmd, shell=True)
        contenu = result.decode().split('\n')
        for line in contenu:
            if "lxc.cgroup.memory.limit_in_bytes" in line:
                my_info = line.split(' = ')
                if 'M' in my_info[1]:
                    temp = my_info[1].split('M')
                    return int(temp[0])
                else:
                    temp = my_info[1].split('G')
                    return int(temp[0]) * 1024
        return 1024
    except Exception as exception:
        my_logger.critical('ERROR: get_mem():' + str(exception) + '\n')
        print("unable to get ram information from our linux container")


# information about container's Size
def get_size(container_name):
    try:
        print("Getting the size of the container")
        cmd = 'du -sh /var/lib/lxc/{}/'.format(container_name)
        result = subprocess.check_output(cmd, shell=True)
        my_info = result.decode().split('\t')
        for i in range(1, int(len(my_info[0]) + 1)):
            if my_info[0][i - 1] == 'M':
                res = my_info[0].split('M')
                return int(res[0])
            elif my_info[0][i - 1] == 'G':
                res = my_info[0].split('G')
                first_number = float(res[0])
                second_number = float(1000.0)
                answer = (first_number * second_number)
                return answer
    except Exception as exception:
        my_logger.critical('ERROR: get_size():' + str(exception) + '\n')
        print("unable to get disk information from our linux container")


# Get the live CPU consumption
def get_live_cpu(container_name):
    container_attach(container_name, ["python3", "/root/cpu.py"])
    with open('/var/lib/lxc/%s/rootfs/root/cpu' % (container_name,), 'r') as f:
        cpu_usage = float(f.readline())
    print(cpu_usage)
    return cpu_usage


# Get the live Memory consumption
def get_live_mem(container_name):
    s = 0
    i = 0
    for line in open('/sys/fs/cgroup/memory/lxc/%s/memory.stat' % (container_name,), 'r'):
        if "total_cache" in line:
            x = line.split(' ')
            s = s + int(x[1])
        if "total_rss" in line:
            if i == 0:
                x = line.split(' ')
                s = s + int(x[1])
                i = 1

    return (s/1024)/1024


# List of all the containers
def list_containers():
    try:
        list_all_containers = []
        for container in lxc.list_containers(as_object=True):
            list_all_containers.append(container.name)
        return list_all_containers
    except Exception as exception:
        my_logger.critical('ERROR: list_containers():' + str(exception) + '\n')
        print("unable to get the list of containers from our linux container")


# Verify unique name of containers
def verify_unique_name(container_name):
    try:
        if container_name in lxc.list_containers():
            return True
        return False
    except Exception as exception:
        my_logger.critical('ERROR: verify_unique_name():' + str(exception) + '\n')
        print("unable to verify the unique name from our linux container")


# Container status
def containers_status(container_name):
    try:
        c = lxc.Container(container_name)
        if c.state == 'RUNNING' and len(c.get_ips()) == 1:
            print("container is running")
            return c.state, c.get_ips()[0]
        print("container is stopped")
        return c.state, 0
    except Exception as exception:
        my_logger.critical('ERROR: containers_status():' + str(exception) + '\n')
        print("unable to get containers status from our linux container")


# containers's CPU/RAM resources
def get_container_resources(container_name):
    try:
        container = lxc.Container(container_name)
        if not container.defined:
            return 0, 0
        return get_cpu(container_name), get_mem(container_name)
    except Exception as exception:
        my_logger.critical('ERROR: get_container_resources():' + str(exception) + '\n')
        print("unable to get container resources from our linux container")


# Start a container after the creation
def start_container(container_name):
    try:
        c = lxc.Container(container_name)
        if not c.defined:
            return False
        if c.start():
            print(c.state)
            return True
        return False
    except Exception as exception:
        my_logger.critical('ERROR: start_container():' + str(exception) + '\n')
        print("unable to start the container from our linux container")


# Get IP address of container
def get_ip_container(container_name):
    try:
        c = lxc.Container(container_name)
        if not c.defined:
            return False
        return c.get_ips()
    except Exception as exception:
        my_logger.critical('ERROR: get_ip_container():' + str(exception) + '\n')
        print("unable to get container ip address from our linux container")


# attach containers
def container_attach(container_name, command):
    c = lxc.Container(container_name)
    if not c.defined:
        return False
    return c.attach_wait(lxc.attach_run_command, command)


# Get containers' PID
def container_pid(container_name):
    try:
        c = lxc.Container(container_name)
        if not c.defined:
            return False
        return c.init_pid
    except Exception as exception:
        my_logger.critical('ERROR: container_pid():' + str(exception) + '\n')
        print("unable to get container's PID from our linux container")


def container_status_pid(container_name):
    try:
        c = lxc.Container(container_name)
        if not c.defined:
            return False, 0
        if c.state == 'RUNNING':
            return True, c.init_pid
        else:
            return False, 0
    except Exception as exception:
        my_logger.critical('ERROR: container_status_pid():' + str(exception) + '\n')
        print("unable to get container's PID and the running status from our linux container")


def delete_container(container_name):
    try:
        c = lxc.Container(container_name)
        if not c.defined:
            return False
        c.stop()
        if c.destroy():
            return True
        return False
    except Exception as exception:
        my_logger.critical('ERROR: delete_container():' + str(exception) + '\n')
        print("unable to delete the container from our linux container")
        return False


# Used for old dashboard
def container_dashboard_resources(container_name):
    try:
        c = lxc.Container(container_name)
        container_ip = c.get_ips()[0]
        return container_ip, get_live_cpu(container_name), get_live_mem(container_name), get_size(container_name)
    except Exception as exception:
        my_logger.critical('ERROR: container_dashboard_resources():' + str(exception) + '\n')
        print("unable to get container dashboard resources from our linux container")


def get_running_containers():
    number_running_container = 0
    for i in range(len(list_containers())):
        status, ip = containers_status(list_containers()[i])
        if status != "STOPPED" and ip != 0:
            number_running_container += 1
    return number_running_container


# Used to clone containers from images or templates
def clone_from_template(template, clone_name):
    c = lxc.Container(template)
    if not c.defined:
        return False
    new_container = c.clone(clone_name)
    return new_container.defined
