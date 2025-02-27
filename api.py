from flask import Flask, render_template, request
import socket
import requests
import sys
from node import Node, from_json, known_node, REPLICA_FACTOR, STRONG_CONSISTENCY
import hashlib
import json
import copy
from helpers import get_local_ip,   get_url, is_port_in_use

app = Flask(__name__)
node = None

@app.route('/set_predecessor',methods = ['POST'])
def set_predecessor() -> str:
    global node
    result = from_json(request.form.to_dict())
    node.predecessor = {
        "id": result["id"],
        "ip": result["ip"],
        "port": result["port"]
    }
    print(f"Node {node.id} set predecessor to {node.predecessor['id']}")
    return f"Node {node.id} set predecessor to {node.predecessor['id']}"

@app.route('/set_successor',methods = ['POST'])
def set_successor() -> str:
    global node
    result = from_json(request.form.to_dict())
    node.successor = {
        "id": result["id"],
        "ip": result["ip"],
        "port": result["port"]
    }
    print(f"Node {node.id} set successor to {node.successor['id']}")
    return f"Node {node.id} set successor to {node.successor['id']}"

@app.route('/get_predecessor', methods=['GET'])
def get_predecessor():
    global node
    if node.predecessor is None:
        return json.dumps({"message": "No predecessor"})  # Return a valid JSON response
    print(f"Node {node.id} predecessor is {node.predecessor['id']}")
    return json.dumps(node.predecessor)

@app.route('/get_successor',methods = ['GET'])
def get_successor() -> str:
    global node
    if node.successor is None:
        return json.dumps({"message": "No successor"})
    print(f"Node {node.id} successor is {node.successor['id']}")
    return json.dumps(node.successor)

@app.route('/join',methods = ['POST'])
def join_route() -> str:
    global node
    result = from_json(request.form.to_dict())
    known_node = {
        "ip": result["ip"],
        "port": result["port"],
        "id": result["id"]
    }
    join_response = node.join(known_node)
    return json.dumps(join_response)
    
@app.route('/share_with_predecessor',methods = ['GET'])
def share_with_predecessor_route() -> str:
    global node
    shared_dict = node.share_with_predecessor()
    return json.dumps(shared_dict)

@app.route('/find_successor',methods = ['POST'])
def find_successor_route() -> str:
    global node
    result = request.form.to_dict()
    key = int(result["key"])
    successor = node.find_successor(key)
    return json.dumps(successor)

@app.route('/insert', methods=['POST'])
def insert_route():
    global node, REPLICA_FACTOR
    data = request.form.to_dict()
    key = data.get('key')
    value = data.get('value')
    remaining_replicas = int(data.get('remaining_replicas', REPLICA_FACTOR))
    result = node.insert(key, value, remaining_replicas)
    return json.dumps(result)

@app.route('/replicate', methods=['POST'])
def replicate_route():
    key = request.form.get("key")
    value = request.form.get("value")
    # Here, you may store the replica in a separate structure or merge with self.songs,
    # depending on your design.
    node.songs[key] = value  # For simplicity, we update the same store.
    return json.dumps({"status": "success", "node": node.id, "action": "replicate", "key": key})


@app.route('/delete', methods=['POST'])
def delete_route():
    global node, REPLICA_FACTOR
    data = request.form.to_dict()
    key = data.get('key')
    remaining_replicas = int(data.get('remaining_replicas', REPLICA_FACTOR))
    result = node.delete(key, remaining_replicas)
    return json.dumps(result)

@app.route('/query', methods=['GET'])
def query_route():
    global node
    key = request.args.get("key")
    start = request.args.get('start', type=int, default=None)
    remaining = request.args.get("remaining_replicas", default=REPLICA_FACTOR, type=int)
    result = node.query(key, start, remaining_replicas=remaining)
    return json.dumps(result)

@app.route('/depart', methods=['GET'])
def depart():
    global node
    if not node.successor or not node.predecessor:
        return "Node has no successor or predecessor", 400
    # here we remove the node from the network by updating successor's and predessor's pointers
    requests.post(get_url(node.predecessor['ip'], node.predecessor['port']) + '/set_successor', data = node.successor)
    requests.post(get_url(node.successor['ip'], node.successor['port']) + '/set_predecessor', data = node.predecessor)
    if REPLICA_FACTOR == 1:
        res = requests.post(get_url(node.successor['ip'], node.successor['port']) + '/heritage', data = node.songs)
        if not res.ok:
            return "Heritage failed - but Node has departed", 500
    # after removing node from the network, insert all its songs to the network beggining from its successor
    if REPLICA_FACTOR > 1:
        # a not optimal way to re-distribute (insert replicas) - beginning from the REPLICA_FACTOR-th predecessor would be faster
        for key in node.songs:
            res = requests.post(get_url(node.successor['ip'], node.successor['port']) + '/insert', data = {"key": key, "value": node.songs[key]})
            print(f"\nfor key: {key}")
            print(res.json())
    # set successor and predecessor of node to None for debugging purposes
    node.successor = None
    node.predecessor = None
    node.songs = {}
    print(f"Node {node.id} has departed")
    return f"Node {node.id} has departed"

@app.route('/heritage', methods=['POST'])
def heritage_route():
    global node
    key_values = request.form.to_dict()
    node.heritage(key_values)
    return "Heritage successful", 200

@app.route('/show-network',methods = ['POST'])
def show_network() -> str:
    global node
    
    result = from_json(request.form.to_dict())
    known_node = {
        "ip": result["ip"],
        "port": result["port"],
        "id": result["id"]
    }
    out = f"{node.id}"
    if node.successor["ip"] != known_node["ip"] or node.successor["port"] != known_node["port"]:
        out += f" -> {requests.post(get_url(node.successor['ip'], node.successor['port']) + '/show-network', data = known_node).text}"
    return out

@app.route('/contents', methods=['GET'])
def contents():
    global node
    return json.dumps(node.songs)

if __name__ == '__main__':
    ip: str = get_local_ip()  # Automatically get the local IP address
    port: int = int(sys.argv[1]) if len(sys.argv) > 1 else known_node["port"]  # Default port if not provided
    node = Node(ip,port)

    # check that port is not in use
    if is_port_in_use(ip, port):
        print(f"Port {port} is already in use. Exiting.")
        sys.exit(1)
    
    # Node joins the P2P network through the known (bootstrap) node
    join_response = node.join(known_node)
    print("Join response:", join_response)

    # listen for requests from other nodes
    app.run(host = ip, port = int(port), debug = True, use_reloader = False)