"""Faster exact algorithms for Cover (CMPT 360, Option 4).

Same chain DP as baseline.py, plus three ideas:
  1. Pruning: a sprinkler that waters no orange tree is never needed.
  2. General case: each DP transition is a range-minimum query over the right ends
     of earlier intervals, answered by two segment trees.  O((s + o + c) log(s + o + c)).
  3. Equal-radius case (one sprinkler model, so no interval contains another): both
     query ranges slide monotonically, so two monotone deques replace the trees.
     O(s + o + c) after sorting.
solve() picks case 3 automatically when it applies.

Run:  python fasterAlgo.py [instance.txt]    (no argument = the assignment's example)
"""
from bisect import bisect_left
from collections import deque

from common import counters, main

INF = float("inf")


class MinTree:
    """Iterative segment tree: point 'improve to min', range min with argmin."""

    def __init__(self, n):
        self.size = 1
        while self.size < n:
            self.size *= 2
        self.val = [INF] * (2 * self.size)
        self.arg = [-1] * (2 * self.size)

    def improve(self, pos, v, who):
        p = pos + self.size
        if v >= self.val[p]:
            return
        self.val[p], self.arg[p] = v, who
        p //= 2
        while p:
            a, b = 2 * p, 2 * p + 1
            k = a if self.val[a] <= self.val[b] else b
            if self.val[p] == self.val[k] and self.arg[p] == self.arg[k]:
                break
            self.val[p], self.arg[p] = self.val[k], self.arg[k]
            p //= 2

    def query(self, lo, hi):
        """min over positions lo..hi-1 -> (value, who)"""
        best, who = INF, -1
        lo += self.size
        hi += self.size
        while lo < hi:
            if lo & 1:
                if self.val[lo] < best:
                    best, who = self.val[lo], self.arg[lo]
                lo += 1
            if hi & 1:
                hi -= 1
                if self.val[hi] < best:
                    best, who = self.val[hi], self.arg[hi]
            lo //= 2
            hi //= 2
        return best, who


def prepare(O, C, S, R):
    """Sort, prune sprinklers that water no orange, remove duplicate intervals.
    Returns sorted O, C and the surviving intervals sorted by (left, right)."""
    O, C = sorted(O), sorted(C)
    o_le, o_lt = counters(O)
    first = {}
    for i in range(len(S)):
        l, r = S[i] - R[i], S[i] + R[i]
        if o_le(r) > o_lt(l):                   # waters at least one orange
            first.setdefault((l, r), i)
    iv = sorted(first)
    return O, C, iv, [first[t] for t in iv]


def _finish(O, iv, idx, f, par, ole_r):
    best, end = INF, -1
    for j in range(len(iv)):
        if ole_r[j] == len(O) and f[j] < best:
            best, end = f[j], j
    if end < 0:
        raise ValueError("infeasible instance")
    chosen = []
    while end >= 0:
        chosen.append(idx[end])
        end = par[end]
    return best, chosen[::-1]


def _tree(O, C, iv, idx):
    """General case on prepared input, O((s + o + c) log(s + o + c))."""
    c_le, c_lt = counters(C)
    o_le, o_lt = counters(O)
    n = len(iv)
    rs = sorted({r for _, r in iv})             # right ends, the trees' key space
    A, B = MinTree(len(rs)), MinTree(len(rs))   # A: f[i] - cle_r[i], B: f[i]
    f, par = [INF] * n, [-1] * n
    ole_r = [0] * n
    for j, (lj, rj) in enumerate(iv):
        cle_r, clt_l = c_le(rj), c_lt(lj)
        ole_r[j] = o_le(rj)
        k = o_lt(lj)                            # oranges left of lj
        best, who = INF, -1
        if k == 0:                              # start a chain
            best = cle_r - clt_l
        # overlap: earlier right end in [lj, rj)
        v, i = A.query(bisect_left(rs, lj), bisect_left(rs, rj))
        if v + cle_r < best:
            best, who = v + cle_r, i
        # gap: earlier right end in [last orange before lj, lj)
        lo = bisect_left(rs, O[k - 1]) if k else 0
        v, i = B.query(lo, bisect_left(rs, lj))
        if v + cle_r - clt_l < best:
            best, who = v + cle_r - clt_l, i
        f[j], par[j] = best, who
        if best < INF:
            pos = bisect_left(rs, rj)
            A.improve(pos, best - cle_r, j)
            B.improve(pos, best, j)
    return _finish(O, iv, idx, f, par, ole_r)


def is_proper(iv):
    """No interval contains another <=> right ends strictly increase in (left, right) order."""
    return all(iv[j - 1][1] < iv[j][1] for j in range(1, len(iv)))


def _proper(O, C, iv, idx):
    """No-containment case (e.g. equal radii) on prepared input: O(s + o + c) after sorting."""
    assert is_proper(iv)
    n = len(iv)
    L = [l for l, _ in iv]
    Rt = [r for _, r in iv]
    # all four counts with forward-only pointers, since L and Rt both increase
    cle_r, clt_l, ole_r, olt_l = [0] * n, [0] * n, [0] * n, [0] * n
    a = b = c = d = 0
    for j in range(n):
        while a < len(C) and C[a] <= Rt[j]: a += 1
        while b < len(C) and C[b] < L[j]: b += 1
        while c < len(O) and O[c] <= Rt[j]: c += 1
        while d < len(O) and O[d] < L[j]: d += 1
        cle_r[j], clt_l[j], ole_r[j], olt_l[j] = a, b, c, d

    f, par = [INF] * n, [-1] * n
    over = deque()   # candidates for overlap, increasing f[i] - cle_r[i]
    gap = deque()    # candidates for gap, increasing f[i]
    first_reach = 0  # first i with Rt[i] >= L[j]
    first_gap = 0    # first i with Rt[i] >= last orange before L[j]
    added = 0        # intervals before this index have been offered to `gap`
    for j in range(n):
        lj = L[j]
        while first_reach < j and Rt[first_reach] < lj:
            first_reach += 1
        k = olt_l[j]
        if k:
            p = O[k - 1]
            while first_gap < n and Rt[first_gap] < p:
                first_gap += 1
        while added < first_reach:              # Rt[added] < lj: a gap candidate
            if f[added] < INF:
                while gap and f[gap[-1]] >= f[added]:
                    gap.pop()
                gap.append(added)
            added += 1
        while over and over[0] < first_reach:
            over.popleft()
        while gap and gap[0] < (first_gap if k else 0):
            gap.popleft()

        best, who = (cle_r[j] - clt_l[j], -1) if k == 0 else (INF, -1)
        if over:
            i = over[0]
            v = f[i] - cle_r[i] + cle_r[j]
            if v < best:
                best, who = v, i
        if gap:
            i = gap[0]
            v = f[i] + cle_r[j] - clt_l[j]
            if v < best:
                best, who = v, i
        f[j], par[j] = best, who
        if best < INF:
            key = best - cle_r[j]
            while over and f[over[-1]] - cle_r[over[-1]] >= key:
                over.pop()
            over.append(j)
    return _finish(O, iv, idx, f, par, ole_r)


def solve_tree(O, C, S, R):
    return _tree(*prepare(O, C, S, R)) if O else (0, [])


def solve_proper(O, C, S, R):
    return _proper(*prepare(O, C, S, R)) if O else (0, [])


def solve(O, C, S, R):
    """Exact answer; uses the linear-time method when no interval contains another."""
    if not O:
        return 0, []
    prepared = prepare(O, C, S, R)
    return _proper(*prepared) if is_proper(prepared[2]) else _tree(*prepared)


if __name__ == "__main__":
    main("fasterAlgo", solve)
