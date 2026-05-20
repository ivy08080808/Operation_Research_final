# Greedy v1 vs Greedy v2 vs Gurobi

Greedy v2 keeps the original greedy solver untouched and adds a delay-aware rolling-DP heuristic.
It enumerates meaningful purchase quantities per ingredient-week, including just-in-time regular purchase, discount-threshold purchase, and purchases that cover several future weeks. It then chooses the least-cost local plan over the remaining horizon for that ingredient.

All timings are average wall-clock seconds over 20 repeated runs.

| Instance | Greedy v1 Cost | Greedy v2 Cost | Gurobi Cost | v1 Gap % | v2 Gap % | v1 Avg (s) | v2 Avg (s) | Gurobi Avg (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2282.30 | 2264.05 | 2264.05 | 0.8061% | 0.0000% | 0.0000699 | 0.0003622 | 0.0099403 |
| 2 | 859.50 | 859.50 | 859.50 | 0.0000% | 0.0000% | 0.0000445 | 0.0001143 | 0.0014687 |
| 3 | 1564.00 | 1340.40 | 1340.40 | 16.6816% | 0.0000% | 0.0000611 | 0.0009265 | 0.0147207 |
| 4-S2 | 1778.80 | 1778.80 | 1778.80 | 0.0000% | 0.0000% | 0.0000522 | 0.0003669 | 0.0054443 |
| 5 | 10060.05 | 9431.60 | 9431.45 | 6.6649% | 0.0016% | 0.0000869 | 0.0007792 | 0.0101493 |

## Short Analysis

### What changed

Greedy v1 is myopic: when a discount looks attractive inside the shelf-life window, it tends to buy early and carry inventory forward. This is fast, but it can create excessive holding cost.

Greedy v2 is delay-aware. It considers multiple purchase timings and quantities for each ingredient. This lets it avoid buying in week 1 when week 2 demand can already trigger the discount, which was the main failure mode in Instances 3 and 5.

### Instance 3

The original greedy bought too early and paid high holding cost. Greedy v2 waits for the demand spike weeks, matching Gurobi's cost exactly on this instance.

### Instance 5

The original greedy had high holding cost because it bulk-bought large amounts early. Greedy v2 reduces that behavior and nearly matches Gurobi. The remaining gap is only 0.0016%.

### Runtime tradeoff

Greedy v2 is slower than v1 because it evaluates more candidate actions, but it is still much faster than Gurobi on these instances. On Instance 5, v2 averages about 0.00078 seconds versus Gurobi's 0.01015 seconds.
