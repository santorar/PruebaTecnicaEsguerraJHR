from sqlalchemy.orm import Session
from app.models.tercero import Tercero

def get_terceros(db: Session, skip: int = 0, limit: int = 100) -> list[Tercero]:
    return db.query(Tercero).filter(Tercero.activo == True).offset(skip).limit(limit).all()

def get_tercero(db: Session, id: int) -> Tercero | None:
    return db.query(Tercero).filter(Tercero.id == id, Tercero.activo == True).first()

def get_tercero_by_documento(db: Session, numero_documento: str, tipo_documento_id: int) -> Tercero | None:
    return db.query(Tercero).filter(
        Tercero.numero_documento == numero_documento,
        Tercero.tipo_documento_id == tipo_documento_id,
        Tercero.activo == True
    ).first()

def create_tercero(db: Session, nombre: str, numero_documento: str, tipo_documento_id: int) -> Tercero:
    db_tercero = Tercero(
        nombre=nombre,
        numero_documento=numero_documento,
        tipo_documento_id=tipo_documento_id,
        activo=True
    )
    db.add(db_tercero)
    db.commit()
    db.refresh(db_tercero)
    return db_tercero

def update_tercero(db: Session, tercero_id: int, nombre: str, numero_documento: str, tipo_documento_id: int) -> Tercero | None:
    db_tercero = db.query(Tercero).filter(Tercero.id == tercero_id, Tercero.activo == True).first()
    if db_tercero is None:
        return None
    db_tercero.nombre = nombre
    db_tercero.numero_documento = numero_documento
    db_tercero.tipo_documento_id = tipo_documento_id
    db.commit()
    db.refresh(db_tercero)
    return db_tercero

def delete_tercero(db: Session, tercero_id: int) -> bool:
    db_tercero = db.query(Tercero).filter(Tercero.id == tercero_id, Tercero.activo == True).first()
    if db_tercero is None:
        return False
    db_tercero.activo = False
    db.commit()
    return True
