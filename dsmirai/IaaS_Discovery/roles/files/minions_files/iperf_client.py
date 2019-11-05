import iperf3
import sys


def run(ip_client, ip_server, port=6969):
    """
    IPerf client for network evaluation
    :param ip_client:
    :param ip_server:
    :param port:
    :return:
    """
    client = iperf3.Client()
    client.duration = 1
    client.bind_address = ip_client
    client.server_hostname = ip_server
    client.port = port
    # client.blksize = 1234
    client.num_streams = 1
    client.zerocopy = True
    client.verbose = False
    client.reverse = True
    result = client.run()
    if result.error:
        print(result.error)
    else:
        print('')
        print('Test completed:')
        print('  started at         {0}'.format(result.time))
        print('  bytes transmitted  {0}'.format(result.sent_bytes))

        print('Average transmitted data in all sorts of networky formats:')
        print('  bits per second      (bps)   {0}'.format(result.sent_bps))
        print('  Kilobits per second  (kbps)  {0}'.format(result.sent_kbps))
        print('  Megabits per second  (Mbps)  {0}'.format(result.sent_Mbps))
        print('  KiloBytes per second (kB/s)  {0}'.format(result.sent_kB_s))
        print('  MegaBytes per second (MB/s)  {0}'.format(result.sent_MB_s))
    return result.sent_bytes, result.sent_bps, result.sent_Mbps, result.sent_MB_s
