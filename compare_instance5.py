from pprint import pprint
from time import perf_counter

from greedy_inventory import plain_dict, project_ingredient_demand, solve_greedy
from gurobi_inventory import compare_results, solve_gurobi


DISH_DEMAND_5 = {
    "D1 (Salad)": {1: 80, 2: 95, 3: 70, 4: 110},
    "D2 (Stir-fry)": {1: 70, 2: 80, 3: 90, 4: 85},
    "D3 (Roast)": {1: 60, 2: 75, 3: 65, 4: 80},
    "D4 (Soup)": {1: 55, 2: 60, 3: 70, 4: 65},
    "D5 (Sandwich)": {1: 90, 2: 85, 3: 95, 4: 100},
    "D6 (Bowl)": {1: 75, 2: 80, 3: 85, 4: 90},
}

RECIPE_5 = {
    "D1 (Salad)": {
        "Chicken": 0,
        "Beef": 0,
        "Tomato": 2,
        "Spinach": 1,
        "Egg": 1,
        "Rice": 0,
    },
    "D2 (Stir-fry)": {
        "Chicken": 1,
        "Beef": 0,
        "Tomato": 0,
        "Spinach": 2,
        "Egg": 0,
        "Rice": 1,
    },
    "D3 (Roast)": {
        "Chicken": 0,
        "Beef": 1,
        "Tomato": 1,
        "Spinach": 0,
        "Egg": 0,
        "Rice": 0,
    },
    "D4 (Soup)": {
        "Chicken": 1,
        "Beef": 0,
        "Tomato": 1,
        "Spinach": 1,
        "Egg": 0,
        "Rice": 0,
    },
    "D5 (Sandwich)": {
        "Chicken": 0,
        "Beef": 1,
        "Tomato": 0,
        "Spinach": 0,
        "Egg": 1,
        "Rice": 0,
    },
    "D6 (Bowl)": {
        "Chicken": 1,
        "Beef": 0,
        "Tomato": 0,
        "Spinach": 0,
        "Egg": 1,
        "Rice": 2,
    },
}

PARAMS_5 = {
    "Chicken": {
        "regular_cost": 4.50,
        "discount_cost": 3.85,
        "discount_threshold": 200,
        "shelf_life": 2,
        "holding_cost": 0.400,
        "waste_cost": 1.20,
        "M": 485,
    },
    "Beef": {
        "regular_cost": 6.00,
        "discount_cost": 5.10,
        "discount_threshold": 150,
        "shelf_life": 2,
        "holding_cost": 0.500,
        "waste_cost": 1.80,
        "M": 340,
    },
    "Tomato": {
        "regular_cost": 1.00,
        "discount_cost": 0.82,
        "discount_threshold": 300,
        "shelf_life": 1,
        "holding_cost": 0.040,
        "waste_cost": 0.25,
        "M": 365,
    },
    "Spinach": {
        "regular_cost": 0.80,
        "discount_cost": 0.66,
        "discount_threshold": 280,
        "shelf_life": 1,
        "holding_cost": 0.030,
        "waste_cost": 0.18,
        "M": 345,
    },
    "Egg": {
        "regular_cost": 0.50,
        "discount_cost": 0.42,
        "discount_threshold": 400,
        "shelf_life": 2,
        "holding_cost": 0.050,
        "waste_cost": 0.08,
        "M": 550,
    },
    "Rice": {
        "regular_cost": 0.30,
        "discount_cost": 0.24,
        "discount_threshold": 500,
        "shelf_life": 3,
        "holding_cost": 0.030,
        "waste_cost": 0.05,
        "M": 765,
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


def discount_counts(result):
    enabled = plain_dict(result["discount_enabled"])
    return {
        ingredient: sum(weeks.values())
        for ingredient, weeks in enabled.items()
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
    ingredient_demand = project_ingredient_demand(DISH_DEMAND_5, RECIPE_5)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, PARAMS_5))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, PARAMS_5))

    comparison = compare_results(greedy_result, gurobi_result)
    comparison["greedy_timing"] = greedy_timing
    comparison["gurobi_timing"] = gurobi_timing
    comparison["speed_ratio_gurobi_over_greedy"] = (
        gurobi_timing["avg_seconds"] / greedy_timing["avg_seconds"]
        if greedy_timing["avg_seconds"]
        else None
    )
    comparison["greedy_discount_weeks"] = discount_counts(greedy_result)
    comparison["gurobi_discount_weeks"] = discount_counts(gurobi_result)

    print("Instance 5 ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print("\nGreedy compact result")
    pprint(compact_plan(greedy_result), sort_dicts=False)
    print("\nGurobi compact result")
    pprint(compact_plan(gurobi_result), sort_dicts=False)
    print("\nGreedy vs Gurobi")
    pprint(comparison, sort_dicts=False)


if __name__ == "__main__":
    main()
