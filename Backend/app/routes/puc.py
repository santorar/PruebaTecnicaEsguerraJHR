from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas import Puc as PucSchema
from app.database import get_db
from app.services import puc as puc_service
from app.services.puc import PucValidationError
from app.repositories import puc as puc_repository


router = APIRouter(prefix="/puc", tags=["puc"])

@router.get("/", response_model=list[PucSchema])
async def read_puc(activo: bool | None = None, skip: int = 0, limit: int = 100):
    db = next(get_db())
    return puc.get_cuentas(db, activo, skip, limit)

@router.get("/{codigo}", response_model=PucSchema)
async def read_cuenta(codigo: str):
    db = next(get_db())
    cuenta = puc.get_cuenta(db, codigo)
    if cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return cuenta

@router.post("/", response_model=PucSchema)
async def create_cuenta(cuenta: PucSchema):
    db = next(get_db())
    if puc.get_cuenta(db, cuenta.codigo):
        raise HTTPException(status_code=400, detail="Cuenta ya existe")
    if cuenta.activo is None:
        cuenta.activo = True
    if cuenta.naturaleza not in ['D', 'C']:
        raise HTTPException(status_code=400, detail="Naturaleza debe ser 'D' o 'C'")
    if cuenta.codigo == "":
        raise HTTPException(status_code=400, detail="Código no puede estar vacío")
    if not cuenta.codigo.isdigit() and len(cuenta.codigo) > 1:
        raise HTTPException(status_code=400, detail="Código debe ser numérico o de un solo carácter")

    try:
        return puc.create_cuenta(db, cuenta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{codigo}", response_model=PucSchema)
async def update_cuenta(codigo: str, cuenta: PucSchema):
    db = next(get_db())
    db_cuenta = puc.get_cuenta(db, codigo)
    if db_cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if cuenta.naturaleza not in ['D', 'C']:
        raise HTTPException(status_code=400, detail="Naturaleza debe ser 'D' o 'C'")
    if cuenta.codigo == "":
        raise HTTPException(status_code=400, detail="Código no puede estar vacío")
    if not cuenta.codigo.isdigit() and len(cuenta.codigo) > 1:
        raise HTTPException(status_code=400, detail="Código debe ser numérico o de un solo carácter")

    try:
        return puc.update_cuenta(db, codigo, cuenta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{codigo}", response_model=PucSchema)
async def delete_cuenta(codigo: str):
    db = next(get_db())
    db_cuenta = puc.get_cuenta(db, codigo)
    if db_cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    try:
        success = puc.delete_cuenta(db, codigo)
        if not success:
            raise HTTPException(status_code=500, detail="Error al eliminar la cuenta")
        return db_cuenta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
