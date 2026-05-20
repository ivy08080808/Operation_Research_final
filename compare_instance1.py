from pprint import pprint
from time import perf_counter

from greedy_inventory import DISH_DEMAND, PARAMS, RECIPE, plain_dict, project_ingredient_demand, solve_greedy
from gurobi_inventory import compare_results, solve_gurobi


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
    ingredient_demand = project_ingredient_demand(DISH_DEMAND, RECIPE)
    greedy_result, greedy_timing = benchmark(solve_greedy, (ingredient_demand, PARAMS))
    gurobi_result, gurobi_timing = benchmark(solve_gurobi, (ingredient_demand, PARAMS))

    comparison = compare_results(greedy_result, gurobi_result)
    comparison["greedy_timing"] = greedy_timing
    comparison["gurobi_timing"] = gurobi_timing
    comparison["speed_ratio_gurobi_over_greedy"] = (
        gurobi_timing["avg_seconds"] / greedy_timing["avg_seconds"]
        if greedy_timing["avg_seconds"]
        else None
    )

    print("Instance 1 ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print("\nGreedy compact result")
    pprint(compact_plan(greedy_result), sort_dicts=False)
    print("\nGurobi compact result")
    pprint(compact_plan(gurobi_result), sort_dicts=False)
    print("\nGreedy vs Gurobi")
    pprint(comparison, sort_dicts=False)


if __name__ == "__main__":
    main()
