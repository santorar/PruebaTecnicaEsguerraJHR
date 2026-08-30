
from pydantic import BaseModel
from datetime import date
from typing import Optional


class Estado(BaseModel):
    id: int | None = None
    nombre: str

    class Config:
        from_attributes = True

class PeriodoContable(BaseModel):
    id: int | None = None
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    estado_id: int | None = None

    estado: Optional[Estado] = None

    class Config:
        from_attributes = True

class Puc(BaseModel):
    codigo: str
    nombre: str
    naturaleza: str
    activo: bool = True

    class Config:
        from_attributes = True

class LineaContable(BaseModel):
    id: int | None = None
    descripcion: str | None = None
    debito: float = 0
    credito: float = 0
    cuenta: str
    tercero_id: int | None = None
    comprobante_id: int | None = None

    class Config:
        from_attributes = True

class Comprobante(BaseModel):
    id: int | None = None
    descripcion: str | None = None
    fecha_creacion: str | None = None
    fecha_actualizacion: str | None = None
    empresa_id: int
    periodo_contable_id: int
    usuario_id: int
    estado_id: int | None = None
    lineas: list[LineaContable] = []
    comprobante_original_id: int | None = None
    comprobante_reversor_id: int | None = None
    comprobante_sustituto_id: int | None = None

    class Config:
        from_attributes = True