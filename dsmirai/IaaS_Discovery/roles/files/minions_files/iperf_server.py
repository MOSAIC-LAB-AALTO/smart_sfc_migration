import iperf3
import sys


def run(ip_server, number_of_request, port=6969):
    """
    IPerf server for network evaluation

    :param ip_server:
    :param number_of_request:
    :param port:
    :return:
    """
    server = iperf3.Server()
    server.bind_address = ip_server
    server.port = port
    server.verbose = False
    i = 0
    while i < number_of_request:
        server.run()
        i += 1
