
from dataclasses import dataclass
from typing import List, Literal
import tomli

EndpointKind = Literal["arpc", "jetstream", "shreder", "yellowstone"]

@dataclass
class Endpoint:
    name: str
    url: str
    x_token: str
    kind: EndpointKind

@dataclass
class Config:
    transactions: int
    account: str
    commitment: str

@dataclass
class ConfigToml:
    config: Config
    endpoint: List[Endpoint]

def load_or_create(path: str) -> ConfigToml:
    with open(path, "rb") as f:
        data = tomli.load(f)

    cfg = data.get("config", {})
    endpoints = data.get("endpoint", [])

    config = Config(
        transactions=int(cfg.get("transactions", 1000)),
        account=str(cfg.get("account", "")),
        commitment=str(cfg.get("commitment", "processed")),
    )
    eps = [Endpoint(**e) for e in endpoints]
    return ConfigToml(config=config, endpoint=eps)
