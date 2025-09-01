#!/usr/bin/env python3

import argparse
import json
import sys
import time
import urllib.request
import matplotlib.pyplot as plt

RED = "\033[31m"
RESET = "\033[0m"


def to_int(hex_qty):
    return int(hex_qty, 16) if hex_qty else None

def rpc_call(url, methods, params=[None], timeout=10):
    assert len(methods) == len(params)

    payload = []

    for i in range(len(methods)):
        method = methods[i]
        _params = params[i]
        if _params is None:
            _params = []
        _payload = {"jsonrpc": "2.0", "id": i, "method": method, "params": _params}
        payload.append(_payload)

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.loads(resp.read().decode())
    if "error" in out:
        raise RuntimeError(out["error"])
    
    blocks = []
    for block in out:
        if "error" in block:
            raise RuntimeError(block["error"])

        blocks.append(to_int(block.get("result").get("number")) if block and block.get("result") else None)

    return blocks


def get_block_numbers(url):
    methods = ["eth_getBlockByNumber", "eth_getBlockByNumber", "eth_getBlockByNumber"]
    params = [["latest", False], ["safe", False], ["finalized", False]]
    return rpc_call(url, methods, params)

def print_header():
    header = (
        f"{'TIME':<19} | {'AGE':>6} | "
        f"{'FINALIZED':>10} | {'F_CHANGE':>8} | "
        f"{'SAFE':>10} | {'S_CHANGE':>8} | "
        f"{'LATEST':>10} | {'L_CHANGE':>8} | "
        f"Δsafe | Δfinal"
    )
    print(header)
    print("-" * len(header))

def main():
    ap = argparse.ArgumentParser(description="ASCII table of Base L2 heads with deltas and AGE")
    ap.add_argument("--rpc-url", help="Base RPC URL")
    ap.add_argument("--interval", type=float, default=2.0, help="Polling interval (sec)")
    ap.add_argument("--header-freq", type=int, default=50, help="Number of rows between header prints")
    ap.add_argument("--plot-file", default="base_heads_plot.png", help="Output image file for the plot")
    args = ap.parse_args()

    start_time = time.time()
    prev_finalized = None
    prev_safe = None
    prev_latest = None
    row_count = 0

    # store values for plotting
    latest_list = []
    safe_list = []
    finalized_list = []

    print_header()

    try:
        while True:
            now = time.time()
            age = int(now - start_time)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")

            (latest, safe, finalized) = get_block_numbers(args.rpc_url)

            latest_list.append(latest)
            safe_list.append(safe)
            finalized_list.append(finalized)

            # change from previous
            f_change = finalized - prev_finalized if (finalized is not None and prev_finalized is not None) else None
            s_change = safe - prev_safe if (safe is not None and prev_safe is not None) else None
            l_change = latest - prev_latest if (latest is not None and prev_latest is not None) else None

            lag_safe = latest - safe if (latest and safe) else None
            lag_final = latest - finalized if (latest and finalized) else None

            row = (
                f"{ts:<19} | {age:>6} | "
                f"{finalized:>10} | {f_change if f_change is not None else '—':>8} | "
                f"{safe:>10} | {s_change if s_change is not None else '—':>8} | "
                f"{latest:>10} | {l_change if l_change is not None else '—':>8} | "
                f"{lag_safe if lag_safe is not None else '—':>5} | "
                f"{lag_final if lag_final is not None else '—':>6}"
            )

            # highlight row in red + stop if any change < 0
            if any(c is not None and c < 0 for c in (f_change, s_change, l_change, lag_safe, lag_final)):
                print(RED + row + RESET)
                raise KeyboardInterrupt
            else:
                print(row)

            sys.stdout.flush()

            prev_finalized = finalized
            prev_safe = safe
            prev_latest = latest

            row_count += 1
            if row_count % args.header_freq == 0:
                print_header()
                row_count = 0

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nBye. Generating plot...")

        plt.figure(figsize=(10, 6))
        plt.plot(latest_list, label="latest block", color="red")
        plt.plot(safe_list, label="safe block", color="blue")
        plt.plot(finalized_list, label="final block", color="green")
        plt.xlabel(f"Sample ({int(args.interval)}s interval)")
        plt.ylabel("Block Number")
        plt.title("Base L2 Sync: Unsafe / Safe / Final Blocks")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(args.plot_file)
        print(f"Plot saved to {args.plot_file}")

if __name__ == "__main__":
    main()
