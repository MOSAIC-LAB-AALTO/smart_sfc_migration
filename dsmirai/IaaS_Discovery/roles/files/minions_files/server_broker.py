#!/usr/bin/env python
import subprocess
import pika
import linux_container as lxc_driver
import virtual_machine as system_driver
import customized_sdn_container as sdn
import core_migration as migration
import Triggers.resource_availability_trigger as rat
import Triggers.service_consumption_trigger as sct
import sys
import scale_up as scale_up
import iperf_client
import json
import utils
import time
import os


class ServerBroker(object):

    def __init__(self, exchange_key='main_queue', ip_mngmt='195.148.125.130', user_name='admin',
                 password='Sm@rt1993'):
        self.credentials = pika.PlainCredentials(user_name, password)
        self.parameters = pika.ConnectionParameters(ip_mngmt, 5672, '/', self.credentials)
        self.connection = pika.BlockingConnection(self.parameters)

        # Prepare the exchange and wait for a request from the client
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=exchange_key, exchange_type='direct')

        result = self.channel.queue_declare(exclusive=True)
        self.channel.queue_declare(queue=str(system_driver.get_ip()) + exchange_key.split('_')[0], durable=True)
        queue1 = 'star' + exchange_key.split('_')[0]
        queue2 = str(system_driver.get_ip())
        self.channel.queue_bind(exchange=exchange_key, queue=str(system_driver.get_ip()) + exchange_key.split('_')[0],
                                routing_key=queue1)
        self.channel.queue_bind(exchange=exchange_key, queue=str(system_driver.get_ip()) + exchange_key.split('_')[0],
                                routing_key=queue2)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue=str(system_driver.get_ip()) + exchange_key.split('_')[0])

        print(" [x] Awaiting RPC requests")
        self.channel.start_consuming()

    def on_request(self, ch, method, props, body):

        print(" I received: {}".format(body))
        print("my correlation id is: {}".format(props.correlation_id))
        x = body.decode().split("#")
        response = ""
        if x[0] == "admin":
            subprocess.Popen(['python3', '/root/minion_sfc/server_broker.py', str(x[1]) + "_queue"], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
            response = 1
            print("The response equals to: {}".format(response))
        elif x[0] == "activate_servers":
            response = 1
            if str(system_driver.get_ip()) in json.loads(x[1]):
                response = utils.unattached_process(str(system_driver.get_ip()),
                                                    json.loads(x[1])[str(system_driver.get_ip())])
        elif x[0] == "monitor_bandwidth":
            response = utils.unattached_process_bandwidth()
        elif x[0] == "network_evaluator":
            response = {}
            j = 0
            for key, value in json.loads(x[1]).items():
                print(value['client'], value['server'])
                if value['client'] == str(system_driver.get_ip()):
                    bytes_transmitted, bits_s, megabits_s, megabytes_s = iperf_client.run(value['client'], value['server'])
                    response[j] = str(bytes_transmitted) + '#' + str(bits_s) + '#' + str(megabits_s) + '#' + \
                        str(megabytes_s)
                    j += 1
            response = json.dumps(response)
        elif x[0] == "available_resource_creation":
            print("***********The Host Node Server Broker -- verify_resource_creation--***********")
            cpu, ram, disk = system_driver.resource_availability()
            response = str(system_driver.get_ip()) + "#" + str(cpu) + "#" + str(ram) + "#" + str(disk)
        elif x[0] == "create":
            print("***********The Host Node Server Broker -- create_container --***********")
            system_driver.default_bridge()
            print("calling the creation library .....")
            response = -1
            if sdn.create_server(x[1], x[3], x[4], x[5], x[6]):
                if sdn.create_client(x[2], x[7], x[8]):
                    if sdn.link_client_to_server(x[2], x[5]):
                        if sdn.create_lxc_ovs(x[9], x[10], x[11], x[12], x[13]):
                            response = 1
            print("The response is equal to: {}".format(response))
        elif x[0] == "container_resources":
            print("***********The Host Node Server Broker -- get_container_resources --***********")
            print("getting the cpu, ram information .....")
            cpu, ram = lxc_driver.get_container_resources(x[1])
            response = str(system_driver.get_ip()) + "#" + str(cpu) + "#" + str(ram)
            print("The response is equal to: {}".format(response))
        elif x[0] == "available_resource_migration":
            print("***********The Host Node Server Broker -- verify_resource_migration --***********")
            if str(system_driver.get_ip()) != x[1]:
                cpu, ram, disk = system_driver.resource_availability()
                response = str(system_driver.get_ip()) + "#" + str(cpu) + "#" + str(ram) + "#" + str(disk)
            else:
                response = str(system_driver.get_ip()) + "#" + str(0) + "#" + str(0) + "#" + str(0)
        elif x[0] == "container_image":
            print("***********The Host Node Server Broker -- container_image --***********")
            print("getting the image name .....")
            response = migration.container_base_image(x[1])
        elif x[0] == "part_migration_check":
            print("***********The Host Node Server Broker -- part_migration_check --***********")
            print("searching for partial migration action .....")
            t1 = time.time()
            base_image = migration.target_container_image(x[1], x[3])
            response = migration.partial_migration_preparation(x[1], x[2], x[3], base_image)
            t2 = time.time()
            system_time = t2 - t1
            with open('/root/result_video_app.txt', "a") as my_file:
                my_file.write("\n({}) System Time: {}\n".format(os.getpid(), system_time))
            print("(118) System Time: {}".format(system_time))
        elif x[0] == "migration":
            print("***********The Host Node Server Broker -- full_migration --***********")
            t1 = time.time()
            print(x[4])
            print(type(x[4]))
            if x[4] == 'False' or x[4] is False:
                response = migration.migrate(x[1], x[2], x[3], False, x[5])
            else:
                response = migration.migrate(x[1], x[2], x[3], True, x[5])
            t2 = time.time()
            system_time = t2 - t1
            with open('/root/result_video_app.txt', "a") as my_file:
                my_file.write("({}) RSYNC time: {}\n".format(os.getpid(), system_time))
            print("RSYNC time: {}".format(system_time))
        elif x[0] == "dump":
            print("***********The Host Node Server Broker -- dump --***********")
            print("dump Process .....")
            response = migration.final_memory_copy(x[1], x[3], x[2], x[5])

        elif x[0] == "dump_restore":
            print("***********The Host Node Server Broker -- dump_restore --***********")
            print("dump_restore Process .....")
            response = migration.dump_restore(x[1], x[2], x[3], x[5])
        elif x[0] == "validate_migration":
            print("***********The Host Node Server Broker -- validate_migration --***********")
            print("Validate-Migration Process .....")
            response = migration.validate_migration(x[1], x[2])
        elif x[0] == "rat_trigger":
            print("***********The Host Node Server Broker -- rat_trigger --***********")
            response = rat.container_list()
        elif x[0] == "sct_trigger":
            print("***********The Host Node Server Broker -- sct_trigger --***********")
            response = sct.container_live_resources()
        elif x[0] == "scale_up_cpu_ram":
            print("***********The Host Node Server Broker -- scale_up_cpu_ram --***********")
            response = scale_up.scale_up_cpu_ram(x[1], x[2], x[3])
        elif x[0] == "scale_up_cpu":
            print("***********The Host Node Server Broker -- scale_up_cpu --***********")
            response = scale_up.scale_up_cpu_full(x[1], x[2])
        elif x[0] == "scale_up_ram":
            print("***********The Host Node Server Broker -- scale_up_ram --***********")
            response = scale_up.scale_up_ram_full(x[1], x[2])
        elif x[0] == "container_dashboard_resources":
            print("***********The Host Node Server Broker -- container_dashboard_resources --***********")
            container_ip, cpu, ram, disk = lxc_driver.container_dashboard_resources(x[1])
            response = str(container_ip) + "#" + str(cpu) + "#" + str(ram) + "#" + str(disk)
        elif x[0] == "environment_cleaner":
            print("***********The Host Node Server Broker -- environment_cleaner --***********")
            subprocess.Popen(['python3', '/root/minion_sfc/environment_cleaner.py'], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
            response = 1
        elif x[0] == "live_container_number":
            print("***********The Host Node Server Broker -- live_container_number --***********")
            response = lxc_driver.get_running_containers()
        elif x[0] == "delete_client_server":
            print("***********The Host Node Server Broker -- delete_client_server --***********")
            response = sdn.delete_sdn_container(x[1], x[2], x[3], x[4],)
        elif x[0] == "delete":
            print("***********The Host Node Server Broker -- delete --***********")
            response = sdn.delete_sdn_container(x[1], x[2])

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == "__main__":
    c = ServerBroker(sys.argv[1])
