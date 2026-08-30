from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Usuario, Comprobante

class Empresa(Base):
    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    nit: Mapped[str] = mapped_column(nullable=False)
    dv: Mapped[int] = mapped_column(nullable=False)

    usuarios: Mapped[list['Usuario']] = relationship(back_populates='empresa')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='empresa')