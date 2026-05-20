from pprint import pprint
from time import perf_counter

from greedy_inventory import (
    DISH_DEMAND,
    PARAMS,
    RECIPE,
    project_ingredient_demand,
    solve_greedy,
)
from greedy_inventory_v2 import solve_greedy_v2
from gurobi_inventory import solve_gurobi

from compare_instance2 import DISH_DEMAND_2, PARAMS_2
from compare_instance3 import DISH_DEMAND_3, PARAMS_3
from compare_instance4 import BASE_PARAMS_4, DISH_DEMAND_4
from compare_instance5 import DISH_DEMAND_5, PARAMS_5, RECIPE_5


INSTANCES = [
    ("1", DISH_DEMAND, RECIPE, PARAMS),
    ("2", DISH_DEMAND_2, RECIPE, PARAMS_2),
    ("3", DISH_DEMAND_3, RECIPE, PARAMS_3),
    ("4-S2", DISH_DEMAND_4, RECIPE, BASE_PARAMS_4),
    ("5", DISH_DEMAND_5, RECIPE_5, PARAMS_5),
]


def timed(callable_, *args):
    start = perf_counter()
    result = callable_(*args)
    elapsed = perf_counter() - start
    return result, elapsed


def benchmark(callable_, args, repeats=20):
    times = []
    result = None
    for _ in range(repeats):
        result, elapsed = timed(callable_, *args)
        times.append(elapsed)
    return result, sum(times) / len(times)


def gap(cost, optimal):
    return {
        "absolute": cost - optimal,
        "percent": ((cost - optimal) / optimal * 100) if optimal else 0,
    }


def main():
    rows = []
    for name, dish_demand, recipe, params in INSTANCES:
        ingredient_demand = project_ingredient_demand(dish_demand, recipe)

        greedy_result, greedy_seconds = benchmark(solve_greedy, (ingredient_demand, params))
        v2_result, v2_seconds = benchmark(solve_greedy_v2, (ingredient_demand, params))
        gurobi_result, gurobi_seconds = benchmark(solve_gurobi, (ingredient_demand, params))

        optimal_cost = gurobi_result["costs"]["total_cost"]
        greedy_cost = greedy_result["costs"]["total_cost"]
        v2_cost = v2_result["costs"]["total_cost"]
        greedy_gap = gap(greedy_cost, optimal_cost)
        v2_gap = gap(v2_cost, optimal_cost)

        rows.append(
            {
                "instance": name,
                "greedy_cost": greedy_cost,
                "v2_cost": v2_cost,
                "gurobi_cost": optimal_cost,
                "greedy_gap_percent": greedy_gap["percent"],
                "v2_gap_percent": v2_gap["percent"],
                "greedy_avg_seconds": greedy_seconds,
                "v2_avg_seconds": v2_seconds,
                "gurobi_avg_seconds": gurobi_seconds,
            }
        )

    pprint(rows, sort_dicts=False)


if __name__ == "__main__":
    main()
