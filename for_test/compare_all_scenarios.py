import argparse
import csv
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from benchmark_utils import prepare_instance
from excel_instance_loader import DEFAULT_SHEET, DEFAULT_WORKBOOK, load_excel_instances
from heuristic_v2 import solve_greedy_v2
from heuristic_baseline import solve_heuristic_baseline
from gurobi_inventory import compare_results, solve_gurobi


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare heuristic v2 and Gurobi across every scenario in Long_Format_Instances."
    )
    parser.add_argument("--workbook", default=DEFAULT_WORKBOOK, help="Path to instances_corrected.xlsx.")
    parser.add_argument("--sheet", default=DEFAULT_SHEET, help="Long-format sheet name.")
    parser.add_argument("--scenario", help="Optional single Scenario_ID, e.g. S1.")
    parser.add_argument(
        "--max-instances-per-scenario",
        type=int,
        help="Optional cap for quick smoke tests.",
    )
    parser.add_argument(
        "--csv-output",
        help="Optional CSV path for per-scenario summary output.",
    )
    parser.add_argument(
        "--detail-csv-output",
        help="Optional CSV path for per-instance detail output.",
    )
    return parser.parse_args()


def timed_solve(solver, ingredient_demand, params, weeks):
    start = perf_counter()
    result = solver(ingredient_demand, params, weeks)
    return result, perf_counter() - start


def evaluate_instance(instance):
    ingredient_demand, params, weeks = prepare_instance(instance)
    baseline_result, baseline_seconds = timed_solve(
        solve_heuristic_baseline, ingredient_demand, params, weeks
    )
    heuristic_result, heuristic_seconds = timed_solve(
        solve_greedy_v2, ingredient_demand, params, weeks
    )
    gurobi_result, gurobi_seconds = timed_solve(solve_gurobi, ingredient_demand, params, weeks)
    baseline_comparison = compare_results(baseline_result, gurobi_result)
    comparison = compare_results(heuristic_result, gurobi_result)
    if abs(baseline_comparison["absolute_gap"]) < 1e-6:
        baseline_comparison["absolute_gap"] = 0.0
        baseline_comparison["relative_gap_percent"] = 0.0
    if abs(comparison["absolute_gap"]) < 1e-6:
        comparison["absolute_gap"] = 0.0
        comparison["relative_gap_percent"] = 0.0

    return {
        "scenario_id": instance["scenario_id"],
        "scenario_name": instance["scenario_name"],
        "instance_id": instance["instance_id"],
        "num_ingredients": len(ingredient_demand),
        "baseline_cost": baseline_comparison["greedy_total_cost"],
        "baseline_gap": baseline_comparison["absolute_gap"],
        "baseline_gap_percent": baseline_comparison["relative_gap_percent"],
        "heuristic_cost": comparison["greedy_total_cost"],
        "gurobi_cost": comparison["gurobi_total_cost"],
        "absolute_gap": comparison["absolute_gap"],
        "relative_gap_percent": comparison["relative_gap_percent"],
        "baseline_seconds": baseline_seconds,
        "heuristic_seconds": heuristic_seconds,
        "gurobi_seconds": gurobi_seconds,
    }


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["scenario_id"], row["scenario_name"])].append(row)

    summary = []
    for (scenario_id, scenario_name), scenario_rows in grouped.items():
        count = len(scenario_rows)
        avg = lambda key: sum(row[key] for row in scenario_rows) / count
        max_gap_row = max(scenario_rows, key=lambda row: row["relative_gap_percent"])
        summary.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "instances": count,
                "avg_heuristic_cost": avg("heuristic_cost"),
                "avg_gurobi_cost": avg("gurobi_cost"),
                "avg_absolute_gap": avg("absolute_gap"),
                "avg_gap_percent": avg("relative_gap_percent"),
                "max_gap_percent": max_gap_row["relative_gap_percent"],
                "max_gap_instance": max_gap_row["instance_id"],
                "avg_heuristic_seconds": avg("heuristic_seconds"),
                "avg_gurobi_seconds": avg("gurobi_seconds"),
                "speed_ratio_gurobi_over_heuristic": (
                    avg("gurobi_seconds") / avg("heuristic_seconds")
                    if avg("heuristic_seconds")
                    else None
                ),
            }
        )

    return sorted(summary, key=lambda row: int(row["scenario_id"].replace("S", "")))


def format_number(value, decimals=4):
    if value is None:
        return ""
    return f"{value:.{decimals}f}"


def print_markdown_table(summary):
    headers = [
        "Scenario",
        "Name",
        "N",
        "Avg Heuristic",
        "Avg Gurobi",
        "Avg Gap %",
        "Max Gap %",
        "Max Gap Inst",
        "Heur Avg s",
        "Gurobi Avg s",
        "Speed Ratio",
    ]
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for row in summary:
        values = [
            row["scenario_id"],
            row["scenario_name"],
            str(row["instances"]),
            format_number(row["avg_heuristic_cost"], 2),
            format_number(row["avg_gurobi_cost"], 2),
            format_number(row["avg_gap_percent"], 4),
            format_number(row["max_gap_percent"], 4),
            row["max_gap_instance"],
            format_number(row["avg_heuristic_seconds"], 6),
            format_number(row["avg_gurobi_seconds"], 6),
            format_number(row["speed_ratio_gurobi_over_heuristic"], 2),
        ]
        print("| " + " | ".join(values) + " |")


def write_csv(path, rows):
    if not rows:
        return
    output_path = Path(path)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    instances = load_excel_instances(args.workbook, args.sheet, args.scenario)

    if args.max_instances_per_scenario is not None:
        capped = []
        seen = defaultdict(int)
        for instance in instances:
            scenario_id = instance["scenario_id"]
            if seen[scenario_id] < args.max_instances_per_scenario:
                capped.append(instance)
                seen[scenario_id] += 1
        instances = capped

    detail_rows = []
    for index, instance in enumerate(instances, start=1):
        print(f"[{index}/{len(instances)}] {instance['instance_id']}", flush=True)
        detail_rows.append(evaluate_instance(instance))

    summary = summarize(detail_rows)
    print("\nScenario summary")
    print_markdown_table(summary)

    if args.csv_output:
        write_csv(args.csv_output, summary)
    if args.detail_csv_output:
        write_csv(args.detail_csv_output, detail_rows)


if __name__ == "__main__":
    main()
