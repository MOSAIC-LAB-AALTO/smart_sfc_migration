import lxc
from random import randint
import os
import virtual_machine as system_driver

LXC_PATH = '/var/lib/lxc/'


# A set of simple methods to scale up/down either CPU or RAM or both of them
def scale_up_cpu(name, cpu):
    # Setting the soft part
    c = lxc.Container(name)
    if len(c.get_cgroup_item("cpuset.cpus")) == 1:
        cpu = randint(0, int(system_driver.get_vm_cpu())-1)
        while cpu == c.get_cgroup_item("cpuset.cpus"):
            cpu = randint(0, int(system_driver.get_vm_cpu())-1)
        c.set_cgroup_item("cpuset.cpus", "{},{}".format(c.get_cgroup_item("cpuset.cpus"), cpu))
    elif all(item in c.get_cgroup_item("cpuset.cpus") for item in [',', '-']):
        temp = c.get_cgroup_item("cpuset.cpus").split(",")
        if '-' in temp[0]:
            min_cpu = temp[0].split("-")[0]
            max_cpu = temp[0].split("-")[1]
            c.set_cgroup_item("cpuset.cpus", "{}-{},{}".format(min_cpu, int(max_cpu)+1, temp[1]))
        else:
            min_cpu = temp[1].split("-")[0]
            max_cpu = temp[1].split("-")[1]
            c.set_cgroup_item("cpuset.cpus", "{}, {}-{}".format(temp[0], int(min_cpu) - 1, max_cpu))
    elif ',' in c.get_cgroup_item("cpuset.cpus"):
        temp = c.get_cgroup_item("cpuset.cpus").split(",")
        i = 0
        while int(temp[i]) < int(system_driver.get_vm_cpu()) and int(temp[i]) == i:
            i += 1
        temp = c.get_cgroup_item("cpuset.cpus")
        c.set_cgroup_item("cpuset.cpus", temp + ',' + str(i))
    else:
        temp = c.get_cgroup_item("cpuset.cpus").split("-")[1]
        c.set_cgroup_item("cpuset.cpus", "0-{}".format(int(temp) + int(cpu)))
    return True


def hard_cpu(name):
    c = lxc.Container(name)
    for line in open('{}{}/config'.format(LXC_PATH, name), "r"):
        if "lxc.cgroup.cpuset.cpus" in line:
            with open('{}{}/config'.format(LXC_PATH, name), "r") as input_file:
                with open('{}{}/config2'.format(LXC_PATH, name), "w") as output_file:
                    for line2 in input_file:
                        if line2 != line:
                            output_file.write(line2)
                        else:
                            output_file.write('\nlxc.cgroup.cpuset.cpus = {}'.format(c.get_cgroup_item("cpuset.cpus")))
                            output_file.write('\n')


            basic_cmd = 'rm {}{}/config'.format(LXC_PATH, name)
            os.system(basic_cmd)
            basic_cmd = 'mv {0}{1}/config2 {0}{1}/config'.format(LXC_PATH, name)
            os.system(basic_cmd)
    return True


def scale_down_cpu(name, cpu):

    # TODO: this is a trivial scale down we need something strong like the lower cpu core will be scaled down
    c = lxc.Container(name)
    if len(c.get_cgroup_item("cpuset.cpus")) == 1:
        return False
    elif all(item in c.get_cgroup_item("cpuset.cpus") for item in [',', '-']):
        temp = c.get_cgroup_item("cpuset.cpus").split(",")
        if '-' in temp[0]:
            min_cpu = temp[0].split("-")[0]
            max_cpu = temp[0].split("-")[1]
        else:
            min_cpu = temp[1].split("-")[0]
            max_cpu = temp[1].split("-")[1]
        c.set_cgroup_item("cpuset.cpus", "{}-{}".format(int(min_cpu), int(max_cpu)))
    elif ',' in c.get_cgroup_item("cpuset.cpus"):
        temp = c.get_cgroup_item("cpuset.cpus").split(",")
        i = 0
        temp2 = ''
        while i < len(temp) - 1:
            if i == 0:
                temp2 = temp[i + 1]
            else:
                temp2 = temp2 + ',' + temp[i + 1]
            i += 1
        c.set_cgroup_item("cpuset.cpus", temp2)
    else:
        temp = c.get_cgroup_item("cpuset.cpus").split("-")[1]
        c.set_cgroup_item("cpuset.cpus", "0-{}".format(int(temp) - int(cpu)))
    return True


def scale_up_ram(name, ram):
    c = lxc.Container(name)
    current_ram = int(c.get_cgroup_item("memory.limit_in_bytes"))/1024/1024
    if c.set_cgroup_item("memory.limit_in_bytes", "{}M".format(int(ram) + int(current_ram))):
        return True
    return False

    # Didn't implement the G value as it accepts only the known values (1G, 2G, 3G ....) which not realistic


def scale_down_ram(name, ram):
    c = lxc.Container(name)
    current_ram = int(c.get_cgroup_item("memory.limit_in_bytes")) / 1024 / 1024
    if int(ram) >= int(current_ram) or int(current_ram) - int(ram) < 512:
        return False
    if c.set_cgroup_item("memory.limit_in_bytes", "{}M".format(int(current_ram) - int(ram))):
        return True
    return False


def hard_ram(name):
    c = lxc.Container(name)
    for line in open('{}{}/config'.format(LXC_PATH, name), "r"):
        if "lxc.cgroup.memory.limit_in_bytes" in line:
            with open('{}{}/config'.format(LXC_PATH, name), "r") as input_file:
                with open('{}{}/config2'.format(LXC_PATH, name), "w") as output_file:
                    for line2 in input_file:
                        if line2 != line:
                            output_file.write(line2)
                        else:
                            output_file.write('\nlxc.cgroup.memory.limit_in_bytes = {}M'.format(int(int(
                                c.get_cgroup_item("memory.limit_in_bytes"))/1024/1024)))
                            output_file.write('\n')

            basic_cmd = 'rm {}{}/config'.format(LXC_PATH, name)
            os.system(basic_cmd)
            basic_cmd = 'mv {0}{1}/config2 {0}{1}/config'.format(LXC_PATH, name)
            os.system(basic_cmd)
    return True


def scale_up_cpu_ram(name, cpu, ram):
    if scale_up_cpu(name, cpu):
        if hard_cpu(name):
            if scale_up_ram(name, ram):
                if hard_ram(name):
                    return True
    return False


def scale_up_cpu_full(name, cpu):
    if scale_up_cpu(name, cpu):
        if hard_cpu(name):
            return True
    return False


def scale_up_ram_full(name, ram):
    if scale_up_ram(name, ram):
        if hard_ram(name):
            return True
    return False
