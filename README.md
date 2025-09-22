# geyserbench-py (Yellowstone only)

Python benchmark for measuring transaction delivery latency via **Yellowstone gRPC (Geyser)**. Subscribes to transactions filtered by account, records the first reporter per signature, and computes delays (ms) for others relative to the fastest.

## Features
- Yellowstone-only provider (Geyser gRPC).
- Account-based filtering (`account_required` / `account_include` depending on proto version).
- Base58 signature normalization (bytes/hex → base58).
- Metrics: first-detection rate, avg/median/p95 delays (ms), min/max, valid/historical counts.
- Per-reporter logs: `./logs/<name>.log` with `[timestamp] [endpoint] <signature>`.

## Requirements
- Python 3.10+
- Packages: `grpcio`, `base58`, `tomli` (or `tomllib` on Python 3.11+)
- Generated Yellowstone protobuf stubs placed in `geyserbench_py/proto/` or importable via `PYTHONPATH`:
  - `geyser_pb2.py`
  - `geyser_pb2_grpc.py`

### Generate stubs
```bash
pip install grpcio-tools
python -m grpc_tools.protoc -I path/to/proto   --python_out=geyserbench_py/proto   --grpc_python_out=geyserbench_py/proto   path/to/proto/geyser.proto
```

## Install
```bash
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt  # or: pip install grpcio base58 tomli
```

## Config (`config.toml`)
```toml
[config]
transactions = 1000
account = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
commitment = "processed"
# historical_grace_ms = 200  # optional: ignore first N ms as historical

[[endpoint]]
name = "yellowstone#1@fra"
url  = "http://host:port"
x_token = ""
kind = "yellowstone"
```

## Run
```bash
python -m geyserbench_py --config config.toml
```

## Notes
- Use unique `endpoint.name` for each reporter when running multiple instances.
- Delays are calculated from monotonic timestamps (ns) and displayed in milliseconds.
