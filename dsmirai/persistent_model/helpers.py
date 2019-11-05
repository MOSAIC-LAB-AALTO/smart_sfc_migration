from mirai.models import Log
from mirai.models import Triggers
from mirai.models import IaaS
from mirai.models import Container
from mirai.models import Client
from mirai.models import IaaSPerformance
import datetime
import random
from netaddr import IPNetwork
from mirai.models import DataSet


# Set of function for dealing the Database
# TODO: we need to see how we can scale this function
def get_ip_port_sdn_network():
    ip_list = IPNetwork("172.16.207.0/24")
    ip_iteration = 0
    ip_address = ""
    while ip_iteration == 0:
        ip_list = list(ip_list)
        # Ansible ports and the third is the broadcast address
        ip_list = ip_list[3:-1]
        random.shuffle(ip_list)
        ip_address = random.choice(ip_list).format()
        if Container.objects.filter(ip_address=ip_address).count() == 0:
            ip_iteration = 1
    return ip_address, ip_address.split(".")[3]


def add_entry_ip_ports(container_id):
    """
    Handle port/Ip attribution
    :param container_id:
    :return:
    """
    ip_address, port_number = get_ip_port_sdn_network()
    process = Container.objects.get(pk=container_id)
    process.ip_address = ip_address
    process.port = port_number
    process.save()
    return process.container_name, process.ram, process.cpu, process.iaas, process.application_type, process.ip_address\
        , process.port


def store_db_log(id, result, usage):
    """
    Store information logs, related to unique usage and general information
    :param id:
    :param result:
    :param usage:
    :return:
    """
    process = Log.objects.get(pk=id)
    process.result = result
    process.usage = usage
    process.save()
    return process.usage


def tracking_iaas_container(container_id, iaas):
    """
    used to update container's location
    :param container_id:
    :param iaas:
    :return:
    """
    process = Container.objects.get(pk=container_id)
    process.iaas = iaas
    process.save()
    return process.iaas


def name_control(container_id):
    """
    used to verify the usage of the container
    :param container_id:
    :return:
    """
    return Log.objects.filter(container__id=container_id, usage=True).count() != 1


def add_vxlan_ip_ports(interface_name):
    """
    related to VxLAN port attribution, could be enhanced or optimized
    :param interface_name:
    :return:
    """
    ip_address, port_number = get_ip_port_sdn_network()
    Container(container_name="overlay_{}".format(interface_name), ip_address=ip_address, port=port_number).save()
    return port_number


def insert_entry_client(container_id, container_name):
    """
    Store client information
    :param container_id:
    :param container_name:
    :return:
    """
    ip_address, port_number = get_ip_port_sdn_network()
    x = Client(container_id=container_id, container_name=container_name, ip_address=ip_address,
               port=port_number)
    x.save()
    return x.container_name, x.ip_address, x.port


def insert_entry(container_id, result, code, usage):
    """
    store containers' information
    :param container_id:
    :param result:
    :param code:
    :param usage:
    :return:
    """
    x = Log(container_id=container_id, result=result, code=code, usage=usage)
    x.save()
    return x.pk


def get_overlay_port(interface_name):
    """
    get VxLAN port
    :param interface_name:
    :return:
    """
    x = Container.objects.filter(container_name="overlay_{}".format(interface_name)).first()
    return x.port


def get_intent_priority(container_id):
    """
    get intent priority to do the traffic re-direction
    :param container_id:
    :return:
    """
    return (Log.objects.filter(container__id=container_id, code="002").count() + 1) * 200



'''
helper related to the Triggers
'''


def insert_entry_triggers(container_id, iaas_id, trigger_type, trigger_action, trigger_time, trigger_result):
    """
    store triggers information for later processing
    :param container_id:
    :param iaas_id:
    :param trigger_type:
    :param trigger_action:
    :param trigger_time:
    :param trigger_result:
    :return:
    """
    x = Triggers(container_id=container_id, iaas_id=iaas_id, trigger_type=trigger_type,
                 trigger_action=trigger_action, trigger_time=trigger_time, trigger_result=trigger_result)
    x.save()
    return x.pk


def update_initial_trigger_entry(container_name, iaas_name, trigger_action, trigger_result):
    process = Triggers.objects.filter(trigger_action="api_call").last()
    process.container_name = container_name
    process.iaas_name = iaas_name
    process.trigger_action = trigger_action
    process.trigger_result = trigger_result
    process.save()


def update_triggers_entry(id, trigger_result):
    process = Triggers.objects.get(pk=id)
    process.trigger_result = trigger_result
    process.save()


'''
helper related to the IaaS discovery
'''


def available_iaas():
    tab = {}
    for entry in IaaS.objects.filter(iaas_state=False, iaas_configuration=False):
            tab[entry.id] = entry.iaas_ip
    return tab


def update_after_failure(ip_address, state, iaas_configuration):
    process = IaaS.objects.get(iaas_ip=ip_address)
    process.iaas_state = state
    process.iaas_configuration = iaas_configuration
    process.iaas_date_configuration = datetime.datetime.now()
    process.save()


def update_state_iaas(ip_address, state):
    process = IaaS.objects.get(iaas_ip=ip_address)
    process.iaas_state = state
    process.iaas_date_discovery = datetime.datetime.now()
    process.save()


def update_configuration_iaas(ip_address, iaas_configuration):
    process = IaaS.objects.get(iaas_ip=ip_address)
    process.iaas_configuration = iaas_configuration
    process.iaas_date_configuration = datetime.datetime.now()
    process.save()


def verify_infinite_handler(ip_address):
    return IaaS.objects.filter(iaas_ip=ip_address, iaas_state=False, iaas_configuration=False).count() == 1


def number_minions():
    return IaaS.objects.filter(iaas_state=True, iaas_configuration=True).count()


def list_of_iaas():
    tab = []
    clouds = IaaS.objects.filter(iaas_state=True, iaas_configuration=True)
    for i in range(len(clouds)):
        tab.append(clouds[i].iaas_ip)
    return tab


def insert_entry_iaas_performance(iaas_id_1, iaas_id_2, bytes_transmitted, bits_s, megabits_s, megabytes_s):
    """
    used for monitoring VM/IaaS/FRD usage
    :param iaas_id_1:
    :param iaas_id_2:
    :param bytes_transmitted:
    :param bits_s:
    :param megabits_s:
    :param megabytes_s:
    :return:
    """
    x = IaaSPerformance(iaas_source_id=iaas_id_1, iaas_destination_id=iaas_id_2, bytes_transmitted=bytes_transmitted,
                        bits_s=bits_s, megabits_s=megabits_s, megabytes_s=megabytes_s)
    x.save()
    return x.pk


def adjust_iaas_performance(iaas_ip_1, iaas_ip_2, kilobytes_s):
    """
    used for limiting the used bandwidth when using network-aware migrations
    :param iaas_ip_1:
    :param iaas_ip_2:
    :param kilobytes_s:
    :return:
    """
    process = IaaSPerformance.objects.filter(iaas_source__iaas_ip=iaas_ip_1, iaas_destination__iaas_ip=iaas_ip_2).last()
    if process.megabytes_s * 1000 > kilobytes_s:
        print('bits_s before: {}'.format(process.bits_s))
        process.bits_s = process.bits_s - kilobytes_s * 8000
        print('megabits_s before: {}'.format(process.megabits_s))
        process.megabits_s = process.megabits_s - (kilobytes_s / 125)
        print('megabytes_s before: {}'.format(process.megabytes_s))
        process.megabytes_s = process.megabytes_s - (kilobytes_s / 1000)

        process.save()
        print('bits_s after: {}'.format(process.bits_s))
        print('megabits_s after: {}'.format(process.megabits_s))
        print('megabytes_s after: {}'.format(process.megabytes_s))

        return kilobytes_s
    else:
        return process.megabytes_s * 1000


def db_cleaner_():
    """
    used for fast testing cases to clean the database
    :return:
    """
    for i in IaaSPerformance.objects.all():
        i.delete()
    for i in IaaS.objects.all():
        i.delete()
    for i in Container.objects.all():
        i.delete()
    for i in Client.objects.all():
        i.delete()

    print('IaaSPerformance: ')
    print(IaaSPerformance.objects.all())
    print('IaaS: ')
    print(IaaS.objects.all())
    print('Container: ')
    print(Container.objects.all())
    print('Client: ')
    print(Client.objects.all())


# Building the Data Set
def insert_data_set(cpu_container, ram_container, cpu_iaas, ram_iaas, disk_iaas, application_type):
    x = DataSet(cpu_container=cpu_container, ram_container=ram_container, cpu_iaas=cpu_iaas, ram_iaas=ram_iaas,
                disk_iaas=disk_iaas, application_type=application_type)
    x.save()
    return x.pk


def update_data_set_1(dump_size, mem_pages, disk_container, pre_dump_size, pre_dump_time, max_bandwidth):
    process = DataSet.objects.filter().last()
    process.dump_size = dump_size
    process.mem_pages = mem_pages
    process.disk_container = disk_container
    process.pre_dump_size = pre_dump_size
    process.pre_dump_time = pre_dump_time
    process.max_bandwidth = max_bandwidth
    process.save()


def update_data_set_2(success, bandwidth_action, downtime, migration_time):
    process = DataSet.objects.filter().last()
    process.success = success
    process.bandwidth_action = bandwidth_action
    process.downtime = downtime
    process.migration_time = migration_time
    process.save()
