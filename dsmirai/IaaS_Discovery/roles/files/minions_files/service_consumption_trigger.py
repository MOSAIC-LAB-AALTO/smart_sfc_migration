import virtual_machine as system_driver
import linux_container as lxc_driver


def container_live_resources():
    """
    SCT trigger minion listener, used to gather containers' resources consumption
    :return:
    """
    monitor = {}
    containers = {}
    nb_container = lxc_driver.list_containers()
    vm_cpu = 0
    vm_ram = 0
    vm_disk = 0
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
                live_cpu = lxc_driver.get_live_cpu(nb_container[i])
                live_ram = lxc_driver.get_live_mem(nb_container[i])
                containers[nb_container[i]] = {'cpu': cpu,
                                               'live_cpu': live_cpu,
                                               'ram': ram,
                                               'live_ram': live_ram,
                                               'disk': disk}

    vm_cpu = int(system_driver.get_vm_cpu()) - int(vm_cpu)
    vm_ram = int(system_driver.get_vm_mem()) - int(vm_ram)
    vm_disk = float(system_driver.get_vm_disk()) - float(vm_disk)

    monitor[system_driver.get_ip()] = {'vm_cpu': vm_cpu,
                                       'vm_ram': vm_ram,
                                       'vm_disk': vm_disk,
                                       'containers': containers}

    return monitor
