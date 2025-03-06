import json
import requests
import time
from helpers import *


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

    print("All contents: ", all_contents)
    print("\n\n")

if __name__ == "__main__":
    while True:
        get_contents()
        time.sleep(3)