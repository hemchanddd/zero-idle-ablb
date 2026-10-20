import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS = "/home/hemchand/zero-idle-research/results"
FIG = "/home/hemchand/zero-idle-research/figures"

plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
                     "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
                     "savefig.dpi": 200})

def load(f):
    return pd.read_csv(os.path.join(RESULTS, f))

def main():
    p2 = load("phase2_summary.csv")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(p2))
    b1 = ax.bar(x - 0.2, p2["p50"], 0.4, label="p50", color="tab:blue")
    b2 = ax.bar(x + 0.2, p2["p95"], 0.4, label="p95", color="tab:orange")
    ax.bar_label(b1, fmt="%.2f", fontsize=6.5, rotation=90, padding=1)
    ax.bar_label(b2, fmt="%.2f", fontsize=6.5, rotation=90, padding=1)
    ax.set_xticks(x)
    ax.set_xticklabels(p2["config"], rotation=12, ha="right")
    ax.set_ylabel("guest boot latency (ms)")
    ax.set_ylim(0, p2[["p50", "p95"]].max().max() * 1.25)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_phase2_bars.png"))
    plt.close(fig)

    tags = ["sustained_unik_ctrl", "sustained_unik_unctrl",
            "sustained_unik_ctrl_stress", "sustained_unik_unctrl_stress"]
    labels = ["ctrl healthy", "unctrl healthy", "ctrl transient", "unctrl transient"]
    meds, errs = [], []
    for tag in tags:
        t = load(tag + "_telemetry.csv")
        t = t[t["energy_uj"] >= 0].reset_index(drop=True)
        req = load(tag + "_req.csv")
        req = req[req["status"] == "ok"]
        vals = []
        for w in np.array_split(np.arange(len(t)), 6):
            if len(w) < 2:
                continue
            j = (t["energy_uj"].iloc[w[-1]] - t["energy_uj"].iloc[w[0]]) / 1e6
            t0 = t["t_epoch_ms"].iloc[w[0]]
            t1 = t["t_epoch_ms"].iloc[w[-1]]
            n = len(req[(req["t_epoch_ms"] >= t0) & (req["t_epoch_ms"] <= t1)])
            if n > 0:
                vals.append(j / n)
        vals = np.array(vals)
        meds.append(float(np.median(vals)))
        errs.append([float(np.median(vals) - np.percentile(vals, 25)),
                     float(np.percentile(vals, 75) - np.median(vals))])
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(labels, meds, yerr=np.array(errs).T, capsize=4,
                  color=["tab:blue", "tab:red"] * 2)
    ax.bar_label(bars, fmt="%.3f", fontsize=8, padding=2)
    ax.set_ylabel("package energy per served request (J)")
    ax.set_ylim(0, max(meds) * 1.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_energy.png"))
    plt.close(fig)

    a = load("arm_burst_ctrl_stress.csv")["ready_ms"].to_numpy(dtype=float)
    b = load("arm_burst_unctrl_stress.csv")["ready_ms"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.boxplot([a, b], widths=0.5, showfliers=True)
    ax.set_xticklabels(["controlled (n=40)", "uncontrolled (n=40)"])
    for i, arr in enumerate([a, b], start=1):
        ax.text(i + 0.28, np.median(arr), f"{np.median(arr):.2f}", fontsize=8, va="center")
    ax.set_ylabel("guest boot latency under pressure (ms)")
    ax.set_title("Mann-Whitney U = 15.0, p = 4.39e-14")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig11_burst_stress.png"))
    plt.close(fig)
    print("polish complete")

if __name__ == "__main__":
    main()
