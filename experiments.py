"""Experimental evaluation for the Cover report.  Run:  python experiments.py
Each timed run happens in its own process so that peak memory is measured cleanly.
Writes CSV files to results/ and figures to results/figures/.  Takes about 10 minutes."""
import csv
import json
import os
import random
import resource
import subprocess
import sys
import time
from bisect import bisect_right

TIME_LIMIT = 60.0          # seconds: "reasonable time" for one instance
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")


# ------------------------------------------------------------ one timed run
def single(method, n, seed, kind):
    import baseline
    import fasterAlgo
    from check_correctness import exhaustive
    from common import generate
    rng = random.Random(seed)
    inst = generate(n, n, n, rng, equal_radius=5 if kind == "equal" else None)
    fn = {"exhaustive": exhaustive, "baseline": baseline.solve,
          "tree": fasterAlgo.solve_tree, "deque": fasterAlgo.solve_proper}[method]
    t = time.perf_counter()
    res = fn(*inst)
    secs = time.perf_counter() - t
    cost = res if method == "exhaustive" else res[0]
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(json.dumps({"seconds": secs, "peak_mb": rss_mb, "cost": cost}))


def run_child(method, n, seed, kind):
    out = subprocess.run([sys.executable, __file__, "--single", method, str(n), str(seed), kind],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


# ------------------------------------------------------------ E1 scalability
def e1_scalability():
    plans = [("exhaustive", "random", [4, 8, 12, 16, 18, 20, 22]),
             ("baseline", "random", [250 * 2 ** i for i in range(10)]),
             ("tree", "random", [1000 * 2 ** i for i in range(13)]),
             ("tree", "equal", [1000 * 2 ** i for i in range(13)]),
             ("deque", "equal", [1000 * 2 ** i for i in range(13)])]
    rows = []
    for method, kind, sizes in plans:
        for n in sizes:
            r = run_child(method, n, 7, kind)
            rows.append({"method": method, "radii": kind, "n": n, **r})
            print("E1", method, kind, n, round(r["seconds"], 3), round(r["peak_mb"]), flush=True)
            if r["seconds"] > TIME_LIMIT / 2:   # the next size (2x) would exceed the limit
                break
    write_csv("e1_scalability.csv", rows)
    return rows


# ------------------------------------------------------------ E2 parameters
def greedy_fewest(O, C, S, R):
    """Classic interval-cover greedy: from the first unwatered orange, take the sprinkler
    that reaches furthest right.  Uses the fewest sprinklers, ignores cacti."""
    O = sorted(O)
    iv = sorted((S[i] - R[i], S[i] + R[i], i) for i in range(len(S)))
    chosen, k, p, best = [], 0, 0, None
    while p < len(O):
        x = O[p]
        while k < len(iv) and iv[k][0] <= x:
            if iv[k][1] >= x and (best is None or iv[k][1] > iv[best][1]):
                best = k
            k += 1
        chosen.append(iv[best][2])
        p = bisect_right(O, iv[best][1], p)
    return chosen


def e2_parameters():
    import baseline
    import fasterAlgo
    from common import evaluate, generate
    rng = random.Random(11)
    n = 20_000
    rows = []
    # (a) orange density: how many sprinklers survive pruning, and what that buys
    for o in [20, 200, 2_000, 20_000]:
        O, C, S, R = generate(n, o, n, rng)
        kept = len(fasterAlgo.prepare(O, C, S, R)[2])
        tb = timed(baseline.solve, O, C, S, R)
        tt = timed(fasterAlgo.solve_tree, O, C, S, R)
        rows.append({"experiment": "orange density", "s": n, "o": o, "c": n, "max_radius": "default",
                     "kept_pct": round(100 * kept / n, 1), "baseline_s": tb, "tree_s": tt,
                     "nested_pct": "", "opt": "", "greedy": ""})
        print("E2a", rows[-1], flush=True)
    # (b) radius spread: more nesting, longer intervals; and the cost of ignoring cacti
    spacing = 10
    for rmax in [5, 20, 80, 320]:
        vals = {"opt": 0, "greedy": 0, "nested": 0, "tb": 0.0, "tt": 0.0}
        reps = 5
        for _ in range(reps):
            O, C, S, R = generate(4_000, 4_000, 4_000, rng, length=spacing * 4_000, rmin=1, rmax=rmax)
            iv = fasterAlgo.prepare(O, C, S, R)[2]
            vals["nested"] += sum(iv[j][1] <= iv[j - 1][1] for j in range(1, len(iv))) / max(1, len(iv) - 1)
            vals["tb"] += timed(baseline.solve, O, C, S, R)
            vals["tt"] += timed(fasterAlgo.solve_tree, O, C, S, R)
            vals["opt"] += fasterAlgo.solve_tree(O, C, S, R)[0]
            vals["greedy"] += evaluate(O, C, S, R, greedy_fewest(O, C, S, R))[1]
        rows.append({"experiment": "radius spread", "s": 4_000, "o": 4_000, "c": 4_000, "max_radius": rmax,
                     "kept_pct": "", "baseline_s": round(vals["tb"] / reps, 3),
                     "tree_s": round(vals["tt"] / reps, 3),
                     "nested_pct": round(100 * vals["nested"] / reps, 1),
                     "opt": round(vals["opt"] / reps, 1), "greedy": round(vals["greedy"] / reps, 1)})
        print("E2b", rows[-1], flush=True)
    write_csv("e2_parameters.csv", rows)
    return rows


def timed(fn, *args):
    t = time.perf_counter()
    fn(*args)
    return round(time.perf_counter() - t, 3)


def write_csv(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------ figure
def figure(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink2, grid, surf = "#52514e", "#e4e3df", "#fcfcfb"
    plt.rcParams.update({"figure.facecolor": surf, "axes.facecolor": surf, "savefig.facecolor": surf,
                         "axes.edgecolor": ink2, "xtick.color": ink2, "ytick.color": ink2,
                         "axes.grid": True, "grid.color": grid, "axes.spines.top": False,
                         "axes.spines.right": False, "font.size": 9, "legend.frameon": False,
                         "lines.linewidth": 2})
    series = [("exhaustive", "random", "Exhaustive search", "#e34948", "D"),
              ("baseline", "random", "Baseline DP", "#eb6834", "o"),
              ("tree", "random", "Segment-tree DP", "#2a78d6", "s"),
              ("deque", "equal", "Deque DP (equal radii)", "#1baf7a", "^")]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for key, ylab in [("seconds", "running time (s)"), ("peak_mb", "peak memory (MB)")]:
        ax = axes[0] if key == "seconds" else axes[1]
        for m, kind, label, col, mk in series:
            r = [x for x in rows if x["method"] == m and x["radii"] == kind]
            if key == "peak_mb" and m == "exhaustive":
                continue
            ax.plot([x["n"] for x in r], [x[key] for x in r], color=col, marker=mk, markersize=4, label=label)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("n = sprinklers = oranges = cacti")
        ax.set_ylabel(ylab)
    axes[0].axhline(TIME_LIMIT, color=ink2, linewidth=1, linestyle="--")
    axes[0].text(5, TIME_LIMIT * 1.15, "60 s limit", color=ink2, fontsize=8)
    axes[0].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figures", "fig_scalability.png"), dpi=220)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        single(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
    else:
        os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)
        rows = e1_scalability()
        figure(rows)
        e2_parameters()
