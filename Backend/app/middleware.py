from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

METODOS_MUTANTES = frozenset({"POST", "PUT", "PATCH", "DELETE"})
RUTAS_DOCUMENTACION = frozenset({"/docs", "/redoc", "/openapi.json"})

CABECERAS_SEGURIDAD = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


class CabecerasSeguridadMiddleware(BaseHTTPMiddleware):
    """Mitigación de XSS y sniffing: añade cabeceras de seguridad a todas las
    respuestas de la API. La API solo sirve JSON/XML, por lo que una CSP
    estricta es suficiente; se excluyen las rutas de documentación para no
    romper Swagger UI."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path not in RUTAS_DOCUMENTACION:
            for nombre, valor in CABECERAS_SEGURIDAD.items():
                response.headers.setdefault(nombre, valor)
        return response


class OrigenVerificadoMiddleware(BaseHTTPMiddleware):
    """Defensa en profundidad contra CSRF. La API es stateless (no usa cookies
    ni sesiones, el cuerpo es application/json), por lo que el CSRF clásico no
    aplica; como capa adicional se rechaza toda petición mutante que declare
    un encabezado Origin fuera de la lista de orígenes permitidos. Peticiones
    sin Origin (curl, server-to-server, tests) pasan sin problema."""

    def __init__(self, app, origenes_permitidos: frozenset[str]):
        super().__init__(app)
        self.origenes_permitidos = origenes_permitidos

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in METODOS_MUTANTES:
            origen = request.headers.get("origin")
            if origen and origen not in self.origenes_permitidos:
                return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
        return await call_next(request)
