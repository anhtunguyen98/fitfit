---
description: Generate or update a weekly meal plan for a client. Calculates kcal and macros per meal based on the client's target, dietary restrictions, and preferences. Use when the user wants to plan meals, update a diet plan, or view the current meal schedule.
argument-hint: [client-name]
arguments: [client]
allowed-tools: Bash(cat *) Bash(ls *) Bash(python3 *) Write Read
---

# Meal Planner

**Client:** $client

!`[ -f ".claude/trainer/clients/$client.json" ] && echo "=== Client Profile ===" && python3 -c "
import json, sys
try:
    d = json.load(open('.claude/trainer/clients/$client.json'))
    print(f'  Goal:        {d[\"goal\"]}')
    print(f'  Target kcal: {d[\"target_kcal\"]} kcal/day')
    print(f'  TDEE:        {d[\"tdee\"]} kcal/day')
    print(f'  Restrictions: {', '.join(d[\"dietary_restrictions\"]) or \"none\"}')
except Exception as e:
    print(f'Error reading profile: {e}')
" || echo "ERROR: No profile found for '$client'. Run /trainer-client $client first."`

!`[ -f ".claude/trainer/clients/${client}_meal_plan.json" ] && echo "" && echo "=== Current Meal Plan ===" && python3 -c "
import json
try:
    p = json.load(open('.claude/trainer/clients/${client}_meal_plan.json'))
    for day, meals in p.get('days', {}).items():
        total = sum(m.get('kcal',0) for m in meals)
        print(f'{day}: {total} kcal')
except: pass
" || echo "(no meal plan yet)"`

---

## Instructions

**If no client profile exists:** Tell the user to run `/trainer-client $client` first.

**If profile exists, generate or update a weekly meal plan:**

1. Ask if they want to specify any preferences (e.g. number of meals per day, cuisines, foods to avoid). If not, use defaults (3 main meals + 1 snack).

2. Build a 7-day meal plan. For each day include:
   - Breakfast, Lunch, Dinner, optional Snack
   - Each meal: name, ingredients list, kcal, protein(g), carbs(g), fat(g)
   - Daily total must match the client's `target_kcal` (±50 kcal tolerance)
   - Respect dietary restrictions

3. Macro split guidance by goal:
   - `lose_fat`: protein 35%, carbs 40%, fat 25%
   - `gain_muscle`: protein 30%, carbs 45%, fat 25%
   - `maintain`: protein 25%, carbs 50%, fat 25%
   - `recomposition`: protein 35%, carbs 40%, fat 25%

4. Save the plan to `.claude/trainer/clients/${client}_meal_plan.json`:
```json
{
  "client": "$client",
  "target_kcal": 0,
  "meals_per_day": 4,
  "updated_at": "",
  "days": {
    "Monday": [
      {"meal": "Breakfast", "name": "", "ingredients": [], "kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    ]
  }
}
```

5. Display the plan as a compact weekly table with daily kcal totals. Highlight any day that deviates more than 100 kcal from the target.
