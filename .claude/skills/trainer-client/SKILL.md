---
description: Add, edit, or view a client profile for the personal trainer. Use when the user wants to create a new client, update client details, or view a client's profile. Stores name, age, sex, height, weight, goal, activity level, and dietary restrictions.
argument-hint: [client-name]
arguments: [client]
allowed-tools: Bash(ls *) Bash(cat *) Bash(python3 *) Write Read
---

# Client Profile Manager

**Client:** $client

!`[ -f ".claude/trainer/clients/$client.json" ] && echo "=== Existing profile ===" && cat ".claude/trainer/clients/$client.json" || echo "(no profile found for '$client' — will create new)"`

---

## Instructions

**If `$client` is empty or not provided:**
Ask the user for the client name, then re-run with that name.

**If a profile already exists:**
Show the current profile in a readable format and ask if they want to update any fields.

**If no profile exists:**
Gather the following information by asking the user (ask all at once):
- Full name
- Age
- Sex (male/female)
- Height (cm)
- Current weight (kg)
- Goal: `lose_fat` | `gain_muscle` | `maintain` | `recomposition`
- Activity level: `sedentary` | `light` | `moderate` | `active` | `very_active`
- Dietary restrictions (e.g. vegan, lactose-free, none)
- Any injuries or limitations

Once you have all the data, calculate their BMR and TDEE using the Mifflin-St Jeor formula:
- Male BMR = 10×weight + 6.25×height − 5×age + 5
- Female BMR = 10×weight + 6.25×height − 5×age − 161
- TDEE = BMR × activity multiplier (sedentary=1.2, light=1.375, moderate=1.55, active=1.725, very_active=1.9)
- Target kcal based on goal: lose_fat=TDEE−500, gain_muscle=TDEE+300, maintain=TDEE, recomposition=TDEE−200

Save the profile as `.claude/trainer/clients/<name>.json` using this exact structure:
```json
{
  "name": "",
  "age": 0,
  "sex": "",
  "height_cm": 0,
  "weight_kg": 0,
  "goal": "",
  "activity_level": "",
  "dietary_restrictions": [],
  "injuries": [],
  "bmr": 0,
  "tdee": 0,
  "target_kcal": 0,
  "created_at": "",
  "updated_at": ""
}
```

Use today's date for `created_at` and `updated_at`. After saving, confirm with a summary table showing name, goal, TDEE, and target kcal.
