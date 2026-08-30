from fastapi import FastAPI

from app.routes import puc, comprobante, periodo_contable

app = FastAPI(title="Api Prueba Técnica Esguerra JHR - BalanceApp")


app.include_router(puc.router)
app.include_router(comprobante.router)
app.include_router(periodo_contable.router)