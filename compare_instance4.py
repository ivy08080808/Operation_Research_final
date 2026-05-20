from copy import deepcopy
from pprint import pprint
from time import perf_counter

from greedy_inventory import RECIPE, plain_dict, project_ingredient_demand, solve_greedy
from gurobi_inventory import compare_results, solve_gurobi


DISH_DEMAND_4 = {
    "D1 (Tomato-Egg)": {1: 70, 2: 70, 3: 70, 4: 70},
    "D2 (Spinach)": {1: 50, 2: 50, 3: 50, 4: 50},
    "D3 (Chicken)": {1: 60, 2: 60, 3: 60, 4: 60},
}

BASE_PARAMS_4 = {
    "Chicken Leg": {
        "regular_cost": 5.00,
        "discount_cost": 4.50,
        "discount_threshold": 100,
        "shelf_life": 2,
        "holding_cost": 0.300,
        "waste_cost": 1.00,
        "M": 120,
    },
    "Tomato": {
        "regular_cost": 1.00,
        "discount_cost": 0.85,
        "discount_threshold": 60,
        "shelf_life": 1,
        "holding_cost": 0.050,
        "waste_cost": 0.30,
        "M": 70,
    },
    "Egg": {
        "regular_cost": 0.50,
        "discount_cost": 0.44,
        "discount_threshold": 120,
        "shelf_life": 2,
        "holding_cost": 0.040,
        "waste_cost": 0.10,
        "M": 140,
    },
    "Spinach": {
        "regular_cost": 0.80,
        "discount_cost": 0.74,
        "discount_threshold": 90,
        "shelf_life": 1,
        "holding_cost": 0.030,
        "waste_cost": 0.20,
        "M": 100,
    },
}

SCENARIOS = [
    ("S1", "waste_cost", 0.5, 0.50),
    ("S2", "waste_cost", 1.0, 1.00),
    ("S3", "waste_cost", 2.0, 2.00),
    ("S4", "waste_cost", 5.0, 5.00),
    ("S5", "holding_cost", 0.5, 0.15),
    ("S6", "holding_cost", 2.0, 0.60),
    ("S7", "holding_cost", 5.0, 1.50),
    ("S8", "discount_threshold", 0.5, 50),
    ("S9", "discount_threshold", 1.5, 150),
    ("S10", "discount_threshold", 2.0, 200),
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
    return result, {
        "repeats": repeats,
        "min_seconds": min(times),
        "avg_seconds": sum(times) / len(times),
        "max_seconds": max(times),
    }


def scenario_params(field, concrete_value):
    params = deepcopy(BASE_PARAMS_4)
    params["Chicken Leg"][field] = concrete_value
    return params


def discount_count(result, ingredient=None):
    enabled = plain_dict(result["discount_enabled"])
    if ingredient is not None:
        return sum(enabled[ingredient].values())
    return sum(sum(weeks.values()) for weeks in enabled.values())


def compact_plan(result):
    return {
        "regular_purchase": plain_dict(result["regular_purchase"]),
        "discount_purchase": plain_dict(result["discount_purchase"]),
        "discount_enabled": plain_dict(result["discount_enabled"]),
        "waste": plain_dict(result["waste"]),
        "costs": result["costs"],
    }


def run_scenario(name, field, multiplier, concrete_value, ingredient_demand):
    params = scenario_params(field, concrete_value)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, params))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, params))
    comparison = compare_results(greedy_result, gurobi_result)
    return {
        "scenario": name,
        "changed_parameter": f"Chicken Leg.{field}",
        "multiplier": multiplier,
        "concrete_value": concrete_value,
        "greedy_total_cost": comparison["greedy_total_cost"],
        "gurobi_total_cost": comparison["gurobi_total_cost"],
        "absolute_gap": comparison["absolute_gap"],
        "relative_gap_percent": comparison["relative_gap_percent"],
        "greedy_avg_seconds": greedy_timing["avg_seconds"],
        "gurobi_avg_seconds": gurobi_timing["avg_seconds"],
        "speed_ratio_gurobi_over_greedy": (
            gurobi_timing["avg_seconds"] / greedy_timing["avg_seconds"]
            if greedy_timing["avg_seconds"]
            else None
        ),
        "greedy_chicken_discount_weeks": discount_count(greedy_result, "Chicken Leg"),
        "gurobi_chicken_discount_weeks": discount_count(gurobi_result, "Chicken Leg"),
        "greedy_all_discount_weeks": discount_count(greedy_result),
        "gurobi_all_discount_weeks": discount_count(gurobi_result),
        "greedy_timing": greedy_timing,
        "gurobi_timing": gurobi_timing,
        "greedy_result": greedy_result,
        "gurobi_result": gurobi_result,
    }


def public_summary(row):
    return {
        key: row[key]
        for key in [
            "scenario",
            "changed_parameter",
            "multiplier",
            "concrete_value",
            "greedy_total_cost",
            "gurobi_total_cost",
            "absolute_gap",
            "relative_gap_percent",
            "greedy_avg_seconds",
            "gurobi_avg_seconds",
            "speed_ratio_gurobi_over_greedy",
            "greedy_chicken_discount_weeks",
            "gurobi_chicken_discount_weeks",
        ]
    }


def main():
    ingredient_demand = project_ingredient_demand(DISH_DEMAND_4, RECIPE)
    rows = [
        run_scenario(name, field, multiplier, concrete_value, ingredient_demand)
        for name, field, multiplier, concrete_value in SCENARIOS
    ]

    print("Instance 4 ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print("\nSensitivity summary")
    pprint([public_summary(row) for row in rows], sort_dicts=False)
    print("\nBase scenario compact results (S2)")
    base = next(row for row in rows if row["scenario"] == "S2")
    print("\nGreedy")
    pprint(compact_plan(base["greedy_result"]), sort_dicts=False)
    print("\nGurobi")
    pprint(compact_plan(base["gurobi_result"]), sort_dicts=False)


if __name__ == "__main__":
    main()
