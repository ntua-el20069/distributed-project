# distributed-project
An implementation of a Chord DHT based app, for Distributed Systems course (NTUA)

## Setup
Using a `python3.10` virtual environment, install dependencies from `requirements.txt`

## Chordify client
Command line interface is provided based on python `typer` library
- Help for all available commands
```
python -m cli --help
```
- Help for a specific command (e.g. `insert`)
```
python -m cli insert --help
```
- Execute a specific command
```
python -m cli insert --key "hello" --value "world"
```
