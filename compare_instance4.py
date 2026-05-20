from pprint import pprint

from benchmark_utils import benchmark, compact_plan, discount_count, prepare_instance
from greedy_inventory import solve_greedy
from gurobi_inventory import compare_results, solve_gurobi
from instances import SENSITIVITY_SCENARIOS, get_instance, make_instance4_scenario


def run_scenario(name, field, multiplier, concrete_value):
    instance = make_instance4_scenario(field, concrete_value)
    ingredient_demand, params, weeks = prepare_instance(instance)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, params, weeks))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, params, weeks))
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
        "greedy_result": greedy_result,
        "gurobi_result": gurobi_result,
    }


def public_summary(row):
    keys = [
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
    return {key: row[key] for key in keys}


def main():
    base_instance = get_instance("4")
    ingredient_demand, _, _ = prepare_instance(base_instance)
    rows = [
        run_scenario(name, field, multiplier, concrete_value)
        for name, field, multiplier, concrete_value in SENSITIVITY_SCENARIOS
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
