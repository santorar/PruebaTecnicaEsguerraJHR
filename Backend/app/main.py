from fastapi import FastAPI

from routes import puc

app = FastAPI(title="Api Prueba Técnica Esguerra JHR - BalanceApp")


app.include_router(puc.router)
