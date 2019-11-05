import dsmirai.client_broker as client_broker
from dsmirai.persistent_model import helpers
from django.conf import settings
from mirai.models import IaaS, Container, Client
import dsmirai.onos_helpers as onos_helpers


def delete(container_id, container_name, ip_server_container):
    """
    Delete an SDN container
    :param container_id:
    :param container_name:
    :param ip_server_container:
    :return:
    """
    queue_name = "creation_queue"
    rmq = client_broker.ClientBroker(queue_name)
    onos = onos_helpers.OnosHelpers()

    if not helpers.name_control(container_id):
        print("The requested container is already in a another process")
        id_request = helpers.insert_entry(container_id, "4", "002", False)
        return
    else:
        id_request = helpers.insert_entry(container_id, "None", "002", True)
        print("***********The Global Orchestrator***********")
        print("The requested container is not in another process")
        server_device, server_port_number, ip_vm_server = onos.sdn_host_information(
            settings.IP_SDN_CONTROLLER, ip_server_container)

        print("the device destination is: {}".format(server_device))
        print("the port number destination is: {}".format(server_port_number))
        print("the ip address destination is: {}".format(ip_server_container))

        ip_client_container = Client.objects.get(container__id=container_id).ip_address
        client = Client.objects.get(container__id=container_id).container_name
        client_device, client_port_number, ip_vm_client = onos.sdn_host_information(
            settings.IP_SDN_CONTROLLER, ip_client_container)
        print("the device source is: {}".format(client_device))
        print("the port number source is: {}".format(client_port_number))
        print("the ip address source is: {}".format(ip_client_container))

        ovs_source = onos.friendly_ovs_name(client_device, ip_vm_client)
        print("ovs_source is: {}".format(ovs_source))

        ovs_destination = onos.friendly_ovs_name(server_device, ip_vm_server)
        print("ovs_destination is: {}".format(ovs_destination))

        if ip_vm_server == ip_vm_client:
            if rmq.delete_container(container_name, ovs_destination, ip_vm_server, client, ovs_source) is True or "True":
                print("deleted both server and client on the same hosts")

        else:
            if rmq.delete_container(container_name, ip_vm_server, ovs_destination) is True or "True":
                if rmq.delete_container(client, ip_vm_client, ovs_source) is True or "True":
                    print("deleted both server and client on different hosts")
        Client.objects.get(container__id=container_id).delete()
    return container_name
