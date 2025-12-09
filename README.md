# geyserbench-py (Yellowstone only)

Python benchmark for measuring transaction delivery latency via **Yellowstone gRPC (Geyser)**. Subscribes to transactions filtered by account, records the first reporter per signature, and computes delays (ms) for others relative to the fastest.

## Install
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Config (`config.toml`)
```toml
[config]
transactions = 1000

[[endpoint]]
name = "yellowstone#1@fra"
url  = "http://host:port"
x_token = ""
kind = "yellowstone"
```

## Run
```bash
python main.py
```

## Notes
- Use unique `endpoint.name` for each reporter when running multiple instances.
- Delays are calculated from monotonic timestamps (ns) and displayed in milliseconds.