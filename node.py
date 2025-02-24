import hashlib
import requests
import json
from helpers import get_url, get_local_ip
from flask import request
import threading

REPLICA_FACTOR = 3          # Number of replicas for each key
STRONG_CONSISTENCY = True   # When true linearizability, else eventual consistency
MAX_NODES = 2**7

DEBUG = True

# make a hash function that takes in a string and returns an integer
def hash_function(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest(), 16) % MAX_NODES

known_ip: str = get_local_ip()
known_port: int = 5000

known_node = {
    "ip": known_ip,
    "port": known_port,
    "id": hash_function(f"{known_ip}:{known_port}")
}

def identification(node : 'Node') -> dict:
    return {
        "id": node.id,
        "ip": node.ip,
        "port": node.port
    }

def from_json(res: dict) -> dict:
    if "message" in res.keys():
        return res
    return {
        "id": int(res["id"]),
        "ip": res["ip"],
        "port": int(res["port"])
    } 



class Node:
    def __init__(self, ip: str, port: int):
        self.ip : str = ip
        self.port : int = port
        self.songs = {} # key: song title, value: ip (and/or) port of node that stores the song
        self.id : int = hash_function(f"{ip}:{port}")
        self.successor: dict = None
        self.predecessor: dict = None
        print("Node created with id: " + str(self.id))
    
    def join(self, known_node: dict) -> dict:

        if self.ip == known_node["ip"] and self.port == known_node["port"]: # if the node is the first node in the network
            self.successor = identification(self)
            self.predecessor = identification(self)
            print("\n" + 20*"$" + f"  The first Node {self.id} joined the network  " + 20*"$" + "\n")
            return {"message": "1st node successfully joined the network"}
        
        if DEBUG: print("\n" + f"Node {self.id} joining network with known node {known_node['id']}")
        
        self.successor = from_json(requests.post(get_url(known_node['ip'], known_node['port']) + "/find_successor", data = {"key": self.id}).json())
        print(f"Node {self.id} set successor to {self.successor['id']}")
        
        self.predecessor = from_json(requests.get(get_url(self.successor["ip"], self.successor["port"]) + "/get_predecessor").json())
        print(f"Node {self.id} set predecessor to {self.predecessor['id']}")

        requests.post(get_url(self.successor["ip"], self.successor["port"]) + "/set_predecessor", data = identification(self))

        requests.post(get_url(self.predecessor["ip"], self.predecessor["port"]) + "/set_successor", data = identification(self))
        
        print(20*"$" + f"  Node {self.id} joined the network  " + 20*"$" + "\n")

        # use a request to the successor to get the songs that should be inherited
        shared_dict : dict = requests.get(get_url(self.successor['ip'], self.successor['port']) + '/share_with_predecessor').json()
        self.heritage(shared_dict)
        
        return {"message": "Successfully joined the network"}
    
    def is_responsible_for_key(self, key: int) -> bool:
        pass

    def find_successor(self, key: int) -> dict:
        if self.id == key: # key = node id
            return identification(self)
        
        if self.id == self.successor['id']: # if there is only one node in the network
            return identification(self)
        
        if self.id < self.successor['id']:
            if self.id < key <= self.successor['id']:
                return self.successor
            else:
                return from_json(requests.post(get_url(self.successor['ip'], self.successor['port']) + "/find_successor", data = {"key": key}).json())

        if self.id > self.successor['id']:
            if key > self.id or key <= self.successor['id']:
                return self.successor
            else:
                return from_json(requests.post(get_url(self.successor['ip'], self.successor['port']) + "/find_successor", data = {"key": key}).json())
            
    def check_responsible(self, key: str) -> bool:
        key_hash = hash_function(key)
        if self.predecessor is None or self.predecessor['id'] == self.id:
            responsible_node = True
        else:
            if self.predecessor['id'] < self.id:
                responsible_node = (self.predecessor['id'] < key_hash <= self.id)
            else:
                responsible_node = (key_hash > self.predecessor['id'] or key_hash <= self.id)
        return responsible_node

    def insert_key_value_into_songlist(self, key: str, value: str) -> dict:
        if key in self.songs:
            current_values = self.songs[key].split(",")
            # If the new value is already present, do nothing.
            if value in current_values:
                action = "value already exists"
            else:
                self.songs[key] += f",{value}"  # Use comma as separator
                action = "append"
        else:
            # save localy
            self.songs[key] = value
            action = "insert"
        print(f"Node {self.id}: {action} {key} -> {self.songs[key]}")
        return {self.id: {"status": "success", "node": self.id, "action": action, "current_value": self.songs[key] } }

    def forward(self, data: dict, endpoint: str) -> dict:
        if self.successor:
            print(f"Node {self.id}: Forwarding {endpoint} to successor: node {self.successor}")
            return requests.post(get_url(self.successor['ip'], self.successor['port']) + endpoint, data = data).json()
        else:
            print(f"Node {self.id}: No successor to forward to")
            return {"message": "No successor"}

    def insert(self, key: str, value: str, remaining_replicas: int) -> dict:
        global REPLICA_FACTOR, STRONG_CONSISTENCY
        responsible_node = self.check_responsible(key)
        # CAUTION: This is only the strong consistency implementation

        if responsible_node or remaining_replicas < REPLICA_FACTOR:
            local_result = self.insert_key_value_into_songlist(key, value)
            remaining_replicas -= 1
            if remaining_replicas > 0:
                # Forward to the successor
                data = {"key": key, "value": value, "remaining_replicas": remaining_replicas}
                if STRONG_CONSISTENCY: # wait for replica write to be done before returning
                    succ_res = self.forward(data, "/insert")
                    return {**local_result, **succ_res}
                else: # in eventual consistency, return immediately
                    threading.Thread(target=self.forward, args=(data, "/insert")).start()
                    return local_result
            else: # replica write done
                return local_result
        
        else:
            successor = self.successor
            print(f"Node {self.id}: not responsible for this key, forwarding to successor: node {successor}")
            return requests.post(get_url(successor['ip'], successor['port']) + "/insert", data = {"key": key, "value": value}).json()
        
    def delete(self, key: str) -> dict:
        responsible_node = self.check_responsible(key)
        if responsible_node:
            try:
                # save localy
                del self.songs[key]
                print(f"Node {self.id}: Deleted {key}")
                return {"status": "success", "node": self.id, "action": "delete", "key": key}
            except KeyError:
                print(f"Node {self.id}: Key '{key}' not found for deletion.")
                return {"status": "fail", "node": self.id, "action": "delete", "key": key, "message": "Key not found"}
        else:
            # forward to the responisible node
            successor = self.successor
            print(f"Node {self.id}: not responsible for this key, forwarding to successor: node {successor}")
            return requests.post(get_url(successor['ip'], successor['port']) + "/delete", data = {"key": key}).json()

    def query(self, key: str, start: int = None, remaining_replicas: int = None) -> dict:
        global REPLICA_FACTOR, STRONG_CONSISTENCY
        if remaining_replicas is None:
            remaining_replicas = REPLICA_FACTOR
        
        if key == "*":
            start = self.id if start is None else start
            
            # Check if we've completed the full circle
            if self.successor['id'] == start:
                return {
                    "status": "success",
                    "node": self.id,
                    "action": "query",
                    "result": {str(self.id): self.songs.copy()}
                }
            
            # Get next node's response
            try:
                successor_response = requests.get(
                    get_url(self.successor['ip'], self.successor['port']) + "/query",
                    params={"key": "*", "start": start}
                ).json()
            except requests.exceptions.RequestException:
                successor_response = {"result": {}}

            # Merge results
            combined_result = {str(self.id): self.songs.copy()}
            combined_result.update(successor_response.get("result", {}))
            
            return {
                "status": "success",
                "node": self.id,
                "action": "query",
                "result": combined_result
            }
        else:
            # For a specific key, first check if this node is responsible (primary).
            if self.check_responsible(key) or (remaining_replicas < REPLICA_FACTOR):
                # We are the primary for this key; now start the chain read.
                # Here, we decrement remaining_replicas for each replica in the chain.
                if remaining_replicas > 1:
                    successor = self.successor
                    print(f"Node {self.id} (primary): forwarding chain read for key '{key}' to successor {successor} with remaining_replicas={remaining_replicas-1}")
                    try:
                        response = requests.get(
                            get_url(successor['ip'], successor['port']) + "/query",
                            params={
                                "key": key,
                                "remaining_replicas": remaining_replicas - 1
                            }
                        )
                        return response.json()
                    except requests.exceptions.RequestException as e:
                        print(f"Error forwarding query from node {self.id}: {e}")
                        return {
                            "status": "fail",
                            "node": self.id,
                            "action": "query",
                            "key": key,
                            "message": "Error forwarding query"
                        }
                else:
                    # remaining_replicas == 1, this node is the tail.
                    value = self.songs.get(key)
                    if value is None:
                        print(f"Node {self.id} (tail): Key '{key}' not found.")
                        return {
                            "status": "fail",
                            "node": self.id,
                            "action": "query",
                            "key": key,
                            "message": "Key not found"
                        }
                    else:
                        print(f"Node {self.id} (tail): Found <{key}, {value}>")
                        return {
                            "status": "success",
                            "node": self.id,
                            "action": "query",
                            "key": key,
                            "value": value,
                            "hash_key": hash_function(key)
                        }
            else:
                # If the node is not responsible for the key, simply forward without decrementing remaining_replicas.
                successor = self.successor
                print(f"Node {self.id}: not primary for key '{key}', forwarding to successor {successor} without altering replica count.")
                return requests.get(
                    get_url(successor['ip'], successor['port']) + "/query",
                    params={"key": key, "remaining_replicas": remaining_replicas}
                ).json()    

    def heritage(self, key_values: dict):
        self.songs.update(key_values)

    def share_with_predecessor(self) -> dict:
        if not self.predecessor:
            return {}
        shared_dict = {}
        keys_to_delete = []
        for key, value in self.songs.items():
            key_hash = hash_function(key)
            if key_hash <= self.predecessor['id']:
                # if predecessor is responsible for the key give it
                shared_dict[key] = value
                keys_to_delete.append(key)
        for dkey in keys_to_delete:
            del self.songs[dkey]
        print(f"Node {self.id} shared {shared_dict} with predecessor {self.predecessor['id']} \n and now has {self.songs}")

        return shared_dict

    def _get_start_param(self) -> int:
        """Helper to retrieve start parameter from request context"""
        from flask import request  # Import inside method for thread safety
        return int(request.args.get("start", default=self.id, type=int))
        


        