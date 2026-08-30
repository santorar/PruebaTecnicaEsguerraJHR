from app.database import Base
from app.models import Comprobante, Empresa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False, index=True)
    correo: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    clave_encriptada: Mapped[str] = mapped_column(nullable=False)

    empresa_id: Mapped[int] = mapped_column(ForeignKey('empresa.id'))
    empresa: Mapped['Empresa'] = relationship(back_populates='usuarios')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='usuario')