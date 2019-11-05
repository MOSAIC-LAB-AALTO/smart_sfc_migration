from dsmirai.persistent_model import helpers
import dsmirai.client_broker as client_broker
from mirai.models import IaaS
import time


def get_active_sessions(list_of_clouds):
    """
    Helper used for getting clients/servers IP addresses
    :param list_of_clouds:
    :return:
    """
    i = 1
    tab = {}
    while i < len(list_of_clouds):
        tab[list_of_clouds[i]] = i
        i += 1
    return tab


def get_client_server_pairs(list_of_clouds):
    """
    Helper for getting client/server pairs to use IPerf
    :param list_of_clouds:
    :return client/server pairs:
    """
    s = set()
    tab = {}
    k = 0
    for i in range(len(list_of_clouds)):
        s.add(i)
        for j in set(range(len(list_of_clouds))) - s:
            tab[k] = {"client": list_of_clouds[i], "server": list_of_clouds[j]}
            k += 1
    return tab


def run():
    """
    Used to gather available bandwidth between any given two nodes in the network architecture
    :return:
    """
    queue_name = "iaas_consumption_queue"
    rmq = client_broker.ClientBroker(queue_name)
    list_of_clouds = helpers.list_of_iaas()
    print("Starting the servers ....")
    active_sessions = get_active_sessions(list_of_clouds)
    rmq.activate_servers("star" + queue_name.split('_')[0], active_sessions)
    time.sleep(3)
    print("Starting the clients processes ....")
    client_server = get_client_server_pairs(list_of_clouds)
    results = rmq.network_evaluator("star" + queue_name.split('_')[0], client_server)
    print(results)
    i = 0
    for key, value in client_server.items():
        helpers.insert_entry_iaas_performance(IaaS.objects.get(iaas_ip=value["client"]).id,
                                              IaaS.objects.get(iaas_ip=value["server"]).id, results[i][0],
                                              results[i][1], results[i][2], results[i][3])
        i += 1


def bandwidth_live_evaluator():
    """
    Used to monitor bandwidth
    :return:
    """
    queue_name = "iaas_consumption_queue"
    rmq = client_broker.ClientBroker(queue_name)
    print('start the infinite time monitoring')
    rmq.monitor_bandwidth("star" + queue_name.split('_')[0])
    print('done')
