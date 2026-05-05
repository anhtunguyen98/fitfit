import json
from datetime import date, datetime
from sqlalchemy.orm import Session
from . import models, schemas
from .calculators import (
    calculate_bmr, calculate_tdee, calculate_target_kcal,
    calculate_kcal_balance, summarize_food_items,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_metrics(client: models.Client, data: dict) -> dict:
    w = data.get("weight_kg") or client.weight_kg
    h = data.get("height_cm") or client.height_cm
    a = data.get("age") or client.age
    s = data.get("sex") or client.sex
    g = data.get("goal") or client.goal
    al = data.get("activity_level") or client.activity_level
    if all([w, h, a, s]):
        bmr = calculate_bmr(w, h, a, s)
        tdee = calculate_tdee(bmr, al) if al else bmr
        target = calculate_target_kcal(tdee, g) if g else tdee
        return {"bmr": bmr, "tdee": tdee, "target_kcal": target}
    return {}


# ── Clients ───────────────────────────────────────────────────────────────────

def create_client(db: Session, data: schemas.ClientCreate) -> models.Client:
    payload = data.model_dump()
    payload["dietary_restrictions"] = json.dumps(payload.get("dietary_restrictions", []))
    payload["injuries"] = json.dumps(payload.get("injuries", []))
    metrics = _compute_metrics(models.Client(), payload)
    payload.update(metrics)
    client = models.Client(**payload)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_client(db: Session, client_id: int) -> models.Client | None:
    return db.query(models.Client).filter(models.Client.id == client_id).first()


def list_clients(db: Session, skip: int = 0, limit: int = 100) -> list[models.Client]:
    return db.query(models.Client).offset(skip).limit(limit).all()


def update_client(db: Session, client_id: int, data: schemas.ClientUpdate) -> models.Client | None:
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        return None
    updates = data.model_dump(exclude_none=True)
    if "dietary_restrictions" in updates:
        updates["dietary_restrictions"] = json.dumps(updates["dietary_restrictions"])
    if "injuries" in updates:
        updates["injuries"] = json.dumps(updates["injuries"])
    for k, v in updates.items():
        setattr(client, k, v)
    metrics = _compute_metrics(client, updates)
    for k, v in metrics.items():
        setattr(client, k, v)
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int) -> bool:
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        return False
    db.delete(client)
    db.commit()
    return True


# ── Meal Plans ────────────────────────────────────────────────────────────────

def create_meal_plan(db: Session, client_id: int, plan_data: dict) -> models.MealPlan:
    db.query(models.MealPlan).filter(
        models.MealPlan.client_id == client_id,
        models.MealPlan.is_active == True,
    ).update({"is_active": False})
    plan = models.MealPlan(client_id=client_id, plan_data=json.dumps(plan_data))
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_active_meal_plan(db: Session, client_id: int) -> models.MealPlan | None:
    return db.query(models.MealPlan).filter(
        models.MealPlan.client_id == client_id,
        models.MealPlan.is_active == True,
    ).first()


def list_meal_plans(db: Session, client_id: int) -> list[models.MealPlan]:
    return db.query(models.MealPlan).filter(
        models.MealPlan.client_id == client_id
    ).order_by(models.MealPlan.generated_at.desc()).all()


# ── Workout Plans ─────────────────────────────────────────────────────────────

def create_workout_plan(db: Session, client_id: int, plan_data: dict) -> models.WorkoutPlan:
    db.query(models.WorkoutPlan).filter(
        models.WorkoutPlan.client_id == client_id,
        models.WorkoutPlan.is_active == True,
    ).update({"is_active": False})
    plan = models.WorkoutPlan(client_id=client_id, plan_data=json.dumps(plan_data))
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_active_workout_plan(db: Session, client_id: int) -> models.WorkoutPlan | None:
    return db.query(models.WorkoutPlan).filter(
        models.WorkoutPlan.client_id == client_id,
        models.WorkoutPlan.is_active == True,
    ).first()


def list_workout_plans(db: Session, client_id: int) -> list[models.WorkoutPlan]:
    return db.query(models.WorkoutPlan).filter(
        models.WorkoutPlan.client_id == client_id
    ).order_by(models.WorkoutPlan.generated_at.desc()).all()


# ── Daily Logs ────────────────────────────────────────────────────────────────

def create_or_update_log(
    db: Session, client_id: int, data: schemas.DailyLogCreate
) -> models.DailyLog:
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    target_kcal = client.target_kcal or 2000.0

    food_dicts = [f.model_dump() for f in data.food_items]
    totals = summarize_food_items(food_dicts)
    balance = calculate_kcal_balance(totals["total_kcal"], target_kcal)

    existing = db.query(models.DailyLog).filter(
        models.DailyLog.client_id == client_id,
        models.DailyLog.log_date == data.log_date,
    ).first()

    if existing:
        existing.body_weight_kg = data.body_weight_kg
        existing.food_items = json.dumps(food_dicts)
        existing.total_kcal_consumed = totals["total_kcal"]
        existing.total_protein_g = totals["total_protein_g"]
        existing.total_carbs_g = totals["total_carbs_g"]
        existing.total_fat_g = totals["total_fat_g"]
        existing.workout_done = data.workout_done
        existing.workout_notes = data.workout_notes or ""
        existing.general_notes = data.general_notes or ""
        existing.kcal_balance = balance
        db.commit()
        db.refresh(existing)
        log = existing
    else:
        log = models.DailyLog(
            client_id=client_id,
            log_date=data.log_date,
            body_weight_kg=data.body_weight_kg,
            food_items=json.dumps(food_dicts),
            total_kcal_consumed=totals["total_kcal"],
            total_protein_g=totals["total_protein_g"],
            total_carbs_g=totals["total_carbs_g"],
            total_fat_g=totals["total_fat_g"],
            workout_done=data.workout_done,
            workout_notes=data.workout_notes or "",
            general_notes=data.general_notes or "",
            kcal_balance=balance,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

    log.food_items = json.loads(log.food_items)
    return log


def get_log(db: Session, client_id: int, log_date: date) -> models.DailyLog | None:
    log = db.query(models.DailyLog).filter(
        models.DailyLog.client_id == client_id,
        models.DailyLog.log_date == log_date,
    ).first()
    if log:
        log.food_items = json.loads(log.food_items or "[]")
    return log


def list_logs(db: Session, client_id: int, start_date: date, end_date: date) -> list[models.DailyLog]:
    logs = db.query(models.DailyLog).filter(
        models.DailyLog.client_id == client_id,
        models.DailyLog.log_date >= start_date,
        models.DailyLog.log_date <= end_date,
    ).order_by(models.DailyLog.log_date.desc()).all()
    for log in logs:
        log.food_items = json.loads(log.food_items or "[]")
    return logs


def delete_log(db: Session, client_id: int, log_date: date) -> bool:
    log = db.query(models.DailyLog).filter(
        models.DailyLog.client_id == client_id,
        models.DailyLog.log_date == log_date,
    ).first()
    if not log:
        return False
    db.delete(log)
    db.commit()
    return True
