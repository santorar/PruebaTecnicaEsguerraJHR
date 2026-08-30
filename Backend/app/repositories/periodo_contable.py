from sqlalchemy.orm import Session
from app.models.periodo_contable import PeriodoContable
from app.models.general import Estado

def get_periodo_contable_activo(db: Session, id: int) -> PeriodoContable | None:
    estado_activo = db.query(Estado).filter(Estado.nombre == "abierto").first()
    if estado_activo is None:
        raise Exception("Estado 'abierto' no encontrado en la base de datos")

    return db.query(PeriodoContable).filter(PeriodoContable.id == id, PeriodoContable.estado_id == estado_activo.id).first()