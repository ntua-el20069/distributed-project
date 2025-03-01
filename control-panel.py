from flask import Flask, render_template, request, jsonify
import socket
import requests
import sys
from helpers import *

app = Flask(__name__)

my_ip = get_local_ip()

nodes = []


@app.route('/', methods = ['GET'])
def all_contents():
    global nodes
    return render_template("all-contents.html", no_of_nodes = len(nodes))

@app.route('/get-contents', methods=['GET'])
def get_contents():
    global nodes
    all_contents = []

    for node in nodes:
        url = f"http://{node['ip']}:{node['port']}/contents"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
            data = {
                "title": f'''Node ({hash_function(f'{node["ip"]}:{node["port"]}')}) - {node['ip']}:{node['port']}''',
                "contents": response.json()
            }
            all_contents.append(data)
        except requests.RequestException as e:
            all_contents.append({
                "title": f'''Node ({hash_function(f'{node["ip"]}:{node["port"]}')}) - {node['ip']}:{node['port']}''',
                "error": str(e)
            })

    return jsonify(all_contents)  # Corrected JSON response

if __name__ == '__main__':
    # make it get one argument (local/aws) default aws
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        nodes = [ {"ip": my_ip, "port": known_node["port"] + i} for i in range(5) ]
    else:
        nodes = [ {"ip": ip, "port": known_node["port"]} for ip in get_vms_ips() ]
    print(f"Nodes: {nodes}")
    app.run(debug=True, host='0.0.0.0', port=11000, use_reloader=False)