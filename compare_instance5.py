from pprint import pprint

from benchmark_utils import benchmark, compact_plan, discount_counts, prepare_instance
from greedy_inventory import solve_greedy
from gurobi_inventory import compare_results, solve_gurobi
from instances import get_instance


def main():
    instance = get_instance("5")
    ingredient_demand, params, weeks = prepare_instance(instance)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, params, weeks))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, params, weeks))

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

    print(f"{instance['name']} ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print("\nGreedy compact result")
    pprint(compact_plan(greedy_result), sort_dicts=False)
    print("\nGurobi compact result")
    pprint(compact_plan(gurobi_result), sort_dicts=False)
    print("\nGreedy vs Gurobi")
    pprint(comparison, sort_dicts=False)


if __name__ == "__main__":
    main()
