from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencias import obtener_usuario_actual
from app.main import app
from app.models.comprobante import Comprobante, LineaContable
from app.models.empresa import Empresa
from app.models.general import Estado, UvtValor
from app.models.periodo_contable import PeriodoContable
from app.models.puc import Puc
from app.models.tercero import TipoDocumento, Tercero
from app.models.usuario import Usuario
from app.services.empresa import calcular_dv

ANIO = 2025
VALOR_UVT_PRUEBA = Decimal("100000.00")


@pytest.fixture()
def sesion():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture()
def cliente(sesion, monkeypatch, tmp_path):
    class ConfiguracionPrueba:
        exogena_files_dir = str(tmp_path / "exogena_files")

    monkeypatch.setattr("app.services.reportes.get_settings", lambda: ConfiguracionPrueba())

    def override_get_db():
        yield sesion

    app.dependency_overrides[get_db] = override_get_db
    # Los tests ejercitan los endpoints directamente sin flujo de login;
    # se anula la autenticación salvo en los tests específicos de auth.
    app.dependency_overrides[obtener_usuario_actual] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def datos(sesion):
    estados = {}
    for nombre in ["borrador", "contabilizado", "anulado", "abierto", "cerrado"]:
        estado = Estado(nombre=nombre)
        sesion.add(estado)
        estados[nombre] = estado

    tipo_nit = TipoDocumento(nombre="NIT")
    tipo_cc = TipoDocumento(nombre="CC")
    sesion.add_all([tipo_nit, tipo_cc])
    sesion.flush()

    empresa = Empresa(nombre="Compania Pruebas", nit="900123456", dv=calcular_dv("900123456"))
    empresa_nit_malo = Empresa(nombre="Empresa Nit Malo", nit="900123457", dv=0)
    sesion.add_all([empresa, empresa_nit_malo])

    cuentas = {
        "620501": Puc(codigo="620501", nombre="Gasto operacional", naturaleza="D"),
        "236501": Puc(codigo="236501", nombre="Retencion en la fuente por pagar", naturaleza="C"),
        "220501": Puc(codigo="220501", nombre="Proveedores", naturaleza="C"),
        "110505": Puc(codigo="110505", nombre="Caja", naturaleza="D"),
    }
    sesion.add_all(cuentas.values())

    tercero_1 = Tercero(nombre="Proveedor Uno & Hnos", numero_documento="79123456", tipo_documento=tipo_cc)
    tercero_2 = Tercero(nombre="Importadora Dos", numero_documento="800987654", tipo_documento=tipo_nit)
    tercero_3 = Tercero(nombre="Proveedores Tres", numero_documento="71122334", tipo_documento=tipo_cc)
    sesion.add_all([tercero_1, tercero_2, tercero_3])

    usuario = Usuario(
        nombre="Contador",
        correo="contador@pruebas.com",
        clave_encriptada="hash-de-prueba",
        empresa=empresa,
    )
    periodo = PeriodoContable(
        nombre="2025",
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 12, 31),
        estado=estados["abierto"],
    )
    sesion.add_all([usuario, periodo])
    sesion.add(UvtValor(anio=ANIO, valor=VALOR_UVT_PRUEBA))
    sesion.flush()

    def crear_comprobante(estado, lineas, fecha=datetime(2025, 3, 10, 12, 0, 0)):
        comprobante = Comprobante(
            empresa=empresa,
            periodo_contable=periodo,
            usuario=usuario,
            estado=estado,
            fecha_contabilizacion=fecha,
        )
        for linea in lineas:
            comprobante.lineas.append(LineaContable(**linea))
        sesion.add(comprobante)
        return comprobante

    crear_comprobante(estados["contabilizado"], [
        {"descripcion": "Compra", "debito": Decimal("1000000"), "credito": Decimal("0"), "cuenta": "620501", "tercero": tercero_1},
        {"descripcion": "Retencion", "debito": Decimal("0"), "credito": Decimal("190000"), "cuenta": "236501", "tercero": tercero_1},
        {"descripcion": "Proveedores", "debito": Decimal("0"), "credito": Decimal("810000"), "cuenta": "220501", "tercero": tercero_1},
    ])

    crear_comprobante(estados["contabilizado"], [
        {"descripcion": "Gasto menor", "debito": Decimal("500000"), "credito": Decimal("0"), "cuenta": "620501", "tercero": tercero_2},
        {"descripcion": "Salida caja", "debito": Decimal("0"), "credito": Decimal("500000"), "cuenta": "110505", "tercero": tercero_2},
    ], fecha=datetime(2025, 5, 20, 12, 0, 0))

    crear_comprobante(estados["contabilizado"], [
        {"descripcion": "Gasto minimo", "debito": Decimal("50000"), "credito": Decimal("0"), "cuenta": "620501", "tercero": tercero_3},
        {"descripcion": "Salida caja", "debito": Decimal("0"), "credito": Decimal("50000"), "cuenta": "110505", "tercero": tercero_3},
    ], fecha=datetime(2025, 7, 4, 12, 0, 0))

    original = crear_comprobante(estados["contabilizado"], [
        {"descripcion": "Compra anulada", "debito": Decimal("300000"), "credito": Decimal("0"), "cuenta": "620501", "tercero": tercero_1},
        {"descripcion": "Salida caja", "debito": Decimal("0"), "credito": Decimal("300000"), "cuenta": "110505", "tercero": tercero_1},
    ], fecha=datetime(2025, 8, 1, 12, 0, 0))
    original.estado = estados["anulado"]
    reversor = crear_comprobante(estados["contabilizado"], [
        {"descripcion": "Reversion compra anulada", "debito": Decimal("0"), "credito": Decimal("300000"), "cuenta": "620501", "tercero": tercero_1},
        {"descripcion": "Entrada caja", "debito": Decimal("300000"), "credito": Decimal("0"), "cuenta": "110505", "tercero": tercero_1},
    ], fecha=datetime(2025, 8, 2, 12, 0, 0))
    reversor.comprobante_original = original

    sesion.commit()
    sesion.refresh(empresa)
    sesion.refresh(empresa_nit_malo)
    return {
        "empresa": empresa,
        "empresa_nit_malo": empresa_nit_malo,
        "estados": estados,
    }
