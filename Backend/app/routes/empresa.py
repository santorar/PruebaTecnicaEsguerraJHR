from app.schemas import Empresa as EmpresaSchema, EmpresaCreate, EmpresaUpdate
from app.database import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services import empresa as empresa_service
from app.repositories import empresa as empresa_repository

router = APIRouter(prefix="/empresa", tags=["empresa"])

@router.get("/", response_model=list[EmpresaSchema])
def read_empresas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return empresa_repository.get_empresas(db, skip, limit)

@router.get("/{empresa_id}", response_model=EmpresaSchema)
def read_empresa(empresa_id: int, db: Session = Depends(get_db)):
    db_empresa = empresa_repository.get_empresa(db, empresa_id)
    if db_empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db_empresa

@router.post("/", response_model=EmpresaSchema, status_code=201)
def create_empresa(empresa_data: EmpresaCreate, db: Session = Depends(get_db)):
    try:
        return empresa_service.create_empresa(db, empresa_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{empresa_id}", response_model=EmpresaSchema)
def update_empresa(empresa_id: int, empresa_data: EmpresaUpdate, db: Session = Depends(get_db)):
    try:
        return empresa_service.update_empresa(db, empresa_id, empresa_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{empresa_id}", response_model=EmpresaSchema)
def delete_empresa(empresa_id: int, db: Session = Depends(get_db)):
    try:
        return empresa_service.delete_empresa(db, empresa_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
