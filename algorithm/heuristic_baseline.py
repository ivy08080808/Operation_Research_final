from collections import defaultdict


def clean_number(value, tolerance=1e-7):
    if abs(value) < tolerance:
        return 0
    rounded = round(value)
    if abs(value - rounded) < tolerance:
        return int(rounded)
    return value


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


def solve_heuristic_baseline(ingredient_demand, params, weeks=None, category_capacities=None):
    """Baseline heuristic v2-1.

    This version intentionally ignores discount opportunities and carryover.
    It buys exactly each week's ingredient demand at regular price, consumes it
    immediately, and leaves no inventory or waste.
    """
    weeks = sorted(next(iter(ingredient_demand.values()))) if weeks is None else list(weeks)
    category_capacities = infer_category_capacities(params, category_capacities)
    category_usage = {
        category: {week: 0.0 for week in weeks}
        for category in category_capacities
    }

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
        shelf_life = params[ingredient]["shelf_life"]
        category = str(params[ingredient].get("category_id"))

        for week in weeks:
            regular_qty = float(weekly_demand[week])
            discount_qty = 0.0

            if category in category_usage:
                category_usage[category][week] += regular_qty
                if category_usage[category][week] > category_capacities[category] + 1e-7:
                    raise ValueError(
                        f"Category capacity exceeded for category {category}, week {week}"
                    )

            result["regular_purchase"][ingredient][week] = clean_number(regular_qty)
            result["discount_purchase"][ingredient][week] = 0
            result["discount_enabled"][ingredient][week] = 0
            result["purchase"][ingredient][week] = clean_number(regular_qty)
            result["waste"][ingredient][week] = 0

            for age in range(1, shelf_life + 1):
                result["inventory"][ingredient][week][age] = 0
                result["use"][ingredient][week][age] = clean_number(
                    regular_qty if age == 1 else 0
                )

            result["costs"]["purchase_cost"] += (
                regular_qty * params[ingredient]["regular_cost"]
            )

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
