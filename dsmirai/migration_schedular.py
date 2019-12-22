from billiard import Manager
from billiard.context import Process
import dsmirai.client_broker as client_broker
import os
import time
import dsmirai.bandwidth_selector as bw_slct
from dsmirai.persistent_model import helpers


manager = Manager()


def dummy_function(container_name, lxc_ovs, LXC_IMAGE, LXC_OVS_IMAGE, image_type, image_type_ovs, ip_source,
                   ip_destination, NUM_ITERATION, sfc_type, acquired_bandwidth):
    container_list = [(container_name, LXC_IMAGE, image_type), (lxc_ovs, LXC_OVS_IMAGE, image_type_ovs)]
    jobs = []
    return_dict = manager.dict()
    resp = 0
    for part in range(len(migration_actions[sfc_type])):
        print("the migration phase is: {}".format(part))
        for i in range(len(container_list)):
            p = Process(name='migrate_{}'.format(container_list[i][0]), target=migration_actions[sfc_type][part],
                        args=(container_list[i][0], container_list[i][1], container_list[i][2], ip_source,
                              ip_destination, NUM_ITERATION, acquired_bandwidth, return_dict,))
            jobs.append(p)
            p.start()
        for proc in jobs:
            proc.join()
        print(jobs)
        jobs = []

        j = 0
        while j < len(return_dict.values()) and return_dict.values()[j] != "Error":
            print("the returned value is: {}".format(return_dict.values()))
            j += 1
        if j >= len(return_dict.values()):
            resp = 1
            continue
        resp = 404
        return resp

    print("the last return: {}".format(resp))
    return resp


def round_robin_function(container_name, lxc_ovs, LXC_IMAGE, LXC_OVS_IMAGE, image_type, image_type_ovs, ip_source,
                   ip_destination, NUM_ITERATION, sfc_type, acquired_bandwidth):
    container_list = [(container_name, LXC_IMAGE, image_type), (lxc_ovs, LXC_OVS_IMAGE, image_type_ovs)]
    jobs = []
    return_dict = manager.dict()
    resp = 0
    for part in range(len(migration_actions[sfc_type])):
        print("the migration phase is: {}".format(part))
        for i in range(len(container_list)):
            p = Process(name='migrate_{}'.format(container_list[i][0]), target=migration_actions[sfc_type][part],
                        args=(container_list[i][0], container_list[i][1], container_list[i][2], ip_source,
                              ip_destination, NUM_ITERATION, acquired_bandwidth, return_dict,))
            jobs.append(p)
            p.start()
        for proc in jobs:
            proc.join()
        print(jobs)
        jobs = []

        j = 0
        while j < len(return_dict.values()) and return_dict.values()[j] != "Error":
            print("the returned value is: {}".format(return_dict.values()))
            j += 1
        if j >= len(return_dict.values()):
            resp = 1
            continue
        resp = 404
        return resp

    print("the last return: {}".format(resp))
    return resp


def dummy_sfc_migration(container_name, LXC_IMAGE, image_type, ip_source, ip_destination, NUM_ITERATION,
                        acquired_bandwidth, return_dict):
    print("***********The Global Orchestrator --dummy_sfc_migration-- ***********")
    queue_name = "migration_queue"
    rmq = client_broker.ClientBroker(queue_name)
    t1 = time.time()
    result = rmq.part_migration_check(LXC_IMAGE, ip_destination, container_name, image_type)
    t2 = time.time()
    system_time = t2 - t1
    with open('/root/result_video_app.txt', "a") as my_file:
        my_file.write("\n ({}) System Time: {}\n".format(os.getpid(), system_time))
    if result == 1:
        print("image based migration detected")
        print("starting the image based migration")
    elif result == 2:
        print("base migration detected")
        print("starting the base migration")
    else:
        print("Full-Migration action")
        print("starting a Full-Migration")
    if rmq.migration(container_name, ip_destination, NUM_ITERATION, ip_source, "migration", True, acquired_bandwidth) \
            != 1:
        return_dict[container_name] = "Error"
        return
    return_dict[container_name] = container_name
    t2 = time.time()
    normal_time = t2 - t1
    with open('/root/result_video_app.txt', "a") as my_file:
        my_file.write("({}) Total Time Control: {}\n".format(os.getpid(), normal_time))
    print("Total Time Control: {}".format(normal_time))
    return


def basic_sfc_migration(container_name, LXC_IMAGE, image_type, ip_source, ip_destination, NUM_ITERATION,
                        bandwidth_value, return_dict):
    print("***********The Global Orchestrator --basic_sfc_migration-- ***********")
    queue_name = "migration_queue"
    rmq = client_broker.ClientBroker(queue_name)
    t1 = time.time()
    result = rmq.part_migration_check(LXC_IMAGE, ip_destination, container_name, image_type)
    t2 = time.time()
    system_time = t2 - t1
    with open('/root/result_video_app.txt', "a") as my_file:
        my_file.write("\n ({}) System Time: {}\n".format(os.getpid(), system_time))
    if result == 1:
        print("image based migration detected")
        print("starting the image based migration")
    elif result == 2:
        print("base migration detected")
        print("starting the base migration")
    else:
        print("Full-Migration action")
        print("starting a Full-Migration")
    decision, disk_size, pre_dump_size, t_pre_dump, total_time = rmq.migration(container_name, ip_destination,
                                                                               NUM_ITERATION, ip_source, "migration",
                                                                               False, bandwidth_value)
    if decision != 1:
        return_dict[container_name] = "Error"
        return
    dump_size, dump_time, mem_pages = rmq.migration(container_name, ip_destination, NUM_ITERATION, ip_source, "dump",
                                                    False, bandwidth_value)
    print('The dump size is: {}'.format(dump_size))
    return_dict[container_name] = {"dump_size": dump_size, "dump_time": dump_time, "mem_pages": mem_pages,
                                   "total_time": total_time}
    # TODO: Store in a database table
    helpers.update_data_set_1(dump_size, mem_pages, disk_size, pre_dump_size, t_pre_dump, bandwidth_value)
    return dump_size, dump_time, mem_pages, total_time


def dump_restore(container_name, LXC_IMAGE, image_type, ip_source, ip_destination, NUM_ITERATION, bandwidth_value,
                 return_dict):
    print("***********The Global Orchestrator --dump_restore-- ***********")
    queue_name = "migration_queue"
    rmq = client_broker.ClientBroker(queue_name)
    t1 = time.time()
    # TODO: Call bw_slct.get_smart_bw_value()

    selected_bandwidth = bw_slct.get_smart_bw_value((float(return_dict[container_name]["dump_size"]),
                                                     float(return_dict[container_name]["mem_pages"])), 'ddpg')
    # TODO: selected_bandwidth to be modified into selected_bandwidth[0] for DDPG
    action_time, success = rmq.migration(container_name, ip_destination, NUM_ITERATION, ip_source, "dump_restore",
                                         False, selected_bandwidth[0].item())
    if success != 1:
        return_dict[container_name] = "Error"
        return
    t2 = time.time()
    system_time = t2 - t1
    with open('/root/result_video_app.txt', "a") as my_file:
        my_file.write("\n ({}) downtime_system Time: {}\n".format(os.getpid(), system_time))
    downtime = action_time + return_dict[container_name]["dump_time"]
    total_time = return_dict[container_name]["total_time"] + downtime
    return_dict[container_name] = {"downtime": downtime, "total_time": total_time}
    # TODO: selected_bandwidth to be modified into selected_bandwidth[0] for DDPG
    helpers.update_data_set_2(success, selected_bandwidth[0].item(), action_time, total_time)
    return


migration_actions = {"dummy": [dummy_sfc_migration], "wait": [basic_sfc_migration, dump_restore], "basic": [],
                     "network": ["disk", "pre_dump", "dump_restore"]}

