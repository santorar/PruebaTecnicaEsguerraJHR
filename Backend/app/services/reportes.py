import logging
import re
import threading
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.general import GeneracionExogena
from app.repositories import reportes as reportes_repository
from app.repositories import empresa as empresa_repository
from app.repositories import estado as estado_repository
from app.schemas import ExogenaGenerarRequest, LibroMayorRequest, LibroMayorResponse
from app.services import empresa as empresa_service

logger = logging.getLogger(__name__)

DOS_DECIMALES = Decimal("0.01")
PREFIJO_CUENTA_RETENCION = "236"

CATALOGO_UVT_SIMULADOR = {
    2024: Decimal("47065.00"),
    2025: Decimal("49799.00"),
    2026: Decimal("52374.00"),
}
PATRON_VALOR_UVT = re.compile(r"UVT[^0-9$]{0,30}(20\d{2})[^$]{0,60}?\$\s*([\d.,]+)")


def get_libro_mayor(db: Session, request: LibroMayorRequest) -> list[LibroMayorResponse]:
    resultado = []
    acumulado = Decimal('0')
    lineas = reportes_repository.get_comprobante_libro_mayor(db, request)

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


def _formato_monto(valor: Decimal) -> str:
    return str(valor.quantize(DOS_DECIMALES))


def _construir_xml(nit: str, dv: int, razon_social: str, anio_gravable: int, registros: list[dict], total_valor_bruto: Decimal, total_retencion: Decimal) -> bytes:
    raiz = ET.Element("InformacionExogena", {"version": "1.0"})
    ET.SubElement(raiz, "Informante", {
        "nit": nit,
        "dv": str(dv),
        "razonSocial": razon_social,
        "anioGravable": str(anio_gravable),
    })
    nodo_registros = ET.SubElement(raiz, "Registros")
    for registro in registros:
        ET.SubElement(nodo_registros, "Registro", {
            "tipoDoc": registro["tipoDoc"],
            "numDoc": registro["numDoc"],
            "nombre": registro["nombre"],
            "concepto": registro["concepto"],
            "valorBruto": registro["valorBruto"],
            "valorRetencion": registro["valorRetencion"],
        })
    ET.SubElement(raiz, "Totales", {
        "registros": str(len(registros)),
        "totalValorBruto": _formato_monto(total_valor_bruto),
        "totalRetencion": _formato_monto(total_retencion),
    })
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True)


def _guardar_archivo(generacion_id: int, nit: str, anio_gravable: int, contenido: bytes) -> Path:
    nit_limpio = ''.join(c for c in nit if c.isdigit())
    directorio = Path(get_settings().exogena_files_dir)
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / f"exogena_{nit_limpio}_{anio_gravable}_{generacion_id}.xml"
    ruta.write_bytes(contenido)
    return ruta


def generar_exogena(db: Session, request: ExogenaGenerarRequest) -> GeneracionExogena:
    empresa = empresa_repository.get_empresa(db, request.empresa_id)
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # el NIT del informante debe validarse con el algoritmo del digito de verificacion
    try:
        dv_calculado = empresa_service.calcular_dv(empresa.nit)
    except ValueError:
        raise HTTPException(status_code=400, detail="El NIT de la empresa no es válido para el cálculo del dígito de verificación")
    if dv_calculado != empresa.dv:
        raise HTTPException(status_code=400, detail="El NIT de la empresa no pasa la validación del dígito de verificación")

    umbral_pesos = None
    valor_uvt = Decimal("0")
    if request.umbral_uvt > 0:
        uvt = estado_repository.get_valor_uvt(db, request.anio_gravable)
        if uvt is None:
            raise HTTPException(status_code=400, detail=f"No existe valor de UVT para el año gravable {request.anio_gravable}")
        valor_uvt = uvt.valor
        umbral_pesos = request.umbral_uvt * uvt.valor

    fecha_inicial = datetime(request.anio_gravable, 1, 1, 0, 0, 0)
    fecha_final = datetime(request.anio_gravable, 12, 31, 23, 59, 59)
    movimientos = reportes_repository.get_movimientos_exogena(db, fecha_inicial, fecha_final)
    if not movimientos:
        raise HTTPException(status_code=400, detail=f"No hay movimientos contables asociados a terceros para el año gravable {request.anio_gravable}")

    # los movimientos se agrupan por tercero y concepto (cuenta PUC completa).
    # La query ya agrupa por (tercero, cuenta); aqui se ajusta cada grupo a los valores del
    # reporte y se acumula el valor total de cada tercero para aplicar el umbral.
    grupos: dict[int, dict] = {}
    for mov in movimientos:
        neto = mov.neto.quantize(DOS_DECIMALES)
        es_retencion = mov.cuenta.startswith(PREFIJO_CUENTA_RETENCION)
        if es_retencion:
            if neto >= 0:
                logger.info(
                    "Movimiento de retención no reportable (sin retención neta practicada): tercero=%s cuenta=%s neto=%s",
                    mov.tercero_documento, mov.cuenta, neto
                )
                continue
            valor_bruto = Decimal("0")
            valor_retencion = -neto
        else:
            if neto <= 0:
                logger.info(
                    "Movimiento no reportable (sin pago neto): tercero=%s cuenta=%s neto=%s",
                    mov.tercero_documento, mov.cuenta, neto
                )
                continue
            valor_bruto = neto
            valor_retencion = Decimal("0")

        grupo = grupos.setdefault(mov.tercero_id, {
            "tipoDoc": mov.tipo_documento,
            "numDoc": mov.tercero_documento,
            "nombre": mov.tercero_nombre,
            "registros": [],
            "total": Decimal("0"),
        })
        grupo["registros"].append({
            "tipoDoc": mov.tipo_documento,
            "numDoc": mov.tercero_documento,
            "nombre": mov.tercero_nombre,
            "concepto": mov.cuenta,
            "valorBruto": valor_bruto,
            "valorRetencion": valor_retencion,
        })
        grupo["total"] += valor_bruto + valor_retencion

    # un tercero se excluye si su valor total no supera el umbral uvt
    registros = []
    registros_excluidos = 0
    for tercero_id in sorted(grupos):
        grupo = grupos[tercero_id]
        if umbral_pesos is not None and grupo["total"] <= umbral_pesos:
            registros_excluidos += 1
            logger.info(
                "Tercero excluido por umbral: doc=%s nombre=%s valor_total=%s umbral_uvt=%s umbral_pesos=%s valor_uvt=%s",
                grupo["numDoc"], grupo["nombre"], grupo["total"], request.umbral_uvt, umbral_pesos, valor_uvt
            )
            continue
        registros.extend(grupo["registros"])

    if not registros:
        raise HTTPException(status_code=400, detail="Ningún tercero supera el umbral mínimo definido para el año gravable")

    # los totales de control se calculan solo con los registros incluidos
    total_valor_bruto = sum((r["valorBruto"] for r in registros), Decimal("0"))
    total_retencion = sum((r["valorRetencion"] for r in registros), Decimal("0"))

    contenido_xml = _construir_xml(
        nit=empresa.nit,
        dv=empresa.dv,
        razon_social=empresa.nombre,
        anio_gravable=request.anio_gravable,
        registros=[
            {**r, "valorBruto": _formato_monto(r["valorBruto"]), "valorRetencion": _formato_monto(r["valorRetencion"])}
            for r in registros
        ],
        total_valor_bruto=total_valor_bruto,
        total_retencion=total_retencion,
    )

    generacion = GeneracionExogena(
        empresa_id=empresa.id,
        anio_gravable=request.anio_gravable,
        umbral_uvt=request.umbral_uvt,
        valor_uvt=valor_uvt,
        registros_incluidos=len(registros),
        registros_excluidos=registros_excluidos,
        total_valor_bruto=total_valor_bruto,
        total_retencion=total_retencion,
        ruta_archivo="",
        nombre_archivo="",
    )
    reportes_repository.create_generacion_exogena(db, generacion)

    # el XML se guarda fisicamente y el registro queda asociado a su ruta
    try:
        ruta = _guardar_archivo(generacion.id, empresa.nit, request.anio_gravable, contenido_xml)
    except OSError:
        db.rollback()
        logger.exception("No se pudo guardar el archivo XML de la generación exógena")
        raise HTTPException(status_code=500, detail="No se pudo guardar el archivo XML en disco")
    generacion.ruta_archivo = str(ruta)
    generacion.nombre_archivo = ruta.name
    db.commit()
    db.refresh(generacion)

    logger.info(
        "Generación exógena id=%s empresa=%s anio=%s registros=%s excluidos=%s bruto=%s retencion=%s archivo=%s",
        generacion.id, empresa.nit, request.anio_gravable, generacion.registros_incluidos,
        generacion.registros_excluidos, total_valor_bruto, total_retencion, generacion.ruta_archivo
    )
    return generacion


def listar_generaciones_exogena(db: Session, skip: int = 0, limit: int = 100) -> list[GeneracionExogena]:
    return reportes_repository.get_generaciones_exogena(db, skip, limit)


def obtener_generacion_exogena(db: Session, generacion_id: int) -> GeneracionExogena:
    generacion = reportes_repository.get_generacion_exogena(db, generacion_id)
    if generacion is None:
        raise HTTPException(status_code=404, detail="Generación de información exógena no encontrada")
    if not Path(generacion.ruta_archivo).is_file():
        logger.warning("Archivo de la generación exógena %s no encontrado en disco: %s", generacion_id, generacion.ruta_archivo)
        raise HTTPException(status_code=404, detail="El archivo de la generación no está disponible")
    return generacion


def _extraer_valor_uvt_html(texto: str, anio: int) -> Decimal:
    for coincidencia in PATRON_VALOR_UVT.finditer(texto):
        anio_encontrado, monto = coincidencia.groups()
        if int(anio_encontrado) == anio:
            return Decimal(monto.replace(".", "").replace(",", "."))
    raise ValueError(f"No se encontró el valor de la UVT {anio} en la fuente externa")


def _consultar_uvt_externa(anio: int) -> Decimal:
    respuesta = httpx.get(
        get_settings().uvt_api_url,
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    respuesta.raise_for_status()
    return _extraer_valor_uvt_html(respuesta.text, anio)


def _consultar_uvt_simulador(anio: int) -> Decimal:
    respuesta = httpx.get(
        f"{get_settings().uvt_simulador_url}/api/exogena/uvt-simulador/{anio}",
        timeout=5,
    )
    respuesta.raise_for_status()
    return Decimal(str(respuesta.json()["valor"]))


def _intentar_con_reintentos(consultar, anio: int, intentos: int, pausa_segundos: float) -> tuple[Decimal, int]:
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            return consultar(anio), intento
        except Exception as error:
            ultimo_error = error
            if intento < intentos:
                time.sleep(pausa_segundos * intento)
    raise ultimo_error


def sincronizar_uvt(db: Session | None = None, anios: list[int] | None = None) -> list[dict]:
    sesion_propia = db is None
    db = db if db is not None else SessionLocal()
    anios = anios or [datetime.now().year, datetime.now().year + 1]
    resultados = []
    try:
        for anio in anios:
            resultado = {"anio": anio, "valor": None, "fuente": None, "exitoso": False}
            detalle = None
            try:
                valor, _ = _intentar_con_reintentos(_consultar_uvt_externa, anio, intentos=3, pausa_segundos=1.0)
                fuente = "externa"
            except Exception as error_externa:
                try:
                    valor, _ = _intentar_con_reintentos(_consultar_uvt_simulador, anio, intentos=2, pausa_segundos=0.5)
                    fuente = "simulador_local"
                    detalle = f"Fallback local tras fallo de la fuente externa: {error_externa}"
                except Exception as error_simulador:
                    detalle = f"Fuente externa: {error_externa} | Simulador local: {error_simulador}"
                    logger.error("Fallo la sincronización de la UVT %s. %s", anio, detalle)
                    estado_repository.registrar_actualizacion_uvt(
                        db, fuente="externa+simulador_local", exitoso=False, anio=anio, valor=None, detalle=detalle
                    )
                    resultado["detalle"] = detalle
                    resultados.append(resultado)
                    continue
            estado_repository.upsert_valor_uvt(db, anio, valor, fuente)
            estado_repository.registrar_actualizacion_uvt(db, fuente=fuente, exitoso=True, anio=anio, valor=valor, detalle=detalle)
            logger.info("UVT %s actualizada a %s desde %s", anio, valor, fuente)
            resultado.update(valor=valor, fuente=fuente, exitoso=True)
            resultados.append(resultado)
    finally:
        if sesion_propia:
            db.close()
    return resultados


_sincronizacion_bloqueo = threading.Lock()
_sincronizando = False


def programar_sincronizacion_uvt(anios: list[int] | None = None) -> bool:
    global _sincronizando
    with _sincronizacion_bloqueo:
        if _sincronizando:
            return False
        _sincronizando = True

    def _ejecutar():
        global _sincronizando
        try:
            sincronizar_uvt(anios=anios)
        except Exception:
            logger.exception("Fallo la sincronización de UVT programada")
        finally:
            with _sincronizacion_bloqueo:
                _sincronizando = False

    threading.Thread(target=_ejecutar, daemon=True).start()
    return True


def iniciar_bucle_sincronizacion_uvt():
    def _bucle():
        while True:
            try:
                sincronizar_uvt()
            except Exception:
                logger.exception("Fallo el ciclo de sincronización de UVT")
            time.sleep(get_settings().uvt_intervalo_segundos)

    threading.Thread(target=_bucle, daemon=True, name="sincronizacion-uvt").start()


def listar_valores_uvt(db: Session) -> list:
    return estado_repository.get_valores_uvt(db)


def listar_logs_actualizacion_uvt(db: Session, skip: int = 0, limit: int = 50) -> list:
    return estado_repository.get_logs_actualizacion_uvt(db, skip, limit)
