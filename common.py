"""Shared helpers for the Cover problem (CMPT 360, Option 4): input parsing,
checking a selection, and random instance generators."""
from bisect import bisect_left, bisect_right
import sys


def read_instance(path):
    """File format: four lines 'O: ...', 'C: ...', 'S: ...', 'R: ...' (numbers separated
    by spaces). Lines starting with # are ignored."""
    data = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, rest = line.partition(":")
            data[key.strip().upper()] = [float(t) if "." in t else int(t) for t in rest.split()]
    O, C, S, R = (data.get(k, []) for k in "OCSR")
    if len(S) != len(R):
        raise ValueError("S and R must have the same length")
    if any(r < 0 for r in R):
        raise ValueError("radii must be non-negative")
    return O, C, S, R


def evaluate(O, C, S, R, chosen):
    """Return (all oranges watered?, number of cacti watered) for the chosen sprinkler
    indices. Independent of the algorithms: used to check their answers."""
    iv = sorted((S[i] - R[i], S[i] + R[i]) for i in chosen)
    merged = []  # union of the chosen intervals as disjoint closed intervals
    for l, r in iv:
        if merged and l <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], r)
        else:
            merged.append([l, r])
    lefts = [m[0] for m in merged]

    def watered(x):
        k = bisect_right(lefts, x) - 1
        return k >= 0 and x <= merged[k][1]

    return all(watered(x) for x in O), sum(watered(x) for x in C)


def is_feasible(O, S, R):
    return evaluate(O, [], S, R, range(len(S)))[0]


def report(name, O, C, S, R, cost, chosen):
    ok, cacti = evaluate(O, C, S, R, chosen)
    assert ok and cacti == cost, "internal error: selection does not match its cost"
    pos = [S[i] for i in chosen]
    print(f"{name}: selected sprinklers at positions {pos} (indices {sorted(chosen)})")
    print(f"All {len(O)} orange trees are watered; {cost} of {len(C)} cacti are watered.")


def main(name, solve):
    if len(sys.argv) > 1:
        O, C, S, R = read_instance(sys.argv[1])
    else:  # the example from the assignment
        O, C, S, R = [2, 6, 11], [4, 8, 14], [3, 7, 12], [2, 2, 1]
    if not is_feasible(O, S, R):
        sys.exit("Infeasible input: some orange tree is not watered even with all sprinklers on.")
    cost, chosen = solve(O, C, S, R)
    report(name, O, C, S, R, cost, chosen)


# ---------------------------------------------------------------- generators
def generate(s, o, c, rng, length=None, rmin=1, rmax=None, equal_radius=None):
    """Random feasible instance with integer positions on [0, length].
    Oranges are drawn inside random sprinklers, so all sprinklers on waters every tree.
    equal_radius=r gives every sprinkler radius r (the 'same sprinkler model' case)."""
    length = length if length is not None else 10 * max(s, o, c, 1)
    rmax = rmax if rmax is not None else max(rmin, length // max(s, 1))
    S = [rng.randint(0, length) for _ in range(s)]
    R = [equal_radius if equal_radius is not None else rng.randint(rmin, rmax) for _ in range(s)]
    O = []
    for _ in range(o):
        i = rng.randrange(s)
        O.append(rng.randint(S[i] - R[i], S[i] + R[i]))
    C = [rng.randint(-rmax, length + rmax) for _ in range(c)]
    return O, C, S, R


def counters(points):
    """count_le(x), count_lt(x) for a sorted list of points."""
    return (lambda x: bisect_right(points, x)), (lambda x: bisect_left(points, x))
