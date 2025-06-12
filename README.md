# Tunnel_Over_Anything

This is a project to allow for the transmission of UDP packets over a discrete tunnel made up of ICMP, DNS, or other common packets to evade IDS/IPS, EDR, or Captive Portal. Tunnel Over Anything (TOE) is best used in conjunction with [OpenVPN](https://openvpn.net/) which is a free VPN client and server software. Details on configuring TOE to work with OpenVPN are detailed later on.

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