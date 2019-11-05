from mirai.models import Log, Triggers, IaaS, IaaSConsumption, Container, Client
import time
import dsmirai.client_broker as client_broker
import random
import numpy as np
import datetime
from django.conf import settings


# file used for user interface
# TODO: use real call to IaaS to gather the number of running containers.
def get_online_container():
    rmq = client_broker.ClientBroker("iaas_consumption_queue")
    return rmq.live_container_number()


def container_dashboard_resources(container_name, iaas_name):
    rmq = client_broker.ClientBroker("iaas_consumption_queue")
    iaas_ip = IaaS.objects.get(iaas_name=iaas_name).iaas_ip
    return rmq.container_dashboard_resources(container_name, iaas_ip)


def container_video_url(container_name):
    return "http://{}:{}".format(settings.ORCHESTRATOR_IP, int(Client.objects.get(container_name=container_name).port)
                                 + 1024)


# Dashboard_Resource_Consumption
def insert_entry_iaas_consumption(iaas_id, iaas_cpu, iaas_ram, iaas_disk, iaas_time):
    x = IaaSConsumption(iaas_id=iaas_id, iaas_cpu=iaas_cpu, iaas_ram=iaas_ram, iaas_disk=iaas_disk,
                        iaas_time=iaas_time)
    x.save()
    return x.pk


def iaas_resource_consumption():
    """
    Daemon for monitoring VM/IaaS and storing in a Database
    :return:
    """
    queue_name = "iaas_consumption_queue"
    rmq = client_broker.ClientBroker(queue_name)
    while True:
        table_statistics = rmq.verify_resource("star" + queue_name.split('_')[0], "creation")
        for i in range(len(table_statistics)):
            iaas_id = IaaS.objects.get(iaas_ip=str(table_statistics[i][0])).id
            insert_entry_iaas_consumption(iaas_id, table_statistics[i][1], table_statistics[i][2],
                                          table_statistics[i][3], datetime.datetime.now())
        time.sleep(30)
