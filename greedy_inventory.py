from collections import defaultdict


def project_ingredient_demand(dish_demand, recipe):
    ingredients = sorted({i for dish in recipe.values() for i in dish})
    weeks = sorted(next(iter(dish_demand.values())))
    projected = {i: {t: 0 for t in weeks} for i in ingredients}
    for dish, weekly_demand in dish_demand.items():
        for t, servings in weekly_demand.items():
            for ingredient, units in recipe[dish].items():
                projected[ingredient][t] += servings * units
    return projected


def holding_cost_for_plan(quantity, weekly_need, holding_cost):
    remaining = quantity
    holding = 0
    for offset, demand in enumerate(weekly_need):
        used = min(remaining, demand)
        remaining -= used
        if offset < len(weekly_need) - 1:
            holding += remaining * holding_cost
    return holding


def should_discount(quantity, weekly_need, params):
    if quantity < params["discount_threshold"]:
        return False
    regular = sum(weekly_need) * params["regular_cost"]
    discount = quantity * params["discount_cost"]
    discount += holding_cost_for_plan(quantity, weekly_need, params["holding_cost"])
    leftover = max(0, quantity - sum(weekly_need))
    discount += leftover * params["waste_cost"]
    return discount < regular


def solve_greedy(ingredient_demand, params, weeks=None):
    weeks = sorted(next(iter(ingredient_demand.values()))) if weeks is None else list(weeks)
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
        p = params[ingredient]
        shelf_life = p["shelf_life"]
        inventory = {age: 0 for age in range(1, shelf_life + 1)}

        for t in weeks:
            demand = weekly_demand[t]

            # Buy before serving this week. Discount candidates look ahead only as
            # far as the ingredient can survive.
            available_old = sum(inventory.values())
            residual_now = max(0, demand - available_old)
            future_weeks = [week for week in weeks if t <= week < t + shelf_life]
            uncovered_window = max(
                0,
                sum(weekly_demand[week] for week in future_weeks) - available_old,
            )

            discount_qty = min(p["M"], uncovered_window)
            use_discount = should_discount(
                discount_qty,
                [weekly_demand[week] for week in future_weeks],
                p,
            )

            regular_qty = 0 if use_discount else residual_now
            discount_qty = discount_qty if use_discount else 0
            inventory[1] += regular_qty + discount_qty

            result["regular_purchase"][ingredient][t] = regular_qty
            result["discount_purchase"][ingredient][t] = discount_qty
            result["discount_enabled"][ingredient][t] = int(use_discount)
            result["purchase"][ingredient][t] = regular_qty + discount_qty

            result["costs"]["purchase_cost"] += regular_qty * p["regular_cost"]
            result["costs"]["purchase_cost"] += discount_qty * p["discount_cost"]

            remaining_demand = demand
            for age in range(shelf_life, 0, -1):
                used = min(inventory[age], remaining_demand)
                inventory[age] -= used
                remaining_demand -= used
                result["use"][ingredient][t][age] = used

            if remaining_demand:
                raise ValueError(f"Unmet demand for {ingredient} in week {t}: {remaining_demand}")

            expired = inventory[shelf_life]
            result["waste"][ingredient][t] = expired
            result["costs"]["waste_cost_total"] += expired * p["waste_cost"]
            inventory[shelf_life] = 0

            for age in range(1, shelf_life + 1):
                result["inventory"][ingredient][t][age] = inventory[age]
                result["costs"]["holding_cost_total"] += inventory[age] * p["holding_cost"]

            inventory = {
                age + 1: inventory[age]
                for age in range(1, shelf_life)
            } | {1: 0}

    result["costs"]["total_cost"] = (
        result["costs"]["purchase_cost"]
        + result["costs"]["holding_cost_total"]
        + result["costs"]["waste_cost_total"]
    )
    return result


def plain_dict(value):
    if isinstance(value, defaultdict):
        value = dict(value)
    if isinstance(value, dict):
        return {k: plain_dict(v) for k, v in value.items()}
    return value
