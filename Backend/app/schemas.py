
from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional


class Empresa(BaseModel):
    id: int | None = None
    nombre: str
    nit: str
    dv: int | None = None
    activo: bool | None = None

    class Config:
        from_attributes = True

class EmpresaCreate(BaseModel):
    nombre: str
    nit: str

class EmpresaUpdate(BaseModel):
    nombre: str

class Usuario(BaseModel):
    id: int | None = None
    nombre: str
    correo: str
    empresa_id: int
    activo: bool | None = None

    class Config:
        from_attributes = True

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    clave: str
    confirmacion_clave: str
    empresa_id: int

    @field_validator('correo')
    @classmethod
    def validar_correo(cls, v):
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Correo electrónico inválido')
        return v

class UsuarioUpdate(BaseModel):
    nombre: str
    empresa_id: int

class UsuarioUpdateClave(BaseModel):
    clave_actual: str
    clave_nueva: str
    confirmacion_clave_nueva: str

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
    fecha_creacion: datetime | None = None
    fecha_actualizacion: datetime | None = None
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

class TipoDocumento(BaseModel):
    id: int | None = None
    nombre: str

    class Config:
        from_attributes = True

class Tercero(BaseModel):
    id: int | None = None
    nombre: str
    numero_documento: str
    tipo_documento_id: int
    activo: bool | None = None

    class Config:
        from_attributes = True

class TerceroCreate(BaseModel):
    nombre: str
    numero_documento: str
    tipo_documento_id: int

class TerceroUpdate(BaseModel):
    nombre: str
    numero_documento: str
    tipo_documento_id: int