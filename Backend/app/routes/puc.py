from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas import Puc as PucSchema
from app.database import get_db
from app.services import puc as puc_service
from app.services.puc import PucValidationError
from app.repositories import puc as puc_repository


router = APIRouter(prefix="/puc", tags=["puc"])


@router.get("/", response_model=list[PucSchema])
def read_puc(activo: bool | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return puc_repository.get_cuentas(db, activo, skip, limit)


@router.get("/{codigo}", response_model=PucSchema)
def read_cuenta(codigo: str, db: Session = Depends(get_db)):
    cuenta = puc_repository.get_cuenta(db, codigo)
    if cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return cuenta


@router.post("/", response_model=PucSchema, status_code=201)
def create_cuenta(cuenta: PucSchema, db: Session = Depends(get_db)):
    try:
        return puc_service.crear_cuenta(
            db=db,
            codigo=cuenta.codigo,
            nombre=cuenta.nombre,
            naturaleza=cuenta.naturaleza,
            activo=cuenta.activo
        )
    except PucValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.put("/{codigo}", response_model=PucSchema)
def update_cuenta(codigo: str, cuenta: PucSchema, db: Session = Depends(get_db)):
    try:
        return puc_service.actualizar_cuenta(
            db=db,
            codigo=codigo,
            nombre=cuenta.nombre,
            naturaleza=cuenta.naturaleza,
            activo=cuenta.activo
        )
    except PucValidationError as e:
        if e.message == "Cuenta no encontrada":
            raise HTTPException(status_code=404, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)


@router.delete("/{codigo}", response_model=PucSchema)
def delete_cuenta(codigo: str, db: Session = Depends(get_db)):
    try:
        return puc_service.eliminar_cuenta(db=db, codigo=codigo)
    except PucValidationError as e:
        raise HTTPException(status_code=404, detail=e.message)
