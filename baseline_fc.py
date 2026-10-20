import concurrent.futures
import csv
import json
import os
import select
import signal
import subprocess
import sys
import time
import urllib.request

KERNEL = "/home/hemchand/zero-idle-research/hello-vmlinux.bin"
ROOTFS = "/home/hemchand/zero-idle-research/fc-rootfs.ext4"
RESULTS = "/home/hemchand/zero-idle-research/results"

def stop_process(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        proc.wait()

def http_ok(url, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.02)
    return False

def fc_request(req_id):
    octet = 10 + req_id
    tap = "fctap%d" % req_id
    guest_ip = "10.0.%d.2" % octet
    url = "http://%s:8080/" % guest_ip
    subprocess.run(["ip", "tuntap", "add", "dev", tap, "mode", "tap"], check=True)
    subprocess.run(["ip", "addr", "add", "10.0.%d.1/24" % octet, "dev", tap], check=True)
    subprocess.run(["ip", "link", "set", tap, "up"], check=True)
    cfg = {
        "boot-source": {
            "kernel_image_path": KERNEL,
            "boot_args": "console=ttyS0 reboot=k panic=1 pci=off noapic root=/dev/vda rw init=/init guestip=%s" % guest_ip,
        },
        "drives": [{
            "drive_id": "rootfs",
            "path_on_host": ROOTFS,
            "is_root_device": True,
            "is_read_only": False,
        }],
        "machine-config": {"vcpu_count": 1, "mem_size_mib": 64, "smt": False},
        "network-interfaces": [{
            "iface_id": "eth0",
            "host_dev_name": tap,
            "guest_mac": "AA:FC:00:00:%02x:%02x" % ((octet >> 8) & 255, octet & 255),
        }],
    }
    cfg_path = "/tmp/fc_%d.json" % req_id
    with open(cfg_path, "w") as f:
        json.dump(cfg, f)
    t0 = time.monotonic()
    sock_path = "/tmp/fc_%d.sock" % req_id
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    proc = subprocess.Popen(
        ["firecracker", "--api-sock", "/tmp/fc_%d.sock" % req_id, "--config-file", cfg_path],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
    ready_ms = -1.0
    e2e_ms = -1.0
    status = "timeout"
    buf = b""
    deadline = t0 + 15.0
    ready = False
    while time.monotonic() < deadline:
        r, _, _ = select.select([proc.stdout], [], [], 0.5)
        if r:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk:
                break
            buf += chunk
            if b"READY" in buf:
                ready = True
                break
        if proc.poll() is not None:
            break
    if ready:
        ready_ms = (time.monotonic() - t0) * 1000
        if http_ok(url, 5.0):
            e2e_ms = (time.monotonic() - t0) * 1000
            status = "ok"
        else:
            status = "http_fail"
    stop_process(proc)
    subprocess.run(["ip", "link", "del", tap], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return [req_id, int(t0 * 1000), round(ready_ms, 2), round(e2e_ms, 2), status]

def main():
    count = int(sys.argv[1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
        rows = list(pool.map(fc_request, range(count)))
    rows.sort(key=lambda r: r[0])
    path = os.path.join(RESULTS, "arm_firecracker.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["req_id", "t_epoch_ms", "ready_ms", "e2e_ms", "status"])
        writer.writerows(rows)
    print("wrote", path)

if __name__ == "__main__":
    main()

