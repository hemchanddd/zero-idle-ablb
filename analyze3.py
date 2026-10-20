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

def load(fname):
    return pd.read_csv(os.path.join(RESULTS, fname))

def main():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    s = load("smoke_telemetry.csv")
    ts = (s["t_epoch_ms"] - s["t_epoch_ms"].iloc[0]) / 1000.0
    axes[0].plot(ts, s["vm_rss_mb"], color="tab:blue")
    axes[0].set_xlabel("time (s)")
    axes[0].set_ylabel("VM RSS (MB)")
    axes[0].set_title("burst drain: zero to peak to zero")
    for tag, color in [("sustained_unik_ctrl_stress", "tab:blue"), ("sustained_unik_unctrl_stress", "tab:red")]:
        t = load(tag + "_telemetry.csv")
        tt = (t["t_epoch_ms"] - t["t_epoch_ms"].iloc[0]) / 1000.0
        axes[1].plot(tt, t["vm_rss_mb"], color=color, label=tag.split("_")[-1])
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("VM RSS (MB)")
    axes[1].legend(fontsize=8)
    axes[1].set_title("sustained 10 rps under 6 GB pressure")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_rss_trace.png"), dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ctrl = load("arm_burst_ctrl_stress.csv")
    idx = np.arange(len(ctrl))
    axes[0].step(idx, ctrl["wait_ms"], where="post", label="admission wait")
    axes[0].step(idx, ctrl["ready_ms"], where="post", label="guest boot")
    axes[0].set_xlabel("request index")
    axes[0].set_ylabel("milliseconds")
    axes[0].legend(fontsize=8)
    axes[0].set_title("forty-request burst")
    t = load("sustained_unik_ctrl_stress_telemetry.csv")
    tt = (t["t_epoch_ms"] - t["t_epoch_ms"].iloc[0]) / 1000.0
    axes[1].plot(tt, t["waiting"], color="tab:blue", label="queued requests")
    ax2 = axes[1].twinx()
    ax2.plot(tt, t["limit"], color="tab:green", linestyle="--", label="admission limit")
    ax2.set_ylabel("limit")
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("queue depth")
    axes[1].set_title("controller engagement under pressure")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_queue_limit.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    tags = ["sustained_unik_ctrl", "sustained_unik_unctrl",
            "sustained_unik_ctrl_stress", "sustained_unik_unctrl_stress"]
    labels = ["ctrl healthy", "unctrl healthy", "ctrl pressure", "unctrl pressure"]
    jpr = []
    for tag in tags:
        t = load(tag + "_telemetry.csv")
        e = t["energy_uj"].to_numpy(dtype=float)
        e = e[e >= 0]
        req = load(tag + "_req.csv")
        ok = len(req[req["status"] == "ok"])
        jpr.append((e[-1] - e[0]) / 1e6 / ok if len(e) >= 2 and ok > 0 else float("nan"))
    bars = ax.bar(labels, jpr, color=["tab:blue", "tab:red", "tab:blue", "tab:red"])
    ax.bar_label(bars, fmt="%.3f")
    ax.set_ylabel("joules per request")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_energy.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    styles = [("unikernel controlled 20 rps", "sustained_unik_ctrl_r20.csv", "tab:blue", "-"),
              ("unikernel uncontrolled 20 rps", "sustained_unik_unctrl_r20.csv", "tab:orange", "--"),
              ("container warm 20 rps", "sustained_warm_warm_r20.csv", "tab:green", "-"),
              ("container cold 10 rps", "sustained_pcold_pcold_r10.csv", "tab:red", "-")]
    for label, fname, color, ls in styles:
        x = np.sort(load(fname)["e2e_ms"].to_numpy(dtype=float))
        x = x[x > 0]
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=label, color=color, linestyle=ls)
    ax.set_xscale("log")
    ax.set_xlabel("end-to-end latency (ms, log scale)")
    ax.set_ylabel("CDF")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig7_cdf_sustained.png"), dpi=200)
    plt.close(fig)

    pairs = [
        ("controlled vs uncontrolled 20 rps", "sustained_unik_ctrl_r20.csv", "sustained_unik_unctrl_r20.csv"),
        ("controlled vs uncontrolled 40 rps", "sustained_unik_ctrl_r40.csv", "sustained_unik_unctrl_r40.csv"),
        ("controlled vs uncontrolled 10 rps pressure", "sustained_unik_ctrl_stress_r10.csv", "sustained_unik_unctrl_stress_r10.csv"),
        ("burst stress controlled vs uncontrolled", "arm_burst_ctrl_stress.csv", "arm_burst_unctrl_stress.csv"),
    ]
    with open(os.path.join(TAB, "stats_tests.csv"), "w") as f:
        f.write("comparison,n_a,n_b,median_a,median_b,U,p_value\n")
        for name, fa, fb in pairs:
            ca = "ready_ms" if "burst" in name else "e2e_ms"
            a = load(fa)[ca].to_numpy(dtype=float)
            b = load(fb)[ca].to_numpy(dtype=float)
            a = a[a > 0]
            b = b[b > 0]
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            f.write("%s,%d,%d,%.2f,%.2f,%.1f,%.6g\n" % (name, len(a), len(b), np.median(a), np.median(b), u, p))
    print("analysis3 complete")

if __name__ == "__main__":
    main()
