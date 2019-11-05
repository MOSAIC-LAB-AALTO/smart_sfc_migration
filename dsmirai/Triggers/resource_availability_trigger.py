import dsmirai.virtual_machine as system_driver
import dsmirai.linux_container as lxc_driver


def container_list():
    """
    RAT trigger minion listener, used to gather VM/IaaS/FRD resources consumption and their respective list of
    containers
    :return:
    """
    containers = {}
    vm = {}
    nb_container = lxc_driver.list_containers()
    vm_cpu = 0
    vm_ram = 0
    vm_disk = 0.0

    for i in range(len(nb_container)):
        if nb_container[i] != 'nginxBKserver' and nb_container[i] != 'nginxBKclient':
            container_status, ip = lxc_driver.containers_status(nb_container[i])
            cpu = lxc_driver.get_cpu(nb_container[i])
            ram = lxc_driver.get_mem(nb_container[i])
            disk = lxc_driver.get_size(nb_container[i])
            vm_cpu = int(vm_cpu) + int(cpu)
            vm_ram = int(vm_ram) + int(ram)
            vm_disk = float(vm_disk) + float(disk)
            if container_status == 'RUNNING' and ip != 0:
                containers[nb_container[i]] = {'cpu': cpu,
                                               'ram': ram,
                                               'disk': disk}

    vm[system_driver.get_ip()] = {'cpu': system_driver.get_vm_cpu(),
                                  'live_cpu': vm_cpu,
                                  'ram': system_driver.get_vm_mem(),
                                  'live_ram': vm_ram,
                                  'disk': system_driver.get_vm_disk(),
                                  'live_disk': vm_disk,
                                  'containers': containers}

    return vm
