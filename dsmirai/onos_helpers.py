import pycurl
from io import BytesIO
import json
import dsmirai.utils as system_driver


class OnosHelpers:
    """
    Simple mapping of ONOS's API to enable northbound management
    """

    def __init__(self):
        pass

    @staticmethod
    def onos_rest_connection(request, request_url, post_data=None, user_name='onos', password='rocks'):
        buffer_file = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.USERNAME, user_name)
        c.setopt(pycurl.PASSWORD, password)
        c.setopt(pycurl.CUSTOMREQUEST, request)
        c.setopt(c.URL, request_url)
        if post_data is not None:
            c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json', 'Accept: application/json'])
            c.setopt(c.POST, 1)
            c.setopt(c.POSTFIELDS, post_data)
        else:
            c.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])

        c.setopt(c.WRITEDATA, buffer_file)
        c.perform()
        c.close()
        return buffer_file.getvalue()

    def complex_intent(self, ip_sdn_controller, ingress_device, ingress_port, egress_device, egress_port, priority,
                       ether_type, ip_destination):
        request_type = 'POST'
        post_data1 = '{\"type\": \"PointToPointIntent\", \"appId\": \"org.onosproject.cli\", \"priority\":' + str(
            priority)
        post_data2 = post_data1 + ',\"ingressPoint\": {\"port\":\"' + str(ingress_port)
        post_data3 = post_data2 + '\",\"device\":\"' + str(ingress_device)
        post_data4 = post_data3 + '\"},\"egressPoint\": {\"port\":\"' + str(egress_port)
        post_data5 = post_data4 + '\",\"device\":\"' + str(egress_device)
        post_data6 = post_data5 + '\"},\"selector\": {\"criteria\": [{\"type\": \"ETH_TYPE\",\"ethType\": \"' + str(
            ether_type)
        post_data7 = post_data6 + '\"},{\"type\": \"IPV4_DST\",\"ip\":\"' + str(ip_destination) + '/32\"'
        post_data10 = post_data7 + '}]}}'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/intents'
        body = self.onos_rest_connection(request_type, request_url, post_data10)

    def get_all_inter_ovs_links(self, ip_sdn_controller):
        request_type = 'GET'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/links'
        body = self.onos_rest_connection(request_type, request_url)
        result = body.decode()
        f = json.loads(result)
        link = f["links"]
        list_of_ports_devices = [{'portsrc': element['src']['port'], 'devicesrc': element['src']['device'],
                                  'portdst': element['dst']['port'], 'devicedst': element['dst']['device']} for element
                                 in link]
        return list_of_ports_devices

    def get_sdn_hosts(self, ip_sdn_controller):
        request_type = 'GET'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/hosts'
        body = self.onos_rest_connection(request_type, request_url)
        result = body.decode()
        f = json.loads(result)
        hosts = f["hosts"]
        list_sdn_hosts = [
            {'mac': element['mac'], 'ip_container': element['ipAddresses'][0], 'device':
                element['location']['elementId'], 'port': element['location']['port']} for element in hosts]
        return list_sdn_hosts

    def get_sdn_hosts_by_device(self, ip_sdn_controller, ip_container=""):
        request_type = 'GET'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/hosts'
        body = self.onos_rest_connection(request_type, request_url)
        result = body.decode()
        f = json.loads(result)
        hosts = f["hosts"]
        list_sdn_hosts = [
            {'mac': element['mac'], 'ip_container': element['ipAddresses'][0], 'device':
                element['location']['elementId'], 'port': element['location']['port']} for element in hosts if
            element['ipAddresses'][0] == ip_container]
        return list_sdn_hosts

    def get_sdn_devices(self, ip_sdn_controller):
        request_type = 'GET'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/devices'
        body = self.onos_rest_connection(request_type, request_url)
        result = body.decode()
        f = json.loads(result)
        devices = f["devices"]
        list_sdn_devices = [{'device': element['id'], 'ip_management': element['annotations']['managementAddress']}
                            for element in devices]
        return list_sdn_devices

    def get_all_intents(self, ip_sdn_controller):
        request_type = 'GET'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/intents'
        body = self.onos_rest_connection(request_type, request_url)
        result = body.decode().split(sep='{')
        list_intents = []
        for i in range(2, len(result)):
            temp = result[i].split(sep=',')
            intent_id = temp[1].split(sep=':')[1]
            list_intents.append(intent_id.strip('"'))
        return list_intents

    def delete_devices(self, ip_sdn_controller, list_devices):
        request_type = 'DELETE'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/devices/'
        for i in range(len(list_devices)):
            url_req = request_url + list_devices[i]['device']
            body = self.onos_rest_connection(request_type, url_req)

    def delete_hosts(self, ip_sdn_controller, list_hosts):
        request_type = 'DELETE'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/hosts/'
        for i in range(len(list_hosts)):
            url_req = request_url + list_hosts[i]['mac'] + '/-1'
            body = self.onos_rest_connection(request_type, url_req)

    def delete_intents(self, ip_sdn_controller, intent_list):
        request_type = 'DELETE'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/intents/org.onosproject.cli/'
        for i in range(len(intent_list)):
            url_req = request_url + intent_list[i]
            body = self.onos_rest_connection(request_type, url_req)

    def sdn_host_information(self, ip_sdn_controller, ip_container):
        list_of_containers = self.get_sdn_hosts(str(ip_sdn_controller))
        list_sdn_devices = self.get_sdn_devices(str(ip_sdn_controller))
        ip_vm_hosting_container = ""
        print(ip_container)
        print(list_of_containers)
        print(list_sdn_devices)
        for i in range(0, int(len(list_of_containers))):
            ip = list_of_containers[i]['ip_container']
            if ip == str(ip_container):
                device = list_of_containers[i]['device']
                for j in range(0, int(len(list_sdn_devices))):
                    if list_sdn_devices[j]['device'] == device:
                        ip_vm_hosting_container = list_sdn_devices[j]['ip_management']
                port = list_of_containers[i]['port']
                return device, port, ip_vm_hosting_container

    @staticmethod
    def replace_all(text, dic):
        for i, j in dic.items():
            text = text.replace(i, j)
        return text

    def friendly_ovs_name(self, device1, ip_destination):
        cmd = 'ovs-vsctl --columns=mac_in_use,name list Interface'
        stdin, stdout, stderr = system_driver.ssh_query(cmd, ip_destination, True)
        result = stdout.read()
        stdin.flush()
        device = result.decode().split('\n')
        device1 = device1.replace("of:0000", "")
        for j in range(int(len(device)/3)):
            device.remove('')

        for i in range(len(device)):
            temp = device[i].split(":", 1)[1]
            reps = {'"': '', ':': '', ' ': ''}
            x = self.replace_all(temp, reps)
            if x == device1:
                temp = device[i+1].split(":", 1)[1]
                reps = {'"': '', ' ': ''}
                print(self.replace_all(temp, reps))
                return self.replace_all(temp, reps)

    def mac_style_ovs_name(self, device1, ip_destination):
        cmd = 'ovs-vsctl --columns=mac_in_use,name list Interface'
        stdin, stdout, stderr = system_driver.ssh_query(cmd, ip_destination, True)
        result = stdout.read()
        stdin.flush()
        device = result.decode().split('\n')
        for j in range(int(len(device)/3)):
            device.remove('')

        for i in range(len(device)):
            temp = device[i].split(":", 1)[1]
            reps = {'"': '', ':': '', ' ': ''}
            x = self.replace_all(temp, reps)
            if x == device1:
                temp = device[i-1].split(":", 1)[1]
                reps = {'"': '', ' ': ''}
                print(self.replace_all(temp, reps))
                mac_ovs_name = self.replace_all(temp, reps).replace(":", "")
                mac_ovs_name = "of:0000" + mac_ovs_name
                print(mac_ovs_name)
                return mac_ovs_name

    def verify_links(self, ip_sdn_controller, device_source, device_destination):
        list_of_links = self.get_all_inter_ovs_links(ip_sdn_controller)
        print(list_of_links)
        for i in range(len(list_of_links)):
            print("device source")
            print(list_of_links[i]['devicesrc'])
            print("device destination")
            print(list_of_links[i]['devicedst'])
            if (list_of_links[i]['devicesrc'] == device_source and list_of_links[i]['devicedst'] == device_destination) \
                    or (list_of_links[i]['devicesrc'] == device_destination and
                        list_of_links[i]['devicedst'] == device_source):
                return True
        return False

    def verify_local_distant_devices(self, ip_sdn_controller, device_source, device_destination):
        list_of_devices = self.get_sdn_devices(ip_sdn_controller)
        list_of_chosen_devices = []
        for i in range(len(list_of_devices)):
            if list_of_devices[i]['device'] == device_source or list_of_devices[i]['device'] == device_destination:
                list_of_chosen_devices.append(list_of_devices[i])
        if list_of_chosen_devices[0]['ip_management'] == list_of_chosen_devices[1]['ip_management']:
            return True
        return False

    def setup_turn_around_node(self, ip_sdn_controller, host_ip_address, mac_ovs):
        host = self.get_sdn_hosts_by_device(ip_sdn_controller, host_ip_address)
        self.delete_hosts(ip_sdn_controller, host)
        data_post = {
                "mac": "{}".format(host[0]["mac"]),
                "vlan": "-1",
                "ipAddresses": [
                    "{}".format(host_ip_address)
                                ],
                "location": {
                    "elementId": "{}".format(mac_ovs),
                    "port": "{}".format(host_ip_address.split(".")[3])
                            }
                }
        request_type = 'POST'
        request_url = 'http://' + str(ip_sdn_controller) + ':8181/onos/v1/hosts'
        self.onos_rest_connection(request_type, request_url, json.dumps(data_post))

    @staticmethod
    def get_ovs(i, ip_destination):
        basic_cmd = 'ovs-vsctl list-br'
        stdin, stdout, stderr = system_driver.ssh_query(basic_cmd, ip_destination, True)
        result = stdout.read()
        stdin.flush()
        c = result.decode().split('\n')
        return str(c[i])
