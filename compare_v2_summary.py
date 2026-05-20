from pprint import pprint

from benchmark_utils import benchmark, prepare_instance
from greedy_inventory import solve_greedy
from greedy_inventory_v2 import solve_greedy_v2
from gurobi_inventory import solve_gurobi
from instances import get_instance


INSTANCE_IDS = ["1", "2", "3", "4", "5"]


def gap(cost, optimal):
    return {
        "absolute": cost - optimal,
        "percent": ((cost - optimal) / optimal * 100) if optimal else 0,
    }


def main():
    rows = []
    for instance_id in INSTANCE_IDS:
        instance = get_instance(instance_id)
        ingredient_demand, params, weeks = prepare_instance(instance)

        greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, params, weeks))
        v2_result, v2_timing = benchmark(solve_greedy_v2, (ingredient_demand, params, weeks))
        gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, params, weeks))

        optimal_cost = gurobi_result["costs"]["total_cost"]
        greedy_cost = greedy_result["costs"]["total_cost"]
        v2_cost = v2_result["costs"]["total_cost"]
        greedy_gap = gap(greedy_cost, optimal_cost)
        v2_gap = gap(v2_cost, optimal_cost)

        rows.append(
            {
                "instance": instance["name"],
                "greedy_cost": greedy_cost,
                "v2_cost": v2_cost,
                "gurobi_cost": optimal_cost,
                "greedy_gap_percent": greedy_gap["percent"],
                "v2_gap_percent": v2_gap["percent"],
                "greedy_avg_seconds": greedy_timing["avg_seconds"],
                "v2_avg_seconds": v2_timing["avg_seconds"],
                "gurobi_avg_seconds": gurobi_timing["avg_seconds"],
            }
        )

    pprint(rows, sort_dicts=False)


if __name__ == "__main__":
    main()
