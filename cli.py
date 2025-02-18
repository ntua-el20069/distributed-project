import typer
import requests
from typing import List
from helpers import get_local_ip,   get_url

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
def depart():
    '''node gracefully departs from system'''
    print("Departure of node")

@app.command()
def overlay():
    '''display the overlay network'''
    print("Overlay network")


if __name__ == "__main__":
    app()