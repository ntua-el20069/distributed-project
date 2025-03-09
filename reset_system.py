import requests
from helpers import nodes

def reset_node(node):
    try:
        requests.post(
            f"http://{node['ip']}:{node['port']}/reset",
            timeout=2
        )
    except requests.exceptions.RequestException:
        pass

def reset_all_nodes():
    for node in nodes:
        reset_node(node)

if __name__ == '__main__':
    print("Resetting all nodes...")
    reset_all_nodes()
    print("Reset complete")