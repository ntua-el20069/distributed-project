import requests
import time
from node import Node, known_ip, known_port, known_node
from helpers import get_url, get_local_ip

if __name__ == "__main__":

    last_time = time.time()
    requests.post(get_url(known_ip, known_port) + "/join", data = known_node)
    nodes = [ Node('192.168.1.11', 9000 + i) for i in range(2, 4) ]
    for node in nodes:
        while time.time() - last_time < 2:
            pass
        last_time = time.time()
        requests.post(get_url(node.ip, node.port) + "/join", data = known_node)