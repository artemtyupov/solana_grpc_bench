
import asyncio
from dataclasses import dataclass
from typing import Any
from utils import get_current_timestamp, open_log_file, write_log_entry, TransactionData

@dataclass
class ProviderContext:
    endpoint: Any
    config: Any
    shutdown_event: asyncio.Event
    start_time: float
    comparator: Any

class BaseProvider:
    async def run(self, ctx: ProviderContext) -> None:
        raise NotImplementedError
