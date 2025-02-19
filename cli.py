import typer
from typing import List
import requests
from node import Node, from_json, known_node
from helpers import get_local_ip, get_url, is_port_in_use

app = typer.Typer()

BASE_URL = "http://192.168.1.10:5000"

@app.command()
def insert(key: str = typer.Option(..., help="song title"),
           value: str = typer.Option(..., help="node that stores the song")):
    '''Inserts a key-value pair into the DHT'''
    data = {"key": key, "value": value}
    response = requests.post(f"{BASE_URL}/insert", data=data)
    print(response.json())
"""
@app.command()
def insert(key: str = typer.Option(help = "song title"), value: str = typer.Option(help = "node that stores the song")):
    '''inserts a key-value pair into the DHT'''
    print(f"Insert <key,value> = <{key},{value}>")
"""

@app.command()
def delete(key: str = typer.Option(help = "song title")):
    '''deletes a key-value pair with specified key from the DHT'''
    print(f"Delete key = {key}")

@app.command()
def query(key: List[str] = typer.Option(["*"], help = "song title")) -> str:
    '''Returns the value that corresponds to the given key.
    Using *, returns all key-value pairs in the DHT grouped by node'''
    print(f"Query key = {key} and return value")

@app.command()
# this should CHANGE to no parameters when we deploy to multiple nodes
def depart(port: int = typer.Option(help = "port number")): 
    '''node gracefully departs from system'''
    print("Departure of node")
    ip = get_local_ip()
    if ip == known_node["ip"] and port == known_node["port"]:
        print("Cannot depart from known node")
        return
    res = requests.get(get_url(ip, port) + "/depart")
    print(res.text)

@app.command()
def overlay():
    '''display the overlay network'''
    print("Overlay network")
    out = requests.post(get_url(known_node["ip"], known_node["port"]) + "/show-network", data = known_node)
    print(out.text)

if __name__ == "__main__":
    app()