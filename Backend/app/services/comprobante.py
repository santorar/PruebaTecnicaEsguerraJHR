from sqlalchemy.orm import Session
from app.schemas import Comprobante as ComprobanteSchema, LineaContable as LineaContableSchema
from app.models.comprobante import Comprobante
from app.repositories import comprobante as comprobante_repository, periodo_contable as periodo_contable_repository, estado as estado_repository, puc as puc_repository, empresa as empresa_repository, usuario as usuario_repository
from fastapi import HTTPException

def validar_comprobante(comprobante_data: ComprobanteSchema, db: Session) -> None:
    periodo_contable_id = comprobante_data.periodo_contable_id
    if periodo_contable_repository.get_periodo_contable_activo(db, periodo_contable_id) is None:
        raise HTTPException(status_code=400, detail="El periodo contable no está activo o no existe")
    if not comprobante_data.lineas or len(comprobante_data.lineas) < 2:
        raise HTTPException(status_code=400, detail="El comprobante debe tener al menos dos líneas contables")
    if empresa_repository.get_empresa(db, comprobante_data.empresa_id) is None:
        raise HTTPException(status_code=400, detail="La empresa no está activo o no existe")
    if usuario_repository.get_usuario(db, comprobante_data.usuario_id) is None:
        raise HTTPException(status_code=400, detail="El usuario no está activo o no existe")
    for linea in comprobante_data.lineas:
        if linea.debito < 0 or linea.credito < 0:
            raise HTTPException(status_code=400, detail="Los valores de débito y crédito no pueden ser negativos")

        if round(linea.debito, 2) != linea.debito or round(linea.credito, 2) != linea.credito:
            raise HTTPException(status_code=400, detail="Los valores de débito y crédito no pueden tener más de dos decimales")

        if linea.debito > 0 and linea.credito > 0:
            raise HTTPException(status_code=400, detail="Una línea contable no puede tener valores de débito y crédito al mismo tiempo")

        cuenta_linea = linea.cuenta.strip()  # Eliminar espacios en blanco al inicio y al final
        if not cuenta_linea:
            raise HTTPException(status_code=400, detail="El código de la cuenta no puede estar vacío")

        if not cuenta_linea.isdigit() and len(cuenta_linea) > 1:
            raise HTTPException(status_code=400, detail="El código de la cuenta debe ser numérico o de un solo carácter")

        cuenta_db = puc_repository.get_cuenta(db, cuenta_linea)
        if cuenta_db is None:
            raise HTTPException(status_code=400, detail=f"La cuenta '{cuenta_linea}' no existe en el PUC")

        if cuenta_db.activo is False:
            raise HTTPException(status_code=400, detail=f"La cuenta '{cuenta_linea}' no está activa en el PUC")
        
    total_debito = sum(linea.debito for linea in comprobante_data.lineas)
    total_credito = sum(linea.credito for linea in comprobante_data.lineas)

    if total_debito != total_credito:
        raise HTTPException(status_code=400, detail="El total de débito debe ser igual al total de crédito")
    

def create_comprobante(db: Session, comprobante: ComprobanteSchema) -> Comprobante:
    validar_comprobante(comprobante, db)
    return comprobante_repository.create_comprobante(db, comprobante)


def update_comprobante(db: Session, comprobante_id: int, comprobante: ComprobanteSchema) -> Comprobante | None:
    validar_comprobante(comprobante, db)

    estado_borrador = estado_repository.get_estado_by_nombre(db, "borrador")
    estado_anulado = estado_repository.get_estado_by_nombre(db, "anulado")
    estado_contabilizado = estado_repository.get_estado_by_nombre(db, "contabilizado")
    comprobante_actual = comprobante_repository.get_comprobante(db, comprobante_id)
    if comprobante_actual is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    if comprobante_actual.estado_id == estado_borrador.id:
        return comprobante_repository.update_comprobante(db, comprobante_id, comprobante)
    if comprobante_actual.estado_id == estado_anulado.id:
        raise HTTPException(status_code=400, detail="El comprobante ya esta anulado no se puede actualizar")

    # Creacion del comprobante de anulación
    comprobante_anulacion = ComprobanteSchema(
        descripcion=f"Anulación de comprobante {comprobante_actual.id}",
        empresa_id=comprobante_actual.empresa_id,
        periodo_contable_id=comprobante_actual.periodo_contable_id,
        usuario_id=comprobante_actual.usuario_id,
        estado_id=estado_contabilizado.id,
        comprobante_original_id=comprobante_actual.id
    )
    for linea in comprobante_actual.lineas:
        linea_anulacion = LineaContableSchema(
            descripcion=f"Anulación de línea {linea.id}",
            debito=linea.credito,
            credito=linea.debito,
            cuenta=linea.cuenta,
            tercero_id=linea.tercero_id
        )
        comprobante_anulacion.lineas.append(linea_anulacion)
    db_comprobante_anulacion = comprobante_repository.create_comprobante(db, comprobante_anulacion)
    # Creacion del comprobante de remplazo
    comprobante.comprobante_original_id = comprobante_actual.id
    db_comprobante_sustituto = comprobante_repository.create_comprobante(db, comprobante)
    comprobante_repository.update_comprobante_anulacion(
        db, 
        comprobante_actual, 
        comprobante_reversor_id=db_comprobante_anulacion.id, 
        comprobante_sustituto_id=db_comprobante_sustituto.id
    )
    return db_comprobante_sustituto

    

def update_comprobante_estado(db: Session, comprobante_id: int, estado_id: int) -> Comprobante | None:
    db_comprobante = comprobante_repository.get_comprobante(db, comprobante_id)
    if db_comprobante is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    estado_nuevo = estado_repository.get_estado(db, estado_id)
    if estado_nuevo is None:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    estado_actual = estado_repository.get_estado(db, db_comprobante.estado_id)
    if estado_actual is None:
        raise HTTPException(status_code=404, detail="Estado actual del comprobante no encontrado")
    if estado_actual.nombre != "borrador":
        raise HTTPException(status_code=400, detail="Solo se pueden cambiar estados de comprobantes en estado 'borrador'")
    if estado_nuevo.nombre not in ["contabilizado", "anulado"]:
        raise HTTPException(status_code=400, detail="El nuevo estado debe ser 'contabilizado' o 'anulado'")
    return comprobante_repository.update_comprobante_estado(db, comprobante_id, estado_id)

def delete_comprobante(db: Session, comprobante_id: int):
    db_comprobante = comprobante_repository.get_comprobante(db, comprobante_id)
    if db_comprobante is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    estado_comprobante = estado_repository.get_estado(db, db_comprobante.estado_id)
    if estado_comprobante and estado_comprobante.nombre == "borrador":
        return comprobante_repository.delete_comprobante(db, comprobante_id)
    raise HTTPException(status_code=400, detail="No se puede borrar un comprobante que no sea un borrador")
