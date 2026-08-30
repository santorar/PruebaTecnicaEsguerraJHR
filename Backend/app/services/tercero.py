from sqlalchemy.orm import Session
from app.schemas import TerceroCreate, TerceroUpdate
from app.models.tercero import Tercero
from app.repositories import tercero as tercero_repository, tipo_documento as tipo_documento_repository
from fastapi import HTTPException


def validar_documento(numero_documento: str) -> None:
    if not numero_documento or not numero_documento.strip():
        raise HTTPException(status_code=400, detail="El número de documento no puede estar vacío")
    if len(numero_documento.strip()) < 3:
        raise HTTPException(status_code=400, detail="El número de documento debe tener al menos 3 caracteres")


def create_tercero(db: Session, tercero_data: TerceroCreate) -> Tercero:
    validar_documento(tercero_data.numero_documento)

    if tipo_documento_repository.get_tipo_documento(db, tercero_data.tipo_documento_id) is None:
        raise HTTPException(status_code=400, detail="El tipo de documento no existe")

    if tercero_repository.get_tercero_by_documento(db, tercero_data.numero_documento, tercero_data.tipo_documento_id) is not None:
        raise HTTPException(status_code=400, detail="Ya existe un tercero con ese número de documento y tipo de documento")

    return tercero_repository.create_tercero(
        db=db,
        nombre=tercero_data.nombre,
        numero_documento=tercero_data.numero_documento,
        tipo_documento_id=tercero_data.tipo_documento_id
    )


def update_tercero(db: Session, tercero_id: int, tercero_data: TerceroUpdate) -> Tercero:
    validar_documento(tercero_data.numero_documento)

    if tipo_documento_repository.get_tipo_documento(db, tercero_data.tipo_documento_id) is None:
        raise HTTPException(status_code=400, detail="El tipo de documento no existe")

    tercero_existente = tercero_repository.get_tercero_by_documento(db, tercero_data.numero_documento, tercero_data.tipo_documento_id)
    if tercero_existente is not None and tercero_existente.id != tercero_id:
        raise HTTPException(status_code=400, detail="Ya existe un tercero con ese número de documento y tipo de documento")

    resultado = tercero_repository.update_tercero(
        db=db,
        tercero_id=tercero_id,
        nombre=tercero_data.nombre,
        numero_documento=tercero_data.numero_documento,
        tipo_documento_id=tercero_data.tipo_documento_id
    )
    if resultado is None:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")
    return resultado


def delete_tercero(db: Session, tercero_id: int) -> Tercero:
    db_tercero = tercero_repository.get_tercero(db, tercero_id)
    if db_tercero is None:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    tercero_repository.delete_tercero(db, tercero_id)
    return db_tercero
