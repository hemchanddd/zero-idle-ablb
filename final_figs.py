import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIG = "/home/hemchand/zero-idle-research/figures"

plt.rcParams.update({"font.size": 9, "savefig.dpi": 200})

def box(ax, x, y, w, h, text, fc="#dbeafe"):
    ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="black", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8)

def arrow(ax, x1, y1, x2, y2, text=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", lw=0.9))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, text, fontsize=7, ha="center")

def fig1():
    fig, ax = plt.subplots(figsize=(9, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    ax.axis("off")
    names = ["request\narrives", "admission\nslot", "spawn\nQEMU", "guest\nboot",
             "serial\nREADY", "proxy\nHTTP", "teardown\nRAM = 0"]
    for i, n in enumerate(names):
        box(ax, 0.15 + i * 1.4, 0.9, 1.2, 0.6, n)
        if i:
            arrow(ax, 0.15 + (i - 1) * 1.4 + 1.2, 1.2, 0.15 + i * 1.4, 1.2)
    ax.text(5, 0.35, "zero resident memory between requests", ha="center", fontsize=8, style="italic")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_lifecycle.png"))
    plt.close(fig)

def fig2():
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.set_xlim(0, 6.2)
    ax.set_ylim(0, 3)
    ax.axis("off")
    box(ax, 0.5, 0.4, 5, 2.2, "", fc="#f5f5f5")
    ax.text(3, 2.35, "KVM microVM (64 MB, 1 vCPU)", ha="center", fontsize=9)
    box(ax, 0.9, 1.5, 2.0, 0.6, "Nanos kernel")
    box(ax, 3.1, 1.5, 2.0, 0.6, "static ELF\nHTTP server")
    box(ax, 0.9, 0.7, 2.0, 0.6, "virtio-net\n(SLIRP fwd)")
    box(ax, 3.1, 0.7, 2.0, 0.6, "serial console")
    arrow(ax, 5.1, 1.0, 6.0, 1.0, "READY")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_unikernel_anatomy.png"))
    plt.close(fig)

def fig3():
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    for x, name in [(1.5, "load balancer"), (5, "QEMU SLIRP"), (8.5, "guest")]:
        ax.text(x, 5.6, name, ha="center", fontsize=9)
        ax.plot([x, x], [0.4, 5.4], lw=0.7, color="gray")
    arrow(ax, 1.5, 5.0, 5, 5.0, "spawn")
    arrow(ax, 5, 4.5, 1.5, 4.5, "host port accepts at 42 ms: FALSE ready")
    arrow(ax, 1.5, 3.9, 8.5, 3.9, "early connect: guest-side SYN lost")
    arrow(ax, 8.5, 3.1, 1.5, 3.1, "serial READY at 131 ms: TRUE")
    arrow(ax, 1.5, 2.3, 8.5, 2.3, "HTTP GET")
    arrow(ax, 8.5, 1.6, 1.5, 1.6, "200 OK in 1-2 ms")
    arrow(ax, 1.5, 0.9, 5, 0.9, "SIGTERM to process group")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_readiness_sequence.png"))
    plt.close(fig)

def fig4():
    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.4)
    ax.axis("off")
    box(ax, 0.4, 0.9, 2.4, 0.7, "HEALTHY\nlimit +1 per 0.5 s")
    box(ax, 3.8, 0.9, 2.4, 0.7, "THROTTLE\nlimit -2 per 0.5 s")
    box(ax, 7.2, 0.9, 2.4, 0.7, "FLOOR L_min\nqueue and shed")
    arrow(ax, 2.8, 1.4, 3.8, 1.4, "psi_mem > 10 or psi_cpu > 25")
    arrow(ax, 3.8, 1.0, 2.8, 1.0, "psi_mem < 1 and psi_cpu < 5")
    arrow(ax, 6.2, 1.4, 7.2, 1.4, "limit reaches floor")
    arrow(ax, 7.2, 1.0, 6.2, 1.0, "pressure clears")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_controller_states.png"))
    plt.close(fig)

def fig5():
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    box(ax, 0.3, 1.6, 1.8, 0.8, "Poisson driver\n(open loop)")
    box(ax, 3.0, 1.6, 2.0, 0.8, "asyncio control plane\nadmission controller")
    box(ax, 6.0, 2.7, 1.7, 0.6, "QEMU + Nanos")
    box(ax, 6.0, 1.7, 1.7, 0.6, "Firecracker")
    box(ax, 6.0, 0.7, 1.7, 0.6, "Podman OCI")
    box(ax, 3.0, 0.2, 2.0, 0.6, "telemetry 10 Hz\nRSS, PSI, RAPL")
    arrow(ax, 2.1, 2.0, 3.0, 2.0)
    arrow(ax, 5.0, 2.2, 6.0, 3.0)
    arrow(ax, 5.0, 2.0, 6.0, 2.0)
    arrow(ax, 5.0, 1.8, 6.0, 1.0)
    arrow(ax, 4.0, 0.8, 4.0, 1.6)
    ax.text(8.1, 2.0, "guest serial READY\nplus HTTP exchange", fontsize=8, va="center")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_testbed_topology.png"))
    plt.close(fig)

def fig12():
    floors = [1, 2, 3]
    good = [44.8, 74.9, 97.9]
    shed = [55.2, 25.1, 2.1]
    ready = [151.04, 202.38, 244.40]
    e2e = [5387.15, 2746.77, 541.05]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    x = np.arange(3)
    b1 = axes[0].bar(x - 0.2, good, 0.4, label="goodput", color="tab:blue")
    b2 = axes[0].bar(x + 0.2, shed, 0.4, label="shed", color="tab:red")
    axes[0].bar_label(b1, fmt="%.1f", fontsize=7)
    axes[0].bar_label(b2, fmt="%.1f", fontsize=7)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(["floor 1", "floor 2", "floor 3"])
    axes[0].set_ylabel("percent of arrivals")
    axes[0].legend(fontsize=8)
    axes[1].plot(floors, ready, marker="o", color="tab:orange", label="p50 guest ready")
    axes[1].plot(floors, e2e, marker="s", color="tab:blue", label="p50 end-to-end")
    axes[1].axhline(338.98, ls="--", color="tab:orange", lw=0.8)
    axes[1].axhline(366.28, ls="--", color="tab:blue", lw=0.8)
    axes[1].set_yscale("log")
    axes[1].set_xticks(floors)
    axes[1].set_xticklabels(["floor 1", "floor 2", "floor 3"])
    axes[1].set_ylabel("milliseconds (log)")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig12_floor_sensitivity.png"))
    plt.close(fig)

def main():
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig12()
    extra = [
        "Figure 1. Active-boot request lifecycle: seven stages from arrival to teardown, with aggregate guest memory returning to zero after every response.",
        "Figure 2. Unikernel guest anatomy: Nanos kernel and static ELF HTTP server inside a 64 MB KVM microVM, with readiness signalled over the serial console rather than the network stack.",
        "Figure 3. Readiness signalling sequence: host-side SLIRP acceptance at 42 ms is a false signal whose early connect loses its guest-side SYN, while the serial READY byte at 131 ms is the ground truth used by the control plane.",
        "Figure 4. Admission controller state machine: healthy growth of one slot per 0.5 s, throttle decrements of two slots per 0.5 s above PSI thresholds, and a floor state where queueing and shedding bound host contention.",
        "Figure 5. Five-arm testbed topology: one Poisson driver feeds the asyncio control plane, which launches QEMU/Nanos, Firecracker, or Podman guests while 10 Hz telemetry samples RSS, PSI, and RAPL.",
        "Figure 12. Admission floor sensitivity under swap-backed pressure at 10 rps: goodput rises 44.8, 74.9, 97.9 percent and shed falls 55.2, 25.1, 2.1 percent across floors one to three, while p50 guest ready softens from 151.04 to 244.40 ms against the uncontrolled references of 338.98 ms ready and 366.28 ms end-to-end (dashed lines).",
    ]
    with open(os.path.join(FIG, "captions.txt"), "a") as f:
        f.write("\n\n" + "\n\n".join(extra) + "\n")
    print("conceptual figures complete")

if __name__ == "__main__":
    main()
