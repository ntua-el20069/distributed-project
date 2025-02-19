import socket
import hashlib

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