---
description: Personal trainer and coach hub. Lists all clients, shows overview stats, and routes to sub-commands. Use when the user says "trainer", "show clients", "open trainer", or wants an overview of their coaching dashboard.
argument-hint: [list|help]
allowed-tools: Bash(ls *) Bash(cat *) Bash(python3 *)
---

# Personal Trainer & Coach

**Data directory:** `.claude/trainer/clients/`

!`ls .claude/trainer/clients/ 2>/dev/null | sed 's/\.json//' | sort | awk 'BEGIN{print "=== Clients ==="} NF{print "  •", $0} END{if(NR==0) print "  (no clients yet)"}'`

---

## How to use

| Command | Action |
|---------|--------|
| `/trainer-client [name]` | Add or view a client profile |
| `/trainer-meal [name]` | Generate or update weekly meal plan |
| `/trainer-workout [name]` | Generate or update weekly gym schedule |
| `/trainer-log [name]` | Log a session (food, workout, weight) |
| `/trainer-report [name]` | View progress report and kcal balance |

## Instructions

Show the client list above and the command table. If no clients exist, encourage the user to run `/trainer-client` to add their first client. Keep the response concise. Do not add filler text.
