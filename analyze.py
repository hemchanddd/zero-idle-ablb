import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

RESULTS = "/home/hemchand/zero-idle-research/results"
FIG = "/home/hemchand/zero-idle-research/figures"
TAB = "/home/hemchand/zero-idle-research/tables"

SUSTAINED = {
    "unikernel controlled 20 rps": ("sustained_unik_ctrl_r20.csv", "e2e_ms"),
    "unikernel controlled 40 rps": ("sustained_unik_ctrl_r40.csv", "e2e_ms"),
    "unikernel uncontrolled 20 rps": ("sustained_unik_unctrl_r20.csv", "e2e_ms"),
    "unikernel uncontrolled 40 rps": ("sustained_unik_unctrl_r40.csv", "e2e_ms"),
    "container warm 20 rps": ("sustained_warm_warm_r20.csv", "e2e_ms"),
    "container warm 40 rps": ("sustained_warm_warm_r40.csv", "e2e_ms"),
    "container cold 10 rps": ("sustained_pcold_pcold_r10.csv", "e2e_ms"),
    "firecracker burst 10": ("arm_firecracker.csv", "e2e_ms"),
    "burst controlled stress": ("arm_burst_ctrl_stress.csv", "ready_ms"),
    "burst uncontrolled stress": ("arm_burst_unctrl_stress.csv", "ready_ms"),
}

def pct(x, q):
    return float(np.percentile(x, q))

def main():
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(TAB, exist_ok=True)
    rows = []
    data = {}
    for label, (fname, col) in SUSTAINED.items():
        df = pd.read_csv(os.path.join(RESULTS, fname))
        x = df[col].to_numpy(dtype=float)
        x = x[x > 0]
        data[label] = x
        rows.append([label, len(x), round(100.0 * len(x) / len(df), 2), round(pct(x, 50), 2),
                     round(pct(x, 95), 2), round(pct(x, 99), 2), round(x.max(), 2),
                     round(x.mean(), 2), round(x.std(), 2)])
    summary = pd.DataFrame(rows, columns=["arm", "n_ok", "ok_pct", "p50", "p95", "p99", "max", "mean", "sd"])
    summary.to_csv(os.path.join(TAB, "stats_summary.csv"), index=False)

    tests = []
    pairs = [
        ("controlled vs uncontrolled 20 rps", "unikernel controlled 20 rps", "unikernel uncontrolled 20 rps"),
        ("controlled vs uncontrolled 40 rps", "unikernel controlled 40 rps", "unikernel uncontrolled 40 rps"),
        ("burst stress controlled vs uncontrolled", "burst controlled stress", "burst uncontrolled stress"),
    ]
    for name, a, b in pairs:
        u, p = stats.mannwhitneyu(data[a], data[b], alternative="two-sided")
        tests.append([name, len(data[a]), len(data[b]), round(float(u), 1), float(p)])
    tdf = pd.DataFrame(tests, columns=["comparison", "n_a", "n_b", "U", "p_value"])
    tdf.to_csv(os.path.join(TAB, "stats_tests.csv"), index=False)

    p2 = pd.read_csv(os.path.join(RESULTS, "phase2_summary.csv"))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    xpos = np.arange(len(p2))
    ax.bar(xpos - 0.2, p2["p50"], 0.4, label="p50")
    ax.bar(xpos + 0.2, p2["p95"], 0.4, label="p95")
    ax.set_xticks(xpos)
    ax.set_xticklabels(p2["config"], rotation=15)
    ax.set_ylabel("boot latency (ms)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_phase2_bars.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label in ["unikernel controlled 20 rps", "unikernel uncontrolled 20 rps",
                  "container warm 20 rps", "container cold 10 rps"]:
        x = np.sort(data[label])
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=label)
    ax.set_xlabel("end-to-end latency (ms)")
    ax.set_ylabel("CDF")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig7_cdf_sustained.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for tag, color in [("sustained_unik_ctrl", "tab:blue"), ("sustained_unik_unctrl", "tab:red")]:
        t = pd.read_csv(os.path.join(RESULTS, tag + "_telemetry.csv"))
        ts = (t["t_epoch_ms"] - t["t_epoch_ms"].iloc[0]) / 1000.0
        ax.plot(ts, t["vm_rss_mb"], color=color, label=tag.split("_")[-1])
    warm = pd.read_csv(os.path.join(RESULTS, "arm_podman_warm.csv"))
    ax.axhline(warm["rss_mb"].mean(), color="tab:orange", linestyle="--", label="warm container resident")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("VM RSS (MB)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_rss_trace.png"), dpi=200)
    plt.close(fig)

    t = pd.read_csv(os.path.join(RESULTS, "sustained_unik_ctrl_telemetry.csv"))
    ts = (t["t_epoch_ms"] - t["t_epoch_ms"].iloc[0]) / 1000.0
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ts, t["waiting"], color="tab:blue", label="queued requests")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("queue depth")
    ax2 = ax.twinx()
    ax2.plot(ts, t["limit"], color="tab:green", linestyle="--", label="admission limit")
    ax2.set_ylabel("limit")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_queue_limit.png"), dpi=200)
    plt.close(fig)

    energy = []
    for tag in ["sustained_unik_ctrl", "sustained_unik_unctrl"]:
        t = pd.read_csv(os.path.join(RESULTS, tag + "_telemetry.csv"))
        e = t["energy_uj"].to_numpy(dtype=float)
        e = e[e >= 0]
        req = pd.read_csv(os.path.join(RESULTS, tag + "_req.csv"))
        joules = (e[-1] - e[0]) / 1e6
        energy.append([tag, round(joules, 2), round(joules / max(1, len(req)), 4)])
    edf = pd.DataFrame(energy, columns=["arm", "total_joules", "joules_per_request"])
    edf.to_csv(os.path.join(TAB, "energy_summary.csv"), index=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(edf["arm"], edf["joules_per_request"], color=["tab:blue", "tab:red"])
    ax.set_ylabel("joules per request")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_energy.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([data["burst controlled stress"], data["burst uncontrolled stress"]])
    ax.set_xticklabels(["controlled", "uncontrolled"])
    ax.set_ylabel("boot latency under stress (ms)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig11_burst_stress.png"), dpi=200)
    plt.close(fig)
    print("analysis complete")

if __name__ == "__main__":
    main()
