# Tunnel_over_Anything v0.1.0

Tunnel over Anything (ToA) is a end-to-end tunneling program for transmitting TCP/UDP data in disguised DNS/HTTP/HTTPS/PING packets.

Transport protocols:<br>
    - UDP<br>
    - TCP (planned)<br>

Obfuscation methods:<br>
    - None (relay mode)<br>
    - DNS<br>
    - HTTP/HTTP (planned)<br>
    - PING (planned)<br>

# Implementation

To transport data obfuscated data over a network two instances of ToA are required and at least one node needs to act as a server with an exposed listening port so that a client-server connection can be established.

The traditional setup involves a "client" instance which transmits to a "server" instance. Two ToA instances can also point to each other to allow for either side to initiate a connection.

![Setup diagram](docs/Tunnel_Over_Anything.drawio.svg)

## Running Tunnel_Over_Anything

Run via docker
```
# client example
docker run -v path/to/config.toml:/tunnel_over_anything/config.toml -p 127.0.0.1:<host_port>:<container_port> --restart unless stopped -d tunnel_over_anything:latest

# server example
docker run -v path/to/config.toml:/tunnel_over_anything/config.toml -p <host_port>:<container_port> --restart unless stopped -d tunnel_over_anything:latest
```

Run via python
```
python -m venv .venv
pip install .
python main.py
```