from fastapi import FastAPI
from functools import lru_cache
from app.routes import usuario, puc, periodo_contable, tercero, comprobante

from . import config

app = FastAPI(title="Api Prueba Técnica Esguerra JHR - BalanceApp")
