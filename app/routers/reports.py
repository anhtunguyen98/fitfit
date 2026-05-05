from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, ai_service
from ..database import get_db

router = APIRouter(prefix="/api/clients/{client_id}/reports", tags=["reports"])


@router.post("/generate", response_model=schemas.ProgressReport)
async def generate_report(
    client_id: int,
    body: schemas.GenerateReportRequest = None,
    db: Session = Depends(get_db),
):
    if body is None:
        body = schemas.GenerateReportRequest()

    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    today = date.today()
    start = today - timedelta(days=body.period_days)
    logs = crud.list_logs(db, client_id, start, today)

    weight_trend = [
        {"date": str(l.log_date), "weight_kg": l.body_weight_kg}
        for l in sorted(logs, key=lambda x: x.log_date)
        if l.body_weight_kg is not None
    ]

    kcals = [l.total_kcal_consumed for l in logs if l.total_kcal_consumed]
    avg_kcal = round(sum(kcals) / len(kcals), 1) if kcals else 0.0

    total = len(logs)
    adherence = round(
        sum(1 for l in logs if abs(l.kcal_balance) <= 200) / total * 100, 1
    ) if total else 0.0

    workout_days = sum(1 for l in logs if l.workout_done)
    consistency = round(workout_days / total * 100, 1) if total else 0.0

    recommendations = await ai_service.generate_progress_report(client, logs, body.period_days)

    return schemas.ProgressReport(
        client_id=client_id,
        period_days=body.period_days,
        total_days_logged=total,
        weight_trend=weight_trend,
        avg_kcal_consumed=avg_kcal,
        kcal_adherence_pct=adherence,
        workout_days=workout_days,
        workout_consistency_pct=consistency,
        recommendations=recommendations,
    )
