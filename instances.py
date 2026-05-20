from copy import deepcopy


WEEKS = [1, 2, 3, 4]

RECIPE_BASE = {
    "D1 (Tomato-Egg)": {"Chicken Leg": 0, "Tomato": 1, "Egg": 1, "Spinach": 0},
    "D2 (Spinach)": {"Chicken Leg": 0, "Tomato": 0, "Egg": 0, "Spinach": 2},
    "D3 (Chicken)": {"Chicken Leg": 1, "Tomato": 0, "Egg": 0, "Spinach": 0},
}

INSTANCE_1 = {
    "name": "Instance 1",
    "weeks": WEEKS,
    "dish_demand": {
        "D1 (Tomato-Egg)": {1: 80, 2: 90, 3: 70, 4: 100},
        "D2 (Spinach)": {1: 60, 2: 80, 3: 90, 4: 70},
        "D3 (Chicken)": {1: 50, 2: 60, 3: 80, 4: 90},
    },
    "recipe": RECIPE_BASE,
    "params": {
        "Chicken Leg": {
            "regular_cost": 5.00,
            "discount_cost": 4.50,
            "discount_threshold": 120,
            "shelf_life": 2,
            "holding_cost": 0.300,
            "waste_cost": 1.00,
            "M": 170,
        },
        "Tomato": {
            "regular_cost": 1.00,
            "discount_cost": 0.85,
            "discount_threshold": 85,
            "shelf_life": 1,
            "holding_cost": 0.050,
            "waste_cost": 0.30,
            "M": 100,
        },
        "Egg": {
            "regular_cost": 0.50,
            "discount_cost": 0.44,
            "discount_threshold": 140,
            "shelf_life": 2,
            "holding_cost": 0.040,
            "waste_cost": 0.10,
            "M": 170,
        },
        "Spinach": {
            "regular_cost": 0.80,
            "discount_cost": 0.74,
            "discount_threshold": 160,
            "shelf_life": 1,
            "holding_cost": 0.030,
            "waste_cost": 0.20,
            "M": 180,
        },
    },
}

INSTANCE_2 = {
    "name": "Instance 2",
    "weeks": WEEKS,
    "dish_demand": {
        "D1 (Tomato-Egg)": {1: 40, 2: 35, 3: 30, 4: 40},
        "D2 (Spinach)": {1: 30, 2: 25, 3: 35, 4: 30},
        "D3 (Chicken)": {1: 20, 2: 25, 3: 20, 4: 25},
    },
    "recipe": RECIPE_BASE,
    "params": {
        "Chicken Leg": {
            "regular_cost": 5.00,
            "discount_cost": 4.50,
            "discount_threshold": 200,
            "shelf_life": 1,
            "holding_cost": 0.200,
            "waste_cost": 2.50,
            "M": 25,
        },
        "Tomato": {
            "regular_cost": 1.00,
            "discount_cost": 0.85,
            "discount_threshold": 200,
            "shelf_life": 1,
            "holding_cost": 0.050,
            "waste_cost": 0.80,
            "M": 40,
        },
        "Egg": {
            "regular_cost": 0.50,
            "discount_cost": 0.44,
            "discount_threshold": 200,
            "shelf_life": 1,
            "holding_cost": 0.020,
            "waste_cost": 0.40,
            "M": 40,
        },
        "Spinach": {
            "regular_cost": 0.80,
            "discount_cost": 0.74,
            "discount_threshold": 200,
            "shelf_life": 1,
            "holding_cost": 0.030,
            "waste_cost": 0.70,
            "M": 70,
        },
    },
}

INSTANCE_3 = {
    "name": "Instance 3",
    "weeks": WEEKS,
    "dish_demand": {
        "D1 (Tomato-Egg)": {1: 20, 2: 120, 3: 20, 4: 120},
        "D2 (Spinach)": {1: 10, 2: 80, 3: 10, 4: 80},
        "D3 (Chicken)": {1: 15, 2: 90, 3: 15, 4: 90},
    },
    "recipe": RECIPE_BASE,
    "params": {
        "Chicken Leg": {
            "regular_cost": 5.00,
            "discount_cost": 3.50,
            "discount_threshold": 100,
            "shelf_life": 3,
            "holding_cost": 0.600,
            "waste_cost": 0.50,
            "M": 195,
        },
        "Tomato": {
            "regular_cost": 1.00,
            "discount_cost": 0.70,
            "discount_threshold": 100,
            "shelf_life": 2,
            "holding_cost": 0.200,
            "waste_cost": 0.15,
            "M": 140,
        },
        "Egg": {
            "regular_cost": 0.50,
            "discount_cost": 0.35,
            "discount_threshold": 150,
            "shelf_life": 3,
            "holding_cost": 0.080,
            "waste_cost": 0.05,
            "M": 260,
        },
        "Spinach": {
            "regular_cost": 0.80,
            "discount_cost": 0.55,
            "discount_threshold": 100,
            "shelf_life": 2,
            "holding_cost": 0.160,
            "waste_cost": 0.10,
            "M": 180,
        },
    },
}

INSTANCE_4 = {
    "name": "Instance 4",
    "weeks": WEEKS,
    "dish_demand": {
        "D1 (Tomato-Egg)": {1: 70, 2: 70, 3: 70, 4: 70},
        "D2 (Spinach)": {1: 50, 2: 50, 3: 50, 4: 50},
        "D3 (Chicken)": {1: 60, 2: 60, 3: 60, 4: 60},
    },
    "recipe": RECIPE_BASE,
    "params": {
        "Chicken Leg": {
            "regular_cost": 5.00,
            "discount_cost": 4.50,
            "discount_threshold": 100,
            "shelf_life": 2,
            "holding_cost": 0.300,
            "waste_cost": 1.00,
            "M": 120,
        },
        "Tomato": {
            "regular_cost": 1.00,
            "discount_cost": 0.85,
            "discount_threshold": 60,
            "shelf_life": 1,
            "holding_cost": 0.050,
            "waste_cost": 0.30,
            "M": 70,
        },
        "Egg": {
            "regular_cost": 0.50,
            "discount_cost": 0.44,
            "discount_threshold": 120,
            "shelf_life": 2,
            "holding_cost": 0.040,
            "waste_cost": 0.10,
            "M": 140,
        },
        "Spinach": {
            "regular_cost": 0.80,
            "discount_cost": 0.74,
            "discount_threshold": 90,
            "shelf_life": 1,
            "holding_cost": 0.030,
            "waste_cost": 0.20,
            "M": 100,
        },
    },
}

RECIPE_5 = {
    "D1 (Salad)": {"Chicken": 0, "Beef": 0, "Tomato": 2, "Spinach": 1, "Egg": 1, "Rice": 0},
    "D2 (Stir-fry)": {"Chicken": 1, "Beef": 0, "Tomato": 0, "Spinach": 2, "Egg": 0, "Rice": 1},
    "D3 (Roast)": {"Chicken": 0, "Beef": 1, "Tomato": 1, "Spinach": 0, "Egg": 0, "Rice": 0},
    "D4 (Soup)": {"Chicken": 1, "Beef": 0, "Tomato": 1, "Spinach": 1, "Egg": 0, "Rice": 0},
    "D5 (Sandwich)": {"Chicken": 0, "Beef": 1, "Tomato": 0, "Spinach": 0, "Egg": 1, "Rice": 0},
    "D6 (Bowl)": {"Chicken": 1, "Beef": 0, "Tomato": 0, "Spinach": 0, "Egg": 1, "Rice": 2},
}

INSTANCE_5 = {
    "name": "Instance 5",
    "weeks": WEEKS,
    "dish_demand": {
        "D1 (Salad)": {1: 80, 2: 95, 3: 70, 4: 110},
        "D2 (Stir-fry)": {1: 70, 2: 80, 3: 90, 4: 85},
        "D3 (Roast)": {1: 60, 2: 75, 3: 65, 4: 80},
        "D4 (Soup)": {1: 55, 2: 60, 3: 70, 4: 65},
        "D5 (Sandwich)": {1: 90, 2: 85, 3: 95, 4: 100},
        "D6 (Bowl)": {1: 75, 2: 80, 3: 85, 4: 90},
    },
    "recipe": RECIPE_5,
    "params": {
        "Chicken": {
            "regular_cost": 4.50,
            "discount_cost": 3.85,
            "discount_threshold": 200,
            "shelf_life": 2,
            "holding_cost": 0.400,
            "waste_cost": 1.20,
            "M": 485,
        },
        "Beef": {
            "regular_cost": 6.00,
            "discount_cost": 5.10,
            "discount_threshold": 150,
            "shelf_life": 2,
            "holding_cost": 0.500,
            "waste_cost": 1.80,
            "M": 340,
        },
        "Tomato": {
            "regular_cost": 1.00,
            "discount_cost": 0.82,
            "discount_threshold": 300,
            "shelf_life": 1,
            "holding_cost": 0.040,
            "waste_cost": 0.25,
            "M": 365,
        },
        "Spinach": {
            "regular_cost": 0.80,
            "discount_cost": 0.66,
            "discount_threshold": 280,
            "shelf_life": 1,
            "holding_cost": 0.030,
            "waste_cost": 0.18,
            "M": 345,
        },
        "Egg": {
            "regular_cost": 0.50,
            "discount_cost": 0.42,
            "discount_threshold": 400,
            "shelf_life": 2,
            "holding_cost": 0.050,
            "waste_cost": 0.08,
            "M": 550,
        },
        "Rice": {
            "regular_cost": 0.30,
            "discount_cost": 0.24,
            "discount_threshold": 500,
            "shelf_life": 3,
            "holding_cost": 0.030,
            "waste_cost": 0.05,
            "M": 765,
        },
    },
}

INSTANCES = {
    "1": INSTANCE_1,
    "2": INSTANCE_2,
    "3": INSTANCE_3,
    "4": INSTANCE_4,
    "5": INSTANCE_5,
}

SENSITIVITY_SCENARIOS = [
    ("S1", "waste_cost", 0.5, 0.50),
    ("S2", "waste_cost", 1.0, 1.00),
    ("S3", "waste_cost", 2.0, 2.00),
    ("S4", "waste_cost", 5.0, 5.00),
    ("S5", "holding_cost", 0.5, 0.15),
    ("S6", "holding_cost", 2.0, 0.60),
    ("S7", "holding_cost", 5.0, 1.50),
    ("S8", "discount_threshold", 0.5, 50),
    ("S9", "discount_threshold", 1.5, 150),
    ("S10", "discount_threshold", 2.0, 200),
]


def get_instance(instance_id):
    return deepcopy(INSTANCES[str(instance_id)])


def make_instance4_scenario(field, concrete_value):
    instance = get_instance("4")
    instance["params"]["Chicken Leg"][field] = concrete_value
    return instance
