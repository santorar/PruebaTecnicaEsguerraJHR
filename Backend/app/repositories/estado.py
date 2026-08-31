from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from app.models.general import Estado, UvtValor, UvtActualizacionLog

def get_estados(db: Session) -> list[Estado]:
    return db.query(Estado).all()

def get_estado(db: Session, estado_id: int) -> Estado | None:
    return db.query(Estado).filter(Estado.id == estado_id).first()

def get_estado_by_nombre(db: Session, nombre: str) -> Estado | None:
    return db.query(Estado).filter(Estado.nombre == nombre).first()

def get_valor_uvt(db: Session, anio: int) -> UvtValor | None:
    return db.query(UvtValor).filter(UvtValor.anio == anio).first()

def get_valores_uvt(db: Session) -> list[UvtValor]:
    return db.query(UvtValor).order_by(UvtValor.anio).all()

def upsert_valor_uvt(db: Session, anio: int, valor: Decimal, fuente: str) -> UvtValor:
    registro = get_valor_uvt(db, anio)
    if registro is None:
        registro = UvtValor(anio=anio, valor=valor, fuente=fuente, fecha_actualizacion=datetime.now())
        db.add(registro)
    else:
        registro.valor = valor
        registro.fuente = fuente
        registro.fecha_actualizacion = datetime.now()
    db.commit()
    db.refresh(registro)
    return registro

def registrar_actualizacion_uvt(db: Session, fuente: str, exitoso: bool, anio: int | None, valor: Decimal | None, detalle: str | None) -> UvtActualizacionLog:
    registro = UvtActualizacionLog(fuente=fuente, exitoso=exitoso, anio=anio, valor=valor, detalle=detalle)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

def get_logs_actualizacion_uvt(db: Session, skip: int = 0, limit: int = 50) -> list[UvtActualizacionLog]:
    return db.query(UvtActualizacionLog).order_by(UvtActualizacionLog.id.desc()).offset(skip).limit(limit).all()