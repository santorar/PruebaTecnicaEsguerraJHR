from sqlalchemy.orm import Session
from app.schemas import PeriodoContable as PeriodoContableSchema
from app.models.periodo_contable import PeriodoContable
from app.repositories import periodo_contable as periodo_repository, estado as estado_repository
from fastapi import HTTPException


def create_periodo_contable(db: Session, periodo: PeriodoContableSchema) -> PeriodoContable:
    if periodo.fecha_fin < periodo.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la fecha de inicio")
    return periodo_repository.create_periodo_contable(db, periodo)


def update_periodo_contable(db: Session, periodo_id: int, periodo: PeriodoContableSchema) -> PeriodoContable:
    db_periodo = periodo_repository.get_periodo_contable(db, periodo_id)
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")

    estado = estado_repository.get_estado(db, db_periodo.estado_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="Estado del periodo no encontrado")
    if estado.nombre == "cerrado":
        raise HTTPException(status_code=400, detail="No se puede actualizar un periodo contable cerrado")

    if periodo.fecha_fin < periodo.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la fecha de inicio")

    resultado = periodo_repository.update_periodo_contable(db, periodo_id, periodo)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")
    return resultado


def update_periodo_contable_estado(db: Session, periodo_id: int, estado_id: int) -> PeriodoContable:
    db_periodo = periodo_repository.get_periodo_contable(db, periodo_id)
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")

    estado_actual = estado_repository.get_estado(db, db_periodo.estado_id)
    if estado_actual is None:
        raise HTTPException(status_code=404, detail="Estado actual del periodo no encontrado")
    if estado_actual.nombre == "cerrado":
        raise HTTPException(status_code=400, detail="El periodo contable ya está cerrado, no se puede cambiar de estado")

    estado_nuevo = estado_repository.get_estado(db, estado_id)
    if estado_nuevo is None:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    if estado_nuevo.nombre != "cerrado":
        raise HTTPException(status_code=400, detail="El nuevo estado debe ser 'cerrado'")

    resultado = periodo_repository.update_periodo_contable_estado(db, periodo_id, estado_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")
    return resultado


def delete_periodo_contable(db: Session, periodo_id: int) -> PeriodoContable:
    db_periodo = periodo_repository.get_periodo_contable(db, periodo_id)
    if db_periodo is None:
        raise HTTPException(status_code=404, detail="Periodo contable no encontrado")

    estado = estado_repository.get_estado(db, db_periodo.estado_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="Estado del periodo no encontrado")
    if estado.nombre == "cerrado":
        raise HTTPException(status_code=400, detail="No se puede eliminar un periodo contable cerrado")

    if periodo_repository.tiene_comprobantes(db, periodo_id):
        raise HTTPException(status_code=400, detail="No se puede eliminar un periodo contable con comprobantes creados")

    periodo_repository.delete_periodo_contable(db, periodo_id)
    return db_periodo
