---
description: Log a training session for a client — record food eaten, workout completed, and current body weight. Use when the user wants to log today's meals, record a workout, track weight, or add a daily entry for a client.
argument-hint: [client-name]
arguments: [client]
allowed-tools: Bash(cat *) Bash(ls *) Bash(python3 *) Bash(date *) Write Read
---

# Session Logger

**Client:** $client

!`date "+Today: %A %Y-%m-%d"`

!`[ -f ".claude/trainer/clients/$client.json" ] && python3 -c "
import json
try:
    d = json.load(open('.claude/trainer/clients/$client.json'))
    print(f'Target kcal: {d[\"target_kcal\"]} kcal')
    print(f'Goal:        {d[\"goal\"]}')
except: pass
" || echo "ERROR: No profile found for '$client'. Run /trainer-client $client first."`

!`[ -f ".claude/trainer/clients/${client}_log.json" ] && python3 -c "
import json
try:
    logs = json.load(open('.claude/trainer/clients/${client}_log.json'))
    entries = logs.get('entries', [])
    if entries:
        last = entries[-1]
        print(f'Last entry:  {last[\"date\"]} — {last[\"total_kcal\"]} kcal — weight {last.get(\"weight_kg\",\"?\") }kg')
    print(f'Total logs:  {len(entries)} days')
except: pass
" || echo "(no log entries yet)"`

---

## Instructions

**If no client profile exists:** Tell the user to run `/trainer-client $client` first.

**Gather log data for today by asking:**

1. **Food log** — What did they eat today? Accept a natural description like:
   - "oatmeal 80g, 2 eggs, chicken breast 150g, rice 200g, salad"
   - For each item estimate: kcal, protein(g), carbs(g), fat(g)
   - Sum to get `total_kcal`, `total_protein_g`, `total_carbs_g`, `total_fat_g`

2. **Workout** — Did they train today?
   - If yes: which exercises, sets/reps completed, any notes
   - If no: rest day or missed session? (record honestly)

3. **Body weight** — Current weight in kg (optional, skip if not measured)

4. **Notes** — Any free-form notes (energy level, sleep quality, etc.)

**Kcal balance calculation:**
- Load `target_kcal` from profile
- `kcal_balance = total_kcal - target_kcal`
- Label: surplus if >+100, deficit if <-100, on_target otherwise

**Append the entry to `.claude/trainer/clients/${client}_log.json`:**
```json
{
  "client": "$client",
  "entries": [
    {
      "date": "YYYY-MM-DD",
      "weight_kg": null,
      "total_kcal": 0,
      "total_protein_g": 0,
      "total_carbs_g": 0,
      "total_fat_g": 0,
      "kcal_balance": 0,
      "kcal_status": "on_target",
      "food_items": [],
      "workout_done": true,
      "workout_notes": "",
      "notes": ""
    }
  ]
}
```

If the file already exists, load it and append to the `entries` array. Do not overwrite existing entries.

**After saving**, show a compact daily summary:
- Kcal eaten vs target (with balance)
- Macro breakdown
- Workout status
- Motivational one-liner based on their progress
