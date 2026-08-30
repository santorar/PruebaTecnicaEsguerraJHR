from sqlalchemy.orm import Session
from app.models.empresa import Empresa

def get_empresas(db: Session, skip: int = 0, limit: int = 100) -> list[Empresa]:
    return db.query(Empresa).filter(Empresa.activo == True).offset(skip).limit(limit).all()

def get_empresa(db: Session, id: int) -> Empresa | None:
    return db.query(Empresa).filter(Empresa.id == id, Empresa.activo == True).first()

def get_empresa_by_nit(db: Session, nit: str) -> Empresa | None:
    return db.query(Empresa).filter(Empresa.nit == nit, Empresa.activo == True).first()

def create_empresa(db: Session, nombre: str, nit: str, dv: int) -> Empresa:
    db_empresa = Empresa(
        nombre=nombre,
        nit=nit,
        dv=dv,
        activo=True
    )
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

def update_empresa(db: Session, empresa_id: int, nombre: str) -> Empresa | None:
    db_empresa = db.query(Empresa).filter(Empresa.id == empresa_id, Empresa.activo == True).first()
    if db_empresa is None:
        return None
    db_empresa.nombre = nombre
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

def delete_empresa(db: Session, empresa_id: int) -> bool:
    db_empresa = db.query(Empresa).filter(Empresa.id == empresa_id, Empresa.activo == True).first()
    if db_empresa is None:
        return False
    db_empresa.activo = False
    db.commit()
    return True
