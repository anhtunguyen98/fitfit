---
description: Generate a progress report for a client — shows weight trend, kcal adherence, workout consistency, and goal progress. Use when the user wants to review a client's progress, see stats, or get a coaching summary.
argument-hint: [client-name]
arguments: [client]
allowed-tools: Bash(cat *) Bash(ls *) Bash(python3 *) Read
---

# Progress Report

**Client:** $client

!`[ -f ".claude/trainer/clients/$client.json" ] && [ -f ".claude/trainer/clients/${client}_log.json" ] && python3 -c "
import json
from datetime import datetime

try:
    profile = json.load(open('.claude/trainer/clients/$client.json'))
    logs = json.load(open('.claude/trainer/clients/${client}_log.json'))
    entries = logs.get('entries', [])

    if not entries:
        print('No log entries found.')
    else:
        total = len(entries)
        # Kcal stats
        kcals = [e['total_kcal'] for e in entries if e.get('total_kcal')]
        avg_kcal = sum(kcals) / len(kcals) if kcals else 0
        target = profile.get('target_kcal', 0)
        on_target = sum(1 for e in entries if e.get('kcal_status') == 'on_target')
        deficits  = sum(1 for e in entries if e.get('kcal_status') == 'deficit')
        surpluses = sum(1 for e in entries if e.get('kcal_status') == 'surplus')

        # Weight trend
        weights = [(e['date'], e['weight_kg']) for e in entries if e.get('weight_kg')]
        first_w = weights[0][1] if weights else None
        last_w  = weights[-1][1] if weights else None
        delta_w = round(last_w - first_w, 2) if (first_w and last_w) else None

        # Workout
        workouts = sum(1 for e in entries if e.get('workout_done'))

        print(f'=== {profile[\"name\"]} — {total} days logged ===')
        print(f'Goal:         {profile[\"goal\"]}')
        print(f'Target kcal:  {target} kcal/day')
        print(f'Avg kcal:     {avg_kcal:.0f} kcal/day')
        print(f'On target:    {on_target}/{total} days  |  Deficit: {deficits}  |  Surplus: {surpluses}')
        print(f'Workouts:     {workouts}/{total} days ({100*workouts//total}% consistency)')
        if delta_w is not None:
            arrow = '+' if delta_w > 0 else ''
            print(f'Weight:       {first_w}kg → {last_w}kg  ({arrow}{delta_w} kg)')
        if weights:
            print(f'Last weigh-in: {weights[-1][0]}')
        print()
        print('--- Last 7 entries ---')
        for e in entries[-7:]:
            status = {'on_target':'✓','deficit':'↓','surplus':'↑'}.get(e.get('kcal_status',''),'?')
            w = f\"{e['weight_kg']}kg\" if e.get('weight_kg') else '     '
            wo = 'trained' if e.get('workout_done') else 'rest   '
            print(f\"  {e['date']}  {status} {e.get('total_kcal',0):4d} kcal  {w}  {wo}\")
except Exception as ex:
    print(f'Error: {ex}')
" || echo "ERROR: Missing profile or log for '$client'. Run /trainer-client $client and /trainer-log $client first."`

---

## Instructions

**If no profile or log exists:** Tell the user which command to run first.

**If data exists**, the raw stats are printed above. Now provide a coaching analysis:

1. **Kcal adherence** — Is the client consistently hitting their target? Flag if avg kcal is more than 150 from target.

2. **Weight trend** — Is the trend aligned with the goal?
   - `lose_fat`: expect negative delta
   - `gain_muscle`: expect slight positive delta
   - `maintain` / `recomposition`: expect near-zero
   Comment on whether the rate of change is healthy (0.3–0.7 kg/week ideal for fat loss; 0.2–0.4 kg/week for muscle gain).

3. **Workout consistency** — Flag if below 70%. Suggest scheduling adjustments if needed.

4. **Macro quality** — If protein average is available, flag if below 1.6g/kg body weight (minimum for muscle retention/growth).

5. **Recommendations** — 2–3 specific, actionable coaching recommendations based on the data.

6. **Projected outcome** — At the current rate, when will they reach their goal? Give a realistic estimate.

Keep the analysis direct, data-driven, and encouraging. No vague advice.
