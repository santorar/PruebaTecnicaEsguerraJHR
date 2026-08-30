from app.schemas import Tercero as TerceroSchema, TerceroCreate, TerceroUpdate, TipoDocumento as TipoDocumentoSchema
from app.database import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services import tercero as tercero_service
from app.repositories import tercero as tercero_repository, tipo_documento as tipo_documento_repository

router = APIRouter(prefix="/tercero", tags=["tercero"])

@router.get("/", response_model=list[TerceroSchema])
def read_terceros(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return tercero_repository.get_terceros(db, skip, limit)

@router.get("/{tercero_id}", response_model=TerceroSchema)
def read_tercero(tercero_id: int, db: Session = Depends(get_db)):
    db_tercero = tercero_repository.get_tercero(db, tercero_id)
    if db_tercero is None:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")
    return db_tercero

@router.post("/", response_model=TerceroSchema, status_code=201)
def create_tercero(tercero_data: TerceroCreate, db: Session = Depends(get_db)):
    try:
        return tercero_service.create_tercero(db, tercero_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{tercero_id}", response_model=TerceroSchema)
def update_tercero(tercero_id: int, tercero_data: TerceroUpdate, db: Session = Depends(get_db)):
    try:
        return tercero_service.update_tercero(db, tercero_id, tercero_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{tercero_id}", response_model=TerceroSchema)
def delete_tercero(tercero_id: int, db: Session = Depends(get_db)):
    try:
        return tercero_service.delete_tercero(db, tercero_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

router_tipos_documento = APIRouter(prefix="/tipo-documento", tags=["tipo-documento"])

@router_tipos_documento.get("/", response_model=list[TipoDocumentoSchema])
def read_tipos_documento(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return tipo_documento_repository.get_tipos_documento(db, skip, limit)

@router_tipos_documento.get("/{tipo_documento_id}", response_model=TipoDocumentoSchema)
def read_tipo_documento(tipo_documento_id: int, db: Session = Depends(get_db)):
    db_tipo = tipo_documento_repository.get_tipo_documento(db, tipo_documento_id)
    if db_tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    return db_tipo
