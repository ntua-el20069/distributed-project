import sys
import requests
from cli import BASE_URL
import time
from node import REPLICA_FACTOR, STRONG_CONSISTENCY

nodes_number = 10
base_path = ""

# make a decorator measure time
def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end-start} seconds")
    return wrapper

@measure_time
def insert():
    global nodes_number
    for i in range(nodes_number):
        print(f"Inserting key-value pair into DHT: node {i}")
        with open(base_path + f"insert/insert_0{i}_part.txt", "r") as f:
            for song in f.readlines():
                if not song: continue
                song = song.replace('\n', '')
                requests.post(f"{BASE_URL}/insert", data={"key": song.strip(), "value": i})

@measure_time
def query():
    global nodes_number
    for i in range(nodes_number):
        print(f"Querying key-value pair from DHT: node {i}")
        with open(base_path + f"queries/query_0{i}.txt", "r") as f:
            for song in f.readlines():
                if not song: continue
                response = requests.get(f"{BASE_URL}/query", params={"key": song.strip()})
                print(response.json())

@measure_time
def mixed_requests():
    global nodes_number
    for i in range(nodes_number):
        print(f"Sending requests to DHT: node {i}")
        with open(base_path + f"requests/requests_0{i}.txt", "r") as f:
            for line in f.readlines():
                if not line: continue
                parts = line.split(', ')
                cmd = parts[0].replace('\n', '')
                song = parts[1].replace('\n', '')
                if cmd == "insert":
                    node_that_stores_song = int(parts[2])
                    res = requests.post(f"{BASE_URL}/insert", data={"key": song.strip(), "value": node_that_stores_song})
                    print(res.json())
                elif cmd == "query":
                    response = requests.get(f"{BASE_URL}/query", params={"key": song.strip()})
                    print(response.json())


if __name__ == '__main__':
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
    else:
        print("Invalid experiment argument. Please provide insert, query, or requests")
        sys.exit(1)