import dsmirai.client_broker as client_broker
from dsmirai.persistent_model import helpers
import datetime
from mirai import tasks as trigger
from mirai.models import IaaS, Container



"""
0 = start the trigger
1 = successful trigger event
2 = failure in the trigger event
"""

cpu_threshold = 0.7
ram_threshold = 0.7
queue_name = "sct_queue"
trigger_type = "sct_trigger"


# For using the rat_trigger as a daemon put it into an infinite loop containing a sleep operation
def sct_trigger(iaas_name=None):
    """
    :param iaas_name:
    :return:
    """
    # iaas_name="None" == start the trigger in all the nodes
    rmq = client_broker.ClientBroker(queue_name)
    if iaas_name is None:
        a = rmq.sct_trigger("star" + queue_name.split('_')[0])
    else:
        iaas_ip = IaaS.objects.get(pk=iaas_name).iaas_ip
        a = rmq.sct_trigger(iaas_ip)

    print("The returned value is {}".format(a))
    ntm = decision_sct(a)
    print("the type of the ntm is:")
    print(type(ntm))
    print(ntm)
    for key, value in ntm.items():
        container_id = Container.objects.get(container_name=value['container']).id
        # TODO: verify if not iaas_ip instead of iaas_name.
        iaas_id = IaaS.objects.get(iaas_ip=value['VM_ip']).id
        if not helpers.name_control(container_id):
            print("container {} is in another action waiting for it to finish".format(value['container']))
        else:
            print("the sct_trigger is activated")
            id_request = helpers.insert_entry(container_id, "None", "003", True)
            if 'node_to_migrate_CPU_RAM' in key:

                request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                           "migrate_cpu_ram", datetime.datetime.now(), "0")
                print("migrate both of the cpu and the ram")
                if not rmq.scale_up(value['container'], value['VM_ip'], "scale_up_cpu_ram", value['cpu'], value['ram']):
                    print("Unable to migrate both of the cpu and the ram")
                    helpers.update_triggers_entry(request_id, "2")
                else:
                    while helpers.store_db_log(id_request, "1", False) is not False:
                        print("DB not yet updated")
                    if trigger.lxc_migration.delay(container_id) == value['container']:
                        helpers.update_triggers_entry(request_id, "1")
                    else:
                        helpers.update_triggers_entry(request_id, "2")
            elif 'node_to_migrate_CPU' in key:
                request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                           "migrate_cpu", datetime.datetime.now(), "0")
                print("migrate the cpu")
                if not rmq.scale_up(value['container'], value['VM_ip'], "scale_up_cpu", value['cpu'], 0):
                    print("Unable to migrate the cpu")
                    helpers.update_triggers_entry(request_id, "2")
                else:
                    while helpers.store_db_log(id_request, "1", False) is not False:
                        print("DB not yet updated")
                    if trigger.lxc_migration.delay(container_id) == value['container']:
                        helpers.update_triggers_entry(request_id, "1")
                    else:
                        helpers.update_triggers_entry(request_id, "2")
            elif 'node_to_migrate_RAM' in key:
                request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                           "migrate_ram", datetime.datetime.now(), "0")
                print("migrate the ram")
                if not rmq.scale_up(value['container'], value['VM_ip'], "scale_up_ram", value['ram'], 0):
                    print("Unable to migrate the ram")
                    helpers.update_triggers_entry(request_id, "2")
                else:
                    while helpers.store_db_log(id_request, "1", False) is not False:
                        print("DB not yet updated")
                    if trigger.lxc_migration.delay(container_id) == value['container']:
                        helpers.update_triggers_entry(request_id, "1")
                    else:
                        helpers.update_triggers_entry(request_id, "2")
            elif 'node_to_scaleUp_CPU_RAM' in key:
                request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                           "create_cpu_ram", datetime.datetime.now(), "0")
                print("scale up both of the cpu and the ram")
                if not rmq.scale_up(value['container'], value['VM_ip'], "scale_up_cpu_ram", value['cpu'],
                                    value['ram']):
                    print("Unable to scale up both of the cpu and the ram")
                    helpers.update_triggers_entry(request_id, "2")
                else:
                    helpers.update_triggers_entry(request_id, "1")
                while helpers.store_db_log(id_request, "1", False) is not False:
                    print("DB not yet updated")
            elif 'node_to_scaleUp_CPU' in key:
                request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                           "scale_cpu", datetime.datetime.now(), "0")
                print("scale up the cpu")
                if not rmq.scale_up(value['container'], value['VM_ip'], "scale_up_cpu", value['cpu'], 0):
                    print("Unable to scale ip the cpu")
                    helpers.update_triggers_entry(request_id, "2")
                else:
                    helpers.update_triggers_entry(request_id, "1")
                while helpers.store_db_log(id_request, "1", False) is not None:
                    print("DB not yet updated")
            elif 'node_to_scaleUp_RAM' in key:
                request_id = helpers.insert_entry_triggers(container_id, iaas_id, trigger_type,
                                                           "scale_ram", datetime.datetime.now(), "0")
                print("scale up the ram")
                if not rmq.scale_up(value['container'], value['VM_ip'], "scale_up_ram", value['ram'], 0):
                    print("Unable to scale ip the ram")
                    helpers.update_triggers_entry(request_id, "2")
                else:
                    helpers.update_triggers_entry(request_id, "1")
                while helpers.store_db_log(id_request, "1", False) is not None:
                    print("DB not yet updated")


def decision_sct(solver):
    """
    Service Consumption Trigger enabler
    :param solver:
    :return container to be scaled up/down or migrated:
    """
    ntm = {}
    i = 0
    err = 0
    err2 = 0
    ram_cpu = 0
    for key, value in solver.items():
        if bool(solver[key]['containers']):
            for kk, vv in solver[key]['containers'].items():

                # Implementing semaphore, logic both the memory and the cpu or nothing
                if vv['live_ram'] > vv['ram'] * ram_threshold:
                    if value['vm_ram'] > 1024:
                        if vv['cpu'] * (vv['live_cpu']) > vv['cpu'] * cpu_threshold:
                            if value['vm_cpu'] > 1:
                                value['vm_ram'] = value['vm_ram'] - 1024
                                value['vm_cpu'] = value['vm_cpu'] - 1
                                ntm['node_to_scaleUp_CPU_RAM_{}'.format(i)] = \
                                    {'VM_ip': key, 'container': kk, 'ram': 1024, 'cpu': 1}
                                err = 1
                                print("SCALE UP BOTH THE MEMORY AND THE CPU")

                            else:
                                err2 = 1
                                ntm['node_to_migrate_CPU_RAM_{}'.format(i)] = \
                                    {'VM_ip': key, 'container': kk, 'cpu': 1, 'ram': 1024}
                                print("Scale up the memory")
                                print("MIGRATE NOT ENOUGH CPU RESOURCES")

                        else:
                            value['vm_ram'] = value['vm_ram'] - 1024
                            ntm['node_to_scaleUp_RAM_{}'.format(i)] = \
                                {'VM_ip': key, 'container': kk, 'ram': 1024}
                            print("SCALE UP THE MEMORY")
                    else:
                        ram_cpu = 1

                if err != 1 and err2 != 1:
                    if vv['cpu'] * (vv['live_cpu']) > vv['cpu'] * cpu_threshold:
                        if value['vm_cpu'] > 1:
                            if vv['live_ram'] > vv['ram'] * ram_threshold:
                                if value['vm_ram'] > 1024:
                                    value['vm_ram'] = value['vm_ram'] - 1024
                                    value['vm_cpu'] = value['vm_cpu'] - 1
                                    print("SCALE UP BOTH THE MEMORY AND THE CPU")
                                else:
                                    ntm['node_to_migrate_CPU_RAM_{}'.format(i)] = \
                                        {'VM_ip': key, 'container': kk, 'ram': 1024, 'cpu': 1}
                                    ram_cpu = 0
                                    print("scale up the cpu")
                                    print("MIGRATE NOT ENOUGH MEMORY RESOURCES")
                            else:
                                value['vm_cpu'] = value['vm_cpu'] - 1
                                ntm['node_to_scaleUp_CPU_{}'.format(i)] = \
                                    {'VM_ip': key, 'container': kk, 'cpu': 1}
                                print("SCALE UP THE CPU")
                        else:
                            if ram_cpu == 1:
                                ntm['node_to_migrate_CPU_RAM_{}'.format(i)] = \
                                    {'VM_ip': key, 'container': kk, 'ram': 1024, 'cpu': 1}
                                ram_cpu = 0
                                print("MIGRATE NOT ENOUGH CPU AND RAM RESOURCES")
                            else:
                                # to be erased
                                ntm['node_to_migrate_CPU_{}'.format(i)] = \
                                    {'VM_ip': key, 'container': kk, 'cpu': 1}
                                print("MIGRATE NOT ENOUGH CPU RESOURCES")
                    else:
                        if ram_cpu == 1:
                            ntm['node_to_migrate_RAM_{}'.format(i)] = \
                                {'VM_ip': key, 'container': kk, 'ram': 1024}
                            ram_cpu = 0
                            print("MIGRATE NOT ENOUGH MEMORY RESOURCES")

                else:
                    err = 0
                    err2 = 0
                i += 1
    return ntm
