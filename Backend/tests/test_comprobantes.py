from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.empresa import Empresa
from app.models.general import Estado
from app.models.periodo_contable import PeriodoContable
from app.models.puc import Puc
from app.models.tercero import Tercero
from app.models.usuario import Usuario
from app.schemas import Comprobante as ComprobanteSchema, LineaContable as LineaContableSchema
from app.services import comprobante as comprobante_service

GASTO = "620501"
RETENCION = "236501"
PROVEEDORES = "220501"
CAJA = "110505"
IVA_DESCONTABLE = "240805"


@pytest.fixture()
def contexto(sesion, datos):
    estados = {e.nombre: e.id for e in sesion.query(Estado).all()}
    empresa = sesion.query(Empresa).filter(Empresa.nit == "900123456").first()
    usuario = sesion.query(Usuario).first()
    periodo = sesion.query(PeriodoContable).first()
    terceros = {t.numero_documento: t.id for t in sesion.query(Tercero).all()}
    return {
        "estados": estados,
        "empresa_id": empresa.id,
        "usuario_id": usuario.id,
        "periodo_id": periodo.id,
        "terceros": terceros,
    }


def _linea(cuenta, debito="0", credito="0", tercero_id=None, descripcion=None):
    return {
        "cuenta": cuenta,
        "debito": str(debito),
        "credito": str(credito),
        "tercero_id": tercero_id,
        "descripcion": descripcion,
    }


def _payload(contexto, lineas, **extra):
    cuerpo = {
        "descripcion": "Comprobante de prueba",
        "empresa_id": contexto["empresa_id"],
        "periodo_contable_id": contexto["periodo_id"],
        "usuario_id": contexto["usuario_id"],
        "lineas": lineas,
    }
    cuerpo.update(extra)
    return cuerpo


def _esquema(contexto, lineas):
    return ComprobanteSchema(
        descripcion="Comprobante de prueba",
        empresa_id=contexto["empresa_id"],
        periodo_contable_id=contexto["periodo_id"],
        usuario_id=contexto["usuario_id"],
        lineas=[
            LineaContableSchema(cuenta=cuenta, debito=Decimal(debito), credito=Decimal(credito), tercero_id=tercero_id)
            for cuenta, debito, credito, tercero_id in lineas
        ],
    )


def _crear_compra_valida(cliente, contexto):
    cuenta_iva = cliente.post(
        "/puc/", json={"codigo": IVA_DESCONTABLE, "nombre": "IVA descontable", "naturaleza": "D"}
    )
    assert cuenta_iva.status_code == 201

    creacion = cliente.post("/comprobante/", json=_payload(contexto, [
        _linea(GASTO, debito="1000000", tercero_id=contexto["terceros"]["79123456"], descripcion="Compra"),
        _linea(IVA_DESCONTABLE, debito="190000", descripcion="IVA descontable"),
        _linea(PROVEEDORES, credito="1190000", tercero_id=contexto["terceros"]["79123456"], descripcion="Proveedores"),
    ]))
    assert creacion.status_code == 200, creacion.text
    return creacion.json()


def _contabilizar(cliente, comprobante_id, contexto):
    return cliente.put(f"/comprobante/{comprobante_id}/estado/{contexto['estados']['contabilizado']}")


# --- Reglas 1 a 6: validaciones previas a contabilizar ---


def test_regla_1_rechaza_comprobante_con_una_sola_linea(sesion, contexto):
    esquema = _esquema(contexto, [(CAJA, "100000", "0", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "El comprobante debe tener al menos dos líneas contables"


def test_regla_2_rechaza_valores_negativos(sesion, contexto):
    esquema = _esquema(contexto, [(CAJA, "-100000", "0", None), (RETENCION, "0", "100000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "Los valores de débito y crédito no pueden ser negativos"


def test_regla_2_rechaza_valores_con_mas_de_dos_decimales(sesion, contexto):
    esquema = _esquema(contexto, [(CAJA, "0.005", "0", None), (RETENCION, "0", "100000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "Los valores de débito y crédito no pueden tener más de dos decimales"


def test_regla_3_rechaza_linea_con_debito_y_credito_simultaneos(sesion, contexto):
    esquema = _esquema(contexto, [(CAJA, "100000", "100000", None), (RETENCION, "0", "0", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "Una línea contable no puede tener valores de débito y crédito al mismo tiempo"


def test_regla_2_rechaza_codigo_de_cuenta_invalido(sesion, contexto):
    esquema = _esquema(contexto, [("ABC", "100000", "0", None), (RETENCION, "0", "100000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "El código de la cuenta debe ser numérico o de un solo carácter"


def test_regla_5_rechaza_cuenta_inexistente_en_el_puc(sesion, contexto):
    esquema = _esquema(contexto, [("888888", "100000", "0", None), (RETENCION, "0", "100000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "La cuenta '888888' no existe en el PUC"


def test_regla_5_rechaza_cuenta_inactiva(sesion, contexto):
    sesion.add(Puc(codigo="999", nombre="Cuenta inactiva", naturaleza="D", activo=False))
    sesion.commit()

    esquema = _esquema(contexto, [("999", "100000", "0", None), (RETENCION, "0", "100000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "La cuenta '999' no está activa en el PUC"


def test_escenario_2_rechaza_comprobante_desbalanceado(sesion, contexto):
    esquema = _esquema(contexto, [(CAJA, "500000", "0", None), (RETENCION, "0", "450000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert error.value.detail == "El total de débito debe ser igual al total de crédito"


def test_regla_6_rechaza_comprobante_en_periodo_cerrado(sesion, contexto):
    periodo = sesion.query(PeriodoContable).first()
    periodo.estado_id = contexto["estados"]["cerrado"]
    sesion.commit()

    esquema = _esquema(contexto, [(CAJA, "100000", "0", None), (RETENCION, "0", "100000", None)])
    with pytest.raises(HTTPException) as error:
        comprobante_service.validar_comprobante(esquema, sesion)
    assert "periodo contable no está activo" in error.value.detail


# --- Escenario 1: comprobante válido de una compra ---


def test_escenario_1_comprobante_valido_se_guarda_y_se_contabiliza(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)

    assert cuerpo["estado_id"] == contexto["estados"]["borrador"]
    assert len(cuerpo["lineas"]) == 3

    contabilizado = _contabilizar(cliente, cuerpo["id"], contexto)
    assert contabilizado.status_code == 200
    resultado = contabilizado.json()
    assert resultado["estado_id"] == contexto["estados"]["contabilizado"]

    libro = cliente.post(
        "/libro_mayor/",
        json={"cuenta": GASTO, "fecha_inicial": "2024-01-01", "fecha_final": "2026-12-31"},
    )
    movimiento = [m for m in libro.json() if m["referencia"] == cuerpo["id"]]
    assert len(movimiento) == 1
    assert Decimal(str(movimiento[0]["debito"])) == Decimal("1000000")
    assert movimiento[0]["tercero"] == "Proveedor Uno & Hnos"


# --- Reglas 7 y 9: protección del comprobante contabilizado ---


def test_comprobante_contabilizado_queda_protegido(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)
    comprobante_id = cuerpo["id"]
    assert _contabilizar(cliente, comprobante_id, contexto).status_code == 200

    nueva_linea = cliente.post(f"/comprobante/{comprobante_id}/linea/", json=_linea(CAJA, debito="1000"))
    assert nueva_linea.status_code == 400
    assert "borrador" in nueva_linea.json()["detail"]

    linea_id = cuerpo["lineas"][0]["id"]
    actualizada = cliente.put(
        f"/comprobante/{comprobante_id}/linea/{linea_id}", json=_linea(GASTO, debito="2000000")
    )
    assert actualizada.status_code == 400

    eliminada = cliente.delete(f"/comprobante/{comprobante_id}/linea/{linea_id}")
    assert eliminada.status_code == 400

    cambio_estado = _contabilizar(cliente, comprobante_id, contexto)
    assert cambio_estado.status_code == 400
    assert "borrador" in cambio_estado.json()["detail"]

    borrado = cliente.delete(f"/comprobante/{comprobante_id}")
    assert borrado.status_code == 400
    assert "borrador" in borrado.json()["detail"]

    detalle = cliente.get(f"/comprobante/{comprobante_id}")
    assert detalle.status_code == 200
    assert len(detalle.json()["lineas"]) == 3


def test_comprobante_anulado_no_se_puede_actualizar(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)
    comprobante_id = cuerpo["id"]
    anulado = cliente.put(f"/comprobante/{comprobante_id}/estado/{contexto['estados']['anulado']}")
    assert anulado.status_code == 200

    actualizacion = cliente.put(f"/comprobante/{comprobante_id}", json=_payload(contexto, [
        _linea(CAJA, debito="1000"),
        _linea(RETENCION, credito="1000"),
    ]))
    assert actualizacion.status_code == 400
    assert "anulado" in actualizacion.json()["detail"]


def test_estado_solo_acepta_contabilizado_o_anulado(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)
    comprobante_id = cuerpo["id"]

    estado_invalido = cliente.put(f"/comprobante/{comprobante_id}/estado/{contexto['estados']['abierto']}")
    assert estado_invalido.status_code == 400
    assert "contabilizado" in estado_invalido.json()["detail"]

    estado_inexistente = cliente.put(f"/comprobante/{comprobante_id}/estado/9999")
    assert estado_inexistente.status_code == 400
    assert "Estado no encontrado" in estado_inexistente.json()["detail"]

    anulado = cliente.put(f"/comprobante/{comprobante_id}/estado/{contexto['estados']['anulado']}")
    assert anulado.status_code == 200
    assert anulado.json()["estado_id"] == contexto["estados"]["anulado"]


# --- Ciclo de vida del borrador ---


def test_borrador_permite_agregar_actualizar_y_eliminar_lineas(cliente, contexto):
    creacion = cliente.post("/comprobante/", json=_payload(contexto, [
        _linea(CAJA, debito="500000"),
        _linea(RETENCION, credito="500000"),
    ]))
    assert creacion.status_code == 200
    comprobante_id = creacion.json()["id"]
    lineas = creacion.json()["lineas"]
    assert len(lineas) == 2

    agregada = cliente.post(
        f"/comprobante/{comprobante_id}/linea/",
        json=_linea(PROVEEDORES, descripcion="Ajuste"),
    )
    assert agregada.status_code == 201

    actualizada = cliente.put(
        f"/comprobante/{comprobante_id}/linea/{lineas[0]['id']}", json=_linea(CAJA, debito="700000")
    )
    assert actualizada.status_code == 200
    assert Decimal(str(actualizada.json()["debito"])) == Decimal("700000")

    eliminada = cliente.delete(f"/comprobante/{comprobante_id}/linea/{lineas[0]['id']}")
    assert eliminada.status_code == 200

    restantes = cliente.get(f"/comprobante/{comprobante_id}/linea/")
    assert restantes.status_code == 200
    assert len(restantes.json()) == 2


def test_borrador_se_puede_eliminar_y_luego_no_existe(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)

    eliminado = cliente.delete(f"/comprobante/{cuerpo['id']}")
    assert eliminado.status_code == 200
    assert cliente.get(f"/comprobante/{cuerpo['id']}").status_code == 404


def test_listado_filtra_por_estado(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)

    borradores = cliente.get("/comprobante/", params={"estado_id": contexto["estados"]["borrador"]})
    assert borradores.status_code == 200
    assert cuerpo["id"] in [c["id"] for c in borradores.json()]


def test_consulta_comprobante_inexistente_retorna_404(cliente):
    assert cliente.get("/comprobante/9999").status_code == 404


# --- Escenario 3: reversión con trazabilidad ---


def test_escenario_3_actualizar_contabilizado_genera_reversion_y_sustituto(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)
    original_id = cuerpo["id"]
    assert _contabilizar(cliente, original_id, contexto).status_code == 200

    sustituto = cliente.put(f"/comprobante/{original_id}", json=_payload(contexto, [
        _linea(GASTO, debito="800000", tercero_id=contexto["terceros"]["79123456"], descripcion="Compra corregida"),
        _linea(PROVEEDORES, credito="800000", tercero_id=contexto["terceros"]["79123456"], descripcion="Proveedores"),
    ]))
    assert sustituto.status_code == 200
    datos_sustituto = sustituto.json()
    assert datos_sustituto["comprobante_original_id"] == original_id
    assert datos_sustituto["estado_id"] == contexto["estados"]["borrador"]

    original = cliente.get(f"/comprobante/{original_id}").json()
    assert original["estado_id"] == contexto["estados"]["anulado"]
    assert original["comprobante_sustituto_id"] == datos_sustituto["id"]
    assert original["comprobante_reversor_id"] is not None

    reversor = cliente.get(f"/comprobante/{original['comprobante_reversor_id']}").json()
    assert reversor["comprobante_original_id"] == original_id
    assert reversor["estado_id"] == contexto["estados"]["contabilizado"]

    valores_originales = {
        (l["cuenta"], Decimal(str(l["debito"])), Decimal(str(l["credito"]))) for l in original["lineas"]
    }
    valores_reversor = {
        (l["cuenta"], Decimal(str(l["debito"])), Decimal(str(l["credito"]))) for l in reversor["lineas"]
    }
    assert valores_reversor == {(cuenta, credito, debito) for cuenta, debito, credito in valores_originales}

    contabilizado_sustituto = _contabilizar(cliente, datos_sustituto["id"], contexto)
    assert contabilizado_sustituto.status_code == 200


def test_libro_mayor_refleja_anulacion_y_reversion(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)
    comprobante_id = cuerpo["id"]
    assert _contabilizar(cliente, comprobante_id, contexto).status_code == 200

    anulacion = cliente.put(f"/comprobante/{comprobante_id}", json=_payload(contexto, [
        _linea(GASTO, debito="800000"),
        _linea(PROVEEDORES, credito="800000"),
    ]))
    assert anulacion.status_code == 200

    libro = cliente.post(
        "/libro_mayor/",
        json={"cuenta": GASTO, "fecha_inicial": "2024-01-01", "fecha_final": "2026-12-31"},
    )
    movimientos = libro.json()
    referencias_reversor = [m["referencia"] for m in movimientos]
    reversor_id = cliente.get(f"/comprobante/{comprobante_id}").json()["comprobante_reversor_id"]
    assert reversor_id in referencias_reversor


# --- Escenario 4: período cerrado ---


def test_escenario_4_rechaza_contabilizar_y_registrar_en_periodo_cerrado(cliente, contexto):
    cuerpo = _crear_compra_valida(cliente, contexto)

    cierre = cliente.put(
        f"/periodo-contable/{contexto['periodo_id']}/estado/{contexto['estados']['cerrado']}"
    )
    assert cierre.status_code == 200

    contabilizado = _contabilizar(cliente, cuerpo["id"], contexto)
    assert contabilizado.status_code == 400
    assert "periodo" in contabilizado.json()["detail"].lower()

    nuevo = cliente.post("/comprobante/", json=_payload(contexto, [
        _linea(CAJA, debito="100000"),
        _linea(RETENCION, credito="100000"),
    ]))
    assert nuevo.status_code == 500
    assert "periodo" in nuevo.json()["detail"].lower()


# --- Regla 8 y escenario 6: libro mayor e integridad de numeración ---


def test_libro_mayor_calcula_saldo_acumulado_con_movimientos_ordenados(cliente, datos):
    libro = cliente.post(
        "/libro_mayor/",
        json={"cuenta": GASTO, "fecha_inicial": "2025-01-01", "fecha_final": "2025-12-31"},
    )
    assert libro.status_code == 200
    movimientos = libro.json()
    assert len(movimientos) == 5

    assert [Decimal(str(m["acumulado"])) for m in movimientos] == [
        Decimal("1000000"),
        Decimal("1500000"),
        Decimal("1550000"),
        Decimal("1850000"),
        Decimal("1550000"),
    ]

    fechas = [m["fecha"] for m in movimientos]
    assert fechas == sorted(fechas)
    assert movimientos[0]["tercero"] == "Proveedor Uno & Hnos"
    assert movimientos[1]["tercero"] == "Importadora Dos"
    assert movimientos[2]["tercero"] == "Proveedores Tres"
    assert Decimal(str(movimientos[3]["debito"])) == Decimal("300000")
    assert Decimal(str(movimientos[4]["credito"])) == Decimal("300000")


def test_libro_mayor_filtra_por_rango_de_fechas(cliente, datos):
    libro = cliente.post(
        "/libro_mayor/",
        json={"cuenta": GASTO, "fecha_inicial": "2025-03-01", "fecha_final": "2025-06-30"},
    )
    movimientos = libro.json()
    assert len(movimientos) == 2
    assert Decimal(str(movimientos[-1]["acumulado"])) == Decimal("1500000")


def test_libro_mayor_sin_movimientos_en_rango_retorna_lista_vacia(cliente, datos):
    libro = cliente.post(
        "/libro_mayor/",
        json={"cuenta": RETENCION, "fecha_inicial": "2025-04-01", "fecha_final": "2025-12-31"},
    )
    assert libro.status_code == 200
    assert libro.json() == []


def test_contabilizaciones_consecutivas_generan_referencias_unicas(cliente, contexto):
    ids = []
    for i in range(2):
        creacion = cliente.post("/comprobante/", json=_payload(
            contexto,
            [_linea(CAJA, debito="1000"), _linea(RETENCION, credito="1000")],
            descripcion=f"Comprobante {i + 1}",
        ))
        assert creacion.status_code == 200
        ids.append(creacion.json()["id"])

    assert len(set(ids)) == 2
