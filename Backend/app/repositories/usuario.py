from sqlalchemy.orm import Session
from app.models.usuario import Usuario

def get_usuarios(db: Session, skip: int = 0, limit: int = 100) -> list[Usuario]:
    return db.query(Usuario).filter(Usuario.activo == True).offset(skip).limit(limit).all()

def get_usuario(db: Session, id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == id, Usuario.activo == True).first()

def get_usuario_by_correo(db: Session, correo: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.correo == correo, Usuario.activo == True).first()

def create_usuario(db: Session, nombre: str, correo: str, clave_encriptada: str, empresa_id: int) -> Usuario:
    db_usuario = Usuario(
        nombre=nombre,
        correo=correo,
        clave_encriptada=clave_encriptada,
        empresa_id=empresa_id,
        activo=True
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def update_usuario(db: Session, usuario_id: int, nombre: str, empresa_id: int) -> Usuario | None:
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.activo == True).first()
    if db_usuario is None:
        return None
    db_usuario.nombre = nombre
    db_usuario.empresa_id = empresa_id
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def update_usuario_clave(db: Session, usuario_id: int, clave_encriptada: str) -> Usuario | None:
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.activo == True).first()
    if db_usuario is None:
        return None
    db_usuario.clave_encriptada = clave_encriptada
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: int) -> bool:
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.activo == True).first()
    if db_usuario is None:
        return False
    db_usuario.activo = False
    db.commit()
    return True
