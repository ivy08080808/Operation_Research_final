from pprint import pprint
from time import perf_counter

from greedy_inventory import RECIPE, WEEKS, plain_dict, project_ingredient_demand, solve_greedy
from gurobi_inventory import compare_results, solve_gurobi


DISH_DEMAND_2 = {
    "D1 (Tomato-Egg)": {1: 40, 2: 35, 3: 30, 4: 40},
    "D2 (Spinach)": {1: 30, 2: 25, 3: 35, 4: 30},
    "D3 (Chicken)": {1: 20, 2: 25, 3: 20, 4: 25},
}

PARAMS_2 = {
    "Chicken Leg": {
        "regular_cost": 5.00,
        "discount_cost": 4.50,
        "discount_threshold": 200,
        "shelf_life": 1,
        "holding_cost": 0.200,
        "waste_cost": 2.50,
        "M": 25,
    },
    "Tomato": {
        "regular_cost": 1.00,
        "discount_cost": 0.85,
        "discount_threshold": 200,
        "shelf_life": 1,
        "holding_cost": 0.050,
        "waste_cost": 0.80,
        "M": 40,
    },
    "Egg": {
        "regular_cost": 0.50,
        "discount_cost": 0.44,
        "discount_threshold": 200,
        "shelf_life": 1,
        "holding_cost": 0.020,
        "waste_cost": 0.40,
        "M": 40,
    },
    "Spinach": {
        "regular_cost": 0.80,
        "discount_cost": 0.74,
        "discount_threshold": 200,
        "shelf_life": 1,
        "holding_cost": 0.030,
        "waste_cost": 0.70,
        "M": 70,
    },
}


def timed(callable_, *args, **kwargs):
    start = perf_counter()
    result = callable_(*args, **kwargs)
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
        "waste": plain_dict(result["waste"]),
        "costs": result["costs"],
    }


def main():
    ingredient_demand = project_ingredient_demand(DISH_DEMAND_2, RECIPE)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, PARAMS_2))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, PARAMS_2))

    comparison = compare_results(greedy_result, gurobi_result)
    comparison["greedy_timing"] = greedy_timing
    comparison["gurobi_timing"] = gurobi_timing
    comparison["speed_ratio_gurobi_over_greedy"] = (
        gurobi_timing["avg_seconds"] / greedy_timing["avg_seconds"]
        if greedy_timing["avg_seconds"]
        else None
    )

    print("Instance 2 ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print("\nGreedy compact result")
    pprint(compact_plan(greedy_result), sort_dicts=False)
    print("\nGurobi compact result")
    pprint(compact_plan(gurobi_result), sort_dicts=False)
    print("\nGreedy vs Gurobi")
    pprint(comparison, sort_dicts=False)


if __name__ == "__main__":
    main()
