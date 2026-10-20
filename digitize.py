import csv
import os

RESULTS = "/home/hemchand/zero-idle-research/results"

PHASE2 = [
    ["1 boot", 131.27, 131.27, 131.27, 131.27, 131.27],
    ["10 boots", 125.64, 128.43, 133.50, 133.50, 129.61],
    ["20 boots", 158.81, 170.52, 178.17, 180.04, 170.30],
    ["10 boots + memory stress", 136.10, 144.49, 158.46, 158.46, 146.09],
]

UNCTRL_READY = [255.5, 304.1, 331.6, 330.6, 322.0, 345.6, 344.8, 361.1, 353.1, 336.6,
                369.1, 367.0, 377.4, 362.0, 372.3, 361.7, 390.2, 383.5, 394.0, 391.7,
                369.1, 367.1, 362.7, 372.7, 390.3, 398.9, 401.5, 400.2, 406.5, 403.5,
                405.1, 409.0, 404.5, 393.0, 387.1, 421.4, 399.4, 425.1, 443.2, 439.1]
UNCTRL_PROXY = [4.3, 8.1, 9.1, 7.8, 8.1, 5.2, 7.7, 8.7, 3.7, 5.7,
                7.5, 4.5, 3.6, 3.5, 4.8, 3.9, 2.5, 2.2, 5.4, 2.2,
                3.8, 4.7, 3.4, 2.9, 2.4, 2.4, 1.9, 1.8, 1.8, 3.0,
                2.4, 2.3, 2.2, 2.0, 1.4, 1.7, 1.3, 2.1, 0.9, 1.1]
CTRL_WAIT = [0.0] * 16 + [267.4, 252.2, 277.7, 266.3, 281.9, 274.8, 284.9, 306.4,
                          306.0, 308.1, 308.0, 304.1, 306.8, 307.6, 307.2, 305.6,
                          453.4, 463.9, 480.4, 475.9, 473.9, 466.3, 491.3, 504.9]
CTRL_READY = [251.4, 268.9, 257.9, 259.3, 260.4, 265.1, 269.1, 277.4, 269.3, 272.1,
              274.1, 280.0, 281.1, 275.5, 283.7, 288.9, 183.3, 207.8, 183.6, 205.2,
              191.0, 201.7, 202.0, 183.1, 193.8, 194.1, 196.7, 202.7, 206.0, 213.0,
              218.3, 225.9, 175.8, 167.0, 156.8, 165.8, 170.2, 184.4, 178.4, 180.6]
CTRL_PROXY = [3.7, 3.5, 5.9, 5.0, 5.1, 5.1, 6.0, 7.0, 6.9, 6.9,
              6.3, 6.1, 6.4, 4.7, 2.4, 2.6, 2.2, 2.7, 3.8, 2.3,
              2.2, 3.4, 2.5, 3.2, 2.5, 1.9, 3.1, 3.0, 2.0, 1.8,
              1.8, 1.9, 2.5, 2.3, 1.8, 2.0, 2.3, 1.5, 1.5, 2.2]

def write_burst(path, wait, ready, proxy, limit):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["req_id", "wait_ms", "ready_ms", "proxy_ms", "limit", "status"])
        for i in range(len(ready)):
            w.writerow([i, wait[i], ready[i], proxy[i], limit, "ok"])

def main():
    with open(os.path.join(RESULTS, "phase2_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "min", "p50", "p95", "max", "avg"])
        w.writerows(PHASE2)
    write_burst(os.path.join(RESULTS, "arm_burst_unctrl_stress.csv"),
                [0.0] * 40, UNCTRL_READY, UNCTRL_PROXY, 9999)
    write_burst(os.path.join(RESULTS, "arm_burst_ctrl_stress.csv"),
                CTRL_WAIT, CTRL_READY, CTRL_PROXY, 16)
    print("digitized")

if __name__ == "__main__":
    main()
