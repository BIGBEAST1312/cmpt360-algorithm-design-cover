"""Baseline exact algorithm for Cover (CMPT 360, Option 4).

Chain DP over sprinklers sorted by left endpoint.  O(s^2 + (s + o + c) log(o + c)) time,
O(s) memory.

Run:  python baseline.py [instance.txt]      (no argument = the assignment's example)
"""
from common import counters, main

INF = float("inf")


def solve(O, C, S, R):
    """Return (minimum number of watered cacti, list of chosen sprinkler indices)."""
    if not O:
        return 0, []
    O, C = sorted(O), sorted(C)
    c_le, c_lt = counters(C)
    o_le, o_lt = counters(O)

    # one copy of each distinct interval, sorted by (left, right)
    first = {}
    for i in range(len(S)):
        first.setdefault((S[i] - R[i], S[i] + R[i]), i)
    iv = sorted(first)
    idx = [first[t] for t in iv]
    n = len(iv)
    L = [l for l, _ in iv]
    Rt = [r for _, r in iv]
    cle_r = [c_le(r) for r in Rt]   # cacti <= right end
    clt_l = [c_lt(l) for l in L]    # cacti <  left end
    ole_r = [o_le(r) for r in Rt]   # oranges <= right end
    olt_l = [o_lt(l) for l in L]    # oranges <  left end

    # f[j] = fewest cacti watered by a chain ending at interval j that waters every
    # orange left of Rt[j]; par[j] = previous interval in that chain
    f = [INF] * n
    par = [-1] * n
    for j in range(n):
        lj, rj = L[j], Rt[j]
        if olt_l[j] == 0:                       # j can start the chain
            f[j] = cle_r[j] - clt_l[j]
        for i in range(j):
            if Rt[i] >= rj or f[i] == INF:      # chains have increasing right ends
                continue
            if lj <= Rt[i]:                     # overlap: new cacti in (Rt[i], rj]
                v = f[i] + cle_r[j] - cle_r[i]
            elif olt_l[j] == ole_r[i]:          # gap with no orange inside it
                v = f[i] + cle_r[j] - clt_l[j]
            else:
                continue
            if v < f[j]:
                f[j], par[j] = v, i

    best, end = INF, -1
    for j in range(n):
        if ole_r[j] == len(O) and f[j] < best:  # chain must reach the last orange
            best, end = f[j], j
    if end < 0:
        raise ValueError("infeasible instance")
    chosen = []
    while end >= 0:
        chosen.append(idx[end])
        end = par[end]
    return best, chosen[::-1]


if __name__ == "__main__":
    main("baseline", solve)
