
from pydantic import BaseModel

class Puc(BaseModel):
    codigo: str
    nombre: str
    naturaleza: str
    activo: bool = True

    class Config:
        from_attributes = True

