from fastapi import FastAPI

from app.routes import puc, comprobante, periodo_contable, empresa, usuario, estado, tercero, reportes

app = FastAPI(title="Api Prueba Técnica Esguerra JHR - BalanceApp")


app.include_router(puc.router)
app.include_router(comprobante.router)
app.include_router(periodo_contable.router)
app.include_router(empresa.router)
app.include_router(usuario.router)
app.include_router(estado.router)
app.include_router(tercero.router)
app.include_router(tercero.router_tipos_documento)
app.include_router(reportes.router)