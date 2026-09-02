from decimal import Decimal

import pytest

from app.models.general import UvtValor, UvtActualizacionLog
from app.services import reportes as reportes_service

ANIO_FUTURO = 2099

HTML_FUENTE_EXTERNA = (
    "Valor UVT 2026 Colombia$52.374Según Resolución 000238..."
    "UVT Histórico 2025$49.799UVT Histórico 2024$47.065"
)


def test_proveedor_simulado_retorna_valores_oficiales(cliente, datos):
    respuesta = cliente.get("/api/exogena/uvt-simulador/2026")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"anio": 2026, "valor": 52374.0}


def test_proveedor_simulado_anio_desconocido_404(cliente, datos):
    respuesta = cliente.get(f"/api/exogena/uvt-simulador/{ANIO_FUTURO}")

    assert respuesta.status_code == 404


def test_parseo_de_fuente_externa():
    assert reportes_service._extraer_valor_uvt_html(HTML_FUENTE_EXTERNA, 2026) == Decimal("52374")
    assert reportes_service._extraer_valor_uvt_html(HTML_FUENTE_EXTERNA, 2025) == Decimal("49799")
    assert reportes_service._extraer_valor_uvt_html(HTML_FUENTE_EXTERNA, 2024) == Decimal("47065")

    with pytest.raises(ValueError):
        reportes_service._extraer_valor_uvt_html(HTML_FUENTE_EXTERNA, 2030)


def test_sincronizacion_usa_fuente_externa_exitosa(sesion, monkeypatch):
    consultas_simulador = []

    monkeypatch.setattr(reportes_service, "_consultar_uvt_externa", lambda anio: Decimal("99999.00"))
    monkeypatch.setattr(
        reportes_service,
        "_consultar_uvt_simulador",
        lambda anio: consultas_simulador.append(anio) or Decimal("1.00"),
    )

    resultados = reportes_service.sincronizar_uvt(db=sesion, anios=[ANIO_FUTURO])

    assert resultados == [{"anio": ANIO_FUTURO, "valor": Decimal("99999.00"), "fuente": "externa", "exitoso": True}]
    assert consultas_simulador == []

    registro = sesion.get(UvtValor, ANIO_FUTURO)
    assert registro.valor == Decimal("99999.00")
    assert registro.fuente == "externa"
    assert registro.fecha_actualizacion is not None
    assert sesion.query(UvtActualizacionLog).count() == 1


def test_reintentos_ante_fallas_transitorias(sesion, monkeypatch):
    intentos = {"externa": 0}

    def externa_inestable(anio):
        intentos["externa"] += 1
        if intentos["externa"] < 3:
            raise ConnectionError("fallo transitorio")
        return Decimal("52374.00")

    monkeypatch.setattr(reportes_service, "_consultar_uvt_externa", externa_inestable)
    monkeypatch.setattr(reportes_service, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))

    resultados = reportes_service.sincronizar_uvt(db=sesion, anios=[ANIO_FUTURO])

    assert intentos["externa"] == 3
    assert resultados[0]["exitoso"] is True
    assert resultados[0]["fuente"] == "externa"


def test_sincronizacion_usa_fallback_local_http_cuando_externa_falla(sesion, monkeypatch):
    def externa_caida(anio):
        raise ConnectionError("sitio externo no disponible")

    consultas_simulador = []

    def simulador(anio):
        consultas_simulador.append(anio)
        return Decimal("52374.00")

    monkeypatch.setattr(reportes_service, "_consultar_uvt_externa", externa_caida)
    monkeypatch.setattr(reportes_service, "_consultar_uvt_simulador", simulador)
    monkeypatch.setattr(reportes_service, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))

    resultados = reportes_service.sincronizar_uvt(db=sesion, anios=[ANIO_FUTURO])

    assert consultas_simulador == [ANIO_FUTURO]
    assert resultados[0]["exitoso"] is True
    assert resultados[0]["fuente"] == "simulador_local"

    registro = sesion.get(UvtValor, ANIO_FUTURO)
    assert registro.fuente == "simulador_local"

    logs = sesion.query(UvtActualizacionLog).all()
    assert len(logs) == 1
    assert logs[0].exitoso is True
    assert "Fallback local" in logs[0].detalle


def test_fallo_total_registra_trazabilidad(sesion, monkeypatch):
    monkeypatch.setattr(reportes_service, "_consultar_uvt_externa", _lanzar(ConnectionError("externa caida")))
    monkeypatch.setattr(reportes_service, "_consultar_uvt_simulador", _lanzar(ConnectionError("simulador caido")))
    monkeypatch.setattr(reportes_service, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))

    resultados = reportes_service.sincronizar_uvt(db=sesion, anios=[ANIO_FUTURO])

    assert resultados[0]["exitoso"] is False
    assert sesion.query(UvtValor).filter(UvtValor.anio == ANIO_FUTURO).count() == 0

    logs = sesion.query(UvtActualizacionLog).all()
    assert len(logs) == 1
    assert logs[0].exitoso is False
    assert "externa caida" in logs[0].detalle
    assert "simulador caido" in logs[0].detalle


def test_ejecuciones_repetidas_no_duplican_valores(sesion, monkeypatch):
    monkeypatch.setattr(reportes_service, "_consultar_uvt_externa", lambda anio: Decimal("52374.00"))

    reportes_service.sincronizar_uvt(db=sesion, anios=[ANIO_FUTURO])
    reportes_service.sincronizar_uvt(db=sesion, anios=[ANIO_FUTURO])

    assert sesion.query(UvtValor).filter(UvtValor.anio == ANIO_FUTURO).count() == 1
    assert sesion.query(UvtActualizacionLog).count() == 2


def test_endpoint_actualizar_programa_en_segundo_plano(cliente, datos, monkeypatch):
    programadas = []

    monkeypatch.setattr(reportes_service, "programar_sincronizacion_uvt", lambda anios: programadas.append(anios) or True)

    respuesta = cliente.post("/api/exogena/uvt/actualizar?anio=2027")

    assert respuesta.status_code == 202
    assert programadas == [[2027]]


def test_endpoints_de_trazabilidad_uvt(cliente, datos, sesion):
    sesion.add(UvtValor(anio=2030, valor=Decimal("60000.00"), fuente="externa"))
    sesion.add(UvtActualizacionLog(fuente="externa", exitoso=True, anio=2030, valor=Decimal("60000.00")))
    sesion.commit()

    valores = cliente.get("/api/exogena/uvt").json()
    assert valores[-1] == {
        "anio": 2030,
        "valor": "60000.00",
        "fuente": "externa",
        "fecha_actualizacion": None,
    }

    historial = cliente.get("/api/exogena/uvt/historial").json()
    assert historial[0]["fuente"] == "externa"
    assert historial[0]["exitoso"] is True
    assert historial[0]["anio"] == 2030


def _lanzar(error):
    def _consultar(anio):
        raise error

    return _consultar
