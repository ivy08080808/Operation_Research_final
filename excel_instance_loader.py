from collections import defaultdict

import openpyxl


DEFAULT_WORKBOOK = "instances_corrected.xlsx"
DEFAULT_SHEET = "Long_Format_Instances"

COLUMN_MAP = {
    "scenario_id": "Scenario_ID",
    "scenario_name": "Scenario_Name",
    "instance_id": "Instance_ID",
    "ingredient": "Ingredient_ID",
    "regular_cost": "Regular_Cost_ci",
    "discount_cost": "Discount_Cost_cbar_i",
    "discount_threshold": "Threshold_mi",
    "M": "Upper_Bound_Mi",
    "holding_cost": "Holding_Cost_hi",
    "waste_cost": "Waste_Cost_wi",
    "shelf_life": "Shelf_Life_Li",
}


def load_long_format_rows(workbook_path=DEFAULT_WORKBOOK, sheet_name=DEFAULT_SHEET):
    workbook = openpyxl.load_workbook(workbook_path, data_only=True, read_only=True)
    worksheet = workbook[sheet_name]
    rows = worksheet.iter_rows(values_only=True)
    header = next(rows)
    index = {name: position for position, name in enumerate(header)}
    return [
        {column: row[position] for column, position in index.items()}
        for row in rows
        if row[index[COLUMN_MAP["instance_id"]]] is not None
    ]


def demand_columns(row):
    return sorted(
        [column for column in row if column.startswith("Demand_W")],
        key=lambda column: int(column.replace("Demand_W", "")),
    )


def list_instance_ids(workbook_path=DEFAULT_WORKBOOK, sheet_name=DEFAULT_SHEET, scenario_id=None):
    rows = load_long_format_rows(workbook_path, sheet_name)
    instance_ids = []
    seen = set()
    for row in rows:
        if scenario_id is not None and row[COLUMN_MAP["scenario_id"]] != scenario_id:
            continue
        instance_id = row[COLUMN_MAP["instance_id"]]
        if instance_id not in seen:
            seen.add(instance_id)
            instance_ids.append(instance_id)
    return instance_ids


def load_excel_instance(workbook_path=DEFAULT_WORKBOOK, sheet_name=DEFAULT_SHEET, instance_id=None):
    rows = load_long_format_rows(workbook_path, sheet_name)
    if instance_id is None:
        raise ValueError("instance_id is required when loading from the Excel long-format sheet.")

    selected = [row for row in rows if row[COLUMN_MAP["instance_id"]] == instance_id]
    if not selected:
        raise ValueError(f"Instance_ID not found in workbook: {instance_id}")

    weeks = [int(column.replace("Demand_W", "")) for column in demand_columns(selected[0])]
    ingredient_demand = defaultdict(dict)
    params = {}

    for row in selected:
        ingredient = row[COLUMN_MAP["ingredient"]]
        for week in weeks:
            ingredient_demand[ingredient][week] = float(row[f"Demand_W{week}"])

        params[ingredient] = {
            "regular_cost": float(row[COLUMN_MAP["regular_cost"]]),
            "discount_cost": float(row[COLUMN_MAP["discount_cost"]]),
            "discount_threshold": float(row[COLUMN_MAP["discount_threshold"]]),
            "M": float(row[COLUMN_MAP["M"]]),
            "holding_cost": float(row[COLUMN_MAP["holding_cost"]]),
            "waste_cost": float(row[COLUMN_MAP["waste_cost"]]),
            "shelf_life": int(row[COLUMN_MAP["shelf_life"]]),
        }

    first = selected[0]
    return {
        "name": first[COLUMN_MAP["instance_id"]],
        "scenario_id": first[COLUMN_MAP["scenario_id"]],
        "scenario_name": first[COLUMN_MAP["scenario_name"]],
        "instance_id": first[COLUMN_MAP["instance_id"]],
        "weeks": weeks,
        "ingredient_demand": dict(ingredient_demand),
        "params": params,
    }


def build_instance_from_rows(selected):
    weeks = [int(column.replace("Demand_W", "")) for column in demand_columns(selected[0])]
    ingredient_demand = defaultdict(dict)
    params = {}

    for row in selected:
        ingredient = row[COLUMN_MAP["ingredient"]]
        for week in weeks:
            ingredient_demand[ingredient][week] = float(row[f"Demand_W{week}"])

        params[ingredient] = {
            "regular_cost": float(row[COLUMN_MAP["regular_cost"]]),
            "discount_cost": float(row[COLUMN_MAP["discount_cost"]]),
            "discount_threshold": float(row[COLUMN_MAP["discount_threshold"]]),
            "M": float(row[COLUMN_MAP["M"]]),
            "holding_cost": float(row[COLUMN_MAP["holding_cost"]]),
            "waste_cost": float(row[COLUMN_MAP["waste_cost"]]),
            "shelf_life": int(row[COLUMN_MAP["shelf_life"]]),
        }

    first = selected[0]
    return {
        "name": first[COLUMN_MAP["instance_id"]],
        "scenario_id": first[COLUMN_MAP["scenario_id"]],
        "scenario_name": first[COLUMN_MAP["scenario_name"]],
        "instance_id": first[COLUMN_MAP["instance_id"]],
        "weeks": weeks,
        "ingredient_demand": dict(ingredient_demand),
        "params": params,
    }


def load_excel_instances(workbook_path=DEFAULT_WORKBOOK, sheet_name=DEFAULT_SHEET, scenario_id=None):
    rows = load_long_format_rows(workbook_path, sheet_name)
    grouped = defaultdict(list)
    order = []

    for row in rows:
        if scenario_id is not None and row[COLUMN_MAP["scenario_id"]] != scenario_id:
            continue
        instance_id = row[COLUMN_MAP["instance_id"]]
        if instance_id not in grouped:
            order.append(instance_id)
        grouped[instance_id].append(row)

    return [build_instance_from_rows(grouped[instance_id]) for instance_id in order]
