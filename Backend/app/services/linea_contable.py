from sqlalchemy.orm import Session
from app.schemas import LineaContable as LineaContableSchema
from app.models.comprobante import LineaContable
from app.repositories import linea_contable as linea_repository, comprobante as comprobante_repository, estado as estado_repository, puc as puc_repository
from fastapi import HTTPException


def validar_linea(linea_data: LineaContableSchema, db: Session) -> None:
    if linea_data.debito < 0 or linea_data.credito < 0:
        raise HTTPException(status_code=400, detail="Los valores de débito y crédito no pueden ser negativos")

    if round(linea_data.debito, 2) != linea_data.debito or round(linea_data.credito, 2) != linea_data.credito:
        raise HTTPException(status_code=400, detail="Los valores de débito y crédito no pueden tener más de dos decimales")

    if linea_data.debito > 0 and linea_data.credito > 0:
        raise HTTPException(status_code=400, detail="Una línea contable no puede tener valores de débito y crédito al mismo tiempo")

    cuenta_linea = linea_data.cuenta.strip()
    if not cuenta_linea:
        raise HTTPException(status_code=400, detail="El código de la cuenta no puede estar vacío")

    if not cuenta_linea.isdigit() and len(cuenta_linea) > 1:
        raise HTTPException(status_code=400, detail="El código de la cuenta debe ser numérico o de un solo carácter")

    cuenta_db = puc_repository.get_cuenta(db, cuenta_linea)
    if cuenta_db is None:
        raise HTTPException(status_code=400, detail=f"La cuenta '{cuenta_linea}' no existe en el PUC")

    if cuenta_db.activo is False:
        raise HTTPException(status_code=400, detail=f"La cuenta '{cuenta_linea}' no está activa en el PUC")


def validar_estado_borrador(db: Session, comprobante_id: int) -> None:
    comprobante = comprobante_repository.get_comprobante(db, comprobante_id)
    if comprobante is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    estado = estado_repository.get_estado(db, comprobante.estado_id)
    if estado is None or estado.nombre != "borrador":
        raise HTTPException(status_code=400, detail="Solo se pueden modificar líneas de un comprobante en estado borrador")


def crear_linea(db: Session, comprobante_id: int, linea_data: LineaContableSchema) -> LineaContable:
    validar_estado_borrador(db, comprobante_id)
    validar_linea(linea_data, db)
    
    return linea_repository.create_linea(
        db=db,
        descripcion=linea_data.descripcion,
        debito=linea_data.debito,
        credito=linea_data.credito,
        cuenta=linea_data.cuenta,
        tercero_id=linea_data.tercero_id,
        comprobante_id=comprobante_id
    )


def actualizar_linea(db: Session, comprobante_id: int, linea_id: int, linea_data: LineaContableSchema) -> LineaContable:
    validar_estado_borrador(db, comprobante_id)
    validar_linea(linea_data, db)
    
    db_linea = linea_repository.get_linea_by_id_and_comprobante(db, linea_id, comprobante_id)
    if db_linea is None:
        raise HTTPException(status_code=404, detail="Línea no encontrada en este comprobante")
    
    return linea_repository.update_linea(
        db=db,
        db_linea=db_linea,
        descripcion=linea_data.descripcion,
        debito=linea_data.debito,
        credito=linea_data.credito,
        cuenta=linea_data.cuenta,
        tercero_id=linea_data.tercero_id
    )


def eliminar_linea(db: Session, comprobante_id: int, linea_id: int) -> LineaContable:
    validar_estado_borrador(db, comprobante_id)
    
    db_linea = linea_repository.get_linea_by_id_and_comprobante(db, linea_id, comprobante_id)
    if db_linea is None:
        raise HTTPException(status_code=404, detail="Línea no encontrada en este comprobante")
    
    linea_repository.delete_linea(db, db_linea)
    return db_linea
