from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import init_db
from .routers import clients, meal_plans, workout_plans, logs, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Overfit — AI Personal Trainer", version="1.0.0", lifespan=lifespan, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router)
app.include_router(meal_plans.router)
app.include_router(workout_plans.router)
app.include_router(logs.router)
app.include_router(reports.router)

# Static files must be mounted last
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
