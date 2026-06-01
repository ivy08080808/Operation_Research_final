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
    """
    Simplest heuristic baseline:
    - Do not pre-buy.
    - Do not use discount.
    - In each week, buy exactly enough to satisfy that week's demand.
    """
    weeks = sorted(next(iter(ingredient_demand.values()))) if weeks is None else list(weeks)
    category_capacities = infer_category_capacities(params, category_capacities)

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

    for ingredient, weekly in ingredient_demand.items():
        shelf_life = params[ingredient]["shelf_life"]
        category = str(params[ingredient].get("category_id"))

        for t in weeks:
            demand = float(weekly[t])
            regular_qty = max(0.0, demand)
            discount_qty = 0.0

            result["regular_purchase"][ingredient][t] = clean_number(regular_qty)
            result["discount_purchase"][ingredient][t] = 0
            result["discount_enabled"][ingredient][t] = 0
            result["purchase"][ingredient][t] = clean_number(regular_qty)
            result["waste"][ingredient][t] = 0

            for age in range(1, shelf_life + 1):
                result["inventory"][ingredient][t][age] = 0
                result["use"][ingredient][t][age] = clean_number(regular_qty if age == 1 else 0)

            result["costs"]["purchase_cost"] += regular_qty * params[ingredient]["regular_cost"]

            if category in category_capacities and regular_qty > category_capacities[category] + 1e-7:
                raise ValueError(
                    f"Category capacity exceeded for category {category}, week {t}"
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
