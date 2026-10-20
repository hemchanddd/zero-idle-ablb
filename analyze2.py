import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS = "/home/hemchand/zero-idle-research/results"
FIG = "/home/hemchand/zero-idle-research/figures"

def load(fname):
    return pd.read_csv(os.path.join(RESULTS, fname))

def main():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    arms = [
        ("unikernel controlled 20 rps", "sustained_unik_ctrl_r20.csv", "e2e_ms"),
        ("unikernel uncontrolled 20 rps", "sustained_unik_unctrl_r20.csv", "e2e_ms"),
        ("container warm 20 rps", "sustained_warm_warm_r20.csv", "e2e_ms"),
        ("container cold 10 rps", "sustained_pcold_pcold_r10.csv", "e2e_ms"),
    ]
    for label, fname, col in arms:
        x = np.sort(load(fname)[col].to_numpy(dtype=float))
        x = x[x > 0]
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=label)
    ax.set_xscale("log")
    ax.set_xlabel("end-to-end latency (ms, log scale)")
    ax.set_ylabel("CDF")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig7_cdf_sustained.png"), dpi=200)
    plt.close(fig)

    cold = load("sustained_pcold_pcold_r10.csv")["e2e_ms"].to_numpy(dtype=float)
    over = 100.0 * np.mean(cold > 2000.0)
    print("cold tail above 2000 ms percent:", round(over, 2), "max:", round(cold.max(), 1))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ctrl = load("arm_burst_ctrl_stress.csv")
    idx = np.arange(len(ctrl))
    ax.step(idx, ctrl["wait_ms"], where="post", label="admission wait")
    ax.step(idx, ctrl["ready_ms"], where="post", label="guest boot")
    ax.set_xlabel("request index")
    ax.set_ylabel("milliseconds")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_queue_limit.png"), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for tag, color in [("sustained_unik_ctrl", "tab:blue"), ("sustained_unik_unctrl", "tab:red")]:
        t = load(tag + "_telemetry.csv")
        t = t[t["energy_uj"] >= 0].reset_index(drop=True)
        ts = (t["t_epoch_ms"] - t["t_epoch_ms"].iloc[0]) / 1000.0
        power = np.diff(t["energy_uj"].to_numpy(dtype=float)) / np.diff(ts.to_numpy(dtype=float)) / 1e6
        win = 20
        smooth = np.convolve(power, np.ones(win) / win, mode="valid")
        ax.plot(ts.to_numpy()[win:], smooth, color=color, label=tag.split("_")[-1])
    ax.set_xlabel("time (s)")
    ax.set_ylabel("package power (W)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_energy.png"), dpi=200)
    plt.close(fig)
    print("figures regenerated")

if __name__ == "__main__":
    main()
