import subprocess
import time


def get_live_cpu():
    """
    real-time cpu calculator
    :return:
    """
    j = 0
    cpu_table = []
    while j < 2:
        cmd = "sed -n 's/^cpu\s//p' /proc/stat"
        answer = subprocess.check_output(cmd, shell=True)
        answer = answer.decode().split(' ')
        answer = answer[1:-1]
        cpu_table.append(int(answer[0].encode('ascii', 'ignore')))
        cpu_table.append(int(answer[2].encode('ascii', 'ignore')))
        cpu_table.append(int(answer[3].encode('ascii', 'ignore')))
        j += 1
        time.sleep(1)
    cpu_percentage = 100 * (cpu_table[3] - cpu_table[0] + cpu_table[4] - cpu_table[1]) / (cpu_table[3] - cpu_table[0] +
                                                                                          cpu_table[4] - cpu_table[1] +
                                                                                          cpu_table[5] - cpu_table[2])
    with open('/root/cpu', "w") as my_file:
        my_file.write(str(cpu_percentage))
        my_file.close()
    return cpu_percentage


get_live_cpu()
