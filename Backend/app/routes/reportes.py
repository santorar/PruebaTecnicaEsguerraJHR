from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.database import get_db
from app.schemas import (
    LibroMayorRequest,
    LibroMayorResponse,
    ExogenaGenerarRequest,
    ExogenaGeneracionResponse,
    ExogenaUvtValorResponse,
    ExogenaUvtLogResponse,
)
from sqlalchemy.orm import Session
from app.services import reportes as reportes_service
from app.dependencias import obtener_usuario_actual

router = APIRouter(prefix="/libro_mayor", tags=["libro_mayor"], dependencies=[Depends(obtener_usuario_actual)])

@router.post("/", response_model=list[LibroMayorResponse])
def get_libro_mayor(request: LibroMayorRequest, db: Session = Depends(get_db)):
    return reportes_service.get_libro_mayor(db, request)

router_exogena = APIRouter(prefix="/api/exogena", tags=["exogena"])

@router_exogena.post("/generar")
def generar_exogena(request: ExogenaGenerarRequest, db: Session = Depends(get_db), _: None = Depends(obtener_usuario_actual)):
    try:
        generacion = reportes_service.generar_exogena(db, request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return FileResponse(
        path=generacion.ruta_archivo,
        media_type="application/xml",
        filename=generacion.nombre_archivo
    )

@router_exogena.get("/historial", response_model=list[ExogenaGeneracionResponse])
def listar_historial_exogena(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: None = Depends(obtener_usuario_actual)):
    return reportes_service.listar_generaciones_exogena(db, skip, limit)

@router_exogena.get("/historial/{generacion_id}/archivo")
def descargar_archivo_exogena(generacion_id: int, db: Session = Depends(get_db), _: None = Depends(obtener_usuario_actual)):
    try:
        generacion = reportes_service.obtener_generacion_exogena(db, generacion_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return FileResponse(
        path=generacion.ruta_archivo,
        media_type="application/xml",
        filename=generacion.nombre_archivo
    )

@router_exogena.get("/uvt", response_model=list[ExogenaUvtValorResponse])
def listar_valores_uvt(db: Session = Depends(get_db), _: None = Depends(obtener_usuario_actual)):
    return reportes_service.listar_valores_uvt(db)

@router_exogena.get("/uvt/historial", response_model=list[ExogenaUvtLogResponse])
def listar_historial_uvt(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), _: None = Depends(obtener_usuario_actual)):
    return reportes_service.listar_logs_actualizacion_uvt(db, skip, limit)

@router_exogena.post("/uvt/actualizar", status_code=202)
def actualizar_valores_uvt(anio: int | None = None, _: None = Depends(obtener_usuario_actual)):
    programado = reportes_service.programar_sincronizacion_uvt([anio] if anio else None)
    detalle = "Sincronización de UVT programada en segundo plano" if programado else "Ya existe una sincronización de UVT en curso"
    return {"detail": detalle}

@router_exogena.get("/uvt-simulador/{anio}")
def proveedor_simulado_uvt(anio: int):
    valor = reportes_service.CATALOGO_UVT_SIMULADOR.get(anio)
    if valor is None:
        raise HTTPException(status_code=404, detail=f"El proveedor simulado no tiene valor de UVT para el año {anio}")
    return {"anio": anio, "valor": float(valor)}
