import asyncio
import csv
import itertools
import os
import signal
import sys
import time

import psutil
from aiohttp import web, ClientSession

IMAGE = os.path.expanduser("~/.ops/images/server")
PORTS = itertools.count(9000)
RESULTS = os.path.join(os.getcwd(), "results")
L_MIN = int(sys.argv[sys.argv.index("--lmin") + 1]) if "--lmin" in sys.argv else 1
L_MAX = 16
PSI_INTERVAL = 0.5
SAMPLE_INTERVAL = 0.1
MEM_HIGH = 10.0
CPU_HIGH = 25.0
MEM_LOW = 1.0
CPU_LOW = 5.0
BOOT_TIMEOUT = 15.0
RAPL_PATH = "/sys/class/powercap/intel-rapl:0/energy_uj"

def read_psi(kind):
    with open("/proc/pressure/" + kind) as f:
        for line in f:
            if line.startswith("some"):
                for token in line.split():
                    if token.startswith("avg10="):
                        return float(token.split("=")[1])
    return 0.0

def read_energy():
    try:
        with open(RAPL_PATH) as f:
            return int(f.read().strip())
    except OSError:
        return -1

def vm_rss_mb():
    total = 0
    for proc in psutil.process_iter(["name", "memory_info"]):
        if proc.info["name"] and proc.info["name"].startswith("qemu-system"):
            try:
                total += proc.info["memory_info"].rss
            except Exception:
                pass
    return total / (1024 * 1024)

class AdmissionController:
    def __init__(self, limit):
        self.limit = limit
        self.active = 0
        self.waiting = 0
        self.condition = asyncio.Condition()

    async def acquire(self):
        async with self.condition:
            if self.active >= self.limit:
                self.waiting += 1
                while self.active >= self.limit:
                    await self.condition.wait()
                self.waiting -= 1
            self.active += 1
            return self.limit, self.waiting

    async def release(self):
        async with self.condition:
            self.active -= 1
            self.condition.notify_all()

    async def monitor(self):
        while True:
            await asyncio.sleep(PSI_INTERVAL)
            mem = read_psi("memory")
            cpu = read_psi("cpu")
            async with self.condition:
                if mem > MEM_HIGH or cpu > CPU_HIGH:
                    self.limit = max(L_MIN, self.limit - 2)
                elif mem < MEM_LOW and cpu < CPU_LOW:
                    self.limit = min(L_MAX, self.limit + 1)
                self.condition.notify_all()

CONTROLLER = AdmissionController(8)

class Telemetry:
    def __init__(self, tag):
        os.makedirs(RESULTS, exist_ok=True)
        self.req_file = open(os.path.join(RESULTS, tag + "_req.csv"), "w", newline="")
        self.tel_file = open(os.path.join(RESULTS, tag + "_telemetry.csv"), "w", newline="")
        self.req_writer = csv.writer(self.req_file)
        self.tel_writer = csv.writer(self.tel_file)
        self.req_writer.writerow(["req_id", "t_epoch_ms", "wait_ms", "ready_ms", "proxy_ms", "limit", "queue_depth", "status"])
        self.tel_writer.writerow(["t_epoch_ms", "vm_rss_mb", "host_avail_mb", "psi_mem", "psi_cpu", "energy_uj", "limit", "active", "waiting"])
        self.req_id = 0

    def log_req(self, wait_ms, ready_ms, proxy_ms, limit, queue_depth, status):
        self.req_id += 1
        self.req_writer.writerow([self.req_id, int(time.time() * 1000), round(wait_ms, 2), round(ready_ms, 2), round(proxy_ms, 2), limit, queue_depth, status])
        self.req_file.flush()

    async def sampler(self):
        while True:
            row = [
                int(time.time() * 1000),
                round(vm_rss_mb(), 2),
                round(psutil.virtual_memory().available / (1024 * 1024), 2),
                read_psi("memory"),
                read_psi("cpu"),
                read_energy(),
                CONTROLLER.limit,
                CONTROLLER.active,
                CONTROLLER.waiting,
            ]
            self.tel_writer.writerow(row)
            self.tel_file.flush()
            await asyncio.sleep(SAMPLE_INTERVAL)

    def close(self):
        self.req_file.close()
        self.tel_file.close()

TELEMETRY = None

def qemu_args(port):
    mac = "52:54:00:00:%02x:%02x" % ((port >> 8) & 255, port & 255)
    return [
        "qemu-system-x86_64",
        "-machine", "q35",
        "-device", "pcie-root-port,port=0x10,chassis=1,id=pci.1,bus=pcie.0,multifunction=on,addr=0x3",
        "-device", "pcie-root-port,port=0x11,chassis=2,id=pci.2,bus=pcie.0,addr=0x3.0x6",
        "-device", "pcie-root-port,port=0x12,chassis=3,id=pci.4,bus=pcie.0,addr=0x3.0x4",
        "-device", "virtio-scsi-pci,bus=pci.2,addr=0x0,id=scsi0",
        "-device", "scsi-hd,bus=scsi0.0,drive=hd0",
        "-vga", "none",
        "-smp", "1",
        "-m", "64M",
        "-device", "virtio-rng-pci",
        "-machine", "accel=kvm:tcg",
        "-cpu", "host",
        "-drive", "file=" + IMAGE + ",format=raw,if=none,id=hd0",
        "-device", "virtio-net,bus=pci.4,addr=0x0,netdev=n0,mac=" + mac,
        "-netdev", "user,id=n0,hostfwd=tcp::%d-:8080" % port,
        "-display", "none",
        "-serial", "stdio",
        "-snapshot",
    ]

async def stop_process(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        await proc.wait()

async def wait_ready(proc, timeout):
    try:
        await asyncio.wait_for(proc.stdout.readuntil(b"READY"), timeout)
        return True
    except (asyncio.IncompleteReadError, asyncio.TimeoutError, asyncio.LimitOverrunError):
        return False

async def handle(request):
    t0 = time.monotonic()
    limit, queue_depth = await CONTROLLER.acquire()
    t1 = time.monotonic()
    port = next(PORTS)
    proc = await asyncio.create_subprocess_exec(
        *qemu_args(port),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        start_new_session=True,
    )
    status = "ok"
    ready_ms = -1.0
    proxy_ms = -1.0
    body = b""
    http_status = 503
    try:
        ready = await wait_ready(proc, BOOT_TIMEOUT)
        if not ready:
            status = "boot_timeout"
        else:
            t2 = time.monotonic()
            ready_ms = (t2 - t1) * 1000
            try:
                async with ClientSession() as session:
                    async with session.get("http://127.0.0.1:%d%s" % (port, request.path)) as resp:
                        body = await resp.read()
                        http_status = resp.status
                proxy_ms = (time.monotonic() - t2) * 1000
                if http_status != 200:
                    status = "http_%d" % http_status
            except Exception:
                status = "proxy_fail"
    finally:
        await stop_process(proc)
        await CONTROLLER.release()
        TELEMETRY.log_req((t1 - t0) * 1000, ready_ms, proxy_ms, limit, queue_depth, status)
    return web.Response(status=http_status, body=body, content_type="application/json")

async def init_app():
    global TELEMETRY
    uncontrolled = "--uncontrolled" in sys.argv
    tag = "uncontrolled" if uncontrolled else "controlled"
    if "--tag" in sys.argv:
        tag = sys.argv[sys.argv.index("--tag") + 1]
    if uncontrolled:
        CONTROLLER.limit = 9999
    else:
        asyncio.create_task(CONTROLLER.monitor())
    TELEMETRY = Telemetry(tag)
    asyncio.create_task(TELEMETRY.sampler())
    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handle)
    return app

if __name__ == "__main__":
    web.run_app(init_app(), host="127.0.0.1", port=8000)
