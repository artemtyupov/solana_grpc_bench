
from collections import defaultdict
from utils import percentile

def analyze_delays(comparator, endpoint_names):
    all_signatures = comparator.data
    endpoint_stats = {name: {"first":0, "total":0, "delays":[], "historical":0} for name in endpoint_names}

    fastest_endpoint = None
    highest_rate = 0.0

    for sig, sig_data in all_signatures.items():
        # historical if any endpoint saw tx before its own start_time
        is_hist = any(tx.timestamp < tx.start_time for tx in sig_data.values())

        if is_hist:
            for ep in sig_data.keys():
                endpoint_stats[ep]["historical"] += 1
            continue

        # find first detector
        first_ep, first_tx = min(sig_data.items(), key=lambda kv: kv[1].timestamp)
        endpoint_stats[first_ep]["first"] += 1
        endpoint_stats[first_ep]["total"] += 1

        for ep, tx in sig_data.items():
            if ep == first_ep:
                continue
            endpoint_stats[ep]["delays"].append((tx.timestamp - first_tx.timestamp) * 1000.0)
            endpoint_stats[ep]["total"] += 1

    # pick fastest by first-detection rate
    for ep, st in endpoint_stats.items():
        if st["total"] > 0:
            rate = st["first"] / st["total"]
            if rate > highest_rate:
                highest_rate = rate
                fastest_endpoint = ep

    print("\nDetailed test results")
    print("--------------------------------------------")
    if fastest_endpoint:
        print(f"\nFastest Endpoint: {fastest_endpoint}")
        st = endpoint_stats[fastest_endpoint]
        pct = (st['first']/st['total']*100.0) if st['total'] else 0.0
        print(f"  First detections: {st['first']} out of {st['total']} valid transactions ({pct:.2f}%)")
        if st["historical"]:
            print(f"  Historical transactions detected: {st['historical']}")

        print("\nDelays relative to fastest endpoint:")
        for ep, st in endpoint_stats.items():
            if ep == fastest_endpoint or not st["delays"]:
                continue
            delays = st["delays"]
            avg = sum(delays)/len(delays)
            med = percentile(delays, 0.5)
            p95 = percentile(delays, 0.95)
            print(f"\nEndpoint: {ep}")
            print(f"  Avg delay: {avg:.2f} ms")
            print(f"  Median delay (p50): {med:.2f} ms")
            print(f"  95th percentile: {p95:.2f} ms")
            print(f"  Min/Max delay: {min(delays):.2f}/{max(delays):.2f} ms")
            print(f"  Valid transactions: {st['total']}")
            if st["historical"]:
                print(f"  Historical transactions detected: {st['historical']}")
    else:
        print("Not enough data")
