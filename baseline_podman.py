import concurrent.futures
import csv
import itertools
import os
import subprocess
import sys
import time
import urllib.request

import psutil

IMAGE_NAME = "zeroidle-container"
PORTS = itertools.count(9100)
RESULTS = os.path.join(os.getcwd(), "results")
WARM_PORT = 9090

def container_rss_mb():
    total = 0
    for proc in psutil.process_iter(["name", "memory_info"]):
        if proc.info["name"] == "server.elf":
            try:
                total += proc.info["memory_info"].rss
            except Exception:
                pass
    return total / (1024 * 1024)

def http_ok(port, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/" % port, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.02)
    return False

def cold_request(req_id):
    port = next(PORTS)
    t0 = time.monotonic()
    proc = subprocess.Popen(
        ["podman", "run", "--rm", "-d", "-p", "%d:8080" % port, IMAGE_NAME],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    cid = proc.stdout.read().strip()
    proc.wait()
    ok = http_ok(port, 15.0)
    e2e = (time.monotonic() - t0) * 1000
    subprocess.run(["podman", "rm", "-f", cid],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return [req_id, int(t0 * 1000), round(e2e, 2), round(container_rss_mb(), 2), "ok" if ok else "timeout"]

def warm_request(req_id):
    t0 = time.monotonic()
    ok = http_ok(WARM_PORT, 5.0)
    e2e = (time.monotonic() - t0) * 1000
    return [req_id, int(t0 * 1000), round(e2e, 2), round(container_rss_mb(), 2), "ok" if ok else "timeout"]

def main():
    mode = sys.argv[1]
    count = int(sys.argv[2])
    path = os.path.join(RESULTS, "arm_podman_%s.csv" % mode)
    warm_cid = None
    if mode == "warm":
        proc = subprocess.Popen(
            ["podman", "run", "--rm", "-d", "-p", "%d:8080" % WARM_PORT, IMAGE_NAME],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        warm_cid = proc.stdout.read().strip()
        proc.wait()
        http_ok(WARM_PORT, 15.0)
    worker = cold_request if mode == "cold" else warm_request
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
        rows = list(pool.map(worker, range(count)))
    if warm_cid:
        subprocess.run(["podman", "rm", "-f", warm_cid],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rows.sort(key=lambda r: r[0])
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["req_id", "t_epoch_ms", "e2e_ms", "rss_mb", "status"])
        writer.writerows(rows)
    print("wrote", path)

if __name__ == "__main__":
    main()
