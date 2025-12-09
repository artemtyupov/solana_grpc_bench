
import asyncio
import argparse
from typing import List
from dataclasses import dataclass

from config import load_or_create
from utils import get_current_timestamp, Comparator
from analysis import analyze_delays
from providers import create_provider
from providers.base import ProviderContext

@dataclass
class EndpointCfg:
    name: str
    url: str
    x_token: str
    kind: str

async def run_async(config_path: str):
    cfg = load_or_create(config_path)
    endpoints: List[EndpointCfg] = [EndpointCfg(**e.__dict__) for e in cfg.endpoint]

    start_time = get_current_timestamp()
    shutdown_event = asyncio.Event()
    comparator = Comparator(worker_count=len(endpoints))

    tasks = []
    for ep in endpoints:
        prov = create_provider(ep.kind)
        ctx = ProviderContext(
            endpoint=ep,
            config=cfg.config,
            shutdown_event=shutdown_event,
            start_time=start_time,
            comparator=comparator
        )
        tasks.append(asyncio.create_task(prov.run(ctx)))

    # allow Ctrl+C to trigger shutdown
    loop = asyncio.get_running_loop()
    stop_future = loop.create_future()

    def _sig():
        if not stop_future.done():
            stop_future.set_result(True)
    for sig in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(__import__('signal'), sig), _sig)
        except Exception:
            pass

    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    shutdown_event.set()
    await asyncio.gather(*tasks, return_exceptions=True)

    # Print final analysis
    analyze_delays(comparator, [e.name for e in endpoints])

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.toml", help="Path to config.toml")
    args = parser.parse_args()
    asyncio.run(run_async(args.config))

if __name__ == "__main__":
    run()
