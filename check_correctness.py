"""Compare every algorithm with exhaustive search on random small instances.
Run:  python check_correctness.py"""
import random

import baseline
import fasterAlgo
from common import evaluate, generate, is_feasible


def exhaustive(O, C, S, R):
    """Try all 2^s subsets of sprinklers (bitmasks of watered oranges and cacti)."""
    s = len(S)
    om = [sum(1 << t for t, x in enumerate(O) if S[i] - R[i] <= x <= S[i] + R[i]) for i in range(s)]
    cm = [sum(1 << t for t, x in enumerate(C) if S[i] - R[i] <= x <= S[i] + R[i]) for i in range(s)]
    full = (1 << len(O)) - 1
    best = None
    for mask in range(1 << s):
        o = c = 0
        for i in range(s):
            if mask >> i & 1:
                o |= om[i]
                c |= cm[i]
        if o == full and (best is None or bin(c).count("1") < best):
            best = bin(c).count("1")
    return best


def main(trials=5000, seed=360):
    rng = random.Random(seed)
    methods = {"baseline": baseline.solve, "fasterAlgo.solve_tree": fasterAlgo.solve_tree,
               "fasterAlgo.solve": fasterAlgo.solve}
    counts = {"instances": 0, "equal-radius instances": 0}
    for t in range(trials):
        s, o, c = rng.randint(1, 12), rng.randint(0, 10), rng.randint(0, 12)
        length = rng.choice([10, 20, 60])             # small lengths force many ties
        eq = rng.choice([None, None, rng.randint(0, 4)])
        O, C, S, R = generate(s, o, c, rng, length=length, rmin=0, rmax=rng.randint(1, 8), equal_radius=eq)
        assert is_feasible(O, S, R)
        want = exhaustive(O, C, S, R)
        for name, fn in methods.items():
            cost, chosen = fn(O, C, S, R)
            ok, cacti = evaluate(O, C, S, R, chosen)
            assert ok and cacti == cost == want, (name, O, C, S, R, cost, want)
        if eq is not None:
            cost, chosen = fasterAlgo.solve_proper(O, C, S, R)
            assert cost == want
            counts["equal-radius instances"] += 1
        counts["instances"] += 1
    # larger instances: too big for exhaustive search, so the algorithms check each other
    for t in range(200):
        n = rng.randint(50, 1500)
        eq = rng.choice([None, rng.randint(1, 30)])
        O, C, S, R = generate(n, n, n, rng, equal_radius=eq)
        want = baseline.solve(O, C, S, R)[0]
        for fn in (fasterAlgo.solve_tree, fasterAlgo.solve):
            cost, chosen = fn(O, C, S, R)
            ok, cacti = evaluate(O, C, S, R, chosen)
            assert ok and cacti == cost == want
        if eq is not None:
            assert fasterAlgo.solve_proper(O, C, S, R)[0] == want
        counts["large instances"] = counts.get("large instances", 0) + 1
    # the assignment's example
    ex = ([2, 6, 11], [4, 8, 14], [3, 7, 12], [2, 2, 1])
    print("assignment example optimum (exhaustive):", exhaustive(*ex))
    print("all algorithms match exhaustive search:", counts)


if __name__ == "__main__":
    main()
