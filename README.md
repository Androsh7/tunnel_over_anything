# Tunnel_Over_Anything

Tunnel over anything is a program for transmitting any UDP data (OpenVPN traffic) over the internet disguised as DNS packets. The program is setup on both endpoints client and server, via a docker container and then any data transmitted into either of the endpoints is transported to the other

![Diagram](docs/Tunnel_Over_Anything.drawio.svg)

## Running Tunnel_Over_Anything

Run via docker
```
docker run -v path/to/config.json:/tunnel_over_anything/config.json --restart unless stopped -d tunnel_over_anything:latest
```

Run via python
```
python -m venv .venv
pip install .
python main.py
```