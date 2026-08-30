from sqlalchemy.orm import Session
from app.models.general import Estado

def get_estado(db: Session, estado_id: int) -> Estado | None:
    return db.query(Estado).filter(Estado.id == estado_id).first()

def get_estado_by_nombre(db: Session, nombre: str) -> Estado | None:
    return db.query(Estado).filter(Estado.nombre == nombre).first()