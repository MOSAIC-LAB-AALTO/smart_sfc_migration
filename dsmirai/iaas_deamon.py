import subprocess
from dsmirai.persistent_model import helpers
import time
from django.conf import settings


def iaas_discovery():
    """
    Deamon used for VM/IaaS/FRD registration
    :return:
    """
    while True:
        ping_count = 4
        print(ping_count)
        print("iaas discovery deamon activated")
        ip_addresses = helpers.available_iaas()
        for key, value in ip_addresses.items():
            process = subprocess.Popen(['ping', value, '-c', str(ping_count)],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            return_code = process.wait()
            print('ping returned {0}'.format(return_code))
            print(process.stdout.read())
            if return_code == 0:
                print(value + " available")

                helpers.update_state_iaas(value, True)
                # call Ansible right here

                with open(settings.LINK_ANSIBLE_FOLDER + "hosts", "w") as my_file:
                    my_file.write(value)
                    my_file.close()
                time.sleep(5)

                process = subprocess.Popen(['ansible-playbook', 'playbook.yml'],
                                           cwd=settings.LINK_ANSIBLE_FOLDER,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
                return_code = process.wait()
                print('ansible returned {0}'.format(return_code))
                print(process.stdout.read())

                helpers.update_configuration_iaas(value, True)

        time.sleep(20)

