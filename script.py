import sys
import requests
import time
import threading
from helpers import *

nodes_number = 10
base_path = ""
ips = [] # list of ips (5 vm's)

# make a decorator measure time
def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} {args} took {end-start} seconds")
    return wrapper

@measure_time
def insert_in_node(i: int):
    global nodes_number, ips, nodes
    print(f"Inserting key-value pair into DHT: node {i}")
    with open(base_path + f"insert/insert_0{i}_part.txt", "r") as f:
        for song in f.readlines():
            if not song: continue
            song = song.replace('\n', '')
            requests.post(f"{get_url(nodes[i]['ip'], nodes[i]['port'])}/insert", data={"key": song.strip(), "value": str(i)})

@measure_time
def insert():
    global nodes_number, ips
    for i in range(nodes_number):
        threading.Thread(target=insert_in_node, args=(i,)).start()

@measure_time
def query_in_node(i: int):
    global nodes_number, nodes
    #node_info = nodes[i]
    node_url = get_url(nodes[i]['ip'], nodes[i]['port'])
    print(f"Querying key from node node {i}")
    with open(base_path + f"queries/query_0{i}.txt", "r") as f:
        for song in f.readlines():
            if not song:
                continue
            song = song.strip()
            # Send query request to this node.
            response = requests.get(node_url + "/query", params={"key": song})
            result = response.json()
            print(f"Node {nodes[i]['id']} query for key '{song}' returned: {result}")

@measure_time
def query():
    threads = []
    for i in range(nodes_number):
        t = threading.Thread(target=query_in_node, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

"""@measure_time
def query():
    global nodes_number, ips
    for i in range(nodes_number):
        print(f"Querying key-value pair from DHT: node {i}")
        with open(base_path + f"queries/query_0{i}.txt", "r") as f:
            for song in f.readlines():
                if not song: continue
                response = requests.get(f"{BASE_URL}/query", params={"key": song.strip()})
                print(response.json())"""
   
@measure_time
def mixed_requests():
    global nodes_number, ips
    for i in range(nodes_number):
        print(f"Sending requests to DHT: node {i}")
        with open(base_path + f"requests/requests_0{i}.txt", "r") as f:
            for line in f.readlines():
                if not line: continue
                parts = line.split(', ')
                cmd = parts[0].replace('\n', '')
                song = parts[1].replace('\n', '')
                if cmd == "insert":
                    node_that_stores_song = parts[2].replace('\n', '')
                    res = requests.post(f"{BASE_URL}/insert", data={"key": song.strip(), "value": node_that_stores_song})
                    print(res.json())
                elif cmd == "query":
                    response = requests.get(f"{BASE_URL}/query", params={"key": song.strip()})
                    print(response.json())

@measure_time
def test():
    global nodes_number, ips
    print(f"Inserting key-value pair into DHT (test...)")
    with open(base_path + f"tests/test_insert.txt", "r") as f:
        for song in f.readlines():
            i = len(song) % nodes_number
            if not song: continue
            song = song.replace('\n', '')
            requests.post(f"{BASE_URL}/insert", data={"key": song.strip(), "value": i})    


if __name__ == '__main__':

    ips = get_vms_ips()
    print("IP addreddes of the VM's are: ", end="")
    print(ips)

    # check args for possible values: insert, query, requests
    consistency: str = "linearization" if STRONG_CONSISTENCY else "eventual"
    print(f"Trying Experiment with replication factor: {REPLICA_FACTOR} and consistency level: {consistency}...")
    args = sys.argv[1:]
    if len(args) == 0:
        print("Please provide an experiment argument (insert, query, requests)")
        sys.exit(1)
    if args[0] == "insert":
        print("Experiment: Inserting key-value pair into DHT")
        insert()
    elif args[0] == "query":
        print("Experiment: Querying key-value pair from DHT")
        query()
    elif args[0] == "requests":
        print("Experiment: Sending requests to DHT")
        mixed_requests()
    elif args[0] == "test":
        print("Experiment: Testing DHT")
        test()
    else:
        print("Invalid experiment argument. Please provide insert, query, or requests")
        sys.exit(1)