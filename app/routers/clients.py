import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/", response_model=list[schemas.ClientListItem])
def list_clients(db: Session = Depends(get_db)):
    return crud.list_clients(db)


@router.post("/", response_model=schemas.ClientResponse, status_code=201)
def create_client(data: schemas.ClientCreate, db: Session = Depends(get_db)):
    return crud.create_client(db, data)


@router.get("/{client_id}", response_model=schemas.ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=schemas.ClientResponse)
def update_client(client_id: int, data: schemas.ClientUpdate, db: Session = Depends(get_db)):
    client = crud.update_client(db, client_id, data)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    if not crud.delete_client(db, client_id):
        raise HTTPException(status_code=404, detail="Client not found")
