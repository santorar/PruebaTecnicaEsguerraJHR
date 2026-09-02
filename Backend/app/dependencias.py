from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.repositories import usuario as usuario_repository
from app.services import auth as auth_service

def obtener_usuario_actual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    encabezado = request.headers.get("authorization", "")
    if not encabezado.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = encabezado[len("Bearer "):].strip()
    usuario_id = auth_service.verificar_token(token)
    if usuario_id is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario = usuario_repository.get_usuario(db, usuario_id)
    if usuario is None or usuario.activo is False:
        raise HTTPException(
            status_code=401,
            detail="Usuario no válido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario
