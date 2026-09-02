from app.schemas import Comprobante as ComprobanteSchema, LineaContable as LineaContableSchema
from app.database import get_db
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services import comprobante as comprobante_service, linea_contable as linea_service
from app.repositories import comprobante as comprobante_repository


from app.dependencias import obtener_usuario_actual

router = APIRouter(prefix="/comprobante", tags=["comprobante"], dependencies=[Depends(obtener_usuario_actual)])

@router.get("/", response_model=list[ComprobanteSchema])
def read_comprobantes(estado_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return comprobante_repository.get_comprobantes(db, estado_id, skip, limit)

@router.get("/{comprobante_id}", response_model=ComprobanteSchema)
def read_comprobante(comprobante_id: int, db: Session = Depends(get_db)):
    db_comprobante = comprobante_repository.get_comprobante(db, comprobante_id)
    if db_comprobante is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return db_comprobante

@router.post("/", response_model=ComprobanteSchema)
def create_comprobante(comprobante_data: ComprobanteSchema, db: Session = Depends(get_db)):
    try:
        return comprobante_service.create_comprobante(db, comprobante_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{comprobante_id}/estado/{estado_id}", response_model=ComprobanteSchema)
def update_comprobante_estado(comprobante_id: int, estado_id: int, db: Session = Depends(get_db)):
    try:
        return comprobante_service.update_comprobante_estado(db, comprobante_id, estado_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{comprobante_id}", response_model=ComprobanteSchema)
def update_comprobante(comprobante_id: int, comprobante_data: ComprobanteSchema, db: Session = Depends(get_db)):
    try:
        return comprobante_service.update_comprobante(db, comprobante_id, comprobante_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{comprobante_id}", status_code=200)
def delete_comprobante(comprobante_id: int, db: Session = Depends(get_db)):
    try:
        comprobante_service.delete_comprobante(db, comprobante_id)
        return {"detail": "Comprobante eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{comprobante_id}/linea/", response_model=list[LineaContableSchema])
def read_lineas(comprobante_id: int, db: Session = Depends(get_db)):
    from app.repositories import linea_contable as linea_repository
    return linea_repository.get_lineas_comprobante(db, comprobante_id)


@router.get("/{comprobante_id}/linea/{linea_id}", response_model=LineaContableSchema)
def read_linea(comprobante_id: int, linea_id: int, db: Session = Depends(get_db)):
    from app.repositories import linea_contable as linea_repository
    db_linea = linea_repository.get_linea_by_id_and_comprobante(db, linea_id, comprobante_id)
    if db_linea is None:
        raise HTTPException(status_code=404, detail="Línea no encontrada en este comprobante")
    return db_linea


@router.post("/{comprobante_id}/linea/", response_model=LineaContableSchema, status_code=201)
def create_linea(comprobante_id: int, linea_data: LineaContableSchema, db: Session = Depends(get_db)):
    try:
        return linea_service.crear_linea(db, comprobante_id, linea_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{comprobante_id}/linea/{linea_id}", response_model=LineaContableSchema)
def update_linea(comprobante_id: int, linea_id: int, linea_data: LineaContableSchema, db: Session = Depends(get_db)):
    try:
        return linea_service.actualizar_linea(db, comprobante_id, linea_id, linea_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{comprobante_id}/linea/{linea_id}", response_model=LineaContableSchema)
def delete_linea(comprobante_id: int, linea_id: int, db: Session = Depends(get_db)):
    try:
        return linea_service.eliminar_linea(db, comprobante_id, linea_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))