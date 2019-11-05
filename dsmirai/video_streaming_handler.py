import subprocess


def enable_remote_video_streaming(minion_address, orchestrator_port, client_ip_address, ssh_port=22, remote_port=80,
                                  user_name='root', key_file='/root/.ssh/id_rsa',
                                  project_directory='/root/PycharmProjects/mirai_project/dsmirai/'):
    subprocess.Popen(['python', 'video_streaming_forwarder.py', '{}:{}'.format(minion_address, ssh_port),
                      '-r', '{}'.format(remote_port), '-p', '{}'.format(orchestrator_port), '-r',
                      '192.168.0.{}:{}'.format(client_ip_address.split('.')[3], remote_port), '--user',
                      '{}'.format(user_name), '--key', '{}'.format(key_file)], cwd='{}'.format(project_directory),
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return 1
