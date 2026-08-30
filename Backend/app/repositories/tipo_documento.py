from sqlalchemy.orm import Session
from app.models.tercero import TipoDocumento

def get_tipos_documento(db: Session, skip: int = 0, limit: int = 100) -> list[TipoDocumento]:
    return db.query(TipoDocumento).offset(skip).limit(limit).all()

def get_tipo_documento(db: Session, id: int) -> TipoDocumento | None:
    return db.query(TipoDocumento).filter(TipoDocumento.id == id).first()
