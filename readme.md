# Cover — CMPT 360 Algorithm Design Module, Option 4

Choose sprinklers so that every orange tree is watered and as few cacti as possible are watered.

## Requirements
Python 3.10 or newer. Only `experiments.py` needs extra packages:
```
pip install matplotlib
```

## Main programs
| File | Algorithm | Time |
|---|---|---|
| `baseline.py` | chain dynamic program | O(s² + n log n) |
| `fasterAlgo.py` | pruning + segment-tree DP; linear deque DP when all radii are equal | O(n log n); O(n) after sorting |

Run either one on an input file, or with no argument to solve the assignment's example:
```
python baseline.py examples/example.txt
python fasterAlgo.py examples/example.txt
```
Output: the chosen sprinkler positions and the number of watered cacti.

Input file format (one array per line, numbers separated by spaces):
```
O: 2 6 11
C: 4 8 14
S: 3 7 12
R: 2 2 1
```
Note: with these numbers the optimum is **2** watered cacti (all three sprinklers are needed,
because only the sprinkler at 7 reaches the orange tree at 6). The assignment text says 1,
which does not match its own numbers.

## Other files
- `common.py` — input parsing, an independent checker for a selection, random instance generator
- `check_correctness.py` — compares all algorithms with exhaustive search (`python check_correctness.py`, ~15 s)
- `experiments.py` — all experiments and the figure in the report (`python experiments.py`, ~10 min)
- `results/` — experiment output (CSV) and `results/figures/`
