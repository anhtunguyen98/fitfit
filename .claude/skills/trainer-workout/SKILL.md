---
description: Generate or update a weekly gym workout schedule for a client. Plans exercises, sets, reps, and rest days based on the client's goal, experience, and available days. Use when the user wants to create a training program, update a workout plan, or view the current gym schedule.
argument-hint: [client-name]
arguments: [client]
allowed-tools: Bash(cat *) Bash(ls *) Bash(python3 *) Write Read
---

# Workout Planner

**Client:** $client

!`[ -f ".claude/trainer/clients/$client.json" ] && echo "=== Client Profile ===" && python3 -c "
import json
try:
    d = json.load(open('.claude/trainer/clients/$client.json'))
    print(f'  Goal:        {d[\"goal\"]}')
    print(f'  Activity:    {d[\"activity_level\"]}')
    print(f'  Injuries:    {', '.join(d[\"injuries\"]) or \"none\"}')
except Exception as e:
    print(f'Error: {e}')
" || echo "ERROR: No profile found for '$client'. Run /trainer-client $client first."`

!`[ -f ".claude/trainer/clients/${client}_workout_plan.json" ] && echo "" && echo "=== Current Workout Plan ===" && python3 -c "
import json
try:
    p = json.load(open('.claude/trainer/clients/${client}_workout_plan.json'))
    for day, w in p.get('days', {}).items():
        focus = w.get('focus','rest') if isinstance(w, dict) else 'rest'
        print(f'  {day}: {focus}')
except: pass
" || echo "(no workout plan yet)"`

---

## Instructions

**If no client profile exists:** Tell the user to run `/trainer-client $client` first.

**If profile exists, generate or update a weekly workout plan:**

1. Ask the user:
   - How many days per week can they train? (default: 4)
   - Experience level: beginner | intermediate | advanced
   - Equipment available: full_gym | home_dumbbells | bodyweight
   - Any specific preferences (e.g. no cardio, prefer free weights)

2. Design a weekly program matching their goal:
   - `lose_fat`: 3–4 resistance days + 2 HIIT/cardio days, circuit-style
   - `gain_muscle`: 4–5 resistance days (push/pull/legs split or upper/lower), progressive overload focus
   - `maintain`: 3 full-body resistance + 1–2 light cardio
   - `recomposition`: 4 resistance days with moderate cardio

3. For each training day include:
   - Muscle focus (e.g. "Chest & Triceps")
   - 5–7 exercises, each with: name, sets, reps (or duration), rest between sets
   - Warm-up and cool-down notes
   - Estimated session duration

4. Mark rest days explicitly. Account for injuries by excluding exercises that stress those areas.

5. Save to `.claude/trainer/clients/${client}_workout_plan.json`:
```json
{
  "client": "$client",
  "days_per_week": 4,
  "experience": "",
  "equipment": "",
  "updated_at": "",
  "days": {
    "Monday": {
      "focus": "",
      "duration_min": 0,
      "warmup": "",
      "exercises": [
        {"name": "", "sets": 0, "reps": "", "rest_sec": 0, "notes": ""}
      ],
      "cooldown": ""
    },
    "Tuesday": {"focus": "rest"}
  }
}
```

6. Display the weekly schedule as a table with focus and duration per day. Add a note for progressive overload: increase weight or reps by ~5% each week.
