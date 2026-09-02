from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import usuario as usuario_repository
from app.schemas import LoginRequest, TokenResponse, Usuario as UsuarioSchema, UsuarioCreate
from app.services import auth as auth_service
from app.services.usuario import create_usuario, verificar_clave

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/registro", response_model=UsuarioSchema, status_code=201)
def registro(datos: UsuarioCreate, db: Session = Depends(get_db)):
    return create_usuario(db, datos)

@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    usuario = usuario_repository.get_usuario_by_correo(db, datos.correo)
    if usuario is None or not verificar_clave(datos.clave, usuario.clave_encriptada):
        raise HTTPException(status_code=401, detail="Correo o clave incorrectos")
    if usuario.activo is False:
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    return TokenResponse(
        token=auth_service.generar_token(usuario.id),
        usuario=UsuarioSchema.model_validate(usuario),
    )
