from sqlalchemy.orm import Session
from app.schemas import UsuarioCreate, UsuarioUpdate, UsuarioUpdateClave
from app.models.usuario import Usuario
from app.repositories import usuario as usuario_repository, empresa as empresa_repository
from fastapi import HTTPException
import bcrypt


def hash_clave(clave: str) -> str:
    return bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_clave(clave: str, clave_encriptada: str) -> bool:
    return bcrypt.checkpw(clave.encode('utf-8'), clave_encriptada.encode('utf-8'))


def create_usuario(db: Session, usuario_data: UsuarioCreate) -> Usuario:
    if usuario_data.clave != usuario_data.confirmacion_clave:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    if len(usuario_data.clave) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    if usuario_repository.get_usuario_by_correo(db, usuario_data.correo) is not None:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo")

    if empresa_repository.get_empresa(db, usuario_data.empresa_id) is None:
        raise HTTPException(status_code=400, detail="La empresa no existe")

    clave_encriptada = hash_clave(usuario_data.clave)

    return usuario_repository.create_usuario(
        db=db,
        nombre=usuario_data.nombre,
        correo=usuario_data.correo,
        clave_encriptada=clave_encriptada,
        empresa_id=usuario_data.empresa_id
    )


def update_usuario(db: Session, usuario_id: int, usuario_data: UsuarioUpdate) -> Usuario:
    db_usuario = usuario_repository.get_usuario(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if empresa_repository.get_empresa(db, usuario_data.empresa_id) is None:
        raise HTTPException(status_code=400, detail="La empresa no existe")

    resultado = usuario_repository.update_usuario(
        db=db,
        usuario_id=usuario_id,
        nombre=usuario_data.nombre,
        empresa_id=usuario_data.empresa_id
    )
    if resultado is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return resultado


def update_usuario_clave(db: Session, usuario_id: int, usuario_data: UsuarioUpdateClave) -> Usuario:
    db_usuario = usuario_repository.get_usuario(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verificar_clave(usuario_data.clave_actual, db_usuario.clave_encriptada):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    if usuario_data.clave_nueva != usuario_data.confirmacion_clave_nueva:
        raise HTTPException(status_code=400, detail="Las contraseñas nuevas no coinciden")

    if len(usuario_data.clave_nueva) < 6:
        raise HTTPException(status_code=400, detail="La contraseña nueva debe tener al menos 6 caracteres")

    clave_encriptada = hash_clave(usuario_data.clave_nueva)

    resultado = usuario_repository.update_usuario_clave(
        db=db,
        usuario_id=usuario_id,
        clave_encriptada=clave_encriptada
    )
    if resultado is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return resultado


def delete_usuario(db: Session, usuario_id: int) -> Usuario:
    db_usuario = usuario_repository.get_usuario(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario_repository.delete_usuario(db, usuario_id)
    return db_usuario
