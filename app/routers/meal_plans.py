import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, ai_service
from ..database import get_db

router = APIRouter(prefix="/api/clients/{client_id}/meal-plans", tags=["meal-plans"])


def _serialize(plan) -> dict:
    return {
        "id": plan.id,
        "client_id": plan.client_id,
        "plan_data": json.loads(plan.plan_data) if isinstance(plan.plan_data, str) else plan.plan_data,
        "generated_at": plan.generated_at,
        "is_active": plan.is_active,
    }


@router.post("/generate", response_model=schemas.MealPlanResponse, status_code=201)
async def generate_meal_plan(client_id: int, db: Session = Depends(get_db)):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    plan_data = await ai_service.generate_meal_plan(client)
    plan = crud.create_meal_plan(db, client_id, plan_data)
    return _serialize(plan)


@router.get("/active", response_model=schemas.MealPlanResponse)
def get_active_meal_plan(client_id: int, db: Session = Depends(get_db)):
    plan = crud.get_active_meal_plan(db, client_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No active meal plan")
    return _serialize(plan)


@router.get("/", response_model=list[schemas.MealPlanResponse])
def list_meal_plans(client_id: int, db: Session = Depends(get_db)):
    return [_serialize(p) for p in crud.list_meal_plans(db, client_id)]
