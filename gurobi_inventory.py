from collections import defaultdict

try:
    import gurobipy as gp
    from gurobipy import GRB
except ModuleNotFoundError as exc:
    gp = None
    GRB = None
    GUROBI_IMPORT_ERROR = exc


def solve_gurobi(ingredient_demand, params, weeks=None, verbose=False, mip_gap=1e-9):
    if gp is None:
        raise RuntimeError(
            "gurobipy is not installed in this Python environment. "
            "Install gurobipy and run this file with a valid Gurobi license."
        ) from GUROBI_IMPORT_ERROR

    weeks = sorted(next(iter(ingredient_demand.values()))) if weeks is None else list(weeks)
    ingredients = list(ingredient_demand)
    model = gp.Model("perishable_inventory_milp")
    model.Params.OutputFlag = 1 if verbose else 0
    model.Params.MIPGap = mip_gap

    regular_purchase = {}
    discount_purchase = {}
    discount_enabled = {}
    use = {}
    inventory = {}
    waste = {}

    for i in ingredients:
        shelf_life = params[i]["shelf_life"]
        for t in weeks:
            regular_purchase[i, t] = model.addVar(lb=0, name=f"regular[{i},{t}]")
            discount_purchase[i, t] = model.addVar(lb=0, name=f"discount[{i},{t}]")
            discount_enabled[i, t] = model.addVar(vtype=GRB.BINARY, name=f"discount_on[{i},{t}]")
            waste[i, t] = model.addVar(lb=0, name=f"waste[{i},{t}]")
            for a in range(1, shelf_life + 1):
                use[i, t, a] = model.addVar(lb=0, name=f"use[{i},{t},{a}]")
                inventory[i, t, a] = model.addVar(lb=0, name=f"inv[{i},{t},{a}]")

    model.update()

    for i in ingredients:
        p = params[i]
        shelf_life = p["shelf_life"]
        for t in weeks:
            model.addConstr(
                regular_purchase[i, t] <= p["M"] * (1 - discount_enabled[i, t]),
                name=f"regular_max[{i},{t}]",
            )
            model.addConstr(
                discount_purchase[i, t] >= p["discount_threshold"] * discount_enabled[i, t],
                name=f"discount_min[{i},{t}]",
            )
            model.addConstr(
                discount_purchase[i, t] <= p["M"] * discount_enabled[i, t],
                name=f"discount_max[{i},{t}]",
            )

            model.addConstr(
                gp.quicksum(use[i, t, a] for a in range(1, shelf_life + 1))
                == ingredient_demand[i][t],
                name=f"demand[{i},{t}]",
            )

            if shelf_life > 1:
                model.addConstr(
                    inventory[i, t, 1]
                    == regular_purchase[i, t] + discount_purchase[i, t] - use[i, t, 1],
                    name=f"flow_new[{i},{t}]",
                )

            for a in range(2, shelf_life):
                previous_t = weeks[weeks.index(t) - 1] if t != weeks[0] else None
                previous = inventory[i, previous_t, a - 1] if previous_t is not None else 0
                model.addConstr(
                    inventory[i, t, a] == previous - use[i, t, a],
                    name=f"flow_age[{i},{t},{a}]",
                )

            if shelf_life == 1:
                model.addConstr(
                    waste[i, t]
                    == regular_purchase[i, t] + discount_purchase[i, t] - use[i, t, 1],
                    name=f"waste_l1[{i},{t}]",
                )
                model.addConstr(inventory[i, t, 1] == 0, name=f"expire_l1[{i},{t}]")
            else:
                previous_t = weeks[weeks.index(t) - 1] if t != weeks[0] else None
                previous = inventory[i, previous_t, shelf_life - 1] if previous_t is not None else 0
                model.addConstr(
                    waste[i, t] == previous - use[i, t, shelf_life],
                    name=f"waste[{i},{t}]",
                )
                model.addConstr(
                    inventory[i, t, shelf_life] == 0,
                    name=f"expire[{i},{t}]",
                )

    purchase_cost = gp.quicksum(
        regular_purchase[i, t] * params[i]["regular_cost"]
        + discount_purchase[i, t] * params[i]["discount_cost"]
        for i in ingredients
        for t in weeks
    )
    holding_cost = gp.quicksum(
        inventory[i, t, a] * params[i]["holding_cost"]
        for i in ingredients
        for t in weeks
        for a in range(1, params[i]["shelf_life"] + 1)
    )
    waste_cost = gp.quicksum(
        waste[i, t] * params[i]["waste_cost"]
        for i in ingredients
        for t in weeks
    )

    model.setObjective(purchase_cost + holding_cost + waste_cost, GRB.MINIMIZE)
    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Gurobi did not find an optimal solution. Status={model.Status}")

    result = {
        "regular_purchase": defaultdict(dict),
        "discount_purchase": defaultdict(dict),
        "discount_enabled": defaultdict(dict),
        "purchase": defaultdict(dict),
        "inventory": defaultdict(lambda: defaultdict(dict)),
        "use": defaultdict(lambda: defaultdict(dict)),
        "waste": defaultdict(dict),
        "costs": {
            "purchase_cost": purchase_cost.getValue(),
            "holding_cost_total": holding_cost.getValue(),
            "waste_cost_total": waste_cost.getValue(),
            "total_cost": model.ObjVal,
        },
    }

    for i in ingredients:
        for t in weeks:
            regular = regular_purchase[i, t].X
            discount = discount_purchase[i, t].X
            result["regular_purchase"][i][t] = clean_number(regular)
            result["discount_purchase"][i][t] = clean_number(discount)
            result["discount_enabled"][i][t] = int(round(discount_enabled[i, t].X))
            result["purchase"][i][t] = clean_number(regular + discount)
            result["waste"][i][t] = clean_number(waste[i, t].X)
            for a in range(1, params[i]["shelf_life"] + 1):
                result["inventory"][i][t][a] = clean_number(inventory[i, t, a].X)
                result["use"][i][t][a] = clean_number(use[i, t, a].X)

    return result


def clean_number(value, tolerance=1e-7):
    if abs(value) < tolerance:
        return 0
    rounded = round(value)
    if abs(value - rounded) < tolerance:
        return int(rounded)
    return value


def compare_results(greedy_result, optimal_result):
    greedy_cost = greedy_result["costs"]["total_cost"]
    optimal_cost = optimal_result["costs"]["total_cost"]
    absolute_gap = greedy_cost - optimal_cost
    relative_gap = absolute_gap / optimal_cost if optimal_cost else 0
    return {
        "greedy_total_cost": greedy_cost,
        "gurobi_total_cost": optimal_cost,
        "absolute_gap": absolute_gap,
        "relative_gap_percent": relative_gap * 100,
    }
