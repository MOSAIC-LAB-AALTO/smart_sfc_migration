import dsmirai.onos_helpers as onos_helpers
import dsmirai.client_broker as client_broker
import time


def clean_onos():
    """
    Used for cleaning ONOS, could be erased as it is just for demo tests
    :return:
    """
    rmq = client_broker.ClientBroker("iaas_consumption_queue")
    x = rmq.environment_cleaner()
    print(x)
    time.sleep(3)
    ip_sdn_controller = "195.148.125.90"
    onos = onos_helpers.OnosHelpers()
    devices = onos.get_sdn_devices(ip_sdn_controller)
    intents = onos.get_all_intents(ip_sdn_controller)
    hosts = onos.get_sdn_hosts(ip_sdn_controller)
    print(devices)
    print(intents)
    print(hosts)
    onos.delete_hosts(ip_sdn_controller, hosts)
    onos.delete_intents(ip_sdn_controller, intents)
    while len(intents) != 0:
        intents = onos.get_all_intents(ip_sdn_controller)
        onos.delete_intents(ip_sdn_controller, intents)
    onos.delete_devices(ip_sdn_controller, devices)
    return 1


