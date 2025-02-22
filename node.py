import hashlib
import requests
import json
from helpers import get_url, get_local_ip
from flask import request

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

    def insert(self, key: str, value: str) -> dict:
        key_hash = hash_function(key)
        responsible_node = self.find_successor(key_hash) # find the node responsible for the key
        if responsible_node['id'] != self.id:
            successor = self.successor
            print(f"Node {self.id}: not responsible for this key, forwarding to successor: node {successor}")
            return requests.post(get_url(successor['ip'], successor['port']) + "/insert", data = {"key": key, "value": value}).json()
        else:   
            if key in self.songs:
                    self.songs[key] += f",{value}"  # Use comma as separator
                    action = "append"
            else:
                # save localy
                self.songs[key] = value
                action = "insert"
            print(f"Node {self.id}: {action} {key} -> {self.songs[key]}")
            return {"status": "success", "node": self.id, "action": action, "current_value": self.songs[key]}
        
    def delete(self, key: str) -> dict:
        key_hash = hash_function(key)
        responsible_node = self.find_successor(key_hash) # find the node responsible for the key
        if responsible_node['id'] == self.id:
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

    def query(self, key: str) -> dict:
        if key == "*":
            # Get the start parameter from request arguments (GET params)
            start = request.args.get("start", default=self.id, type=int)
            
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
            key_hash = hash_function(key)
            responsible_node = self.find_successor(key_hash)
            if responsible_node['id'] == self.id:
                value = self.songs.get(key)
                if value is None:
                    print(f"Node {self.id}: Key '{key}' not found.")
                    return {
                        "status": "fail",
                        "node": self.id,
                        "action": "query",
                        "key": key,
                        "message": "Key not found"
                    }
                else:
                    print(f"Found <key,value>: <{key}, {value}> in node {self.id}")
                    return {
                        "status": "success",
                        "node": self.id,
                        "action": "query",
                        "key": key,
                        "value": value
                    }
            else:
                # forward to the responisible node
                successor = self.successor
                print(f"Node {self.id}: not responsible for this key, forwarding to successor: node {successor}")
                return requests.get(
                    get_url(successor['ip'], successor['port']) + "/query",
                    params={"key": key}
                ).json()
    
    def _get_start_param(self) -> int:
        """Helper to retrieve start parameter from request context"""
        from flask import request  # Import inside method for thread safety
        return int(request.args.get("start", default=self.id, type=int))
        


        