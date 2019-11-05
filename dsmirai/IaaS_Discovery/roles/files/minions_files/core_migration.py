import subprocess
import os
import time
import utils as system_driver
import linux_container as lxc_driver
import virtual_machine as os_driver
import logging
import json

my_logger = logging.getLogger('control_log_core_migration')

NOK = -1
OK = 1

LXC_IMAGES_FOLDER = "/var/cache/lxc"
LXC_PATH = "/var/lib/lxc/"
INTERFACE_PATH = "rootfs/etc/network/interfaces"


def get_mem_pages():
    with open('/root/statistic.txt', 'r') as f:
        datastore = json.load(f)
    mem_pages = datastore['entries'][0]['dump']['pages_written']
    print(mem_pages)
    cmd_del = "rm -rf /root/statistic.txt"
    subprocess.check_output(cmd_del, shell=True)
    return mem_pages


def container_base_image(container_name):
    for line in open('{}{}/config'.format(LXC_PATH, container_name), "r"):
        if "Parameters passed to the template" in line:
            line2 = line.split(" ")
            i = 0
            while line2[i] != "-r":
                i += 1
            return line2[i + 1]


def container_image(lxc_base_image, path):
    cmd = "ls {}".format(path)
    result = subprocess.check_output(cmd, shell=True)
    my_info = result.decode().split('\n')
    i = 0
    while my_info[i] != str(lxc_base_image) and i < (len(my_info) - 1):
        i += 1
    if i >= (len(my_info) - 1):
        return False
    else:
        return True


def target_container_image(lxc_base_image, lxc_image):
    tab = \
        {
            'base': False,
            'image': False
        }
    if container_image(lxc_base_image, LXC_IMAGES_FOLDER):
        tab['base'] = True
    if container_image(lxc_image, LXC_PATH):
        tab['image'] = True
    return tab


def partial_migration_preparation(image_type, container_name, lxc_image, base_image):

    try:
        if base_image['image']:
            print("Found clone image...")
            if lxc_driver.clone_from_template(lxc_image, container_name):
                response = 1
        elif base_image['base']:
            print("Found base image...")
            cmd = 'lxc-create -t ubuntu -n {} -- -r {} -a amd64'.format(container_name, image_type)
            a = subprocess.check_output(cmd, shell=True)
            response = 2
        else:
            return False

        cmd = "rm -rf {}{}/config".format(LXC_PATH, container_name)
        subprocess.check_output(cmd, shell=True)

        cmd = "rm -rf {}{}/{}".format(LXC_PATH, container_name, INTERFACE_PATH)
        subprocess.check_output(cmd, shell=True)
        return response
    except Exception as exception:
        my_logger.critical('ERROR: partial_migration_preparation():' + str(exception) + '\n')
        print("unable to check for a partial possible migration ...")
        return False


def delete_checkpoint_folder(container_name, ip_destination):
    """
    Used to delete checkpoint folders
    :param container_name:
    :param ip_destination:
    :return:
    """

    checkpoint_folder = "{}{}/checkpoint".format(LXC_PATH, container_name)
    basic_cmd = 'rm -rf {}/*'.format(checkpoint_folder)
    stdin, stdout, stderr = system_driver.ssh_query(basic_cmd, ip_destination, True)
    result = subprocess.check_output(basic_cmd, shell=True)


def mount_checkpoint_folder(container_name, ip_destination):
    """
    Used to mount checkpoint folders
    :param container_name:
    :param ip_destination:
    :return:
    """
    if not os.path.exists('{}/{}/checkpoint'.format(LXC_PATH, container_name)):
        os.makedirs('{}/{}/checkpoint'.format(LXC_PATH, container_name))
    try:
        checkpoint_folder = '{}/{}/checkpoint'.format(LXC_PATH, container_name)
        mount_cmd = 'mount -t tmpfs -o size=1500M,mode=0777 tmpfs {}'.format(checkpoint_folder)
        stdin, stdout, stderr = system_driver.ssh_query(mount_cmd, ip_destination, True)
        mkdir_cmd_1 = 'mkdir {}/{}'.format(LXC_PATH, container_name)
        mkdir_cmd_2 = 'mkdir {}'.format(checkpoint_folder)
        stdin, stdout, stderr = system_driver.ssh_query(mkdir_cmd_1, ip_destination, True)
        stdin, stdout, stderr = system_driver.ssh_query(mkdir_cmd_2, ip_destination, True)
        result = subprocess.check_output(mount_cmd, shell=True)
        stdin, stdout, stderr = system_driver.ssh_query(mount_cmd, ip_destination, True)
        return OK
    except Exception as exception:
        my_logger.critical('ERROR: mount_checkpoint_folder():' + str(exception) + '\n')
        print("unable to mount the checkpoint folder ...")
        return NOK


def send_data(data_folder, ip_destination, bandwidth_value):

    rsync_cmd = 'rsync -aAXHltzh --bwlimit={2} --numeric-ids --devices --rsync-path="sudo rsync" {0}/ root@{1}:{0}/' \
        .format(data_folder, ip_destination, bandwidth_value)
    print(rsync_cmd)
    t1 = time.time()
    result2 = subprocess.check_output(rsync_cmd, shell=True)
    t2 = time.time()
    t_rsync_dump = t2 - t1
    with open('/root/result_video_app.txt', "a") as my_file:
        my_file.write("({}) t_rsync_dump Time: {}\n".format(os.getpid(), t_rsync_dump))
    print("t_rsync_dump Time: {}".format(t_rsync_dump))


def disk_copy(container_name, ip_destination, bandwidth_value):
    """
    Disk/rootfs copy i.e. disk migration
    :param container_name:
    :param ip_destination:
    :param bandwidth_value:
    :return:
    """
    try:
        print("starting disk copy .....")
        decision, pid = lxc_driver.container_status_pid(container_name)
        if decision:
            # deleting all the non necessary folders
            delete_checkpoint_folder(container_name, ip_destination)
            size = os_driver.get_size_folder(container_name, "/")
            # rsync the folder
            rsync_cmd = 'rsync -aAXHltzh --bwlimit={3} --numeric-ids --devices --rsync-path="sudo rsync" {0}{1} root@{2}:{0}'.format(
                LXC_PATH,
                container_name,
                ip_destination, bandwidth_value)
            result = subprocess.check_output(rsync_cmd, shell=True)
            mount_checkpoint_folder(container_name, ip_destination)
            return size
    except Exception as exception:
        my_logger.critical('ERROR: disk_copy:' + str(exception) + '\n')
        print("unable to copy the disk ...")
        return NOK


def get_general_arguments(container_name):
    """
    General arguments for live migration
    :param container_name:
    :return:
    """
    try:
        print("Getting the main arguments.....")
        decision, pid = lxc_driver.container_status_pid(container_name)
        if decision:
            general_args = '--tcp-established --cgroup-dump-controller c1'
            general_args = general_args + ' --file-locks'
            general_args = general_args + ' --link-remap --force-irmap'
            general_args = general_args + ' --manage-cgroups'
            general_args = general_args + ' --ext-mount-map auto'
            general_args = general_args + ' --enable-external-sharing'
            general_args = general_args + ' --enable-external-masters'
            general_args = general_args + ' --enable-fs hugetlbfs --enable-fs tracefs'
            general_args = general_args + ' -vvvvvv'
            general_args = general_args + ' -t ' + str(pid)
            return str(general_args)
    except Exception as exception:
        my_logger.critical('ERROR: get_general_arguments:' + str(exception) + '\n')
        print("unable to get the main arguments ...")
        return NOK


def live_memory_copy(container_name, num_iteration, ip_destination, bandwidth_value):
    """
    Iterative migration
    :param container_name:
    :param num_iteration:
    :param ip_destination:
    :param bandwidth_value:
    :return:
    """
    try:
        print("starting live memory copy .....")

        print("ready to be in pre-dump phases")
        for i in range(1, int(num_iteration)):
            print("iteration :{}".format(i))
            print(str(int(num_iteration) - 1))
            checkpoint_folder = '{}{}/checkpoint/{}'.format(LXC_PATH, container_name, i)
            mkdir_cmd = 'mkdir ' + checkpoint_folder
            result = subprocess.check_output(mkdir_cmd, shell=True)
            if i == 1:
                # First iteration
                action = 'pre-dump'
                args = '--track-mem --leave-running'

            else:
                # Other iterations
                args = '--prev-images-dir=../' + str(i - 1) + '/ --track-mem --leave-running'
                action = 'pre-dump'

            criu_cmd = 'criu ' + action + ' -D ' + checkpoint_folder + ' -o ' + checkpoint_folder + '/' + action + \
                       '.log ' + get_general_arguments(container_name) + ' ' + args
            print(criu_cmd)
            result1 = subprocess.check_output(criu_cmd, shell=True)
            print("rsync of the {} iteration ..".format(i))

            rsync_cmd = 'rsync -aAXHltzh --bwlimit={2} --numeric-ids --devices --rsync-path="sudo rsync" {0}/ root@{1}:{0}/' \
                .format(checkpoint_folder, ip_destination, bandwidth_value)
            print(rsync_cmd)
            result2 = subprocess.check_output(rsync_cmd, shell=True)

    except Exception as exception:
        my_logger.critical('ERROR: live_memory_copy:' + str(exception) + '\n')
        print("unable to copy the live memory ...")
        return NOK


def retry_module(container_name, num_iteration, ip_destination, bandwidth_value):
    """
    Retry module in case last blocking iteration fails
    :param container_name:
    :param num_iteration:
    :param ip_destination:
    :param bandwidth_value:
    :return:
    """
    j = 0
    t_diff = 0
    checkpoint_folder = ""
    while j < 3:
        try:
            # do cleaning
            cmd = 'rm  -rf {}{}/checkpoint/{}/*'.format(LXC_PATH, container_name, num_iteration)
            result3 = subprocess.check_output(cmd, shell=True)
            # redo dump
            checkpoint_folder = '{}{}/checkpoint/{}'.format(LXC_PATH, container_name, num_iteration)
            if num_iteration == 3 or num_iteration == "3":
                args = '--prev-images-dir=../' + str(int(num_iteration) - 1) + '/ --track-mem --leave-stopped'
                action = 'dump'
            else:
                action = 'dump'
                args = '-s --track-mem'

            print(get_general_arguments(container_name))
            criu_cmd = 'criu ' + action + ' -D ' + checkpoint_folder + ' -o ' + checkpoint_folder + '/' + action + \
                       '.log ' + get_general_arguments(container_name) + ' ' + args
            t1 = time.time()
            subprocess.check_output(criu_cmd, shell=True)
            t2 = time.time()
            t_diff = t2 - t1
            j = 5
        except Exception as exception:
            my_logger.critical('ERROR: retry_module:' + str(exception) + '\n')
            print("unable to use the retry_module ...")
            j += 1
    if j <= 3:
        print("failed to dump")
    else:
        print("successful dump")
        crit_cmd = 'crit decode -i {}/stats-dump --pretty 2>{} | tee -a /root/statistic.txt'.format(checkpoint_folder,
                                                                                                    container_name)
        subprocess.check_output(crit_cmd, shell=True)

        size = os_driver.get_size_folder(container_name)
        mem_pages = get_mem_pages()
        return size, t_diff, mem_pages


def final_memory_copy(container_name, num_iteration, ip_destination, bandwidth_value):
    """
    Last blocking iteration
    :param container_name:
    :param num_iteration:
    :param ip_destination:
    :param bandwidth_value:
    :return:
    """
    try:
        print("ready to be in dump phase")
        print("iteration :{}".format(num_iteration))
        checkpoint_folder = '{}{}/checkpoint/{}'.format(LXC_PATH, container_name, num_iteration)
        mkdir_cmd = 'mkdir ' + checkpoint_folder
        result = subprocess.check_output(mkdir_cmd, shell=True)
        args = '--prev-images-dir=../' + str(int(num_iteration) - 1) + '/ --track-mem --leave-stopped'
        action = 'dump'
        criu_cmd = 'criu ' + action + ' -D ' + checkpoint_folder + ' -o ' + checkpoint_folder + '/' + action + \
                   '.log ' + get_general_arguments(container_name) + ' ' + args
        print(criu_cmd)
        t1 = time.time()
        subprocess.check_output(criu_cmd, shell=True)
        t2 = time.time()
        t_diff = t2 - t1
        crit_cmd = 'crit decode -i {}/stats-dump --pretty 2>{} | tee -a /root/statistic.txt'.format(checkpoint_folder,
                                                                                                    container_name)
        subprocess.check_output(crit_cmd, shell=True)
        size = os_driver.get_size_folder(container_name)
        mem_pages = get_mem_pages()
        return size, t_diff, mem_pages
    except Exception as exception:
        my_logger.critical('ERROR: unable_to_perform_dump_iterative:' + str(exception) + '\n')
        print("unable to perform dump")
        print("let's try a new one")
        return retry_module(container_name, num_iteration, ip_destination, bandwidth_value)


def dumb_memory_copy(container_name, ip_destination, bandwidth_value):
    """
    Non iterative page memory migration copy
    :param container_name:
    :param ip_destination:
    :param bandwidth_value:
    :return:
    """
    try:
        print("ready to be in dumb migration")
        checkpoint_folder = '{}{}/checkpoint/1'.format(LXC_PATH, container_name)
        mkdir_cmd = 'mkdir ' + checkpoint_folder
        result = subprocess.check_output(mkdir_cmd, shell=True)
        action = 'dump'
        args = '-s --track-mem'
        criu_cmd = 'criu ' + action + ' -D ' + checkpoint_folder + ' -o ' + checkpoint_folder + '/' + action + '.log ' \
                   + get_general_arguments(container_name) + ' ' + args
        print(criu_cmd)
        result1 = subprocess.check_output(criu_cmd, shell=True)
        rsync_cmd = 'rsync -aAXHltzh --bwlimit={2} --numeric-ids --devices --rsync-path="sudo rsync" {0}/ root@{1}:{0}/'.format(
            checkpoint_folder,
            ip_destination, bandwidth_value)
        result2 = subprocess.check_output(rsync_cmd, shell=True)
    except Exception as exception:
        my_logger.critical('ERROR: unable_to_perform_dump_iterative:' + str(exception) + '\n')
        print("unable to perform dump")
        print("let's try a new one")
        retry_module(container_name, 1, ip_destination, bandwidth_value)


def restore(container_name, ip_destination, num_iteration):
    """
    Restore feature used after the last iteration
    :param container_name:
    :param ip_destination:
    :param num_iteration:
    :return:
    """
    try:
        print("Restore phase strat")
        restore_cmd = 'lxc-checkpoint -r -n {0} -D /var/lib/lxc/{0}/checkpoint/{1}/ -vvvvv'.format(container_name,
                                                                                                   num_iteration)
        stdin, stdout, stderr = system_driver.ssh_query(restore_cmd, ip_destination, True)
    except Exception as exception:
        my_logger.critical('ERROR: restore:' + str(exception) + '\n')
        print("Restore phase failed")


def wait_clean(container_name, ip_destination):
    """
    Wait for restarting, clean the checkpoint folders
    :param container_name:
    :param ip_destination:
    :return:
    """
    try:
        print("starting the cleaning phase")
        wait_cmd = 'lxc-wait -n {} -s RUNNING'.format(container_name)
        stdin, stdout, stderr = system_driver.ssh_query(wait_cmd, ip_destination, True)
        time.sleep(5)
        umount_cmd = '/root/umount.sh {}'.format(container_name)
        result = subprocess.check_output(umount_cmd, shell=True)
        stdin, stdout, stderr = system_driver.ssh_query(umount_cmd, ip_destination, True)
    except Exception as exception:
        my_logger.critical('ERROR: wait_clean:' + str(exception) + '\n')
        print("failed to clean")


def validate_migration(container_name, ip_client):
    """
    used to test pings after migrating
    :param container_name:
    :param ip_client:
    :return:
    """
    response = 1
    while response != 0:
        response = lxc_driver.container_attach(container_name, ["ping", "-c", "1", str(ip_client)])
    return OK


def migrate(container_name, ip_destination, num_iteration, decision=True, bandwidth_value=35000):
    """
    Core migration method for controlling the whole migration process
    :param container_name:
    :param ip_destination:
    :param num_iteration:
    :param decision:
    :param bandwidth_value:
    :return:
    """
    try:
        t_pre_dump = 0.0
        pre_dump_size = 0.0
        t1 = time.time()
        disk_size = disk_copy(container_name, ip_destination, bandwidth_value)
        t2 = time.time()
        t_diff = t2 - t1
        with open('/root/result_video_app.txt', "a") as my_file:
            my_file.write("\n({}) App/Disk Time: {}\n".format(os.getpid(), t_diff))
        print("App/Disk Time: {}".format(t_diff))
        if decision:
            if int(num_iteration) == 1:
                dumb_memory_copy(container_name, ip_destination, bandwidth_value)
            else:
                t1 = time.time()
                live_memory_copy(container_name, num_iteration, ip_destination, bandwidth_value)
                t2 = time.time()
                t_pre_dump = t2 - t1
                with open('/root/result_video_app.txt', "a") as my_file:
                    my_file.write("({}) Pre-dumps Time: {}\n".format(os.getpid(), t_pre_dump))
                print("Pre-dumps Time: {}".format(t_pre_dump))
            t1 = time.time()
            # TODO: to re-add the tabulation after tests.
            final_memory_copy(container_name, num_iteration, ip_destination, bandwidth_value)
            data_folder = '{}{}/checkpoint/{}'.format(LXC_PATH, container_name, num_iteration)
            send_data(data_folder, ip_destination, bandwidth_value)
            restore(container_name, ip_destination, num_iteration)
            t2 = time.time()
            t_downtime = t2 - t1
            with open('/root/result_video_app.txt', "a") as my_file:
                my_file.write("({}) Downtime time: {}\n".format(os.getpid(), t_downtime))
            print("Downtime time: {}".format(t_downtime))
            t1 = time.time()
            wait_clean(container_name, ip_destination)
            if not lxc_driver.delete_container(container_name):
                return NOK
            t2 = time.time()
            t_clean = t2 - t1
            with open('/root/result_video_app.txt', "a") as my_file:
                my_file.write("({}) Cleaning Time: {}\n".format(os.getpid(), t_clean))
            print("Cleaning Time: {}".format(t_clean))
            return OK
        else:
            if int(num_iteration) == 1:
                dumb_memory_copy(container_name, ip_destination, bandwidth_value)
            else:
                t1 = time.time()
                pre_dump_size = live_memory_copy(container_name, num_iteration, ip_destination, bandwidth_value)
                t2 = time.time()
                t_pre_dump = t2 - t1
                with open('/root/result_video_app.txt', "a") as my_file:
                    my_file.write("({}) Pre-dumps Time: {}\n".format(os.getpid(), t_pre_dump))
                print("Pre-dumps Time: {}".format(t_pre_dump))
            return OK, disk_size, pre_dump_size, t_pre_dump, t_pre_dump + t_diff
    except Exception as exception:
        my_logger.critical('ERROR: migrate:' + str(exception) + '\n')
        print("failed to migrate ...")
        return NOK


def dump_restore(container_name, ip_destination, num_iteration, bandwidth_value):
    """
    Migration procedure used for separating last iteration and restore from the other part
    :param container_name:
    :param ip_destination:
    :param num_iteration:
    :param bandwidth_value:
    :return:
    """
    try:
        t1 = time.time()
        # TODO: to re-add the tabulation after tests.
        data_folder = '{}{}/checkpoint/{}'.format(LXC_PATH, container_name, num_iteration)
        send_data(data_folder, ip_destination, bandwidth_value)
        restore(container_name, ip_destination, num_iteration)
        t2 = time.time()
        t_downtime = t2 - t1
        with open('/root/result_video_app.txt', "a") as my_file:
            my_file.write("({}) Downtime time: {}\n".format(os.getpid(), t_downtime))
        print("Downtime time: {}".format(t_downtime))
        t1 = time.time()
        wait_clean(container_name, ip_destination)
        if not lxc_driver.delete_container(container_name):
            return NOK
        t2 = time.time()
        t_clean = t2 - t1
        with open('/root/result_video_app.txt', "a") as my_file:
            my_file.write("({}) Cleaning Time: {}\n".format(os.getpid(), t_clean))
        print("Cleaning Time: {}".format(t_clean))
        return t_downtime, OK
    except Exception as exception:
        my_logger.critical('ERROR: dump_restore:' + str(exception) + '\n')
        print("failed to dump_restore ...")
        return NOK
