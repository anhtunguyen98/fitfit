import json as _json
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


# ── Client ────────────────────────────────────────────────────────────────────

class ClientBase(BaseModel):
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    dietary_restrictions: list[str] = []
    injuries: list[str] = []

    @field_validator('dietary_restrictions', 'injuries', mode='before')
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            try:
                return _json.loads(v)
            except Exception:
                return []
        return v or []


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    dietary_restrictions: Optional[list[str]] = None
    injuries: Optional[list[str]] = None


class ClientResponse(ClientBase):
    id: int
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    target_kcal: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ClientListItem(BaseModel):
    id: int
    name: str
    goal: Optional[str] = None
    target_kcal: Optional[float] = None
    weight_kg: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


# ── Plans ─────────────────────────────────────────────────────────────────────

class MealPlanResponse(BaseModel):
    id: int
    client_id: int
    plan_data: dict
    generated_at: Optional[datetime] = None
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanResponse(BaseModel):
    id: int
    client_id: int
    plan_data: dict
    generated_at: Optional[datetime] = None
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# ── Daily Log ─────────────────────────────────────────────────────────────────

class FoodItem(BaseModel):
    name: str
    kcal: float
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0


class DailyLogCreate(BaseModel):
    log_date: date
    body_weight_kg: Optional[float] = None
    food_items: list[FoodItem] = []
    workout_done: bool = False
    workout_notes: Optional[str] = ""
    general_notes: Optional[str] = ""


class DailyLogUpdate(BaseModel):
    body_weight_kg: Optional[float] = None
    food_items: Optional[list[FoodItem]] = None
    workout_done: Optional[bool] = None
    workout_notes: Optional[str] = None
    general_notes: Optional[str] = None


class DailyLogResponse(BaseModel):
    id: int
    client_id: int
    log_date: date
    body_weight_kg: Optional[float] = None
    food_items: list[dict] = []
    total_kcal_consumed: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    workout_done: bool
    workout_notes: Optional[str] = ""
    general_notes: Optional[str] = ""
    kcal_balance: float
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Report ────────────────────────────────────────────────────────────────────

class GenerateReportRequest(BaseModel):
    period_days: int = 30


class ProgressReport(BaseModel):
    client_id: int
    period_days: int
    total_days_logged: int
    weight_trend: list[dict]
    avg_kcal_consumed: float
    kcal_adherence_pct: float
    workout_days: int
    workout_consistency_pct: float
    recommendations: str
