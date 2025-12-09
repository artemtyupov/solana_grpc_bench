
from .base import BaseProvider
from .yellowstone import GeyserClient

def create_provider(kind: str) -> BaseProvider:
    if kind == "yellowstone":
        return GeyserClient()
    raise ValueError(f"Unsupported provider kind: {kind}")
