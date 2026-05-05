from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/clients/{client_id}/logs", tags=["logs"])


@router.post("/", response_model=schemas.DailyLogResponse, status_code=201)
def create_log(client_id: int, data: schemas.DailyLogCreate, db: Session = Depends(get_db)):
    if not crud.get_client(db, client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return crud.create_or_update_log(db, client_id, data)


@router.get("/", response_model=list[schemas.DailyLogResponse])
def list_logs(
    client_id: int,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    start = start_date or (today - timedelta(days=30))
    end = end_date or today
    return crud.list_logs(db, client_id, start, end)


@router.get("/{log_date}", response_model=schemas.DailyLogResponse)
def get_log(client_id: int, log_date: date, db: Session = Depends(get_db)):
    log = crud.get_log(db, client_id, log_date)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.delete("/{log_date}", status_code=204)
def delete_log(client_id: int, log_date: date, db: Session = Depends(get_db)):
    if not crud.delete_log(db, client_id, log_date):
        raise HTTPException(status_code=404, detail="Log not found")
