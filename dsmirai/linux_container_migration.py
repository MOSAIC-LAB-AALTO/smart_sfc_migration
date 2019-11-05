
import dsmirai.client_broker as client_broker
import dsmirai.intent_based_networking as intent_based_networking
from operator import itemgetter
from dsmirai.persistent_model import helpers
import dsmirai.onos_helpers as onos_helpers
from django.conf import settings
from mirai.models import IaaS, Container, Client
import dsmirai.migration_schedular as mig_sch
from dsmirai import network_evaluator



"""
Code communication: migrate = 002

1/-1 = migrate/not migrate
2 = not present
3 = resources not available
4 = race condition

"""


def migrate(container_id, target_cloud=None):
    """
    Used to allow SDN enabled container to be migrated
    :param container_id:
    :param target_cloud:
    :return:
    """
    queue_name = "migration_queue"
    rmq = client_broker.ClientBroker(queue_name)
    onos = onos_helpers.OnosHelpers()
    intents = intent_based_networking.IntentBasedNetworking()

    print("***********The Global Orchestrator***********")
    print("the server: {}".format(container_id))
    if not helpers.name_control(container_id):
        print("The requested container is already in a another process")
        id_request = helpers.insert_entry(container_id, "4", "002", False)
        return
    else:
        id_request = helpers.insert_entry(container_id, "None", "002", True)
        print("***********The Global Orchestrator***********")
        print("The requested container is not in another process")
        ip_server_container = Container.objects.get(pk=container_id).ip_address
        server_device, server_port_number, ip_vm_server = onos.sdn_host_information(
            settings.IP_SDN_CONTROLLER, ip_server_container)

        print("the device destination is: {}".format(server_device))
        print("the port number destination is: {}".format(server_port_number))
        print("the ip address destination is: {}".format(ip_server_container))

        ip_client_container = Client.objects.get(container_name="c{}".format(container_id)).ip_address
        client_device, client_port_number, ip_vm_client = onos.sdn_host_information(
            settings.IP_SDN_CONTROLLER, ip_client_container)
        print("the device source is: {}".format(client_device))
        print("the port number source is: {}".format(client_port_number))
        print("the ip address source is: {}".format(ip_client_container))

        ovs_in_ip_address = Client.objects.get(container_name="i{}".format(container_id)).ip_address
        ovs_in_device, ovs_in_port_number, ip_vm_ovs_in = onos.sdn_host_information(settings.IP_SDN_CONTROLLER,
                                                                                    ovs_in_ip_address)
        print("the device ovs_in is: {}".format(ovs_in_device))
        print("the port number ovs_in is: {}".format(ovs_in_port_number))
        print("the ip address ovs_in is: {}".format(ovs_in_ip_address))

        ovs_out_ip_address = Client.objects.get(container_name="o{}".format(container_id)).ip_address
        ovs_out_device, ovs_out_port_number, ip_vm_ovs_out = onos.sdn_host_information(settings.IP_SDN_CONTROLLER,
                                                                                       ovs_out_ip_address)
        print("the device ovs_out is: {}".format(ovs_out_device))
        print("the port number ovs_out is: {}".format(ovs_out_port_number))
        print("the ip address ovs_out is: {}".format(ovs_out_ip_address))

        container_name = Container.objects.get(pk=container_id).container_name
        table_statistics = rmq.get_container_resources(container_name, ip_vm_server)
        container_resources = max(table_statistics, key=itemgetter(1, 2))
        ip_source = container_resources[0]
        cpu = container_resources[1]
        ram = container_resources[2]
        print("***********The Global Orchestrator***********")
        print("the ip address of the source vm is: {}".format(ip_source))
        print("the cpu of the chosen container is: {}".format(cpu))
        print("the ram of the chosen container is: {}".format(ram))
        # verify resources needed and avoid ip_source
        if target_cloud is None:
            table_statistics = rmq.verify_resource("star" + queue_name.split('_')[0], "migration", ip_source)
        else:
            target_ip = IaaS.objects.get(pk=target_cloud).iaas_ip
            table_statistics = rmq.verify_resource(target_ip, "creation")

        winner_minion = max(table_statistics, key=itemgetter(1, 2, 3))
        print("***************************************************************")
        print(winner_minion[1])
        print(type(winner_minion[1]))

        print(winner_minion[2])
        print(type(winner_minion[2]))

        print(cpu)
        print(type(cpu))

        print(ram)
        print(type(ram))
        print("***************************************************************")
        # TODO: need to be changed to cover both the server and the ovs-lxc, we assume ovs-lxc == server, thus * 2
        if winner_minion[1] <= cpu * 2 or winner_minion[2] <= ram * 2:
            print("***********The Global Orchestrator***********")
            print("Resources issues, no available resource to host the container in the target destination")
            while helpers.store_db_log(id_request, "3", False) is not False:
                print("DB not yet updated")
            return
        ip_destination = winner_minion[0]
        print("***********The Global Orchestrator***********")
        print("we are able to find a vm destination")
        print("the IP address of the chosen node is: {}".format(ip_destination))

        ovs_source = onos.friendly_ovs_name(client_device, ip_vm_client)
        print("ovs_source is: {}".format(ovs_source))

        old_ovs_destination = onos.friendly_ovs_name(server_device, ip_source)
        print("old_ovs_destination is: {}".format(old_ovs_destination))

        old_ovs_destination_ovs = onos.friendly_ovs_name(ovs_in_device, ip_source)
        print("old_ovs_destination_ovs is: {}".format(old_ovs_destination_ovs))

        ovs_destination = onos.get_ovs(0, ip_destination)
        print("ovs_destination is: {}".format(ovs_destination))

        ovs_destination_ovs = onos.get_ovs(1, ip_destination)
        print("ovs_destination_ovs is: {}".format(ovs_destination_ovs))

        # TODO: maybe to be erased later, as it is used only on traffic  redirection
        mac_ovs_destination = onos.mac_style_ovs_name(ovs_destination, ip_destination)
        print("mac_ovs_destination is: {}".format(mac_ovs_destination))

        mac_ovs_destination_ovs = onos.mac_style_ovs_name(ovs_destination_ovs, ip_destination)
        print("mac_ovs_destination_ovs is: {}".format(mac_ovs_destination_ovs))

        # TODO: here we need a second interface, NO WE DO NOT NEED ANYTHING
        interface_name = ovs_source + ovs_destination_ovs
        print("interface_name is: {}".format(interface_name))

        if not onos.verify_links(settings.IP_SDN_CONTROLLER, client_device, mac_ovs_destination_ovs):

            vxlan_port = helpers.add_vxlan_ip_ports(interface_name)
            print("new vxlan_port is: {}".format(vxlan_port))

            print("starting the VxLAN channel")
            intents.overlay_network(ip_vm_client, ip_destination, ovs_source, ovs_destination_ovs, interface_name,
                                    vxlan_port)
            print("successful VxLAN creation")

        else:
            if not onos.verify_local_distant_devices(settings.IP_SDN_CONTROLLER, client_device,
                                                     mac_ovs_destination_ovs):

                vxlan_port = helpers.get_overlay_port(interface_name)
                print("existing vxlan_port distant is: {}".format(vxlan_port))

            else:
                vxlan_port = 1
                print("existing vxlan_port local is: {}".format(vxlan_port))
        # Setting the IN interface of lxc-ovs
        intents.target_container_bridge_ovs("io{}".format(container_id), ip_destination, ovs_destination_ovs,
                                            ovs_in_port_number)
        # Setting the OUT interface of lxc-ovs
        intents.target_container_bridge_ovs("io{}".format(container_id), ip_destination, ovs_destination_ovs,
                                            ovs_out_port_number, '2')
        # Setting the interface of server
        intents.target_container_bridge_ovs(container_name, ip_destination, ovs_destination,
                                            server_port_number)
        print("SDN network established")
        print("Gathering the migration image info")
        LXC_IMAGE = rmq.get_container_image(ip_source, container_name)
        LXC_OVS_IMAGE = rmq.get_container_image(ip_source, "io{}".format(container_id))
        print("***********The Global Orchestrator***********")
        print("searching for a possible partial migration .....")

        result = 0
        if rmq.management_task(ip_source, "migration"):
            # TODO: here we need to call another layer to apply our approaches
            '''
            if rmq.part_migration_check(LXC_IMAGE, ip_destination, container_name):
                print("***********The Global Orchestrator***********")
                print("Para-Migration detected")
                print("starting the partial migration")
            else:
                print("***********The Global Orchestrator***********")
                print("Full-Migration action")
                print("starting a Full-Migration")
            result = rmq.migration(container_name, ip_destination, settings.NUM_ITERATION, ip_source)
            '''
        print("Starting the SFC-Migration Schedular ...")
        image_template = "nginxBKserver"
        image_template_ovs = "lxc-ovs"
        # bandwidth with kilobytes/s
        # TODO: The Integration Must happen here, I would suggest in migration scheduler file better (good).
        """
        Here we need to select a value for bandwidth based on a trained model. 
        Scenario:
        1/ The migration should start until the Dump for container1 and container2. 
        2/ Then, we gather both page_numbers and the dump_size.
        3/ We use page_numbers and the dump_size to get two bandwidth values.
        4/ We execute the dump_restore() function to restore.
        
        Code Modifications:
        1/ Heavy changes in mig_sch (i.e. migration scheduler file).
            1/ Changes are in basic_sfc_migration() function, for now the function is doing well until sending the dump 
            files over the network.
            2/ We need to make it stops when doing the pre-dumps, we need to make it stops until doing dumps then 
            collect the dump size and also the memory pages as entries for the model.
            3/ call the model an chose two bandwidth values.
            4/ In dump_restore() function we need to send the dump file then restore. 
        
        """
        print("Getting bandwidth Information")
        network_evaluator.run()
        bandwidth = 3000000
        full_bandwidth = helpers.adjust_iaas_performance(ip_source, ip_destination, bandwidth)
        if full_bandwidth == 0:
            raise TypeError('not enough BW')
        result = mig_sch.dummy_function(container_name, "io{}".format(container_id), LXC_IMAGE, LXC_OVS_IMAGE,
                                        image_template, image_template_ovs, ip_source, ip_destination, settings.NUM_ITERATION,
                                        "wait", full_bandwidth)

        if target_cloud is None:
            target_cloud = IaaS.objects.get(iaas_ip=ip_destination).id
        helpers.tracking_iaas_container(container_id, IaaS.objects.get(pk=target_cloud))
        print("the iaas for the migration is: {}".format(target_cloud))

        print("deleting the SDN network in the source host")
        intent_priority = helpers.get_intent_priority(str(container_id))
        intents.network_redirection_sfc(settings.IP_SDN_CONTROLLER, client_device, mac_ovs_destination,
                                        client_port_number, server_port_number, mac_ovs_destination_ovs,
                                        ovs_in_port_number, ovs_out_port_number, vxlan_port, ip_client_container,
                                        ip_server_container, int(intent_priority))
        intents.network_redirection_sfc_2(settings.IP_SDN_CONTROLLER, client_device, client_port_number, vxlan_port,
                                          ip_server_container, int(intent_priority))
        intents.clean_container_bridge_ovs(container_name, ip_source, old_ovs_destination)
        intents.clean_container_bridge_ovs(container_name, ip_source, old_ovs_destination_ovs)
        intents.clean_container_bridge_ovs(container_name, ip_source, old_ovs_destination_ovs, "2")
        onos.setup_turn_around_node(settings.IP_SDN_CONTROLLER, ovs_in_ip_address, mac_ovs_destination_ovs)
        onos.setup_turn_around_node(settings.IP_SDN_CONTROLLER, ovs_out_ip_address, mac_ovs_destination_ovs)
        answer = rmq.validate_migration(container_name, ip_destination, ip_client_container)
        if answer != 1:
            print("validate migration failed")
            return "Error"
        while helpers.store_db_log(id_request, str(result), False) is not False:
            print("DB not yet updated")
        if result != 1:
            print("system migration part failed")
            return "Error"

        return container_name
