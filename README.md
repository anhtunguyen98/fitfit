# Overfit — AI Personal Trainer & Coach

A web app for managing clients, generating meal plans, workout schedules, and tracking progress. Powered by Qwen3 via vLLM.

---

## Requirements

- Python 3.10+
- Docker with NVIDIA GPU support
- A HuggingFace account and access token ([get one here](https://huggingface.co/settings/tokens))

---

## Step-by-Step Setup

### 1. Clone / enter the project

```bash
cd /vast/tts/robert/other/overfit
```

### 2. Set your HuggingFace token

Open `.env` and fill in your token:

```bash
HF_TOKEN=hf_your_token_here
```

Also confirm the other defaults look right:

```
AI_BASE_URL=http://localhost:8001/v1
AI_MODEL=qwen3
AI_TIMEOUT=120
PORT=8000
```

### 3. Start the AI model (vLLM)

In a **separate terminal**, run:

```bash
./launch_vllm.sh
```

This pulls the `vllm/vllm-openai` Docker image and downloads the Qwen3-30B-A3B weights (~18 GB on first run). Wait until you see:

```
INFO:     Application startup complete.
```

> **Custom GPU / port / tensor parallel:**
> ```bash
> ./launch_vllm.sh Qwen/Qwen3-30B-A3B 8001 2 0,1   # tp=2 on GPUs 0 and 1
> ./launch_vllm.sh Qwen/Qwen3-30B-A3B 8001 1 2      # GPU 2 only
> ```

> **No GPU / testing without vLLM:**
> Skip this step. The app automatically falls back to built-in mock plans within 5 seconds.

### 4. Start the web app

In another terminal:

```bash
./run.sh
```

This creates a Python virtual environment, installs dependencies, and starts the FastAPI server. You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Open in browser

If running **locally**:
```
http://localhost:8000
```

If running on a **remote server** (recommended — SSH tunnel):
```bash
# On your local machine:
ssh -L 8000:localhost:8000 user@your-server-ip
```
Then open `http://localhost:8000` in your browser.

Or access directly via server IP if port 8000 is open:
```
http://your-server-ip:8000
```

---

## Using the App

### Add a client
1. Click **+ Add Client** on the dashboard
2. Fill in name, age, sex, height, weight, goal, and activity level
3. BMR / TDEE / target kcal are calculated automatically

### Generate a meal plan
1. Open a client → **Meal Plan** tab
2. Click **Generate Meal Plan**
3. The AI creates a 7-day plan with kcal and macros per meal

### Generate a workout plan
1. Open a client → **Workout** tab
2. Click **Generate Workout Plan**
3. The AI creates a weekly gym schedule with sets, reps, and rest times

### Log a daily session
1. Open a client → **Daily Log** tab
2. Add food items with kcal / macros
3. Check workout done, add notes, save
4. Kcal balance vs target is calculated automatically

### View progress report
1. Open a client → **Report** tab
2. Click **Generate Report**
3. Shows weight trend, kcal adherence %, workout consistency %, and AI coaching recommendations

---

## API Docs

Interactive API docs are available at:
```
http://localhost:8000/docs
```

---

## Project Structure

```
overfit/
├── run.sh                  # Start the web app
├── launch_vllm.sh          # Start the AI model via Docker
├── .env                    # Configuration (HF token, ports, model)
├── requirements.txt
├── app/
│   ├── main.py             # FastAPI app entry point
│   ├── models.py           # SQLite database models
│   ├── schemas.py          # Request / response types
│   ├── crud.py             # Database operations
│   ├── calculators.py      # BMR / TDEE / macro calculations
│   ├── ai_service.py       # Qwen3 integration + mock fallback
│   └── routers/            # API endpoints
│       ├── clients.py
│       ├── meal_plans.py
│       ├── workout_plans.py
│       ├── logs.py
│       └── reports.py
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

---

## Swapping the AI Model

Edit `.env`:

```bash
# Use a different local model
AI_BASE_URL=http://localhost:8001/v1
AI_MODEL=your-model-name

# Use Claude API (Anthropic)
AI_BASE_URL=https://api.anthropic.com/v1
AI_MODEL=claude-sonnet-4-6

# Use OpenAI
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `fail to load clients` | Make sure `./run.sh` is running |
| Meal plan / workout uses mock data | vLLM not running or still loading — check `./launch_vllm.sh` terminal |
| `could not select device driver "nvidia"` | Run `./launch_vllm.sh` instead of docker-compose |
| Port 8000 already in use | Change `PORT=8001` in `.env` and restart |
| Database error on first run | Delete `overfit.db` and restart `./run.sh` |
