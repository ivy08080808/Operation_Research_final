# Operation Research Final: Perishable Inventory Optimization

This project studies a multi-period perishable inventory optimization problem with procurement, inventory aging, discount activation, holding cost, and waste cost.

The original mathematical formulation is a mixed integer linear program (MILP). This repository implements:

- `greedy_inventory.py`: original greedy heuristic
- `greedy_inventory_v2.py`: improved delay-aware heuristic
- `gurobi_inventory.py`: exact MILP solver using Gurobi
- `instances.py`: all instance data, separated from solver logic
- `run_instance.py`: command-line runner that selects the instance and solver at runtime
- `compare_instance*.py`: benchmark scripts for Instances 1-5
- `compare_v2_summary.py`: comparison of greedy v1, greedy v2, and Gurobi
- `results_summary.md`: original greedy vs Gurobi summary
- `v2_results_summary.md`: greedy v2 improvement summary

## Problem Summary

The optimization object is ingredient flow:

```text
purchase -> inventory aging -> usage -> waste
```

For each ingredient and week, the solver decides:

- regular purchase quantity
- discount purchase quantity
- whether the discount is activated
- age-indexed inventory
- usage from each age bucket
- expired waste

The objective is:

```text
purchase cost + holding cost + waste cost
```

## Model Inputs

Each instance provides:

- weekly dish demand
- recipe matrix
- ingredient parameters:
  - regular cost
  - discount cost
  - discount threshold
  - shelf life
  - holding cost
  - waste cost
  - Big-M purchase bound

Dish demand is preprocessed into ingredient demand:

```python
ingredient_demand[i][t] = sum(recipe[d][i] * dish_demand[d][t] for d in dishes)
```

## Algorithms

### Greedy v1

The original greedy heuristic uses FIFO consumption and a shelf-life lookahead rule. It activates discount if buying enough to cover demand inside the shelf-life window appears cheaper than regular just-in-time purchase.

This is extremely fast, but it can buy too early and create excessive holding cost.

### Greedy v2

Greedy v2 keeps the original solver untouched and adds a delay-aware rolling dynamic heuristic.

For each ingredient, it enumerates meaningful purchase candidates:

- buy just enough regular quantity for current demand
- buy at the discount threshold
- buy enough to cover demand up to a future week within shelf life
- buy bounded by the Big-M limit

It then chooses the least-cost plan over the remaining horizon for that ingredient. This directly addresses the main weakness found in Instances 3 and 5: buying too early.

### Gurobi MILP

The Gurobi solver models the full MILP with:

- continuous purchase, usage, inventory, and waste variables
- binary discount activation variables
- inventory aging flow constraints
- expiration constraints
- demand satisfaction constraints
- discount threshold and Big-M constraints

It is used as the optimal benchmark.

## Main Results

All timings are average wall-clock seconds over 20 repeated runs.

| Instance | Greedy v1 Cost | Greedy v2 Cost | Gurobi Cost | v1 Gap % | v2 Gap % | v1 Avg (s) | v2 Avg (s) | Gurobi Avg (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2282.30 | 2264.05 | 2264.05 | 0.8061% | 0.0000% | 0.0000699 | 0.0003622 | 0.0099403 |
| 2 | 859.50 | 859.50 | 859.50 | 0.0000% | 0.0000% | 0.0000445 | 0.0001143 | 0.0014687 |
| 3 | 1564.00 | 1340.40 | 1340.40 | 16.6816% | 0.0000% | 0.0000611 | 0.0009265 | 0.0147207 |
| 4-S2 | 1778.80 | 1778.80 | 1778.80 | 0.0000% | 0.0000% | 0.0000522 | 0.0003669 | 0.0054443 |
| 5 | 10060.05 | 9431.60 | 9431.45 | 6.6649% | 0.0016% | 0.0000869 | 0.0007792 | 0.0101493 |

## Key Findings

Greedy v1 is very fast and works well when demand is flat or discount is unreachable. However, it can perform poorly when early bulk-buying causes high holding cost.

Greedy v2 fixes this by considering delayed purchase timing. It matches Gurobi on Instances 1, 2, 3, and 4-S2, and nearly matches Gurobi on Instance 5.

The largest improvement is Instance 3:

```text
v1 gap: 16.6816%
v2 gap: 0.0000%
```

For the large-scale Instance 5:

```text
v1 gap: 6.6649%
v2 gap: 0.0016%
```

## How To Run

Use Python 3.12+.

Run a selected instance by passing the instance id and solver before execution:

```bash
python run_instance.py --instance 1 --solver greedy
python run_instance.py --instance 3 --solver v2
python run_instance.py --instance 5 --solver gurobi
```

Available solver names:

- `greedy`
- `v2`
- `gurobi`

Available instance ids:

- `1`
- `2`
- `3`
- `4`
- `5`

To run the Gurobi MILP comparison for each instance:

```bash
python compare_instance1.py
python compare_instance2.py
python compare_instance3.py
python compare_instance4.py
python compare_instance5.py
```

To compare greedy v1, greedy v2, and Gurobi:

```bash
python compare_v2_summary.py
```

## Gurobi Requirement

`gurobi_inventory.py` requires:

```bash
pip install gurobipy
```

and a valid Gurobi license.

If Gurobi is unavailable, the greedy solvers can still run independently.

## File Guide

| File | Purpose |
|---|---|
| `instances.py` | Central instance registry and sensitivity scenarios |
| `run_instance.py` | CLI runner for choosing instance and solver |
| `benchmark_utils.py` | Shared benchmark and output helpers |
| `greedy_inventory.py` | Original greedy heuristic |
| `greedy_inventory_v2.py` | Improved delay-aware heuristic |
| `gurobi_inventory.py` | Exact Gurobi MILP solver |
| `compare_instance1.py` | Instance 1 benchmark |
| `compare_instance2.py` | Instance 2 benchmark |
| `compare_instance3.py` | Instance 3 benchmark |
| `compare_instance4.py` | Instance 4 sensitivity analysis |
| `compare_instance5.py` | Instance 5 large-scale benchmark |
| `compare_v2_summary.py` | v1 vs v2 vs Gurobi benchmark |
| `results_summary.md` | Original greedy vs Gurobi result summary |
| `v2_results_summary.md` | Improved heuristic result summary |
