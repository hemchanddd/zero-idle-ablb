import csv
import os
import random
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

import baseline_fc
import baseline_podman

RESULTS = "/home/hemchand/zero-idle-research/results"
CAPS = {"unik": 24, "warm": 128, "pcold": 6, "fc": 6}

def http_get(url, timeout=20):
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read()
            return (time.monotonic() - t0) * 1000, "ok"
    except urllib.error.HTTPError as e:
        return (time.monotonic() - t0) * 1000, "http_%d" % e.code

def arm_unik(req_id):
    return http_get("http://127.0.0.1:8000/")

def arm_warm(req_id):
    return http_get("http://127.0.0.1:9090/")

def arm_podman_cold(req_id):
    row = baseline_podman.cold_request(req_id)
    return row[2], row[4]

def arm_fc(req_id):
    row = baseline_fc.fc_request(req_id)
    return row[3], row[4]

ARMS = {
    "unik": arm_unik,
    "warm": arm_warm,
    "pcold": arm_podman_cold,
    "fc": arm_fc,
}

def main():
    arm = sys.argv[1]
    rate = float(sys.argv[2])
    duration = float(sys.argv[3])
    tag = sys.argv[4]
    cap = CAPS[arm]
    warm_cid = None
    if arm == "warm":
        proc = subprocess.Popen(
            ["podman", "run", "--rm", "-d", "-p", "9090:8080", "zeroidle-container"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        warm_cid = proc.stdout.read().strip()
        proc.wait()
        baseline_podman.http_ok(9090, 15.0)
    rows = []
    lock = threading.Lock()
    counter = [0]
    active = [0]
    stop_at = time.monotonic() + duration
    next_arrival = time.monotonic()

    def worker(req_id):
        try:
            e2e, status = ARMS[arm](req_id)
        except Exception:
            e2e, status = -1.0, "exception"
        with lock:
            active[0] -= 1
            rows.append([req_id, int(time.time() * 1000), round(e2e, 2), status])

    threads = []
    while time.monotonic() < stop_at:
        next_arrival += random.expovariate(rate)
        delay = next_arrival - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        with lock:
            req_id = counter[0]
            counter[0] += 1
            if active[0] >= cap:
                rows.append([req_id, int(time.time() * 1000), -1.0, "shed"])
                continue
            active[0] += 1
        t = threading.Thread(target=worker, args=(req_id,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    if warm_cid:
        subprocess.run(["podman", "rm", "-f", warm_cid],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rows.sort(key=lambda r: r[0])
    path = os.path.join(RESULTS, "sustained_%s_%s.csv" % (arm, tag))
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["req_id", "t_epoch_ms", "e2e_ms", "status"])
        writer.writerows(rows)
    ok_count = len([r for r in rows if r[3] == "ok"])
    shed = len([r for r in rows if r[3] == "shed"])
    print("wrote", path, "requests", len(rows), "ok", ok_count, "shed", shed)

if __name__ == "__main__":
    main()
