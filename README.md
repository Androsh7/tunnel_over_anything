# Tunnel over Anything
> [!CAUTION]
> THIS TOOL IS FOR AUTHORIZED TESTING AND RESEARCH PURPOSES ONLY
> UNAUTHORIZED USE OF THIS TOOL MAY CONSTITUTE A CRIME

Tunnel over Anything (ToA) is an experimental end-to-end tunneling program that disguises TCP/UDP traffic as legitimate network protocols such as DNS, HTTP, or even ICMP (ping) to evade IDS/IPS detection or escape captive portal firewalls.

Supported Transports:<br>
- ✅ UDP<br>
- ⏳ TCP (planned)<br>

Obfuscation methods:<br>
- ✅ None (raw relay mode)
- ✅ DNS
- ⏳ HTTP/HTTPS (planned)
- ⏳ ICMP Ping (planned)

## How It Works

To transmit obfuscated data over a network, two instances of Tunnel over Anything (ToA) are required. At least one node must operate in server mode with a publicly accessible port to accept incoming connections. The other node runs in client mode, initiating the connection to the server.

![Setup diagram](docs/Tunnel_Over_Anything.drawio.svg)

### Server mode:

In server mode, ToA expects to receive encoded packets on it's listening port, disassemble the data and transmit it via the client connector.

Generally the server connector will be public facing, whereas the client connector will point to a local service.

[Example client config](examples/client_side_config.toml)
```
                   [ ------------- Tunnel over Anything --------------]
encoded packets -> server connector -> disassembler -> client connector -> raw data
encoded packets <- server connector <-   assembler  <- client connector <- raw data
```
### Client mode

In client mode, ToA expects to receive raw packets on it's listening port, assemble the data and transmit it via the client connector.

Generally the server connector will be internally facing, whereas the client connector will point to a public ip.

[Example server config](examples/server_side_config.toml)
```
                   [ ------------- Tunnel over Anything --------------]
       raw data -> server connector ->   assembler  -> client connector -> encoded data
       raw data <- server connector <- disassembler <- client connector <- encoded data
```

## Running Tunnel_Over_Anything

### Run via docker (experimental)
```
# client example
docker run \
    -v path/to/config.toml:/tunnel_over_anything/config.toml \
    -p 127.0.0.1:<host_port>:<container_port> \
    --restart unless-stopped \
    -d \
    tunnel_over_anything:latest
```
```
# server example
docker run \
    -v path/to/config.toml:/tunnel_over_anything/config.toml \
    -p <host_port>:<container_port> \
    --restart unless-stopped \
    -d \
    tunnel_over_anything:latest
```

### Run via python (recommended)
#### Run on linux
```
python -m venv .venv
source .venv/bin/activate
pip install .
python main.py
```
#### Run on windows
```
python -m venv .venv
.\.venv\Scripts\activate.ps1
pip install .
python main.py
```