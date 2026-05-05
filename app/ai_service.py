import json
import logging
import re
import httpx
from .config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    pass


# ── Mocks ─────────────────────────────────────────────────────────────────────

MOCK_MEAL_PLAN: dict = {
    "days": [
        {
            "day": day,
            "meals": [
                {"name": "Breakfast", "foods": ["Oatmeal 80g", "Banana", "Whey protein 30g"],
                 "kcal": 480, "protein_g": 35, "carbs_g": 62, "fat_g": 8},
                {"name": "Lunch", "foods": ["Chicken breast 180g", "Brown rice 150g", "Broccoli 120g"],
                 "kcal": 560, "protein_g": 48, "carbs_g": 58, "fat_g": 9},
                {"name": "Snack", "foods": ["Greek yogurt 200g", "Almonds 20g"],
                 "kcal": 280, "protein_g": 18, "carbs_g": 22, "fat_g": 12},
                {"name": "Dinner", "foods": ["Salmon 200g", "Sweet potato 200g", "Spinach salad"],
                 "kcal": 620, "protein_g": 44, "carbs_g": 52, "fat_g": 18},
            ],
            "day_total_kcal": 1940,
        }
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ],
    "weekly_avg_kcal": 1940,
    "notes": "Mock plan — vLLM unavailable. High protein, balanced macros.",
}

MOCK_WORKOUT_PLAN: dict = {
    "days": [
        {"day": "Monday", "focus": "Push — Chest / Shoulders / Triceps",
         "duration_min": 55,
         "exercises": [
             {"name": "Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90, "notes": ""},
             {"name": "Overhead Press", "sets": 3, "reps": "10-12", "rest_seconds": 75, "notes": ""},
             {"name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "rest_seconds": 60, "notes": ""},
             {"name": "Lateral Raises", "sets": 3, "reps": "15", "rest_seconds": 45, "notes": ""},
             {"name": "Tricep Pushdown", "sets": 3, "reps": "12-15", "rest_seconds": 45, "notes": ""},
         ]},
        {"day": "Tuesday", "focus": "Pull — Back / Biceps",
         "duration_min": 55,
         "exercises": [
             {"name": "Pull-ups", "sets": 4, "reps": "6-8", "rest_seconds": 90, "notes": ""},
             {"name": "Barbell Row", "sets": 4, "reps": "8-10", "rest_seconds": 90, "notes": ""},
             {"name": "Seated Cable Row", "sets": 3, "reps": "12", "rest_seconds": 60, "notes": ""},
             {"name": "Face Pulls", "sets": 3, "reps": "15", "rest_seconds": 45, "notes": ""},
             {"name": "Barbell Curl", "sets": 3, "reps": "10-12", "rest_seconds": 45, "notes": ""},
         ]},
        {"day": "Wednesday", "focus": "rest", "duration_min": 0, "exercises": []},
        {"day": "Thursday", "focus": "Legs — Quads / Hamstrings / Glutes",
         "duration_min": 60,
         "exercises": [
             {"name": "Squat", "sets": 4, "reps": "6-8", "rest_seconds": 120, "notes": ""},
             {"name": "Romanian Deadlift", "sets": 3, "reps": "10", "rest_seconds": 90, "notes": ""},
             {"name": "Leg Press", "sets": 3, "reps": "12-15", "rest_seconds": 75, "notes": ""},
             {"name": "Leg Curl", "sets": 3, "reps": "12-15", "rest_seconds": 60, "notes": ""},
             {"name": "Calf Raise", "sets": 4, "reps": "20", "rest_seconds": 45, "notes": ""},
         ]},
        {"day": "Friday", "focus": "Upper Body — Full",
         "duration_min": 50,
         "exercises": [
             {"name": "Dumbbell Press", "sets": 3, "reps": "10-12", "rest_seconds": 75, "notes": ""},
             {"name": "Dumbbell Row", "sets": 3, "reps": "10-12", "rest_seconds": 75, "notes": ""},
             {"name": "Arnold Press", "sets": 3, "reps": "12", "rest_seconds": 60, "notes": ""},
             {"name": "Cable Fly", "sets": 3, "reps": "15", "rest_seconds": 45, "notes": ""},
             {"name": "Hammer Curl", "sets": 3, "reps": "12", "rest_seconds": 45, "notes": ""},
         ]},
        {"day": "Saturday", "focus": "Cardio / Core", "duration_min": 40,
         "exercises": [
             {"name": "Treadmill jog", "sets": 1, "reps": "30 min", "rest_seconds": 0, "notes": "Zone 2"},
             {"name": "Plank", "sets": 3, "reps": "60s", "rest_seconds": 30, "notes": ""},
             {"name": "Ab wheel", "sets": 3, "reps": "12", "rest_seconds": 30, "notes": ""},
         ]},
        {"day": "Sunday", "focus": "rest", "duration_min": 0, "exercises": []},
    ],
    "rest_days": ["Wednesday", "Sunday"],
    "notes": "Mock plan — vLLM unavailable. Progressive overload: +2.5 kg when all sets completed.",
}

MOCK_RECOMMENDATIONS = (
    "Mock recommendations — vLLM unavailable. "
    "Based on your logs, focus on consistency: aim to hit your calorie target within ±200 kcal daily. "
    "Protein intake is the most critical lever — prioritize hitting 2g/kg body weight before worrying about carb/fat ratios.\n\n"
    "Your workout consistency looks solid. To keep progressing, add progressive overload every 1-2 weeks: "
    "increase the working weight by the smallest available increment once you can complete all sets with good form. "
    "Track your lifts so you never guess — a phone note is enough."
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_thinking(text: str) -> str:
    """Remove Qwen3 <think>...</think> blocks from output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


# ── vLLM calls ────────────────────────────────────────────────────────────────

async def _call_ai(prompt: str, system: str) -> str:
    # Connect fast-fails (5s) so mock is returned immediately when vLLM is down.
    # Read timeout stays long to allow model inference time.
    timeout = httpx.Timeout(connect=5.0, read=settings.ai_timeout, write=30.0, pool=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{settings.ai_base_url}/chat/completions",
                json={
                    "model": settings.ai_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    # Disable Qwen3 thinking mode for faster, structured responses
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            return _strip_thinking(raw)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning("vLLM unavailable: %s — using mock", e)
        raise AIServiceError(str(e))
    except Exception as e:
        logger.warning("vLLM error: %s — using mock", e)
        raise AIServiceError(str(e))


async def _call_ai_json(prompt: str, system: str) -> dict:
    full_system = system + "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation."
    raw = await _call_ai(prompt, full_system)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    raise AIServiceError("Could not parse JSON from model response")


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_meal_plan(client) -> dict:
    import json as _json
    restrictions = (
        client.dietary_restrictions
        if isinstance(client.dietary_restrictions, list)
        else _json.loads(client.dietary_restrictions or "[]")
    )
    system = (
        "You are an expert sports nutritionist. Generate a 7-day meal plan as JSON. "
        "The JSON must have this exact shape: "
        '{"days": [{"day": "Monday", "meals": [{"name": "Breakfast", "foods": ["food1"], '
        '"kcal": 400, "protein_g": 30, "carbs_g": 50, "fat_g": 10}], "day_total_kcal": 1800}], '
        '"weekly_avg_kcal": 1800, "notes": "..."}'
    )
    prompt = (
        f"Client: {client.name}, {client.age}yo {client.sex}, "
        f"{client.weight_kg}kg, {client.height_cm}cm.\n"
        f"Goal: {client.goal}. Target: {client.target_kcal} kcal/day.\n"
        f"Dietary restrictions: {', '.join(restrictions) or 'none'}.\n"
        f"Create a varied, realistic 7-day meal plan hitting the daily kcal target."
    )
    try:
        return await _call_ai_json(prompt, system)
    except AIServiceError:
        return MOCK_MEAL_PLAN


async def generate_workout_plan(client) -> dict:
    import json as _json
    injuries = (
        client.injuries
        if isinstance(client.injuries, list)
        else _json.loads(client.injuries or "[]")
    )
    system = (
        "You are an expert strength and conditioning coach. Generate a weekly workout plan as JSON. "
        "Shape: "
        '{"days": [{"day": "Monday", "focus": "Push", "duration_min": 55, '
        '"exercises": [{"name": "Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90, "notes": ""}]}], '
        '"rest_days": ["Wednesday"], "notes": "..."}'
    )
    prompt = (
        f"Client: {client.name}, goal: {client.goal}, activity: {client.activity_level}.\n"
        f"Injuries/limitations: {', '.join(injuries) or 'none'}.\n"
        f"Design a weekly program. Avoid exercises that stress injured areas. "
        f"Include rest days and progressive overload guidance."
    )
    try:
        return await _call_ai_json(prompt, system)
    except AIServiceError:
        return MOCK_WORKOUT_PLAN


async def generate_progress_report(client, logs: list, period_days: int) -> str:
    if not logs:
        return MOCK_RECOMMENDATIONS

    kcals = [l.total_kcal_consumed for l in logs if l.total_kcal_consumed]
    avg_kcal = round(sum(kcals) / len(kcals), 0) if kcals else 0
    workout_days = sum(1 for l in logs if l.workout_done)
    adherence = round(
        sum(1 for l in logs if abs(l.kcal_balance) <= 200) / len(logs) * 100, 1
    ) if logs else 0
    weights = [(str(l.log_date), l.body_weight_kg) for l in logs if l.body_weight_kg]
    weight_info = (
        f"from {weights[0][1]}kg to {weights[-1][1]}kg" if len(weights) >= 2
        else f"current {weights[0][1]}kg" if weights else "no weight data"
    )

    system = "You are an expert personal trainer writing a coaching summary. Be specific, direct, and encouraging."
    prompt = (
        f"Client: {client.name}, goal: {client.goal}.\n"
        f"Last {period_days} days: {len(logs)} logs, avg {avg_kcal} kcal/day (target {client.target_kcal}), "
        f"adherence {adherence}%, {workout_days} workouts, weight {weight_info}.\n"
        f"Write 2-3 paragraphs of personalized coaching recommendations referencing these numbers."
    )
    try:
        return await _call_ai(prompt, system)
    except AIServiceError:
        return MOCK_RECOMMENDATIONS
