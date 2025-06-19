# Import configuration for tunnel_over_anything

# Standard libraries
import toml

# Third-party libraries
from attrs import define, field, validators

# Project libraries
import src.default as df


@define
class ConnectorConfig:
    """Defines the ConnectorConfig base class"""

    endpoint: str = field(validator=validators.instance_of(str))
    port: int = field(
        converter=int, validator=validators.and_(validators.ge(1), validators.le(65535))
    )
    recv_path: str = field(validator=validators.instance_of(str))
    tx_path: str = field(validator=validators.instance_of(str))


@define
class ClientConfig(ConnectorConfig):
    """Defines the ClientConfig class for configuring ClientConnector objects"""

    @classmethod
    def from_dict(cls, data):
        """Creates a ClientConfig object from a dictionary

        Args:
            data: the dictionary with the client config
        """
        return cls(
            endpoint=data["endpoint"],
            port=data["port"],
            recv_path=df.INBOUND_RAW_PATH,
            tx_path=df.OUTBOUND_PROCESSED_PATH,
        )


@define
class ServerConfig(ConnectorConfig):
    """Defines the ServerConfig class for configuring ServerConnector objects"""

    @classmethod
    def from_dict(cls, data):
        """Creates a ServerConfig object from a dictionary

        Args:
            data: the dictionary with the server config
        """
        return cls(
            endpoint=data["endpoint"],
            port=data["port"],
            recv_path=df.OUTBOUND_RAW_PATH,
            tx_path=df.INBOUND_PROCESSED_PATH,
        )


@define
class PacketConfig:
    """Defines the PacketConfig class for configuring ServerConnector objects"""

    protocol: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(df.PROTOCOLS)
        )
    )
    encoding: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(df.ENCODING)
        )
    )
    mode: str = field(
        validator=validators.and_(
            validators.instance_of(str), validators.in_(["server", "client"])
        )
    )

    @classmethod
    def from_dict(cls, data: dict):
        """Creates a PacketConfig object from a dictionary

        Args:
            data: the dictionary with the packet config
        """
        return cls(
            protocol=data["protocol"].lower(),
            encoding=data["encoding".lower()],
            mode=data["mode"].lower(),
        )


@define
class Config:
    """Defines the Config class for importing the config.toml"""

    client: ClientConfig = field(validator=validators.instance_of(ClientConfig))
    server: ServerConfig = field(validator=validators.instance_of(ServerConfig))
    packet: PacketConfig = field(validator=validators.instance_of(PacketConfig))
    log_level: str = field(
        validator=validators.and_(
            validators.instance_of(str),
            validators.in_(["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        )
    )

    @classmethod
    def load_config(cls, file_name: str = "config.toml"):
        """Creates a Config object from a dictionary

        Args:
            file_name: the name of the toml config file
        """
        with open(file=f"{df.CLIENT_DIR}/{file_name}", mode="r") as file:
            config_dict = toml.load(file)

        return cls(
            client=ClientConfig.from_dict(config_dict["client"]),
            server=ServerConfig.from_dict(config_dict["server"]),
            packet=PacketConfig.from_dict(config_dict["packet"]),
            log_level=config_dict["log_level"].upper(),
        )
