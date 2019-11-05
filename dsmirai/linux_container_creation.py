import dsmirai.client_broker as client_broker
import dsmirai.intent_based_networking as intent_based_networking
from operator import itemgetter
from dsmirai.persistent_model import helpers
import dsmirai.video_streaming_handler as vsh
from django.conf import settings
from mirai.models import IaaS, Container


def create(container_id):
    """
    create an SDN enabled container
    :param container_id:
    :return: container_name
    """
    queue_name = "creation_queue"
    rmq = client_broker.ClientBroker(queue_name)
    intents = intent_based_networking.IntentBasedNetworking()

    container_name, ram, cpu, container_placement, application_type, server_ip_address, server_port_number = \
        helpers.add_entry_ip_ports(container_id)

    id_request = helpers.insert_entry(container_id, "None", "001", True)
    client, client_ip_address, client_port_number = helpers.insert_entry_client(container_id, "c{}".format(container_id))
    ovs_in, ovs_in_ip_address, ovs_in_port_number = helpers.insert_entry_client(container_id, "i{}".format(container_id))
    ovs_out, ovs_out_ip_address, ovs_out_port_number = helpers.insert_entry_client(container_id, "o{}".format(container_id))




    print(f'''
    __________ The Global Orchestrator __________
    the server: {container_name}
    the port number for the server is: {server_port_number}
    the ip address for the server is: {server_ip_address}
    cpu: {cpu}
    ram: {ram}
    placement id: {container_placement.id}
    application_type: {application_type}
    the client: {client}
    the ip address for the client is: {client_ip_address} 
    the port number for the client is: {client_port_number}
    the ovs-in: {ovs_in}
    the ip address for the ovs-in is: {ovs_in_ip_address} 
    the port number for the ovs-in is: {ovs_in_port_number}
    the ovs-out: {ovs_out}
    the ip address for the ovs-out is: {ovs_out_ip_address} 
    the port number for the ovs-out is: {ovs_out_port_number}
    
    ''')


    if container_placement:

        ip_address = container_placement.iaas_ip

        if not ip_address:
            raise TypeError('unknown iaas')

        print('the ip address of the IAAS is: {ip_address}')
        table_statistics = rmq.verify_resource(ip_address, "creation")

    else:
        table_statistics = rmq.verify_resource("star" + queue_name.split('_')[0], "creation")

    winner_minion = max(table_statistics, key=itemgetter(1, 2, 3))

    if 'M' in ram:
        int_ram = int(ram.split('M')[0])
    else:
        int_ram = int(ram.split('G')[0])

    # TODO: for the time being we just suppose that the cpu and ram are the same for lxc-ovs and server.
    if winner_minion[1] < int(cpu) * 2 and winner_minion[2] < int_ram * 2:
        while helpers.store_db_log(id_request, "3", False) is not False:
            print("DB not yet updated")

        raise TypeError('resources issue')

    creation_ip_address = winner_minion[0]

    if application_type != "video":
        # TODO: to be implemented later when adding new VNFs
        raise TypeError(f'application type {application_type} has not implemented yet')
    else:
        print('start the creation itself ....')
        result = 0
        if rmq.management_task(creation_ip_address, "creation"):
            result = rmq.create_container(container_name, client, cpu, ram, server_ip_address,
                                          server_port_number, client_ip_address, client_port_number,
                                          "io{}".format(container_id), ovs_in_ip_address, ovs_in_port_number,
                                          ovs_out_ip_address, ovs_out_port_number, creation_ip_address)

        if not container_placement:

            container_placement = IaaS.objects.get(iaas_ip=creation_ip_address).iaas_name
            helpers.tracking_iaas_container(container_id, container_placement)
            print(f'the id of iaas for the creation is: {container_placement}')
        intents.initial_sfc_path(settings.IP_SDN_CONTROLLER, server_ip_address, client_ip_address, ovs_in_ip_address,
                                 ovs_out_ip_address)

        print(f'''The result is: {result}''')

        if result != 1:
            raise TypeError(f'create_container failed, result {result}')

        vsh.enable_remote_video_streaming(creation_ip_address, str(int(client_port_number) + 1024),
                                          client_ip_address)

        while helpers.store_db_log(id_request, str(result), False) is not False:
            print("DB not yet updated")

    return container_name
