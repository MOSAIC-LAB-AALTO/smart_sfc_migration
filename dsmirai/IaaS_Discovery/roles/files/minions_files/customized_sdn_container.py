import subprocess
import os
import time
import logging
import linux_container as lxc_driver
import utils
my_logger = logging.getLogger('control_log_sdn_container')


LXC_PATH = '/var/lib/lxc/'


def create_server(container_name, cpu, ram, server_ip_address, server_port_number):
    """
    create container server SDN
    :param container_name:
    :param cpu:
    :param ram:
    :param server_ip_address:
    :param server_port_number:
    :return:
    """
    try:
        print("container server creation :")
        basic_cmd = 'lxc-copy -n nginxBKserver -N {}'.format(container_name)
        os.system(basic_cmd)
        time.sleep(2)
        with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
            my_file.write('\n# hax for criu\n')
            my_file.write('lxc.console = none\n')
            my_file.write('lxc.tty = 0\n')
            my_file.write('lxc.cgroup.devices.deny = c 5:1 rwm\n')
            my_file.write('lxc.mount.entry = /sys/firmware/efi/efivars sys/firmware/efi/efivars none bind,optional 0 0\n')
            my_file.write('lxc.mount.entry = /proc/sys/fs/binfmt_misc proc/sys/fs/binfmt_misc none bind,optional 0 0\n')

        # Custom creation
        modify_cpu(container_name, cpu)
        modify_ram(container_name, ram)

        # SDN fashion
        modify_configuration_bridge(container_name)
        ovs_name = get_ovs(0)
        print("the name of the ovs is: {}".format(ovs_name))
        container_bridge_ovs(container_name, str(ovs_name), str(server_port_number))
        set_ip(container_name, server_ip_address)
        time.sleep(5)
        if not lxc_driver.start_container(container_name):
            return False
        time.sleep(2)

        while len(lxc_driver.get_ip_container(container_name)) != 1:
            print("current_ip: {}".format(lxc_driver.get_ip_container(container_name)))
            print("envisaged_ip: {}".format(server_ip_address))
            time.sleep(1)
        response = 0
        while response != 256:
            response = lxc_driver.container_attach(container_name, ["ping", "-c", "1", "172.16.207.90"])
        print("end creation of server")
        return True
    except Exception as exception:
        my_logger.critical('ERROR: create_server():' + str(exception) + '\n')
        print("unable to create server ...")


def create_client(container_name, client_ip_address, client_port_number, brb='2'):
    """
    Create client container SDN
    :param container_name:
    :param client_ip_address:
    :param client_port_number:
    :param brb:
    :return:
    """

    print("client creation: ")

    basic_cmd = 'lxc-copy -n nginxBKclient -N {}'.format(container_name)
    os.system(basic_cmd)

    ovs_name = get_ovs(2)
    print("the name of the ovs is: {}".format(ovs_name))
    modify_configuration_bridge(container_name)
    container_bridge_ovs(container_name, ovs_name, client_port_number)
    set_ip(container_name, client_ip_address)

    with open('{}{}/rootfs/etc/network/interfaces'.format(LXC_PATH, container_name), "a") as my_file:
        my_file.write('\nauto vethCltOut{}'.format(client_port_number))
        my_file.write('\niface vethCltOut{} inet static'.format(client_port_number))
        my_file.write('\n    address ')
        my_file.write('192.168.0.{}'.format(client_port_number))
        my_file.write('\n')
        my_file.write('    netmask 255.255.255.0')
        my_file.write('\n')
        my_file.write('    gateway 192.168.0.{}'.format(brb))

    if not lxc_driver.start_container(container_name):
        return False

    # second interface

    basic_cmd = 'ip link add name vethCltOut{0} type veth peer name vethOutClt{0}'.format(client_port_number)
    os.system(basic_cmd)
    basic_cmd = 'ip link set vethCltOut{} up'.format(client_port_number)
    os.system(basic_cmd)
    basic_cmd = 'ip link set vethOutClt{} up'.format(client_port_number)
    os.system(basic_cmd)
    basic_cmd = 'brctl addif brOut vethOutClt{}'.format(client_port_number)
    os.system(basic_cmd)
    basic_cmd = 'ip link set dev vethCltOut' + str(client_port_number) + ' netns '
    basic_cmd = basic_cmd + str(lxc_driver.container_pid(container_name)) + ' name vethCltOut' + str(client_port_number)
    os.system(basic_cmd)

    response = 0
    while response != 256:
        response = lxc_driver.container_attach(container_name, ["ping", "-c", "1", "172.16.207.90"])
    print("end creation of client")
    time.sleep(2)
    return True


def create_lxc_ovs(container_name, ip_address_1, port_1, ip_address_2, port_2):
    """
    Create LXC-Dummy node for SFC migration
    :param container_name:
    :param ip_address_1:
    :param port_1:
    :param ip_address_2:
    :param port_2:
    :return:
    """
    try:
        print("container lxc-ovs creation :")
        basic_cmd = 'lxc-copy -n lxc-ovs -N {}'.format(container_name)
        os.system(basic_cmd)
        time.sleep(2)
        with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
            my_file.write('\n# hax for criu\n')
            my_file.write('lxc.console = none\n')
            my_file.write('lxc.tty = 0\n')
            my_file.write('lxc.cgroup.devices.deny = c 5:1 rwm\n')
            my_file.write('lxc.mount.entry = /sys/firmware/efi/efivars sys/firmware/efi/efivars none bind,optional 0 0\n')
            my_file.write('lxc.mount.entry = /proc/sys/fs/binfmt_misc proc/sys/fs/binfmt_misc none bind,optional 0 0\n')
        # SDN fashion
        modify_cpu(container_name, "1")
        modify_ram(container_name, "512M")
        print("SDN fashion 1")
        modify_configuration_bridge(container_name)
        print("SDN fashion 2")
        ovs_name = get_ovs(1)
        print("the name of the ovs is: {}".format(ovs_name))
        container_bridge_ovs(container_name, str(ovs_name), str(port_1))
        container_bridge_ovs(container_name, str(ovs_name), str(port_2), '2')

        set_ip(container_name, ip_address_1, True, ip_address_2)
        time.sleep(5)
        if not lxc_driver.start_container(container_name):
            return False
        time.sleep(2)

        while len(lxc_driver.get_ip_container(container_name)) < 2:
            print("current_ip: {}".format(lxc_driver.get_ip_container(container_name)))
            print("envisaged_ip_1: {}".format(ip_address_1))
            print("envisaged_ip_2: {}".format(ip_address_2))
            time.sleep(1)
        print("first address got with success")
        response = 0
        while response != 256:
            response = lxc_driver.container_attach(container_name, ["ping", "-I", "eth0", "-c", "1", "172.16.207.90"])

        response = 0
        while response != 256:
            response = lxc_driver.container_attach(container_name, ["ping", "-I", "eth1", "-c", "1", "172.16.207.90"])

        print("Pushing OpenFlow rules to the OVS_LXC_FW")
        lxc_driver.container_attach(container_name, ["ip", "link", "add", "name", "br0", "type", "bridge"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "br0", "up"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth0", "master", "br0"])
        lxc_driver.container_attach(container_name, ["ip", "link", "set", "dev", "eth1", "master", "br0"])

        '''lxc_driver.container_attach(container_name, ["ovs-vsctl", "add-br", "lxc-fw"])
        lxc_driver.container_attach(container_name, ["ovs-vsctl", "add-port", "lxc-fw", "eth0"])
        lxc_driver.container_attach(container_name, ["ovs-vsctl", "add-port", "lxc-fw", "eth1"])
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "del-flows", "lxc-fw"])
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "add-flow", "lxc-fw", "priority=4000,dl_type=0x8942,"
                                                                                        "action=drop"])
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "add-flow", "lxc-fw", "priority=4000,udp,tp_src=68,"
                                                                                        "tp_dst=67,action=drop"])
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "add-flow", "lxc-fw", "priority=4000,udp,tp_src=67,"
                                                                                        "tp_dst=68,action=drop"])
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "add-flow", "lxc-fw", "priority=4000,arp,action=drop"]
                                    )
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "add-flow", "lxc-fw", "priority=0,in_port=1,action=2"]
                                    )
        lxc_driver.container_attach(container_name, ["ovs-ofctl", "add-flow", "lxc-fw", "priority=0,in_port=2,action=1"]
                                    )'''

        print("end lxc-ovs of server")
        return True
    except Exception as exception:
        my_logger.critical('ERROR: create_lxc_ovs():' + str(exception) + '\n')
        print("unable to create lxc-ovs ...")


def delete_sdn_container(container_name, ovs_destination, client=None, ovs_source=None):
    """
    Delete SDN container
    :param container_name:
    :param ovs_destination:
    :param client:
    :param ovs_source:
    :return:
    """
    if client:
        utils.clean_container_bridge_ovs(client, ovs_source)
        if not lxc_driver.delete_container(container_name):
            return False
    utils.clean_container_bridge_ovs(container_name, ovs_destination)
    if lxc_driver.delete_container(container_name):
            return True
    return False


def modify_cpu(container_name, val):
    """
    Update CPU config file (hard update)
    :param container_name:
    :param val:
    :return:
    """
    i = 0
    for line in open('{}{}/config'.format(LXC_PATH, container_name), "r"):
        if "lxc.cgroup.cpuset.cpus" in line:
            with open('{}{}/config'.format(LXC_PATH, container_name), "r") as input_file:
                with open('{}{}/config2'.format(LXC_PATH, container_name), "wb") as output_file:
                    for line2 in input_file:
                        if line2 != line:
                            output_file.write(line2)
            basic_cmd = 'rm {}{}/config'.format(LXC_PATH, container_name)
            os.system(basic_cmd)
            basic_cmd = 'mv {0}{1}/config2 {0}{1}/config'.format(LXC_PATH, container_name)
            os.system(basic_cmd)
            if val == "1":
                with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
                    my_file.write('\nlxc.cgroup.cpuset.cpus =')
                    my_file.write(' ')
                    my_file.write(str(int(val)-1))
                    my_file.write('\n')
            else:
                with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
                    my_file.write('\nlxc.cgroup.cpuset.cpus =')
                    my_file.write(' 0-')
                    my_file.write(str(int(val)-1))
                    my_file.write('\n')

            i = 1
    if i == 0:
        if val == "1":
            with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
                my_file.write('\nlxc.cgroup.cpuset.cpus =')
                my_file.write(' ')
                my_file.write(str(int(val) - 1))
                my_file.write('\n')
        else:
            with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
                my_file.write('\nlxc.cgroup.cpuset.cpus =')
                my_file.write(' 0-')
                my_file.write(str(int(val) - 1))
                my_file.write('\n')


# customized Memory
def modify_ram(container_name, val):
    """
    Update RAM config file (hard update)
    :param container_name:
    :param val:
    :return:
    """
    i = 0
    for line in open(LXC_PATH + str(container_name) + '/config', "r"):
        if "lxc.cgroup.memory.limit_in_bytes" in line:
            with open(LXC_PATH + str(container_name) + '/config', "r") as input_file:
                with open(LXC_PATH + str(container_name) + '/config2', "wb") as output_file:
                    for line2 in input_file:
                        if line2 != line:
                            output_file.write(line2)

            basic_cmd = 'rm {}{}/config'.format(LXC_PATH, container_name)
            os.system(basic_cmd)
            basic_cmd = 'mv {0}{1}/config2 {0}{1}/config'.format(LXC_PATH, container_name)
            os.system(basic_cmd)

            with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
                my_file.write('\nlxc.cgroup.memory.limit_in_bytes =')
                my_file.write(' ')
                my_file.write(val)
                my_file.write('\n')

            i = 1
    if i == 0:
        with open('{}{}/config'.format(LXC_PATH, container_name), "a") as my_file:
            my_file.write('\nlxc.cgroup.memory.limit_in_bytes =')
            my_file.write(' ')
            my_file.write(val)
            my_file.write('\n')


# bridge creation for each container
def modify_configuration_bridge(container_name, diff='2'):
    """
    bridge creation for each container
    :param container_name:
    :param diff:
    :return:
    """
    print("BEGIN modify_configuration_bridge")
    for line in open('{}{}/config'.format(LXC_PATH, container_name), "r"):
        if "lxc.network.link" in line:
            with open('{}{}/config'.format(LXC_PATH, container_name), "r") as input_file:
                with open('{}{}/config2'.format(LXC_PATH, container_name), "w") as output_file:
                    for line2 in input_file:
                        if line2 != line:
                            output_file.write(line2)
                        elif "br1" in line2:
                            output_file.write('lxc.network.link =')
                            output_file.write(' ')
                            output_file.write('br{}{}'.format(diff, container_name))
                            output_file.write('\n')
                        else:
                            output_file.write('\nlxc.network.link =')
                            output_file.write(' ')
                            output_file.write('br{}'.format(container_name))
                            output_file.write('\n')

            basic_cmd = 'rm {}{}/config'.format(LXC_PATH, container_name)
            os.system(basic_cmd)
            basic_cmd = 'mv {0}{1}/config2 {0}{1}/config'.format(LXC_PATH, container_name)
            os.system(basic_cmd)
    print("END modify_configuration_bridge")


def container_bridge_ovs(container_name, ovs_name, ovs_port, diff=''):
    """
    Setting container ovs_bridge configurations
    :param container_name:
    :param ovs_name:
    :param ovs_port:
    :param diff:
    :return:
    """

    basic_cmd = 'ip link add name veth{0}Ovs{1} type veth peer name vethOvs{1}{0}'.format(container_name, diff)
    os.system(basic_cmd)

    basic_cmd = "ip link set vethOvs{0}{1} up".format(diff, container_name)
    os.system(basic_cmd)

    basic_cmd = "ip link set veth{0}Ovs{1} up".format(container_name, diff)
    os.system(basic_cmd)

    basic_cmd = "brctl addbr br{0}{1}".format(diff, container_name)
    os.system(basic_cmd)

    basic_cmd = "ifconfig br{0}{1} up".format(diff, container_name)
    os.system(basic_cmd)

    basic_cmd = "brctl addif br{1}{0} veth{0}Ovs{1}".format(container_name, diff)
    os.system(basic_cmd)

    basic_cmd = "sudo ovs-vsctl add-port {2} vethOvs{3}{0} -- set Interface vethOvs{3}{0} ofport_request={1}".format(
        container_name, ovs_port, ovs_name, diff)
    print(basic_cmd)
    os.system(basic_cmd)


def set_ip(container_name, ip_address, decision=False, ip_address_2=""):
    """
    IP setting
    :param container_name:
    :param ip_address:
    :param decision:
    :param ip_address_2:
    :return:
    """
    print("BEGIN set_ip")
    for line in open('{}{}/rootfs/etc/network/interfaces'.format(LXC_PATH, container_name), "r"):
        if "iface eth0 inet dhcp" in line or "auto eth0" in line:
            with open('{}{}/rootfs/etc/network/interfaces'.format(LXC_PATH, container_name), "r") as input_file:
                with open('{}{}/rootfs/etc/network/interfaces2'.format(LXC_PATH, container_name), "a") as output_file:
                    for line2 in input_file:
                        if line2 != line:
                            output_file.write(line2)

            basic_cmd = 'rm {}{}/rootfs/etc/network/interfaces'.format(LXC_PATH, container_name)
            os.system(basic_cmd)
            basic_cmd = 'mv {0}{1}/rootfs/etc/network/interfaces2 {0}{1}/rootfs/etc/network/interfaces'.format(
                LXC_PATH, container_name)
            os.system(basic_cmd)
    system_ip_configuration(container_name, ip_address, '0')
    if decision:
        system_ip_configuration(container_name, ip_address_2, '1')
    print("END set_ip")


def system_ip_configuration(container_name, ip_address, interface_number):
    """
    IP setting
    :param container_name:
    :param ip_address:
    :param interface_number:
    :return:
    """
    with open('{}{}/rootfs/etc/network/interfaces'.format(LXC_PATH, container_name), "a") as my_file:
        my_file.write('\nauto eth{}'.format(interface_number))
        my_file.write('\n')
        my_file.write('iface eth{} inet static'.format(interface_number))
        my_file.write('\n    address ')
        my_file.write(str(ip_address))
        my_file.write('\n')
        my_file.write('    netmask 255.255.255.0')
        my_file.write('\n')


def link_client_to_server(container_name, ip_address):
    """
    used for nginx usage
    :param container_name:
    :param ip_address:
    :return:
    """
    try:
        print("linking client to server :")

        for line in open(LXC_PATH + str(container_name) + '/rootfs/etc/nginx/sites-available/default', "r"):
            if "proxy_pass" in line:
                with open(LXC_PATH + str(container_name) + '/rootfs/etc/nginx/sites-available/default', "r") as input_file:
                    with open(LXC_PATH + str(container_name) + '/rootfs/etc/nginx/sites-available/default2', "w") as \
                            output_file:
                        for line2 in input_file:
                            if line2 != line:
                                output_file.write(line2)
                            else:
                                output_file.write("                ")
                                output_file.write("proxy_pass")
                                output_file.write("      ")
                                output_file.write("http://" + str(ip_address) + "/test.mp4;")
                                output_file.write('\n')

                basic_cmd = 'rm ' + LXC_PATH + str(container_name) + '/rootfs/etc/nginx/sites-available/default'
                os.system(basic_cmd)
                basic_cmd = 'mv ' + LXC_PATH + str(container_name) + '/rootfs/etc/nginx/sites-available/default2 ' \
                            + LXC_PATH + str(container_name) + '/rootfs/etc/nginx/sites-available/default'
                os.system(basic_cmd)
        time.sleep(2)
        lxc_driver.container_attach(container_name, ["/etc/init.d/nginx", "restart"])
        return True
    except Exception as exception:
        my_logger.critical('ERROR: link_client_to_server():' + str(exception) + '\n')
        print("unable to link client to server ...")
        return False


def get_ovs(i):
    """
    Get set of OvSs running insides a given VM/IaaS
    :param i:
    :return:
    """
    basic_cmd = 'ovs-vsctl list-br'
    result = subprocess.check_output(basic_cmd, shell=True)
    c = result.decode().split('\n')
    return str(c[i])
