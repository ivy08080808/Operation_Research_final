# Inventory Solver Comparison Summary

All timings are average wall-clock seconds over 20 repeated runs on the same machine.

## Main Instance Comparison

| Instance | Theme | Greedy Cost | Gurobi Cost | Abs. Gap | Gap % | Greedy Avg (s) | Gurobi Avg (s) | Gurobi / Greedy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Base case | 2282.30 | 2264.05 | 18.25 | 0.8061% | 0.0001374 | 0.0118142 | 85.96x |
| 2 | No discount | 859.50 | 859.50 | 0.00 | 0.0000% | 0.0000511 | 0.0017469 | 34.17x |
| 3 | Carryover | 1564.00 | 1340.40 | 223.60 | 16.6816% | 0.0000604 | 0.0184050 | 304.57x |
| 4-S2 | Sensitivity base | 1778.80 | 1778.80 | 0.00 | 0.0000% | 0.0000568 | 0.0071271 | 125.44x |
| 5 | Large scale | 10060.05 | 9431.45 | 628.60 | 6.6649% | 0.0000937 | 0.0156487 | 167.08x |

## Instance 4 Sensitivity Summary

| Scenario | Changed Chicken Leg Parameter | Greedy Cost | Gurobi Cost | Gap % | Greedy Avg (s) | Gurobi Avg (s) | Chicken Discount Weeks: Greedy / Gurobi |
|---|---:|---:|---:|---:|---:|---:|---:|
| S1 | waste_cost = 0.50 | 1778.80 | 1778.80 | 0.0000% | 0.0000561 | 0.0079530 | 2 / 2 |
| S2 | waste_cost = 1.00 | 1778.80 | 1778.80 | 0.0000% | 0.0000568 | 0.0071271 | 2 / 2 |
| S3 | waste_cost = 2.00 | 1778.80 | 1778.80 | 0.0000% | 0.0001131 | 0.0064607 | 2 / 2 |
| S4 | waste_cost = 5.00 | 1778.80 | 1778.80 | 0.0000% | 0.0000572 | 0.0056368 | 2 / 2 |
| S5 | holding_cost = 0.15 | 1760.80 | 1760.80 | 0.0000% | 0.0000539 | 0.0053103 | 2 / 2 |
| S6 | holding_cost = 0.60 | 1814.80 | 1810.80 | 0.2209% | 0.0000870 | 0.0054333 | 2 / 2 |
| S7 | holding_cost = 1.50 | 1862.80 | 1862.80 | 0.0000% | 0.0000574 | 0.0050772 | 0 / 0 |
| S8 | threshold = 50 | 1796.80 | 1742.80 | 3.0985% | 0.0000853 | 0.0048534 | 3 / 4 |
| S9 | threshold = 150 | 1862.80 | 1862.80 | 0.0000% | 0.0000584 | 0.0039404 | 0 / 0 |
| S10 | threshold = 200 | 1862.80 | 1862.80 | 0.0000% | 0.0000778 | 0.0037602 | 0 / 0 |

## Per-instance Notes

### Instance 1: Base Case

Greedy is very close to optimal, with only a 0.8061% gap. It captures most discount and carryover opportunities, but misses a better timing choice for Chicken Leg and a small Tomato threshold-overbuy opportunity that Gurobi uses.

### Instance 2: No Discount

Both methods return the same solution. Since every ingredient has shelf life 1 and every discount threshold is unreachable, the problem collapses into just-in-time regular purchasing.

### Instance 3: Carryover

Greedy performs poorly relative to the other cases. It bulk-buys too early and pays high holding cost. Gurobi shows that many ingredients should instead be bought in the spike week itself because the spike demand already reaches the discount threshold.

### Instance 4: Sensitivity

The flat demand makes greedy mostly optimal because there are fewer timing tradeoffs. The main exception is S8, where a low Chicken Leg threshold allows Gurobi to trigger discount in all four weeks, while greedy triggers it only three times.

### Instance 5: Large Scale

Greedy remains extremely fast but has a 6.6649% gap. It avoids waste but accumulates excessive holding cost. Gurobi accepts small waste on some ingredients and sharply reduces holding cost, producing a better total cost.
