from fastapi import FastAPI

from app.routes import puc, comprobante

app = FastAPI(title="Api Prueba Técnica Esguerra JHR - BalanceApp")


app.include_router(puc.router)
app.include_router(comprobante.router)