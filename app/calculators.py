ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + 5 if sex.lower() == "male" else base - 161, 1)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 1)


def calculate_target_kcal(tdee: float, goal: str) -> float:
    offsets = {"lose_weight": -500, "gain_muscle": 300, "maintain": 0}
    return round(tdee + offsets.get(goal, 0), 1)


def calculate_macros(target_kcal: float, goal: str, weight_kg: float) -> dict:
    protein_g = round(weight_kg * 2.0)
    fat_g = round((target_kcal * 0.25) / 9)
    carbs_g = round((target_kcal - protein_g * 4 - fat_g * 9) / 4)
    return {"protein_g": protein_g, "carbs_g": max(carbs_g, 0), "fat_g": fat_g}


def calculate_kcal_balance(consumed_kcal: float, target_kcal: float) -> float:
    return round(consumed_kcal - target_kcal, 1)


def summarize_food_items(food_items: list[dict]) -> dict:
    return {
        "total_kcal": round(sum(f.get("kcal", 0) for f in food_items), 1),
        "total_protein_g": round(sum(f.get("protein_g", 0) for f in food_items), 1),
        "total_carbs_g": round(sum(f.get("carbs_g", 0) for f in food_items), 1),
        "total_fat_g": round(sum(f.get("fat_g", 0) for f in food_items), 1),
    }
