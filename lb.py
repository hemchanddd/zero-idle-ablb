import asyncio
import itertools
import os
import signal
import sys
import time

from aiohttp import web, ClientSession

IMAGE = os.path.expanduser("~/.ops/images/server")
PORTS = itertools.count(9000)
L_MIN = 1
L_MAX = 16
PSI_INTERVAL = 0.5
MEM_HIGH = 10.0
CPU_HIGH = 25.0
MEM_LOW = 1.0
CPU_LOW = 5.0
BOOT_TIMEOUT = 15.0

def read_psi(kind):
    with open("/proc/pressure/" + kind) as f:
        for line in f:
            if line.startswith("some"):
                for token in line.split():
                    if token.startswith("avg10="):
                        return float(token.split("=")[1])
    return 0.0

class AdmissionController:
    def __init__(self, limit):
        self.limit = limit
        self.active = 0
        self.condition = asyncio.Condition()

    async def acquire(self):
        async with self.condition:
            while self.active >= self.limit:
                await self.condition.wait()
            self.active += 1
            return self.limit

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
    granted = await CONTROLLER.acquire()
    t1 = time.monotonic()
    port = next(PORTS)
    proc = await asyncio.create_subprocess_exec(
        *qemu_args(port),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        ready = await wait_ready(proc, BOOT_TIMEOUT)
        if not ready:
            return web.Response(status=504, text="boot timeout")
        t2 = time.monotonic()
        try:
            async with ClientSession() as session:
                async with session.get("http://127.0.0.1:%d%s" % (port, request.path)) as resp:
                    body = await resp.read()
                    status = resp.status
        except Exception:
            return web.Response(status=502, text="proxy failure")
        t3 = time.monotonic()
        print("served port=%d wait=%.1f ready=%.1f proxy=%.1f limit=%d" % (
            port, (t1 - t0) * 1000, (t2 - t1) * 1000, (t3 - t2) * 1000, granted), flush=True)
        return web.Response(status=status, body=body, content_type="application/json")
    finally:
        await stop_process(proc)
        await CONTROLLER.release()

async def init_app():
    if "--uncontrolled" in sys.argv:
        CONTROLLER.limit = 9999
        print("Running in UNCONTROLLED mode (limit=9999, monitor disabled)", flush=True)
    else:
        asyncio.create_task(CONTROLLER.monitor())
        print("Running in CONTROLLED mode (PSI monitor active)", flush=True)
    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handle)
    return app

if __name__ == "__main__":
    web.run_app(init_app(), host="127.0.0.1", port=8000)
