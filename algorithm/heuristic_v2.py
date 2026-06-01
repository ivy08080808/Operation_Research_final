from collections import defaultdict
from functools import lru_cache

# Normalize near-zero / near-integer floats to cleaner outputs.
def clean_number(value, tolerance=1e-7):
    if abs(value) < tolerance:
        return 0
    rounded = round(value)
    if abs(value - rounded) < tolerance:
        return int(rounded)
    return value


# Simulate one week under FIFO consumption and shelf-life aging.
def simulate_week(start_inventory, demand, regular_qty, discount_qty, params):
    shelf_life = params["shelf_life"]
    capacity_used = sum(start_inventory.values()) + regular_qty + discount_qty
    inventory = dict(start_inventory)
    inventory[1] += regular_qty + discount_qty

    # Consume oldest inventory first to minimize waste.
    use = {}
    remaining_demand = demand
    for age in range(shelf_life, 0, -1):
        used = min(inventory[age], remaining_demand)
        inventory[age] -= used
        remaining_demand -= used
        use[age] = used

    if remaining_demand:
        return None

    # Expire the oldest bucket and compute per-week costs.
    waste = inventory[shelf_life]
    inventory[shelf_life] = 0
    holding_cost = sum(inventory.values()) * params["holding_cost"]
    waste_cost = waste * params["waste_cost"]
    purchase_cost = (
        regular_qty * params["regular_cost"]
        + discount_qty * params["discount_cost"]
    )

    end_inventory = dict(inventory)
    # Age remaining inventory forward for next week's initial state.
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
        "capacity_used": capacity_used,
    }


# Generate feasible (regular, discount) purchase actions for a week.
def action_candidates(t_index, weeks, weekly_demand, start_inventory, params, capacity_limit=None):
    t = weeks[t_index]
    shelf_life = params["shelf_life"]
    threshold = params["discount_threshold"]
    big_m = params["M"]
    demand_now = weekly_demand[t]
    available = sum(start_inventory.values())
    residual_now = max(0, demand_now - available)

    # Baseline action: buy just enough regular quantity for this week.
    actions = {(residual_now, 0)}
    if threshold > big_m:
        return capacity_feasible_actions(actions, start_inventory, capacity_limit)

    # Add discount candidates that can cover demand within shelf-life horizon.
    future_weeks = weeks[t_index : min(len(weeks), t_index + shelf_life)]
    for end_offset in range(1, len(future_weeks) + 1):
        needed = max(
            0,
            sum(weekly_demand[week] for week in future_weeks[:end_offset]) - available,
        )
        for discount_qty in {
            threshold,
            needed,
            max(threshold, needed),
            min(big_m, max(threshold, needed)),
        }:
            if threshold <= discount_qty <= big_m and discount_qty >= residual_now:
                actions.add((0, discount_qty))

    return capacity_feasible_actions(actions, start_inventory, capacity_limit)


# Filter actions by remaining category/storage capacity, if given.
def capacity_feasible_actions(actions, start_inventory, capacity_limit):
    if capacity_limit is None:
        return sorted(actions)
    available_capacity = capacity_limit - sum(start_inventory.values())
    return sorted(
        (regular_qty, discount_qty)
        for regular_qty, discount_qty in actions
        if regular_qty + discount_qty <= available_capacity + 1e-7
    )


# Solve one ingredient optimally via memoized dynamic programming.
def solve_ingredient_v2(ingredient, weekly_demand, params, capacity_remaining=None):
    weeks = sorted(weekly_demand)
    shelf_life = params["shelf_life"]
    zero_inventory = tuple(0 for _ in range(shelf_life))

    @lru_cache(maxsize=None)
    def best_from(t_index, inventory_tuple):
        # Base case: all weeks are planned.
        if t_index == len(weeks):
            return 0, []

        start_inventory = {
            age: inventory_tuple[age - 1]
            for age in range(1, shelf_life + 1)
        }
        best_cost = float("inf")
        best_plan = None

        week = weeks[t_index]
        capacity_limit = capacity_remaining.get(week) if capacity_remaining is not None else None
        # Try all feasible actions and keep the minimum total (current + future) cost.
        for regular_qty, discount_qty in action_candidates(
            t_index, weeks, weekly_demand, start_inventory, params, capacity_limit
        ):
            simulated = simulate_week(
                start_inventory,
                weekly_demand[week],
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
                        "week": week,
                        "regular_qty": regular_qty,
                        "discount_qty": discount_qty,
                        "simulated": simulated,
                    }
                ] + future_plan

        return best_cost, best_plan

    # Start from empty inventory and reconstruct the best plan.
    _, plan = best_from(0, zero_inventory)
    if plan is None:
        raise ValueError(f"No capacity-feasible plan found for ingredient {ingredient}")
    return plan


# Solve all ingredients, optionally under shared category capacities.
def solve_greedy_v2(ingredient_demand, params, weeks=None, category_capacities=None):
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

    # Build capacity bookkeeping and ingredient processing order per category.
    category_capacities = infer_category_capacities(params, category_capacities)
    if category_capacities:
        category_remaining = {
            category: {week: capacity for week in weeks}
            for category, capacity in category_capacities.items()
        }
        ordered_ingredients = []
        for category in sorted(category_capacities):
            category_ingredients = [
                ingredient
                for ingredient in ingredient_demand
                if str(params[ingredient].get("category_id")) == category
            ]
            category_ingredients = sorted(
                category_ingredients,
                key=lambda ingredient: (
                    params[ingredient]["shelf_life"],
                    -sum(ingredient_demand[ingredient][week] for week in weeks),
                    ingredient,
                ),
            )
            for position, ingredient in enumerate(category_ingredients):
                ordered_ingredients.append(
                    (
                        ingredient,
                        category,
                        category_ingredients[position + 1 :],
                    )
                )
    else:
        category_remaining = {}
        ordered_ingredients = [
            (ingredient, None, [])
            for ingredient in ingredient_demand
        ]

    # Solve each ingredient sequentially and write outputs into result tables.
    for ingredient, category, later_ingredients in ordered_ingredients:
        weekly_demand = {week: ingredient_demand[ingredient][week] for week in weeks}
        remaining = category_remaining.get(category)
        ingredient_capacity = None
        if remaining is not None:
            ingredient_capacity = {
                week: remaining[week]
                - sum(ingredient_demand[later][week] for later in later_ingredients)
                for week in weeks
            }
        if ingredient_capacity is not None:
            plan = solve_ingredient_v2(
                ingredient,
                weekly_demand,
                params[ingredient],
                ingredient_capacity,
            )
        else:
            plan = solve_ingredient_v2(ingredient, weekly_demand, params[ingredient], remaining)
        # Materialize week-level decision variables, inventory states, and costs.
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

            # Deduct used capacity and guard against over-allocation.
            if remaining is not None:
                remaining[t] -= simulated["capacity_used"]
                if remaining[t] < -1e-6:
                    raise ValueError(
                        f"Category capacity exceeded for category {category}, week {t}"
                    )

    # Clean numeric noise and finalize total cost.
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


# Resolve category capacities from explicit input or ingredient parameters.
def infer_category_capacities(params, category_capacities):
    if category_capacities is not None:
        return {str(category): float(capacity) for category, capacity in category_capacities.items()}

    inferred = {}
    for ingredient_params in params.values():
        category = ingredient_params.get("category_id")
        capacity = ingredient_params.get("category_capacity")
        if category is not None and capacity is not None:
            inferred[str(category)] = float(capacity)
    return inferred
