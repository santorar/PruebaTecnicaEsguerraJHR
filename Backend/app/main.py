import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware import CabecerasSeguridadMiddleware, OrigenVerificadoMiddleware
from app.routes import puc, comprobante, periodo_contable, empresa, usuario, estado, tercero, reportes
from app.services import reportes as reportes_service

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    reportes_service.iniciar_bucle_sincronizacion_uvt()
    yield


app = FastAPI(title="Api Prueba Técnica Esguerra JHR - BalanceApp", lifespan=lifespan)

settings = get_settings()

# El orden de registro importa: el último middleware añadido es el más externo.
# CORS queda al exterior para responder el preflight (OPTIONS) antes que la
# verificación de origen y añadir sus cabeceras también a las respuestas de error.
app.add_middleware(CabecerasSeguridadMiddleware)
app.add_middleware(OrigenVerificadoMiddleware, origenes_permitidos=frozenset(settings.origenes_permitidos))
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_permitidos,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(puc.router)
app.include_router(comprobante.router)
app.include_router(periodo_contable.router)
app.include_router(empresa.router)
app.include_router(usuario.router)
app.include_router(estado.router)
app.include_router(tercero.router)
app.include_router(tercero.router_tipos_documento)
app.include_router(reportes.router)
app.include_router(reportes.router_exogena)