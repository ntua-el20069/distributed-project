import sys
import requests
import time
import threading
from helpers import *

TOTAL_REQUESTS = 500
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
        if func.__name__ in ["insert", "query", "mixed_requests"]:
            throughput = TOTAL_REQUESTS / (end-start)
            action = "write" if func.__name__ == "insert" else "read" if func.__name__ == "query" else "mixed"
            config = {
                "k": REPLICA_FACTOR,
                "consistency": "strong" if STRONG_CONSISTENCY else "eventual"
            }
            save_throughput(action, config, throughput)
            print(f"Throughtput: {throughput} requests/second")
            return throughput
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
    threads = []
    for i in range(nodes_number):
        t = threading.Thread(target=insert_in_node, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

@measure_time
def query_in_node(i: int):
    global nodes_number, nodes
    node_url = get_url(nodes[i]['ip'], nodes[i]['port'])
    print(f"Querying key from node {i}")
    with open(base_path + f"queries/query_0{i}.txt", "r") as f:
        for song in f.readlines():
            if not song:
                continue
            song = song.strip()
            # Send query request to this node.
            response = requests.get(node_url + "/query", params={"key": song})
            result = response.json()
            # print(f"Node {i} query for key '{song}' returned: {result}")

@measure_time
def query():
    threads = []
    for i in range(nodes_number):
        t = threading.Thread(target=query_in_node, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
                
@measure_time
def mixed_requests_in_node(i: int):
    global nodes_number, nodes
    node_url = get_url(nodes[i]['ip'], nodes[i]['port'])
    print(f"Sending insert-query requests to node {i}")
    with open(base_path + f"requests/requests_0{i}.txt", "r") as f:
        for no_line, line in enumerate(f.readlines()):
            if not line: continue
            parts = line.split(', ')
            cmd = parts[0].replace('\n', '')
            song = parts[1].replace('\n', '')
            request_id = f"(node_{i}, {no_line})"
            if cmd == "insert":
                node_that_stores_song = parts[2].replace('\n', '')
                # in prints there may be line interleaving problem (due to threading)
                # we may use a lock to avoid this
                res = requests.post(f"{node_url}/insert", data={"key": song.strip(), "value": node_that_stores_song})
                print(f"{request_id}:\t Inserted {song.strip()}: {node_that_stores_song}")
                #print(res.json())
            elif cmd == "query":
                response = requests.get(f"{node_url}/query", params={"key": song.strip()})
                data = response.json()
                try:
                    print(f"{request_id}: Queried {song.strip()} -> {data['status']}: {data['value']}")
                except Exception as e:
                    print(f"{request_id}: Queried {song.strip()} -> Faulty Response: {e}")
   
@measure_time
def mixed_requests():
    for i in range(nodes_number):
        mixed_requests_in_node(i)
    '''threads = []
    for i in range(nodes_number):
        t = threading.Thread(target=mixed_requests_in_node, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()'''

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