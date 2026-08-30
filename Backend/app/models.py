from datetime import date, datetime
from decimal import Decimal
from typing import Any
from app.database import Base
from sqlalchemy import CheckConstraint, ForeignKey, CHAR, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Empresa(Base):
    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    nit: Mapped[str] = mapped_column(nullable=False)
    dv: Mapped[int] = mapped_column(nullable=False)

    usuarios: Mapped[list['Usuario']] = relationship(back_populates='empresa')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='empresa')


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False, index=True)
    correo: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    clave_encriptada: Mapped[str] = mapped_column(nullable=False)

    empresa_id: Mapped[int] = mapped_column(ForeignKey('empresa.id'))
    empresa: Mapped['Empresa'] = relationship(back_populates='usuarios')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='usuario')


class Puc(Base):
    __tablename__: str = "puc"

    codigo: Mapped[str] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    naturaleza: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)

    __table_args__: tuple[Any, ...] = (
        CheckConstraint(
            "naturaleza IN ('D', 'C')", name='chk_naturaleza'
        ),
    )

    lineas: Mapped[list['LineaContable']] = relationship(back_populates='cuenta_rel')


class Estado(Base):
    __tablename__: str = "estado"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)

    periodos: Mapped[list['PeriodoContable']] = relationship(back_populates='estado')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='estado')


class PeriodoContable(Base):
    __tablename__: str = "periodo_contable"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(nullable=False)
    fecha_fin: Mapped[date] = mapped_column(nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey('estado.id'), nullable=False, default=1)

    estado: Mapped['Estado'] = relationship(back_populates='periodos')
    comprobantes: Mapped[list['Comprobante']] = relationship(back_populates='periodo_contable')


class Comprobante(Base):
    __tablename__: str = "comprobante"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    fecha_actualizacion: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

    empresa_id: Mapped[int] = mapped_column(ForeignKey('empresa.id'), nullable=False)
    periodo_contable_id: Mapped[int] = mapped_column(ForeignKey('periodo_contable.id'), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuario.id'), nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey('estado.id'), nullable=False, default=1)

    empresa: Mapped['Empresa'] = relationship(back_populates='comprobantes')
    periodo_contable: Mapped['PeriodoContable'] = relationship(back_populates='comprobantes')
    usuario: Mapped['Usuario'] = relationship(back_populates='comprobantes')
    estado: Mapped['Estado'] = relationship(back_populates='comprobantes')
    lineas: Mapped[list['LineaContable']] = relationship(back_populates='comprobante')


class TipoDocumento(Base):
    __tablename__: str = "tipo_documento"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)

    terceros: Mapped[list['Tercero']] = relationship(back_populates='tipo_documento')


class Tercero(Base):
    __tablename__: str = "tercero"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    numero_documento: Mapped[str] = mapped_column(nullable=False)

    tipo_documento_id: Mapped[int] = mapped_column(ForeignKey('tipo_documento.id'), nullable=False)

    tipo_documento: Mapped['TipoDocumento'] = relationship(back_populates='terceros')
    lineas: Mapped[list['LineaContable']] = relationship(back_populates='tercero')


class LineaContable(Base):
    __tablename__: str = "linea_contable"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column(nullable=True)
    debito: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    credito: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)

    cuenta: Mapped[str] = mapped_column(ForeignKey('puc.codigo'), nullable=False)
    tercero_id: Mapped[int | None] = mapped_column(ForeignKey('tercero.id'), nullable=True)
    comprobante_id: Mapped[int] = mapped_column(ForeignKey('comprobante.id'), nullable=False)

    cuenta_rel: Mapped['Puc'] = relationship(back_populates='lineas')
    tercero: Mapped['Tercero | None'] = relationship(back_populates='lineas')
    comprobante: Mapped['Comprobante'] = relationship(back_populates='lineas')
