import dsmirai.onos_helpers as onos_helpers
import dsmirai.utils as system_driver


class IntentBasedNetworking:

    def __init__(self):
        self.onos_helpers = onos_helpers.OnosHelpers()

    def initial_sfc_path(self, ip_sdn_controller, server_ip_address, client_ip_address, ovs_in_ip_address,
                         ovs_out_ip_address):
        """
        Static function for SDN establishment, to be automated later
        :param ip_sdn_controller:
        :param server_ip_address:
        :param client_ip_address:
        :param ovs_in_ip_address:
        :param ovs_out_ip_address:
        :return:
        """

        client_device, client_port_number, ip_vm_client = self.onos_helpers.sdn_host_information(
            ip_sdn_controller, client_ip_address)
        print("the device source is: {}".format(client_device))
        print("the port number source is: {}".format(client_port_number))
        print("the ip address source is: {}".format(client_ip_address))

        server_device, server_port_number, ip_vm_server = self.onos_helpers.sdn_host_information(
            ip_sdn_controller, server_ip_address)
        print("the device destination is: {}".format(server_device))
        print("the port number destination is: {}".format(server_port_number))
        print("the ip address destination is: {}".format(server_ip_address))

        ovs_in_device, ovs_in_port_number, ip_vm_ovs_in = self.onos_helpers.sdn_host_information(
            ip_sdn_controller, ovs_in_ip_address)
        print("the device ovs_in is: {}".format(ovs_in_device))
        print("the port number ovs_in is: {}".format(ovs_in_port_number))
        print("the ip address ovs_in is: {}".format(ovs_in_ip_address))

        ovs_out_device, ovs_out_port_number, ip_vm_ovs_out = self.onos_helpers.sdn_host_information(
            ip_sdn_controller, ovs_out_ip_address)
        print("the device ovs_out is: {}".format(ovs_out_device))
        print("the port number ovs_out is: {}".format(ovs_out_port_number))
        print("the ip address ovs_out is: {}".format(ovs_out_ip_address))

        list_of_links = self.onos_helpers.get_all_inter_ovs_links(ip_sdn_controller)
        print("the list of the link is: {}".format(list_of_links))
        middle_port_1 = ""
        middle_port_2 = ""
        middle_port_3 = ""
        middle_port_4 = ""
        for i in range(0, int(len(list_of_links))):
            device_source = list_of_links[i]['devicesrc']
            device_destination = list_of_links[i]['devicedst']
            if client_device == device_source and ovs_in_device == device_destination:
                middle_port_1 = list_of_links[i]['portsrc']
                middle_port_2 = list_of_links[i]['portdst']
            if ovs_out_device == device_source and server_device == device_destination:
                middle_port_3 = list_of_links[i]['portsrc']
                middle_port_4 = list_of_links[i]['portdst']

        self.onos_helpers.complex_intent(str(ip_sdn_controller), client_device, client_port_number,
                                         client_device, middle_port_1, 100, 2048, server_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_in_device, middle_port_2, ovs_in_device,
                                         ovs_in_port_number, 100, 2048, server_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_out_device, ovs_out_port_number,
                                         ovs_out_device, middle_port_3, 100, 2048, server_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), server_device, middle_port_4, server_device,
                                         server_port_number, 100, 2048, server_ip_address)
        # return path
        self.onos_helpers.complex_intent(str(ip_sdn_controller), server_device, server_port_number,
                                         server_device, middle_port_4, 300, 2048, client_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_out_device, middle_port_3, ovs_out_device,
                                         ovs_out_port_number, 300, 2048, client_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_in_device, ovs_in_port_number,
                                         ovs_in_device, middle_port_2, 300, 2048, client_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), client_device, middle_port_1, client_device,
                                         client_port_number, 300, 2048, client_ip_address)

    def network_redirection_sfc(self, ip_sdn_controller, client_device, server_device, client_port_number,
                                server_port_number, ovs_device, ovs_in_port_number, ovs_out_port_number, vxlan_port,
                                client_ip_address, server_ip_address, priority):
        """
        Used for traffic steering, can be automated later
        :param ip_sdn_controller:
        :param client_device:
        :param server_device:
        :param client_port_number:
        :param server_port_number:
        :param ovs_device:
        :param ovs_in_port_number:
        :param ovs_out_port_number:
        :param vxlan_port:
        :param client_ip_address:
        :param server_ip_address:
        :param priority:
        :return:
        """

        middle_port_1 = ""
        middle_port_2 = ""
        list_of_links = self.onos_helpers.get_all_inter_ovs_links(ip_sdn_controller)
        print("the list of the link is: {}".format(list_of_links))
        for i in range(0, int(len(list_of_links))):
            device_source = list_of_links[i]['devicesrc']
            device_destination = list_of_links[i]['devicedst']
            if ovs_device == device_source and server_device == device_destination:
                middle_port_1 = list_of_links[i]['portsrc']
                middle_port_2 = list_of_links[i]['portdst']

        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_device, vxlan_port, ovs_device,
                                         ovs_in_port_number, int(priority), 2048, server_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_device, ovs_out_port_number, ovs_device,
                                         middle_port_1, int(priority), 2048, server_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), server_device, middle_port_2, server_device,
                                         server_port_number, int(priority), 2048, server_ip_address)

        self.onos_helpers.complex_intent(str(ip_sdn_controller), server_device, server_port_number, server_device,
                                         middle_port_2, int(priority) + 200, 2048, client_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_device, middle_port_1, ovs_device,
                                         ovs_out_port_number, int(priority) + 200, 2048, client_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), ovs_device, ovs_in_port_number, ovs_device,
                                         vxlan_port, int(priority) + 200, 2048, client_ip_address)
        self.onos_helpers.complex_intent(str(ip_sdn_controller), client_device, vxlan_port, client_device,
                                         client_port_number, int(priority) + 200, 2048, client_ip_address)

    def network_redirection_sfc_2(self, ip_sdn_controller, client_device, client_port_number, vxlan_port,
                                  server_ip_address, priority):
        """
        Final traffic re-direction, to be automated
        :param ip_sdn_controller:
        :param client_device:
        :param client_port_number:
        :param vxlan_port:
        :param server_ip_address:
        :param priority:
        :return:
        """
        self.onos_helpers.complex_intent(str(ip_sdn_controller), client_device, client_port_number, client_device,
                                         vxlan_port, int(priority), 2048, server_ip_address)

    @staticmethod
    def overlay_network(ip_source, ip_destination, ovs_source, ovs_destination, interface_name, vxlan_port):
        """
        Overlay network creation
        :param ip_source:
        :param ip_destination:
        :param ovs_source:
        :param ovs_destination:
        :param interface_name:
        :param vxlan_port:
        :return:
        """

        cmd = []
        ip = []

        cmd1 = 'ovs-vsctl add-port ' + str(ovs_source) + '  ' + str(interface_name) + \
               ' -- set interface ' + str(interface_name) + ' type=' + 'vxlan' + ' options:remote_ip=' \
               + str(ip_destination) + ' ofport_request=' + str(vxlan_port)
        cmd.append(cmd1)
        ip.append(ip_source)

        cmd2 = 'ovs-vsctl add-port ' + str(ovs_destination) + '  ' + str(interface_name) \
               + ' -- set interface ' + str(interface_name) + ' type=' + 'vxlan' + \
               ' options:remote_ip=' + str(ip_source) + ' ofport_request=' \
               + str(vxlan_port)
        cmd.append(cmd2)
        ip.append(ip_destination)

        for i in range(len(cmd)):
            a, b, c = system_driver.ssh_query(cmd[i], ip[i], True)

    @staticmethod
    def target_container_bridge_ovs(container_name, ip_destination, ovs_name, ovs_port, diff=''):
        """
        Setting container ovs_bridge configurations
        :param container_name:
        :param ip_destination:
        :param ovs_name:
        :param ovs_port:
        :param diff:
        :return:
        """

        basic_cmd = 'ip link add name veth{0}Ovs{1} type veth peer name vethOvs{1}{0}'.format(container_name, diff)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "ip link set vethOvs{0}{1} up".format(diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "ip link set veth{0}Ovs{1} up".format(container_name, diff)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "brctl addbr br{0}{1}".format(diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "ifconfig br{0}{1} up".format(diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "brctl addif br{1}{0} veth{0}Ovs{1}".format(container_name, diff)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "sudo ovs-vsctl add-port {2} vethOvs{3}{0} -- set Interface vethOvs{3}{0} ofport_request={1}".format(
            container_name, ovs_port, ovs_name, diff)
        print(basic_cmd)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

    @staticmethod
    def clean_container_bridge_ovs(container_name, ip_destination, ovs_source, diff=''):
        """
        Cleaning container ovs-bridge configuration
        :param container_name:
        :param ip_destination:
        :param ovs_source:
        :param diff:
        :return:
        """
        basic_cmd = "brctl delif br{0}{1} veth{1}Ovs{0}".format(diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "ovs-vsctl del-port {0} vethOvs{1}{2}".format(ovs_source, diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "ip link del dev veth{}Ovs{}".format(container_name, diff)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "ifconfig br{}{} down".format(diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)

        basic_cmd = "brctl delbr br{}{}".format(diff, container_name)
        a, b, c = system_driver.ssh_query(basic_cmd, ip_destination, True)
