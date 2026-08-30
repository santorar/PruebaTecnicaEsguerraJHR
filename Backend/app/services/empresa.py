from sqlalchemy.orm import Session
from app.schemas import EmpresaCreate, EmpresaUpdate
from app.models.empresa import Empresa
from app.repositories import empresa as empresa_repository
from fastapi import HTTPException


def calcular_dv(nit: str) -> int:
    nit_limpio = ''.join(c for c in nit if c.isdigit())
    if not nit_limpio:
        raise ValueError("El NIT debe contener al menos un dígito")

    pesos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    nit_invertido = nit_limpio[::-1]

    suma = 0
    for i, digito in enumerate(nit_invertido):
        if i >= len(pesos):
            break
        suma += int(digito) * pesos[i]

    residuo = suma % 11
    if residuo <= 1:
        return residuo
    return 11 - residuo


def validar_nit(nit: str) -> None:
    nit_limpio = ''.join(c for c in nit if c.isdigit())
    if not nit_limpio:
        raise HTTPException(status_code=400, detail="El NIT debe contener dígitos numéricos")
    if len(nit_limpio) < 2:
        raise HTTPException(status_code=400, detail="El NIT debe tener al menos 2 dígitos")


def create_empresa(db: Session, empresa_data: EmpresaCreate) -> Empresa:
    validar_nit(empresa_data.nit)

    if empresa_repository.get_empresa_by_nit(db, empresa_data.nit) is not None:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con ese NIT")

    dv_calculado = calcular_dv(empresa_data.nit)

    return empresa_repository.create_empresa(
        db=db,
        nombre=empresa_data.nombre,
        nit=empresa_data.nit,
        dv=dv_calculado
    )


def update_empresa(db: Session, empresa_id: int, empresa_data: EmpresaUpdate) -> Empresa:
    db_empresa = empresa_repository.get_empresa(db, empresa_id)
    if db_empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    resultado = empresa_repository.update_empresa(db, empresa_id, empresa_data.nombre)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return resultado


def delete_empresa(db: Session, empresa_id: int) -> Empresa:
    db_empresa = empresa_repository.get_empresa(db, empresa_id)
    if db_empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    empresa_repository.delete_empresa(db, empresa_id)
    return db_empresa
