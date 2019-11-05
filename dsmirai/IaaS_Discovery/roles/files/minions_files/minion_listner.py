import subprocess
import time
import requests
import json
import virtual_machine as system_driver


def run():
    """
    listener to detect minions' issues
    :return:
    """
    controller_ip = '195.148.125.104'
    url = 'iaas_delete'
    while True:
        time.sleep(5)
        cmd = 'ps -ax'
        answer = subprocess.check_output(cmd, shell=True)
        if 'server_broker.py' not in answer.decode():
            print("server_broker stopped ")
            list_ip = [{'ip': '{}'.format(str(system_driver.get_ip()))}]
            list_ip = json.dumps(list_ip)
            link_to_orchestrator = 'http://{}/api/{}?iaas_ip='.format(controller_ip, url) + list_ip
            print(link_to_orchestrator)
            requests.get(link_to_orchestrator)


run()
