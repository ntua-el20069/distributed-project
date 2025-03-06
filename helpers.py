import socket
import hashlib

REPLICA_FACTOR = 3          # Number of replicas for each key
STRONG_CONSISTENCY = True   # When true linearizability, else eventual consistency
MAX_NODES = 2**7

DEBUG = True
AWS = True
json_file = "contents.json"

def get_vms_ips() -> list:
    with open("team_12_ips.csv", 'r') as  f:
        ips = f.readlines()[1].split(',')[2:]
    return ips

def get_local_ip() -> str:
    """Get the local IP address of the system."""
    try:
        # Create a socket connection to an external server to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google's public DNS server
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error retrieving local IP: {e}")
        return "127.0.0.1"  # Fallback to localhost if there's an error

def get_url(ip: str, port: int) -> str:
    return f"http://{ip}:{port}"


# make a hash function that takes in a string and returns an integer
def hash_function(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest(), 16) % MAX_NODES

known_ip: str = get_vms_ips()[0] if AWS else get_local_ip()
known_port: int = 5000

known_node = {
    "ip": known_ip,
    "port": known_port,
    "id": hash_function(f"{known_ip}:{known_port}")
}

BASE_URL = get_url(known_node["ip"], known_node["port"])
control_panel_node = 1 # specify 1-5 for the appropriate vm

nodes = []
if not AWS:
    nodes = [ {"ip": get_local_ip(), "port": known_node["port"] + i} for i in range(10) ] # would change to 10 but we do not test locally with 10 terminals
else:
    nodes = [ {"ip": ip, "port": known_node["port"]} for ip in get_vms_ips() ]
    nodes_2 = [ {"ip": ip, "port": known_node["port"] + 1} for ip in get_vms_ips() ]
    nodes.extend(nodes_2)

def from_json(res: dict) -> dict:
    if "message" in res.keys():
        return res
    return {
        "id": int(res["id"]),
        "ip": res["ip"],
        "port": int(res["port"])
    } 


def is_port_in_use(ip: str, port: int) -> bool:
    """
    Check if a port is already in use.
    :param ip: The IP address to bind to.
    :param port: The port to check.
    :return: True if the port is in use, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((ip, port))  # Try to bind to the port
            return False  # Port is available
        except OSError:
            return True  # Port is in use