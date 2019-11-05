import dsmirai.client_broker as client_broker
import datetime
from dsmirai.persistent_model import helpers
from mirai import tasks as trigger
import uuid
from mirai.models import IaaS, Container




"""
0 = start the trigger
1 = successful trigger event
"""
queue_name = "rat_queue"
trigger_type = "rat_trigger"


# For using the rat_trigger as a daemon put it into an infinite loop containing a sleep operation
def rat_trigger(iaas_name=None):
    """
    :param iaas_name:
    :return:
    """
    # iaas_name="None" == start the trigger in all the nodes
    rmq = client_broker.ClientBroker(queue_name)
    if iaas_name is None:
        a = rmq.rat_trigger("star" + queue_name.split('_')[0])
    else:
        iaas_ip = IaaS.objects.get(pk=iaas_name).iaas_ip
        a = rmq.rat_trigger(iaas_ip)
    print("The returned value is {}".format(a))
    ntm = decision_rat(a)

    print(type(ntm))
    print(ntm)
    for key, value in ntm.items():
        container_id = Container.objects.get(container_name=value['container']).id
        # TODO: verify if not iaas_ip instead of iaas_name.
        iaas_id = IaaS.objects.get(iaas_ip=value['VM_ip']).id
        if not helpers.name_control(container_id):
            print("***************************************************************************************")
            print("***************************************************************************************")
            print("container {} is in another action waiting for it to finish".format(value['container']))
            print("***************************************************************************************")
            print("***************************************************************************************")

        else:
            print("the api_rat_trigger is activated")
            id_request = helpers.insert_entry(container_id, "None", "003", True)
            request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                       "migrate_rat", datetime.datetime.now(), "0")
            print("migrate the container {} localized in {}".format(value['container'], value['VM_ip']))
            while helpers.store_db_log(id_request, "1", False) is not False:
                print("DB not yet updated")
            if trigger.lxc_migration.delay(container_id) == value['container']:
                helpers.update_triggers_entry(request_id, "1")
            else:
                helpers.update_triggers_entry(request_id, "2")


def decision_rat(solver):
    """
    Resource Availability Trigger enabler
    :param solver:
    :return container to be migrated:
    """
    ntm = {}
    i = 0
    print(solver)
    for key, value in solver.items():

        while value['live_disk'] > value['disk'] * 0.8 and bool(solver[key]['containers']):
            print("*********************** DISK Section ***********************")
            disk_max = 0
            disk_key_max = "init"
            for kk, vv in solver[key]['containers'].items():
                if disk_max < vv['disk']:
                    disk_max = vv['disk']
                    disk_key_max = kk
            value['live_disk'] = value['live_disk'] - disk_max
            value['live_ram'] = value['live_ram'] - solver[key]['containers'][disk_key_max]['ram']
            value['live_cpu'] = value['live_cpu'] - solver[key]['containers'][disk_key_max]['cpu']

            ntm['node_to_migrate_{}'.format(i)] = {'VM_ip': key, 'container': disk_key_max}
            i = i + 1
            del solver[key]['containers'][disk_key_max]

        while value['live_ram'] > value['ram'] * 0.8 and bool(solver[key]['containers']):
            print("*********************** RAM Section ***********************")
            ram_max = 0
            ram_key_max = "init"
            for kk, vv in solver[key]['containers'].items():
                if ram_max < vv['ram']:
                    ram_max = vv['ram']
                    ram_key_max = kk
            value['live_ram'] = value['live_ram'] - ram_max
            value['live_disk'] = value['live_disk'] - solver[key]['containers'][ram_key_max]['disk']
            value['live_cpu'] = value['live_cpu'] - solver[key]['containers'][ram_key_max]['cpu']
            ntm['node_to_migrate_{}'.format(i)] = {'VM_ip': key, 'container': ram_key_max}
            i = i + 1

            del solver[key]['containers'][ram_key_max]

        while value['live_cpu'] > value['cpu'] * 0.4 and bool(solver[key]['containers']):
            print("*********************** CPU Section ***********************")
            cpu_max = 0
            cpu_key_max = "init"
            for kk, vv in solver[key]['containers'].items():
                if cpu_max < vv['cpu']:
                    cpu_max = vv['cpu']
                    cpu_key_max = kk
            value['live_cpu'] = value['live_cpu'] - cpu_max
            print(value['live_cpu'])
            value['live_ram'] = value['live_ram'] - solver[key]['containers'][cpu_key_max]['ram']
            print(value['live_ram'])
            value['live_disk'] = value['live_disk'] - solver[key]['containers'][cpu_key_max]['disk']
            print(value['live_disk'])
            ntm['node_to_migrate_{}'.format(i)] = {'VM_ip': key, 'container': cpu_key_max}
            i = i + 1

            del solver[key]['containers'][cpu_key_max]

    return ntm
