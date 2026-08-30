from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import PeriodoContable, Comprobante

class Estado(Base):
    __tablename__: str = "estado"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)

    periodos: Mapped[list['PeriodoContable']] = relationship(back_populates='estado')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='estado')