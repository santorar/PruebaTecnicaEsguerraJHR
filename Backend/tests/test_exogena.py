import logging
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from app.models.general import GeneracionExogena

ANIO = 2025


def _generar(cliente, empresa_id, umbral=0, anio=ANIO):
    return cliente.post(
        "/api/exogena/generar",
        json={"empresa_id": empresa_id, "anio_gravable": anio, "umbral_uvt": umbral},
    )


def test_generar_rechaza_nit_con_dv_invalido(cliente, datos):
    respuesta = _generar(cliente, datos["empresa_nit_malo"].id)

    assert respuesta.status_code == 400
    assert "dígito de verificación" in respuesta.json()["detail"]


def test_generar_sin_valor_uvt_para_el_anio(cliente, datos):
    respuesta = _generar(cliente, datos["empresa"].id, umbral=10, anio=2030)

    assert respuesta.status_code == 400
    assert "UVT" in respuesta.json()["detail"]


def test_generar_sin_movimientos_para_el_anio(cliente, datos):
    respuesta = _generar(cliente, datos["empresa"].id, umbral=0, anio=2024)

    assert respuesta.status_code == 400
    assert "No hay movimientos" in respuesta.json()["detail"]


def test_generar_xml_con_estructura_totales_y_neteo_de_anulados(cliente, datos):
    respuesta = _generar(cliente, datos["empresa"].id, umbral=0)

    assert respuesta.status_code == 200
    assert "application/xml" in respuesta.headers["content-type"]
    assert "attachment" in respuesta.headers["content-disposition"]
    assert respuesta.headers["content-disposition"].endswith('.xml"')

    raiz = ET.fromstring(respuesta.content)
    assert raiz.tag == "InformacionExogena"
    assert raiz.attrib["version"] == "1.0"

    informante = raiz.find("Informante")
    assert informante.attrib["nit"] == "900123456"
    assert informante.attrib["anioGravable"] == "2025"
    assert informante.attrib["razonSocial"] == "Compania Pruebas"
    assert int(informante.attrib["dv"]) >= 0

    registros = raiz.find("Registros").findall("Registro")
    assert len(registros) == 4

    por_concepto = {(r.attrib["numDoc"], r.attrib["concepto"]): r.attrib for r in registros}
    assert por_concepto[("79123456", "620501")]["valorBruto"] == "1000000.00"
    assert por_concepto[("79123456", "620501")]["valorRetencion"] == "0.00"
    assert por_concepto[("79123456", "236501")]["valorRetencion"] == "190000.00"
    assert por_concepto[("79123456", "236501")]["valorBruto"] == "0.00"
    assert por_concepto[("800987654", "620501")]["valorBruto"] == "500000.00"
    assert por_concepto[("71122334", "620501")]["valorBruto"] == "50000.00"

    nombre_con_ampersand = por_concepto[("79123456", "620501")]["nombre"]
    assert nombre_con_ampersand == "Proveedor Uno & Hnos"

    totales = raiz.find("Totales").attrib
    assert totales["registros"] == "4"
    assert totales["totalValorBruto"] == "1550000.00"
    assert totales["totalRetencion"] == "190000.00"

    suma_bruto = sum(Decimal(r.attrib["valorBruto"]) for r in registros)
    suma_retencion = sum(Decimal(r.attrib["valorRetencion"]) for r in registros)
    assert Decimal(totales["totalValorBruto"]) == suma_bruto
    assert Decimal(totales["totalRetencion"]) == suma_retencion


def test_umbral_excluye_terceros_con_trazabilidad_en_log(cliente, datos, caplog):
    with caplog.at_level(logging.INFO, logger="app.services.reportes"):
        respuesta = _generar(cliente, datos["empresa"].id, umbral=10)

    assert respuesta.status_code == 200
    raiz = ET.fromstring(respuesta.content)
    registros = raiz.find("Registros").findall("Registro")
    assert len(registros) == 2
    assert all(r.attrib["numDoc"] == "79123456" for r in registros)
    assert raiz.find("Totales").attrib["registros"] == "2"

    assert "Tercero excluido por umbral" in caplog.text
    assert "800987654" in caplog.text
    assert "71122334" in caplog.text

    historial = cliente.get("/api/exogena/historial").json()
    assert historial[0]["registros_incluidos"] == 2
    assert historial[0]["registros_excluidos"] == 2
    assert Decimal(str(historial[0]["umbral_uvt"])) == Decimal("10")
    assert Decimal(str(historial[0]["valor_uvt"])) == Decimal("100000.00")


def test_umbral_valor_igual_al_limite_excluye_tercero(cliente, datos):
    respuesta = _generar(cliente, datos["empresa"].id, umbral=5)

    assert respuesta.status_code == 200
    registros = ET.fromstring(respuesta.content).find("Registros").findall("Registro")
    numeros = {r.attrib["numDoc"] for r in registros}
    assert numeros == {"79123456"}
    assert len(registros) == 2


def test_umbral_sin_terceros_que_superen_rechaza(cliente, datos):
    respuesta = _generar(cliente, datos["empresa"].id, umbral=20)

    assert respuesta.status_code == 400
    assert "umbral" in respuesta.json()["detail"]


def test_historial_registra_generaciones_y_permite_redescarga(cliente, datos, sesion):
    primera = _generar(cliente, datos["empresa"].id, umbral=0)
    segunda = _generar(cliente, datos["empresa"].id, umbral=10)
    assert primera.status_code == 200 and segunda.status_code == 200

    historial = cliente.get("/api/exogena/historial").json()
    assert [g["id"] for g in historial] == [2, 1]
    assert historial[0]["anio_gravable"] == ANIO
    assert historial[0]["nombre_archivo"] != historial[1]["nombre_archivo"]

    generacion = sesion.get(GeneracionExogena, 1)
    archivo = Path(generacion.ruta_archivo)
    assert archivo.is_file()
    assert archivo.name == historial[1]["nombre_archivo"]

    redescarga = cliente.get("/api/exogena/historial/1/archivo")
    assert redescarga.status_code == 200
    assert redescarga.content == archivo.read_bytes()
    assert redescarga.headers["content-disposition"].endswith(historial[1]["nombre_archivo"] + '"')


def test_redescarga_de_generacion_inexistente(cliente, datos):
    respuesta = cliente.get("/api/exogena/historial/999/archivo")

    assert respuesta.status_code == 404


def test_redescarga_cuando_el_archivo_fue_eliminado(cliente, datos, sesion):
    assert _generar(cliente, datos["empresa"].id, umbral=0).status_code == 200

    generacion = sesion.get(GeneracionExogena, 1)
    Path(generacion.ruta_archivo).unlink()

    respuesta = cliente.get("/api/exogena/historial/1/archivo")

    assert respuesta.status_code == 404
