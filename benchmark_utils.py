from time import perf_counter

def plain_dict(value):
    if isinstance(value, dict):
        return {k: plain_dict(v) for k, v in value.items()}
    return value


def project_ingredient_demand(dish_demand, recipe):
    ingredient_demand = {}
    weeks = sorted(next(iter(dish_demand.values())))
    ingredients = sorted({ingredient for dish in recipe.values() for ingredient in dish})
    for ingredient in ingredients:
        ingredient_demand[ingredient] = {}
        for week in weeks:
            ingredient_demand[ingredient][week] = sum(
                dish_demand[dish].get(week, 0) * recipe[dish].get(ingredient, 0)
                for dish in dish_demand
            )
    return ingredient_demand


def prepare_instance(instance):
    if "ingredient_demand" in instance:
        return instance["ingredient_demand"], instance["params"], instance.get("weeks")
    ingredient_demand = project_ingredient_demand(instance["dish_demand"], instance["recipe"])
    return ingredient_demand, instance["params"], instance.get("weeks")


def timed(callable_, *args):
    start = perf_counter()
    result = callable_(*args)
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


def compact_plan(result, include_inventory=False):
    plan = {
        "regular_purchase": plain_dict(result["regular_purchase"]),
        "discount_purchase": plain_dict(result["discount_purchase"]),
        "discount_enabled": plain_dict(result["discount_enabled"]),
        "waste": plain_dict(result["waste"]),
        "costs": result["costs"],
    }
    if include_inventory:
        plan["inventory"] = plain_dict(result["inventory"])
    return plan


def discount_count(result, ingredient=None):
    enabled = plain_dict(result["discount_enabled"])
    if ingredient is not None:
        return sum(enabled[ingredient].values())
    return sum(sum(weeks.values()) for weeks in enabled.values())


def discount_counts(result):
    enabled = plain_dict(result["discount_enabled"])
    return {
        ingredient: sum(weeks.values())
        for ingredient, weeks in enabled.items()
    }
