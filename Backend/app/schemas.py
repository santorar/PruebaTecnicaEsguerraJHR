
from pydantic import BaseModel

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