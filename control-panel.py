from flask import Flask, render_template, request, jsonify
import socket
import requests
import sys
import json
import subprocess
from helpers import *

app = Flask(__name__)

@app.route('/', methods = ['GET'])
def all_contents():
    global nodes
    return render_template("all-contents.html", no_of_nodes = len(nodes))

@app.route('/remote', methods = ['GET'])
def remote_contents():
    global nodes
    return render_template("remote-contents.html", no_of_nodes = len(nodes))

@app.route('/get-contents', methods=['GET'])
def get_contents():
    '''runs in the VMs to get the contents from all the VMs and save a json file'''
    global nodes, contents_path
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
        
    # Save the retrieved contents to a JSON file
    with open(contents_path, "w", encoding="utf-8") as f:
        json.dump(all_contents, f, indent=4)

    return jsonify(all_contents)  # Corrected JSON response

@app.route('/get-remote-contents', methods=['GET'])
def get_remote_contents():
    '''runs in our local PC to get the contents from the remote VM that runs the control panel (using SCP)'''
    global control_panel_node, contents_path
    remote_path = f"team_12-vm{control_panel_node}:~/distributed-project/{contents_path}"
    local_path = contents_path
    
    try:
        # Execute SCP command to copy the file from the remote machine
        subprocess.run(["scp", remote_path, local_path  ], check=True)
        
        # Read the downloaded JSON file
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"SCP failed: {str(e)}"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # make it get one argument (local/aws) default aws
    # nodes defined in helpers.py
    print(f"Nodes: {nodes}")
    app.run(debug=True, host='0.0.0.0', port=11000, use_reloader=False)