import argparse
from pprint import pprint

from benchmark_utils import compact_plan, prepare_instance
from greedy_inventory import solve_greedy
from greedy_inventory_v2 import solve_greedy_v2
from gurobi_inventory import solve_gurobi
from instances import INSTANCES, get_instance


SOLVERS = {
    "greedy": solve_greedy,
    "v2": solve_greedy_v2,
    "gurobi": solve_gurobi,
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run an inventory solver on a selected instance.")
    parser.add_argument(
        "--instance",
        choices=sorted(INSTANCES),
        required=True,
        help="Instance id to solve.",
    )
    parser.add_argument(
        "--solver",
        choices=sorted(SOLVERS),
        required=True,
        help="Solver to run.",
    )
    parser.add_argument(
        "--show-inventory",
        action="store_true",
        help="Include age-indexed inventory in the printed compact plan.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    instance = get_instance(args.instance)
    ingredient_demand, params, weeks = prepare_instance(instance)
    result = SOLVERS[args.solver](ingredient_demand, params, weeks)

    print(f"{instance['name']} ingredient demand")
    pprint(ingredient_demand, sort_dicts=False)
    print(f"\n{args.solver} result")
    pprint(compact_plan(result, include_inventory=args.show_inventory), sort_dicts=False)


if __name__ == "__main__":
    main()
