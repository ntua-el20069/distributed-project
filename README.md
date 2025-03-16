# distributed-project
An implementation of a Chord - Distributed Hash Table (DHT) based app, for Distributed Systems course (NTUA)

## Setup on Ubuntu Machine
```bash
git clone https://github.com/ntua-el20069/distributed-project.git

# if you intend to run the services on a remote cluster with nodes in the same network, 
# ensure you have team_12_ips.csv on the current working directory of the remote machine
# (copy the file from your local machine using scp command)

mv team_12_ips.csv distributed-project/ && cd distributed-project/

# python3.10 installation
sudo apt update && sudo apt upgrade
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10

sudo apt install python3.10-venv

# Creation of vitrual environment and installation of required python packages
python3.10 -m venv .venv
source .venv/bin/activate
python3.10 -m pip install -r requirements.txt
```

## Run the app
Ensure you firstly open the bootstrap api, which is the node responsible for the other node joins into the P2P network. After you run the api for all nodes, your ready to insert key-value pairs into the DHT or query, by using the command line interface or the experiments script
- On local machine (set `AWS = False` in `helpers.py`), you can run `python api.py [PORT_NUMBER]` providing as ports 5000 (bootstrap node), 5001, 5002, ..., 5009
- On remote machines cluster (set `AWS = True` in `helpers.py`), you can run the api on ports 5000, 5001 for each of the 5 vms provided



## Chordify client
Command line interface is provided based on python `typer` library
Some of the available actions involve insertions of key-value pairs, queries based on keys, graceful departure of a node. 
- Help for all available commands
```
python cli.py --help
```
- Help for a specific command (e.g. `insert`)
```
python cli.py insert --help
```
- Execute a specific command
```
python cli.py insert --key "hello" --value "world"
```

## Experiments Script
You can run 3 types of experiments `insert`, `query`, `requests` 
by running the script following with the corresponding argument, as shown below for insert experiment.
```bash
python script.py insert
```

## Experiments results
We ran experiments for strong and eventual consistency types and replication factor 1, 3, 5.
You can see some experiments results: throughput diagrams, query results and difference on the freshness of the values in `experiments/` directory.

## Visualization of the DHT
While running the APIs you can also run a frontend app which periodically shows the contents of the nodes in the P2P network. You need to run `python control-panel.py` and access the visualization via your browser pressing the indicated link.

## Contributors
- Cleopatra Dimaraki
- Nikolaos Papakonstantopoulos
