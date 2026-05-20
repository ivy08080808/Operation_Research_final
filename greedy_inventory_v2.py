from collections import defaultdict
from functools import lru_cache

from greedy_inventory import plain_dict


def clean_number(value, tolerance=1e-7):
    if abs(value) < tolerance:
        return 0
    rounded = round(value)
    if abs(value - rounded) < tolerance:
        return int(rounded)
    return value


def simulate_week(start_inventory, demand, regular_qty, discount_qty, params):
    shelf_life = params["shelf_life"]
    inventory = dict(start_inventory)
    inventory[1] += regular_qty + discount_qty

    use = {}
    remaining_demand = demand
    for age in range(shelf_life, 0, -1):
        used = min(inventory[age], remaining_demand)
        inventory[age] -= used
        remaining_demand -= used
        use[age] = used

    if remaining_demand:
        return None

    waste = inventory[shelf_life]
    inventory[shelf_life] = 0
    holding_cost = sum(inventory.values()) * params["holding_cost"]
    waste_cost = waste * params["waste_cost"]
    purchase_cost = (
        regular_qty * params["regular_cost"]
        + discount_qty * params["discount_cost"]
    )

    end_inventory = dict(inventory)
    next_inventory = {
        age + 1: inventory[age]
        for age in range(1, shelf_life)
    }
    next_inventory[1] = 0

    return {
        "use": use,
        "waste": waste,
        "end_inventory": end_inventory,
        "next_inventory": next_inventory,
        "purchase_cost": purchase_cost,
        "holding_cost": holding_cost,
        "waste_cost": waste_cost,
        "total_cost": purchase_cost + holding_cost + waste_cost,
    }


def action_candidates(t_index, weeks, weekly_demand, start_inventory, params):
    t = weeks[t_index]
    shelf_life = params["shelf_life"]
    threshold = params["discount_threshold"]
    big_m = params["M"]
    demand_now = weekly_demand[t]
    available = sum(start_inventory.values())
    residual_now = max(0, demand_now - available)

    actions = {(residual_now, 0)}
    if threshold > big_m:
        return sorted(actions)

    future_weeks = weeks[t_index : min(len(weeks), t_index + shelf_life)]
    for end_offset in range(1, len(future_weeks) + 1):
        needed = max(
            0,
            sum(weekly_demand[week] for week in future_weeks[:end_offset]) - available,
        )
        for discount_qty in {threshold, needed, max(threshold, needed), min(big_m, max(threshold, needed))}:
            if threshold <= discount_qty <= big_m:
                regular_qty = max(0, residual_now - discount_qty)
                actions.add((regular_qty, discount_qty))

    return sorted(actions)


def solve_ingredient_v2(ingredient, weekly_demand, params):
    weeks = sorted(weekly_demand)
    shelf_life = params["shelf_life"]
    zero_inventory = tuple(0 for _ in range(shelf_life))

    @lru_cache(maxsize=None)
    def best_from(t_index, inventory_tuple):
        if t_index == len(weeks):
            terminal_waste_cost = sum(inventory_tuple) * params["waste_cost"]
            return terminal_waste_cost, []

        start_inventory = {
            age: inventory_tuple[age - 1]
            for age in range(1, shelf_life + 1)
        }
        best_cost = float("inf")
        best_plan = None

        for regular_qty, discount_qty in action_candidates(
            t_index, weeks, weekly_demand, start_inventory, params
        ):
            simulated = simulate_week(
                start_inventory,
                weekly_demand[weeks[t_index]],
                regular_qty,
                discount_qty,
                params,
            )
            if simulated is None:
                continue

            next_tuple = tuple(
                simulated["next_inventory"][age]
                for age in range(1, shelf_life + 1)
            )
            future_cost, future_plan = best_from(t_index + 1, next_tuple)
            total_cost = simulated["total_cost"] + future_cost
            if total_cost < best_cost:
                best_cost = total_cost
                best_plan = [
                    {
                        "week": weeks[t_index],
                        "regular_qty": regular_qty,
                        "discount_qty": discount_qty,
                        "simulated": simulated,
                    }
                ] + future_plan

        return best_cost, best_plan

    _, plan = best_from(0, zero_inventory)
    return plan


def solve_greedy_v2(ingredient_demand, params, weeks=None):
    result = {
        "regular_purchase": defaultdict(dict),
        "discount_purchase": defaultdict(dict),
        "discount_enabled": defaultdict(dict),
        "purchase": defaultdict(dict),
        "inventory": defaultdict(lambda: defaultdict(dict)),
        "use": defaultdict(lambda: defaultdict(lambda: defaultdict(float))),
        "waste": defaultdict(dict),
        "costs": {
            "purchase_cost": 0,
            "holding_cost_total": 0,
            "waste_cost_total": 0,
            "total_cost": 0,
        },
    }

    for ingredient, weekly_demand in ingredient_demand.items():
        if weeks is not None:
            weekly_demand = {week: weekly_demand[week] for week in weeks}
        plan = solve_ingredient_v2(ingredient, weekly_demand, params[ingredient])
        for step in plan:
            t = step["week"]
            regular_qty = step["regular_qty"]
            discount_qty = step["discount_qty"]
            simulated = step["simulated"]

            result["regular_purchase"][ingredient][t] = clean_number(regular_qty)
            result["discount_purchase"][ingredient][t] = clean_number(discount_qty)
            result["discount_enabled"][ingredient][t] = int(discount_qty > 0)
            result["purchase"][ingredient][t] = clean_number(regular_qty + discount_qty)
            result["waste"][ingredient][t] = clean_number(simulated["waste"])

            for age, value in simulated["use"].items():
                result["use"][ingredient][t][age] = clean_number(value)
            for age, value in simulated["end_inventory"].items():
                result["inventory"][ingredient][t][age] = clean_number(value)

            result["costs"]["purchase_cost"] += simulated["purchase_cost"]
            result["costs"]["holding_cost_total"] += simulated["holding_cost"]
            result["costs"]["waste_cost_total"] += simulated["waste_cost"]

    result["costs"] = {
        key: clean_number(value)
        for key, value in result["costs"].items()
    }
    result["costs"]["total_cost"] = clean_number(
        result["costs"]["purchase_cost"]
        + result["costs"]["holding_cost_total"]
        + result["costs"]["waste_cost_total"]
    )
    return result
