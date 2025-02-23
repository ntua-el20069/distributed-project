from flask import Flask, render_template, request
import socket
import requests
import sys
from node import Node, from_json, known_node
import hashlib
import json
import copy
from helpers import get_local_ip,   get_url, is_port_in_use

app = Flask(__name__)
node = None
REPLICA_FACTOR = 1          # Number of replicas for each key
STRONG_CONSISTENCY = True   # When true linearizability, else eventual consistency

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
    global node
    data = request.form.to_dict()
    key = data.get('key')
    value = data.get('value')
    result = node.insert(key, value)
    return json.dumps(result)

@app.route('/delete', methods=['POST'])
def delete_route():
    global node
    data = request.form.to_dict()
    key = data.get('key')
    result = node.delete(key)
    return json.dumps(result)
"""
@app.route('/query', methods=['GET'])
def query_route():
    global node
    params = request.args.to_dict()
    key = params.get('key')
    result = node.query(key)
    return json.dumps(result)
"""
@app.route('/query', methods=['GET'])
def query_route():
    global node
    
    key = request.args.get('key')
    start = request.args.get('start', type=int, default=node.id)
    
    result = node.query(key, start)
    
    return json.dumps(result)

@app.route('/depart', methods=['GET'])
def depart():
    global node
    if not node.successor or not node.predecessor:
        return "Node has no successor or predecessor", 400
    if node.successor:
        res = requests.post(get_url(node.successor['ip'], node.successor['port']) + '/heritage', data = node.songs)
        if not res.ok:
            return "Heritage failed - Node has not departed", 500
    if node.predecessor and node.successor:
        requests.post(get_url(node.predecessor['ip'], node.predecessor['port']) + '/set_successor', data = node.successor)
        requests.post(get_url(node.successor['ip'], node.successor['port']) + '/set_predecessor', data = node.predecessor)
    # set successor and predecessor of node to None for debugging purposes
    node.successor = None
    node.predecessor = None
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
    port: int = int(sys.argv[1]) if len(sys.argv) > 1 else 5000  # Default port if not provided
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