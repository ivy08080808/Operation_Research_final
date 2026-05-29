import argparse
from pprint import pprint

from benchmark_utils import benchmark, compact_plan, prepare_instance
from excel_instance_loader import DEFAULT_SHEET, DEFAULT_WORKBOOK, list_instance_ids, load_excel_instance
from greedy_inventory_v2 import solve_greedy_v2
from gurobi_inventory import compare_results, solve_gurobi
from instances import INSTANCES, get_instance


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run one Excel long-format instance with heuristic v2, Gurobi, or both."
    )
    parser.add_argument("--workbook", default=DEFAULT_WORKBOOK, help="Path to the .xlsx instance workbook.")
    parser.add_argument("--sheet", default=DEFAULT_SHEET, help="Long-format sheet name.")
    parser.add_argument("--instance-id", help="Excel Instance_ID, e.g. S1_Inst_001.")
    parser.add_argument("--scenario", help="List instance ids in a scenario, e.g. S1.")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run compare mode for all instance ids in the selected scenario.",
    )
    parser.add_argument(
        "--max-instances",
        type=int,
        help="Optional cap for batch runs.",
    )
    parser.add_argument(
        "--legacy-instance",
        choices=sorted(INSTANCES),
        help="Run one of the old built-in demo instances instead of the Excel workbook.",
    )
    parser.add_argument(
        "--solver",
        choices=["v2", "gurobi", "compare"],
        default="compare",
        help="Solver mode. compare runs heuristic v2 and Gurobi and reports the gap.",
    )
    parser.add_argument("--repeats", type=int, default=1, help="Timing repeats.")
    parser.add_argument(
        "--show-inventory",
        action="store_true",
        help="Include age-indexed inventory in printed compact plans.",
    )
    return parser.parse_args()


def load_selected_instance(args):
    if args.legacy_instance:
        return get_instance(args.legacy_instance)
    if not args.instance_id:
        raise ValueError("Use --instance-id for Excel data, or --legacy-instance for old built-in demos.")
    return load_excel_instance(args.workbook, args.sheet, args.instance_id)


def solve_with_timing(solver, ingredient_demand, params, weeks, repeats):
    if repeats > 1:
        return benchmark(solver, (ingredient_demand, params, weeks), repeats=repeats)
    result = solver(ingredient_demand, params, weeks)
    return result, None


def print_timing(label, timing):
    if timing is None:
        return
    print(f"{label} timing")
    pprint(timing, sort_dicts=False)


def run_compare(instance, repeats):
    ingredient_demand, params, weeks = prepare_instance(instance)
    heuristic_result, heuristic_timing = solve_with_timing(
        solve_greedy_v2, ingredient_demand, params, weeks, repeats
    )
    gurobi_result, gurobi_timing = solve_with_timing(
        solve_gurobi, ingredient_demand, params, weeks, repeats
    )
    comparison = compare_results(heuristic_result, gurobi_result)
    return ingredient_demand, heuristic_result, gurobi_result, comparison, heuristic_timing, gurobi_timing


def run_batch(args):
    instance_ids = list_instance_ids(args.workbook, args.sheet, args.scenario)
    if args.max_instances is not None:
        instance_ids = instance_ids[: args.max_instances]

    rows = []
    for instance_id in instance_ids:
        instance = load_excel_instance(args.workbook, args.sheet, instance_id)
        _, _, _, comparison, heuristic_timing, gurobi_timing = run_compare(instance, args.repeats)
        rows.append(
            {
                "instance_id": instance_id,
                "heuristic_cost": comparison["greedy_total_cost"],
                "gurobi_cost": comparison["gurobi_total_cost"],
                "absolute_gap": comparison["absolute_gap"],
                "relative_gap_percent": comparison["relative_gap_percent"],
                "heuristic_avg_seconds": (
                    heuristic_timing["avg_seconds"] if heuristic_timing is not None else None
                ),
                "gurobi_avg_seconds": (
                    gurobi_timing["avg_seconds"] if gurobi_timing is not None else None
                ),
            }
        )

    print(f"Batch comparison for scenario {args.scenario}")
    pprint(rows, sort_dicts=False)
    if rows:
        avg_gap = sum(row["relative_gap_percent"] for row in rows) / len(rows)
        max_gap = max(row["relative_gap_percent"] for row in rows)
        print("\nSummary")
        pprint(
            {
                "instances_compared": len(rows),
                "avg_gap_percent": avg_gap,
                "max_gap_percent": max_gap,
            },
            sort_dicts=False,
        )


def main():
    args = parse_args()

    if args.batch:
        if not args.scenario:
            raise ValueError("--batch requires --scenario.")
        if args.solver != "compare":
            raise ValueError("--batch currently supports --solver compare only.")
        run_batch(args)
        return

    if args.scenario and not args.instance_id:
        print("Available instance ids")
        pprint(list_instance_ids(args.workbook, args.sheet, args.scenario), sort_dicts=False)
        return

    instance = load_selected_instance(args)
    ingredient_demand, params, weeks = prepare_instance(instance)

    print(f"Instance: {instance.get('instance_id', instance['name'])}")
    if "scenario_id" in instance:
        print(f"Scenario: {instance['scenario_id']} - {instance['scenario_name']}")
    print("Ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)

    if args.solver == "v2":
        result, timing = solve_with_timing(solve_greedy_v2, ingredient_demand, params, weeks, args.repeats)
        print("\nHeuristic v2 result")
        pprint(compact_plan(result, include_inventory=args.show_inventory), sort_dicts=False)
        print_timing("\nHeuristic v2", timing)
        return

    if args.solver == "gurobi":
        result, timing = solve_with_timing(solve_gurobi, ingredient_demand, params, weeks, args.repeats)
        print("\nGurobi result")
        pprint(compact_plan(result, include_inventory=args.show_inventory), sort_dicts=False)
        print_timing("\nGurobi", timing)
        return

    _, heuristic_result, gurobi_result, comparison, heuristic_timing, gurobi_timing = run_compare(
        instance, args.repeats
    )

    print("\nHeuristic v2 compact result")
    pprint(compact_plan(heuristic_result, include_inventory=args.show_inventory), sort_dicts=False)
    print("\nGurobi compact result")
    pprint(compact_plan(gurobi_result, include_inventory=args.show_inventory), sort_dicts=False)
    print("\nHeuristic v2 vs Gurobi")
    pprint(comparison, sort_dicts=False)
    print_timing("\nHeuristic v2", heuristic_timing)
    print_timing("\nGurobi", gurobi_timing)


if __name__ == "__main__":
    main()
