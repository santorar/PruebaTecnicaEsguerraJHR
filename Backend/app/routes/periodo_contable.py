from app.schemas import PeriodoContable as PeriodoContableSchema
from app.database import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services import periodo_contable as periodo_service
from app.repositories import periodo_contable as periodo_repository

router = APIRouter(prefix="/periodo-contable", tags=["periodo-contable"])

@router.get("/", response_model=list[PeriodoContableSchema])
def read_periodos_contables(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return periodo_repository.get_periodos_contables(db, skip, limit)

@router.get("/{periodo_id}", response_model=PeriodoContableSchema)
def read_periodo_contable(periodo_id: int, db: Session = Depends(get_db)):
    db_periodo = periodo_repository.get_periodo_contable(db, periodo_id)
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")
    return db_periodo

@router.post("/", response_model=PeriodoContableSchema, status_code=201)
def create_periodo_contable(periodo_data: PeriodoContableSchema, db: Session = Depends(get_db)):
    try:
        return periodo_service.create_periodo_contable(db, periodo_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{periodo_id}", response_model=PeriodoContableSchema)
def update_periodo_contable(periodo_id: int, periodo_data: PeriodoContableSchema, db: Session = Depends(get_db)):
    try:
        return periodo_service.update_periodo_contable(db, periodo_id, periodo_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{periodo_id}/estado/{estado_id}", response_model=PeriodoContableSchema)
def update_periodo_contable_estado(periodo_id: int, estado_id: int, db: Session = Depends(get_db)):
    try:
        return periodo_service.update_periodo_contable_estado(db, periodo_id, estado_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{periodo_id}", response_model=PeriodoContableSchema)
def delete_periodo_contable(periodo_id: int, db: Session = Depends(get_db)):
    try:
        return periodo_service.delete_periodo_contable(db, periodo_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
