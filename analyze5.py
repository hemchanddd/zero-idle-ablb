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
    rows = []
    for tag, drv in [("controlled", "sustained_unik_ctrl_p2_r10.csv"),
                     ("uncontrolled", "sustained_unik_unctrl_p2_r10.csv")]:
        d = load(drv)
        arrivals = len(d)
        ok_rows = d[d["status"] == "ok"]
        shed = len(d[d["status"] == "shed"])
        suffix = "ctrl" if tag == "controlled" else "unctrl"
        req = load("sustained_unik_%s_p2_req.csv" % suffix)
        r = req["ready_ms"].to_numpy(dtype=float)
        r = r[r > 0]
        rows.append([tag, arrivals, len(ok_rows),
                     round(100.0 * len(ok_rows) / arrivals, 1),
                     round(100.0 * shed / arrivals, 1),
                     round(float(np.percentile(r, 50)), 2),
                     round(float(np.percentile(r, 99)), 2)])
    odf = pd.DataFrame(rows, columns=["arm", "arrivals", "served", "goodput_pct",
                                      "shed_pct", "p50_ready_ms", "p99_ready_ms"])
    odf.to_csv(os.path.join(TAB, "overload_summary.csv"), index=False)

    pairs = [
        ("healthy 20 rps e2e", "sustained_unik_ctrl_r20.csv", "sustained_unik_unctrl_r20.csv", "e2e_ms"),
        ("healthy 40 rps e2e", "sustained_unik_ctrl_r40.csv", "sustained_unik_unctrl_r40.csv", "e2e_ms"),
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

    fig, ax = plt.subplots(figsize=(6.5, 4))
    tags = ["sustained_unik_ctrl", "sustained_unik_unctrl",
            "sustained_unik_ctrl_stress", "sustained_unik_unctrl_stress"]
    labels = ["ctrl healthy", "unctrl healthy", "ctrl transient", "unctrl transient"]
    jpr = []
    for tag in tags:
        t = load(tag + "_telemetry.csv")
        e = t["energy_uj"].to_numpy(dtype=float)
        e = e[e >= 0]
        req = load(tag + "_req.csv")
        ok = len(req[req["status"] == "ok"])
        jpr.append((e[-1] - e[0]) / 1e6 / ok if len(e) >= 2 and ok > 0 else float("nan"))
    bars = ax.bar(labels, jpr, color=["tab:blue", "tab:red"] * 2)
    ax.bar_label(bars, fmt="%.3f")
    ax.set_ylabel("joules per served request")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_energy.png"), dpi=200)
    plt.close(fig)
    print("analysis5 complete")

if __name__ == "__main__":
    main()
