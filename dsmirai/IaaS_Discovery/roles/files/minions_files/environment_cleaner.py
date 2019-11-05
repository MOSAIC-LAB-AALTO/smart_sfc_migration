import virtual_machine as system_driver
import linux_container as lxc_driver
import os
import sys


# Set of methods for cleaning minion nodes
def container_list():
    nb_container = lxc_driver.list_containers()
    deleted_container = []
    for i in range(len(nb_container)):
        if nb_container[i] != 'nginxBKserver' and nb_container[i] != 'nginxBKclient' and nb_container[i] != 'lxc-ovs':
            deleted_container.append(nb_container[i])
    return deleted_container


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


def clean_ovs_bridges():
    basic_cmd = "ovs-vsctl del-br br-{}1".format(system_driver.get_ip().split(".")[3])
    os.system(basic_cmd)
    basic_cmd = "ovs-vsctl del-br br-{}2".format(system_driver.get_ip().split(".")[3])
    os.system(basic_cmd)
    basic_cmd = "ovs-vsctl del-br br-{}3".format(system_driver.get_ip().split(".")[3])
    os.system(basic_cmd)


def kill_python_process():
    basic_cmd = "killall python3"
    os.system(basic_cmd)


def core_cleaner(decision):
    container_to_delete = container_list()
    for i in range(len(container_to_delete)):
        clean_container_bridge_ovs(container_to_delete[i], "br-{}1".format(system_driver.get_ip().split(".")[3]))
        clean_container_bridge_ovs(container_to_delete[i], "br-{}2".format(system_driver.get_ip().split(".")[3]))
        clean_container_bridge_ovs(container_to_delete[i], "br-{}3".format(system_driver.get_ip().split(".")[3]))
        clean_container_bridge_ovs(container_to_delete[i], "br-{}3".format(system_driver.get_ip().split(".")[3]), "2")
        lxc_driver.delete_container(container_to_delete[i])
    if decision is True or decision == "True":
        clean_ovs_bridges()


if __name__ == "__main__":
    core_cleaner(sys.argv[1])

