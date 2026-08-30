from app.schemas import Estado as EstadoSchema
from app.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.repositories import estado as estado_repository

router = APIRouter(prefix="/estado", tags=["estado"])

@router.get("/", response_model=list[EstadoSchema])
def read_estados(db: Session = Depends(get_db)):
    return estado_repository.get_estados(db)
