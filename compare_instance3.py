from pprint import pprint
from time import perf_counter

from greedy_inventory import RECIPE, plain_dict, project_ingredient_demand, solve_greedy
from gurobi_inventory import compare_results, solve_gurobi


DISH_DEMAND_3 = {
    "D1 (Tomato-Egg)": {1: 20, 2: 120, 3: 20, 4: 120},
    "D2 (Spinach)": {1: 10, 2: 80, 3: 10, 4: 80},
    "D3 (Chicken)": {1: 15, 2: 90, 3: 15, 4: 90},
}

PARAMS_3 = {
    "Chicken Leg": {
        "regular_cost": 5.00,
        "discount_cost": 3.50,
        "discount_threshold": 100,
        "shelf_life": 3,
        "holding_cost": 0.600,
        "waste_cost": 0.50,
        "M": 195,
    },
    "Tomato": {
        "regular_cost": 1.00,
        "discount_cost": 0.70,
        "discount_threshold": 100,
        "shelf_life": 2,
        "holding_cost": 0.200,
        "waste_cost": 0.15,
        "M": 140,
    },
    "Egg": {
        "regular_cost": 0.50,
        "discount_cost": 0.35,
        "discount_threshold": 150,
        "shelf_life": 3,
        "holding_cost": 0.080,
        "waste_cost": 0.05,
        "M": 260,
    },
    "Spinach": {
        "regular_cost": 0.80,
        "discount_cost": 0.55,
        "discount_threshold": 100,
        "shelf_life": 2,
        "holding_cost": 0.160,
        "waste_cost": 0.10,
        "M": 180,
    },
}


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
    return result, {
        "repeats": repeats,
        "min_seconds": min(times),
        "avg_seconds": sum(times) / len(times),
        "max_seconds": max(times),
    }


def compact_plan(result):
    return {
        "regular_purchase": plain_dict(result["regular_purchase"]),
        "discount_purchase": plain_dict(result["discount_purchase"]),
        "discount_enabled": plain_dict(result["discount_enabled"]),
        "inventory": plain_dict(result["inventory"]),
        "waste": plain_dict(result["waste"]),
        "costs": result["costs"],
    }


def main():
    ingredient_demand = project_ingredient_demand(DISH_DEMAND_3, RECIPE)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, PARAMS_3))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, PARAMS_3))

    comparison = compare_results(greedy_result, gurobi_result)
    comparison["greedy_timing"] = greedy_timing
    comparison["gurobi_timing"] = gurobi_timing
    comparison["speed_ratio_gurobi_over_greedy"] = (
        gurobi_timing["avg_seconds"] / greedy_timing["avg_seconds"]
        if greedy_timing["avg_seconds"]
        else None
    )

    print("Instance 3 ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print("\nGreedy compact result")
    pprint(compact_plan(greedy_result), sort_dicts=False)
    print("\nGurobi compact result")
    pprint(compact_plan(gurobi_result), sort_dicts=False)
    print("\nGreedy vs Gurobi")
    pprint(comparison, sort_dicts=False)


if __name__ == "__main__":
    main()
