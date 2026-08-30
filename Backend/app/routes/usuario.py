from app.schemas import Usuario as UsuarioSchema, UsuarioCreate, UsuarioUpdate, UsuarioUpdateClave
from app.database import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services import usuario as usuario_service
from app.repositories import usuario as usuario_repository

router = APIRouter(prefix="/usuario", tags=["usuario"])

@router.get("/", response_model=list[UsuarioSchema])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return usuario_repository.get_usuarios(db, skip, limit)

@router.get("/{usuario_id}", response_model=UsuarioSchema)
def read_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = usuario_repository.get_usuario(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@router.post("/", response_model=UsuarioSchema, status_code=201)
def create_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return usuario_service.create_usuario(db, usuario_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{usuario_id}", response_model=UsuarioSchema)
def update_usuario(usuario_id: int, usuario_data: UsuarioUpdate, db: Session = Depends(get_db)):
    try:
        return usuario_service.update_usuario(db, usuario_id, usuario_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{usuario_id}/clave", response_model=UsuarioSchema)
def update_usuario_clave(usuario_id: int, usuario_data: UsuarioUpdateClave, db: Session = Depends(get_db)):
    try:
        return usuario_service.update_usuario_clave(db, usuario_id, usuario_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{usuario_id}", response_model=UsuarioSchema)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    try:
        return usuario_service.delete_usuario(db, usuario_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
