import subprocess
import time
import sys
import os
import signal
import select
import random
import concurrent.futures

LOG_DIR = "logs"
TIMEOUT = 20.0
IMAGE = os.path.expanduser("~/.ops/images/server")

def mac_for(instance_id):
    return "52:54:00:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        instance_id & 255,
    )

def qemu_args(instance_id):
    return [
        "qemu-system-x86_64",
        "-machine", "q35",
        "-device", "pcie-root-port,port=0x10,chassis=1,id=pci.1,bus=pcie.0,multifunction=on,addr=0x3",
        "-device", "pcie-root-port,port=0x11,chassis=2,id=pci.2,bus=pcie.0,addr=0x3.0x6",
        "-device", "pcie-root-port,port=0x12,chassis=3,id=pci.4,bus=pcie.0,addr=0x3.0x4",
        "-device", "virtio-scsi-pci,bus=pci.2,addr=0x0,id=scsi0",
        "-device", "scsi-hd,bus=scsi0.0,drive=hd0",
        "-vga", "none",
        "-device", "isa-debug-exit",
        "-smp", "1",
        "-m", "64M",
        "-device", "virtio-rng-pci",
        "-device", "virtio-balloon",
        "-machine", "accel=kvm:tcg",
        "-cpu", "host",
        "-cpu", "max",
        "-drive", "file=" + IMAGE + ",format=raw,if=none,id=hd0",
        "-device", "virtio-net,bus=pci.4,addr=0x0,netdev=n0,mac=" + mac_for(instance_id),
        "-netdev", "user,id=n0",
        "-display", "none",
        "-serial", "stdio",
        "-snapshot",
    ]

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

def boot_instance(instance_id):
    log_path = os.path.join(LOG_DIR, f"boot_{instance_id}.log")
    start_time = time.time()
    with open(log_path, "wb") as log_file:
        proc = subprocess.Popen(qemu_args(instance_id), stdout=subprocess.PIPE, stderr=log_file, start_new_session=True)
        buffer = b""
        while time.time() - start_time < TIMEOUT:
            remaining = TIMEOUT - (time.time() - start_time)
            ready, _, _ = select.select([proc.stdout], [], [], min(remaining, 0.5))
            if ready:
                chunk = os.read(proc.stdout.fileno(), 4096)
                if not chunk:
                    break
                buffer += chunk
                if b"READY" in buffer:
                    elapsed = (time.time() - start_time) * 1000
                    stop_process(proc)
                    return instance_id, elapsed
            if proc.poll() is not None:
                break
        stop_process(proc)
        return instance_id, -1

def percentile(sorted_times, pct):
    idx = min(len(sorted_times) - 1, int(round(pct / 100.0 * (len(sorted_times) - 1))))
    return sorted_times[idx]

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"Booting {count} instances concurrently...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(boot_instance, i) for i in range(count)]
        results = [f.result() for f in futures]
    results.sort(key=lambda x: x[0])
    times = sorted(r[1] for r in results if r[1] > 0)
    failed = [r[0] for r in results if r[1] < 0]
    print(f"Successful boots: {len(times)}/{count}")
    if failed:
        print(f"Failed IDs: {failed}")
    if times:
        print(f"Min: {times[0]:.2f} ms")
        print(f"p50: {percentile(times, 50):.2f} ms")
        print(f"p95: {percentile(times, 95):.2f} ms")
        print(f"Max (p100): {times[-1]:.2f} ms")
        print(f"Average: {sum(times)/len(times):.2f} ms")
