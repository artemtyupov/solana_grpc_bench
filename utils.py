
import time
import os
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class TransactionData:
    timestamp: float
    signature: str
    start_time: float

@dataclass
class Comparator:
    worker_count: int
    data: Dict[str, Dict[str, TransactionData]] = field(default_factory=dict)

    def add(self, from_name: str, data: TransactionData) -> None:
        m = self.data.setdefault(data.signature, {})
        m[from_name] = data

    def get_valid_count(self) -> int:
        return len(self.data)

    def get_all_seen_count(self) -> int:
        # "complete" means seen by all workers
        return sum(1 for m in self.data.values() if len(m) >= self.worker_count)

def get_current_timestamp() -> float:
    return time.time()

def open_log_file(endpoint_name: str):
    os.makedirs("logs", exist_ok=True)
    return open(os.path.join("logs", f"{endpoint_name}.log"), "a", buffering=1, encoding="utf-8")

def write_log_entry(f, timestamp: float, endpoint_name: str, signature: str) -> None:
    f.write(f"[{timestamp:.3f}] [{endpoint_name}] {signature}\n")

def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * p
    f = int(k)
    c = min(f + 1, len(values)-1)
    if f == c:
        return values[f]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1
