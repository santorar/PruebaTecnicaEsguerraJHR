from sqlalchemy.orm import Session, joinedload
from app.schemas import LibroMayorRequest, LibroMayorResponse
from decimal import Decimal
from app.repositories import comprobante as comprobante_repository

def get_libro_mayor(db: Session, request: LibroMayorRequest) -> list[LibroMayorResponse]:
    resultado = []
    acumulado = Decimal('0')
    lineas = comprobante_repository.get_comprobante_libro_mayor(db, request)
    
    for linea in lineas:
        acumulado = acumulado + linea.debito - linea.credito
        
        respuesta = LibroMayorResponse(
            fecha=linea.comprobante.fecha_contabilizacion.date(),
            referencia=linea.comprobante_id,
            descripcion=linea.descripcion or "",
            tercero=linea.tercero.nombre if linea.tercero else None,
            debito=linea.debito,
            credito=linea.credito,
            acumulado=acumulado
        )
        resultado.append(respuesta)
    
    return resultado