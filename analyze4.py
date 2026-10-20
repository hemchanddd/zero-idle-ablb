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

def secs(df):
    return (df["t_epoch_ms"] - df["t_epoch_ms"].iloc[0]) / 1000.0

def main():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    s = load("smoke_telemetry.csv")
    axes[0].plot(secs(s), s["vm_rss_mb"], color="tab:blue", marker=".")
    axes[0].set_xlim(8, 16)
    axes[0].set_xlabel("time (s)")
    axes[0].set_ylabel("VM RSS (MB)")
    axes[0].set_title("burst drain window")
    for tag, color in [("sustained_unik_ctrl_p2", "tab:blue"), ("sustained_unik_unctrl_p2", "tab:red")]:
        t = load(tag + "_telemetry.csv")
        axes[1].plot(secs(t), t["vm_rss_mb"], color=color, label=tag.split("_")[2])
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("VM RSS (MB)")
    axes[1].legend(fontsize=8)
    axes[1].set_title("sustained pressure, swap-backed")
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
    t = load("sustained_unik_ctrl_p2_telemetry.csv")
    axes[1].plot(secs(t), t["waiting"], color="tab:blue", label="queued requests")
    ax2 = axes[1].twinx()
    ax2.plot(secs(t), t["limit"], color="tab:green", linestyle="--", label="admission limit")
    ax2.set_ylabel("limit")
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("queue depth")
    axes[1].set_title("sustained engagement")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_queue_limit.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    tags = ["sustained_unik_ctrl", "sustained_unik_unctrl",
            "sustained_unik_ctrl_stress", "sustained_unik_unctrl_stress",
            "sustained_unik_ctrl_p2", "sustained_unik_unctrl_p2"]
    labels = ["ctrl", "unctrl", "ctrl transient", "unctrl transient", "ctrl swap", "unctrl swap"]
    jpr = []
    for tag in tags:
        t = load(tag + "_telemetry.csv")
        e = t["energy_uj"].to_numpy(dtype=float)
        e = e[e >= 0]
        req = load(tag + "_req.csv")
        ok = len(req[req["status"] == "ok"])
        jpr.append((e[-1] - e[0]) / 1e6 / ok if len(e) >= 2 and ok > 0 else float("nan"))
    bars = ax.bar(labels, jpr, color=["tab:blue", "tab:red"] * 3)
    ax.bar_label(bars, fmt="%.2f")
    ax.set_ylabel("joules per request")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_energy.png"), dpi=200)
    plt.close(fig)

    pairs = [
        ("healthy 20 rps e2e", "sustained_unik_ctrl_r20.csv", "sustained_unik_unctrl_r20.csv", "e2e_ms"),
        ("healthy 40 rps e2e", "sustained_unik_ctrl_r40.csv", "sustained_unik_unctrl_r40.csv", "e2e_ms"),
        ("swap pressure 10 rps e2e", "sustained_unik_ctrl_p2_r10.csv", "sustained_unik_unctrl_p2_r10.csv", "e2e_ms"),
        ("swap pressure 10 rps ready", "sustained_unik_ctrl_p2_req.csv", "sustained_unik_unctrl_p2_req.csv", "ready_ms"),
        ("burst stress ready", "arm_burst_ctrl_stress.csv", "arm_burst_unctrl_stress.csv", "ready_ms"),
    ]
    with open(os.path.join(TAB, "stats_tests.csv"), "w") as f:
        f.write("comparison,n_a,n_b,median_a,median_b,U,p_value\n")
        for name, fa, fb, col in pairs:
            a = load(fa)[col].to_numpy(dtype=float)
            b = load(fb)[col].to_numpy(dtype=float)
            a = a[a > 0]
            b = b[b > 0]
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            f.write("%s,%d,%d,%.2f,%.2f,%.1f,%.6g\n" % (name, len(a), len(b), np.median(a), np.median(b), u, p))
    print("analysis4 complete")

if __name__ == "__main__":
    main()
