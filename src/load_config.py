# Import configuration for tunnel_over_anything

# Standard libraries
import toml

# Project libraries
import src.default as df

# Third-party libraries
from attrs import define, field, validators


@define
class ConnectorConfig:
    connector_type: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(["bind", "connect"])
        )
    )
    endpoint: str = field(validator=validators.instance_of(str))
    port: int = field(
        converter=int, validator=validators.and_(validators.ge(1), validators.le(65535))
    )
    recv_path: str = field(validator=validators.instance_of(str))
    tx_path: str = field(validator=validators.instance_of(str))

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            connector_type=data["connector_type"],
            endpoint=data["endpoint"],
            port=data["port"],
            recv_path=data["recv_path"],
            tx_path=data["tx_path"],
        )


@define
class PacketConfig:
    protocol: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(df.PROTOCOLS)
        )
    )

    @classmethod
    def from_dict(cls, data: dict):
        return cls(protocol=data["protocol"].lower())


@define
class Config:
    client: ConnectorConfig = field(validator=validators.instance_of(ConnectorConfig))
    server: ConnectorConfig = field(validator=validators.instance_of(ConnectorConfig))
    packet: PacketConfig = field(validator=validators.instance_of(PacketConfig))
    log_level: str = field(
        validator=validators.and_(
            validators.instance_of(str),
            validators.in_(["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        )
    )

    @classmethod
    def load_config(cls, file_name: str = "config.toml"):
        # Load config files
        with open(file=f"{df.CLIENT_DIR}/{file_name}", mode="r") as file:
            config_dict = toml.load(file)

        return cls(
            client=ConnectorConfig.from_dict(config_dict["client"]),
            server=ConnectorConfig.from_dict(config_dict["server"]),
            packet=PacketConfig.from_dict(config_dict["packet"]),
            log_level=config_dict["log_level"].upper(),
        )
