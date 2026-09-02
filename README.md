# Prueba técnica Esguerra JHR - Desarrollador Fullstack

Esta es la solución propuesta por Santiago Sierra para la prueba técnica propuesta por Esguerra JHR, a continuación se detallara todo lo necesario para entender, comprender y evaluar la prueba técnica.

## Stack Usado

- **Backend**: Python + FastAPI + SQLAlchemy + Alembic + PostgreSQL (gestor de dependencias: uv).
- **Frontend**: Next.js 16 (App Router, Server/Client Components) + TypeScript strict + React 19 + Tailwind CSS 4 (pnpm). Sin dependencias adicionales: el cliente HTTP es `fetch` nativo con un wrapper tipado.

## Como ejecutar el proyecto?
### Servidor Local

1. Base de datos (docker):

```bash
docker compose up -d
```

2. Backend (puerto 8000), desde la carpeta `Backend/`:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

3. Frontend (puerto 3000), desde la carpeta `Frontend/balanceapp/`:

```bash
pnpm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL apunta a http://localhost:8000
pnpm dev
```

La API de FastAPI queda en http://localhost:8000 (Swagger en `/docs`) y la aplicación web en http://localhost:3000.

### Docker

Puede lanzar todo el aplicativo (DB + migraciones + Backend + Frontend) con un solo comando:
```bash
cp .env.example .env
docker compose up -d --build
```

Qué hace cada servicio al arrancar:

- `db`: PostgreSQL con healthcheck (`pg_isready`).
- `backend`: ejecuta automáticamente las **migraciones de Alembic** (`alembic upgrade head`, incluyen los seeds paramétricos de estados y tipos de documento) y luego arranca la API con uvicorn. Se conecta a la BD usando `POSTGRES_HOST=db`. El directorio de XML de exógena se monta como volumen para persistir los archivos.
- `frontend`: build multi-stage de Next.js (salida `standalone`); `NEXT_PUBLIC_API_URL` se inyecta como build-arg desde el `.env` y debe apuntar a una URL alcanzable desde el navegador del host (por defecto `http://localhost:8000`).

Para detener solo la API y el frontend y seguir desarrollando en local: `docker compose stop backend frontend`.

## Frontend (vistas)

Esta construido con Next.js App Router, usando **Server Components** para las partes de solo lectura y **Client Components** donde hay interacción.

| Vista | Rutas| Componentes clave |
| --- | --- | --- |
| Iniciar sesión / Registrarse | `/iniciar-sesion`, `/registrarse` | Formularios con estados de carga y error; tras el registro hay auto-login. El token se guarda en localStorage + cookie para que los Server Components reenvíen la autorización |
| Registro de comprobantes | `/dashboard`, `/dashboard/nuevo`, `/dashboard/[id]` | `EditorComprobante` (líneas agregables/eliminables, selector de cuenta con búsqueda, tercero opcional, totales de débito/crédito y diferencia en tiempo real, guardar borrador / contabilizar / eliminar, banner de errores del backend, `usuario_id` tomado del usuario autenticado). Los contabilizados se pueden editar previa advertencia en modal (con tooltip que explica que se crea un comprobante reversor que anula el documento errado y un nuevo borrador con los cambios). Incluye modales para crear empresas y para crear/cerrar periodos contables |
| Libro mayor | `/libro-mayor` | Formulario de filtros por cuenta y rango de fechas, tabla con saldo acumulado, estado vacío y errores |
| Información exógena | `/exogena` | Formulario de parámetros (empresa, año gravable, umbral en UVT con conversión a COP usando el valor vigente), descarga del XML y re-descarga desde el historial |

La tabla de comprobantes del dashboard permite **ordenar por cualquier columna** (clic en el encabezado alterna asc/desc) y está **paginada** (10/25/50 filas por página).

Consideraciones Tomadas al hacer el frontend:

- Los estados (`borrador`, `contabilizado`, etc.) **no se pueden hardcodean por id**: por lo cual frontend debe consultar `GET /estado/` y resolver por nombre, ya que los ids dependen del contenido de la tabla.
- Los errores del backend se normalizan en un solo lugar (`lib/api.ts`): mensajes `{"detail": "..."}`, listas de validación de Pydantic (422) y el prefijo `"400: "` que envuelve FastAPI cuando la excepción de negocio se relanza como 500/400.


## Como ejecutar los test?

**Backend** — desde la carpeta `Backend/` (requiere uv):

```bash
uv run pytest
```

Las pruebas usan SQLite en memoria (no necesitan la base de datos de Postgres) y cubren las reglas de negocio de la información exógena (validación del dígito de verificación, agrupación por tercero/concepto, neteo de comprobantes anulados, umbral en UVT con trazabilidad, cuadre de totales de control e historial/re-descarga), la autenticación (registro, login, credenciales inválidas, tokens y endpoints protegidos) y la edición de comprobantes contabilizados (reverso + sustituto).

**Frontend** — desde la carpeta `Frontend/`:

```bash
pnpm exec tsc --noEmit   # typecheck estricto
pnpm lint                # ESLint
pnpm build               # build de producción
```

**E2E de punta a punta** — desde la raíz (levanta backend y frontend reales, ejecuta ~28 verificaciones de seguridad, autenticación, los tres flujos de negocio y el SSR del frontend, y los detiene al terminar):

```bash
docker compose up -d db
./scripts/e2e.sh
```

## Información exógena simplificada

Genera un XML de información exógena a partir de los movimientos contables asociados a terceros para un año gravable.

### Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/api/exogena/generar` | Genera el XML y lo retorna como descarga directa. Body: `{ "empresa_id": 1, "anio_gravable": 2026, "umbral_uvt": 100 }` (umbral opcional, por defecto 0 = sin filtro). |
| GET | `/api/exogena/historial` | Listado de generaciones previas con fecha, parámetros y totales. |
| GET | `/api/exogena/historial/{id}/archivo` | Re-descarga del XML de una generación previa. |

### Almacenamiento de archivos

Los XML se guardan físicamente en disco. El directorio se configura con la variable `EXOGENA_FILES_DIR` (por defecto `Backend/exogena_files/`, se crea automáticamente). Cada archivo se nombra `exogena_{nit}_{año}_{id}.xml`, donde el `id` es el identificador de la generación en el historial, lo que garantiza nombres únicos y permite re-descargar el archivo exacto que se generó. El registro en base de datos guarda la ruta del archivo y los totales de control.

### UVT

El valor oficial de la UVT vive en la tabla paramétrica `uvt_valor`. El umbral expresado en UVT se convierte a pesos con el valor del año gravable solicitado.

### Integración externa del valor de la UVT

La aplicación mantiene actualizado el valor de la UVT desde una fuente externa **sin bloquear las peticiones HTTP en curso**: la sincronización corre en un hilo de fondo (se dispara al arrancar el servidor y luego cada `UVT_INTERVALO_SEGUNDOS`, por defecto 7 dias).

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/exogena/uvt` | Valores de UVT vigentes (año, valor, fuente y fecha de actualización). |
| POST | `/api/exogena/uvt/actualizar?anio=YYYY` | Programa una sincronización en segundo plano (responde 202 de inmediato). Sin `anio` sincroniza el año actual y el siguiente. |
| GET | `/api/exogena/uvt/historial` | Trazabilidad de cada ejecución: fecha, fuente, éxito/fallo, valor obtenido y detalle del error. |
| GET | `/api/exogena/uvt-simulador/{anio}` | Proveedor simulado local (representa una integración externa real y responde por HTTP). |

Estrategia de proveedores:

1. **Fuente externa (primaria)**: consulta por HTTP la página pública configurada en `UVT_API_URL` (por defecto `https://uvt.com.co/`) y extrae el valor del año solicitado. Con 3 reintentos con pausa creciente ante fallas transitorias (timeout, HTTP 5xx, cambio de formato).
2. **Fallback local (simulado, también por HTTP)**: si la fuente externa falla, consulta `GET {UVT_SIMULADOR_URL}/api/exogena/uvt-simulador/{anio}`, un proveedor simulado servido por la propia API con el catálogo de valores oficiales DIAN. Así la integración sigue siendo una consulta HTTP real, desacoplada del proceso que la invoca.

Consideraciones cubiertas: fallos temporales (reintentos + fallback), ejecuciones repetidas (upsert por año: la PK `anio` garantiza que nunca se dupliquen valores, solo se actualizan), y trazabilidad del resultado de cada ejecución (tabla `uvt_actualizacion_log` + logs de la aplicación, con la fuente que atendió cada año). Si un año no existe en ninguna fuente (p. ej. 2027 aún no publicada), la ejecución queda registrada como fallida con el detalle de ambos intentos.

## Autenticación

La API es privada: **todos los endpoints de negocio exigen el header `Authorization: Bearer <token>`**. Los únicos endpoints públicos son `POST /auth/registro`, `POST /auth/login`, `GET /empresa/` (lectura, la necesita el formulario de registro), el simulador UVT (el backend se lo consulta a sí mismo sin token en el fallback de sincronización) y la documentación.

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/auth/registro` | Crea un usuario (nombre, correo, clave, confirmación, empresa). La clave se guarda con bcrypt. |
| POST | `/auth/login` | Valida credenciales bcrypt y retorna `{ "token": "...", "token_type": "bearer", "usuario": {...} }`. |

El token se firma con `itsdangerous.TimestampSigner` usando `SECRET_KEY` y expira según `TOKEN_SEGUNDOS` (por defecto 24 h). No se usan cookies de sesión en el backend, por lo que el análisis de CSRF no cambia.

## Seguridad (CORS / CSRF / XSS)

- **CORS**: `CORSMiddleware` de Starlette con lista de orígenes permitida por configuración (`CORS_ORIGINS`, por defecto `http://localhost:3000,http://127.0.0.1:3000`). `allow_credentials=False` (la API no usa cookies) y solo los métodos/headers necesarios.
- **CSRF**: Como defensa en profundidad, `OrigenVerificadoMiddleware` rechaza con 403 cualquier petición mutante (POST/PUT/PATCH/DELETE) que declare un encabezado `Origin` fuera de la lista permitida.
- **XSS**: `CabecerasSeguridadMiddleware` añade a todas las respuestas de la API: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, CSP estricta (`default-src 'none'; frame-ancestors 'none'`) y `X-XSS-Protection`. Se excluyen las rutas de documentación (`/docs`, `/redoc`, `/openapi.json`) para no romper Swagger UI.

## Decisiones Tomadas: Trade-Ins & Trade-Offs

### Decisiones
1. Para el manejo de jerarquia y ordenamiento de las cuentas del plan de cuentas se planteo utilizar un campo string, el cual ordena correctamente las cuentas y por otro lado se guardo asi ya que para buscar la cuenta padre de una cuenta se puede hacer de la siguiente manera:
  - Las cuentas estan divididas en 4 partes:
    1. Clase: primer digito
    2. Grupo: Los dos primeros digitos
    3. Cuenta: Los cuatro primeros digitos
    4. Subcuenta: Los seis primeros digitos
  - Para la busqueda de la cuenta padre lo que se haria seria tomar la cuenta, ver la cantidad de digitos y se quitan los ultimos dos digitos si el tiene mas de dos digitos, si tiene 2 digitos se toma el primer digito y esa es la cuenta padre, se hizo una implementacion para buscar la cuenta padre y a que distancia de la cuenta original esta.
2. Se utilizo un for-update para evitar errores por concurrencia lo que evita que consulten informacion antigua, en un escenario A y B, A bloquea la peticion de B hasta que se resuelva A y ahi posteriormente la base de datos da una respuesta a B, lo que asegura consistencia, sus limitaciones es que puede empeorar un poco el rendimiento de las consultas en paralelo, si una consulta tarda mucho puede dejar tambien bloqueado a B y no protege si hay logica externa, pero se considero adecuada para esta prueba tecnica.
3. Información exógena simplificada:
  - Los movimientos se agrupan por tercero y concepto, donde el concepto es la cuenta PUC completa de la línea contable (máxima trazabilidad con los datos registrados).
  - Se incluyen los comprobantes en estado `contabilizado` y `anulado` (mismo criterio del libro mayor): al anular se crea un comprobante reversor contabilizado con líneas inversas, por lo que incluir ambos hace que original + reversor neteen a cero. Excluir los anulados dejaría solo la pata inversa y produciría un desbalance inverso para ese tercero.
  - `valorBruto` es el neto débito-crédito del tercero en cuentas no de retención; `valorRetencion` es el neto de retenciones practicadas en cuentas que inician con `236`. Los grupos con neto no reportable (sin pago neto o sin retención neta) se omiten con trazabilidad en el log.
  - El umbral se expresa en UVT y se convierte a pesos con el valor del año gravable; un tercero se excluye si su valor total no supera el umbral (comparación estricta: valor <= umbral excluye), registrando la exclusión en el log. Con umbral 0 se incluyen todos.
  - El NIT del informante se valida recalculando el dígito de verificación con el algoritmo existente (`services/empresa.py`) y comparándolo contra el `dv` guardado; si no coincide se rechaza la generación.
  - Los totales de control del XML se calculan únicamente con los registros incluidos, garantizando que cuadren, y se persisten también en el registro de la generación.
  - El XML se guarda físicamente en disco (no en DB) con el id de la generación en el nombre; la escritura ocurre antes del commit del registro, de modo que no quedan registros en base de datos sin archivo. Trade-off: si el commit falla tras escribir el archivo queda un archivo huérfano, situación aceptable y registrada en el log.

### Trade-Ins

Ventajas de la solución construida:

1. **Arquitectura en capas en el backend** (`routes → services → repositories`): separación de responsabilidades que hace el código testeable (20 tests con SQLite en memoria sin tocar Postgres) y permite cambiar persistencia o reglas sin arrastrar cambios en cascada.
2. **División Server/Client Components en el frontend**: los listados, el libro mayor y el historial se renderizan en servidor; los Client Components se reservan para lo interactivo (editor de comprobantes, formularios con descargas).
3. **Cero dependencias nuevas en el frontend**: Todas las consultas al backend se realizan mediante un cliente HTTP *fetch* nativo tipado, UI propia sobre Tailwind y aritmética propia. Esto nos ayuda con menor superficie de ataque, builds rápidos y sin riesgo de obsolescencia de librerías de terceros.
4. **Precisión monetaria garantizada**: los montos viajan como `Decimal` (string en JSON) y la aritmética de totales se hace en centavos enteros, eliminando los errores de punto flotante típicos en módulos contables.
5. **Datos paramétricos resueltos por nombre, no por id**: los estados (`borrador`, `contabilizado`, `anulado`, `abierto`, `cerrado`) se consultan de la tabla `estado` y se resuelven por nombre, por lo que el sistema no se rompe si los ids cambian entre ambientes.
6. **Manejo de errores centralizado**: un solo normalizador (`lib/api.ts`) traduce los tres formatos de error del backend (`detail` string, listas de validación Pydantic 422, y el prefijo `400: ` de las excepciones relanzadas) a mensajes claros y consistentes en la UI.
7. **Seguridad en capas y sin costo adicional**: allowlist de CORS, verificación de `Origin` como defensa en profundidad contra CSRF, cabeceras de seguridad (CSP estricta, nosniff, frame-deny) y autenticación Bearer con contraseñas bcrypt, todo con dependencias que ya trae el stack.
8. **Concurrencia controlada**: `FOR UPDATE` en la creación/actualización de comprobantes evita carreras que desbalanceen la partida doble bajo peticiones simultáneas.
9. **Integración UVT resiliente**: sincronización en hilo de fondo (no bloquea las peticiones HTTP), reintentos con backoff, fallback simulado por HTTP real, upsert por año y trazabilidad completa de cada ejecución.
10. **Exógena auditable y re-descargable**: cada generación guarda parámetros, totales de control y el archivo en disco con nombre determinístico, lo que permite re-descargar exactamente el XML que se reportó.
11. **Despliegue reproducible**: `docker compose up` levanta base de datos + migraciones + backend + frontend desde un `.env`, y un script E2E de ~30 verifica todo el flujo de negocio de punta a punta.

### Trade-Offs

Desventajas y costos aceptados:

1. **`FOR UPDATE` degrada el paralelismo**: Una transacción lenta bloquea a las demás. Esta solución es unicamente de forma interna del backend por lo que no protege contra lógica externa a la transacción. Se decidio tomar esta alternativa para el alcance de esta prueba.
2. **Ordenamiento y paginación client-side en la tabla de comprobantes**: se escogio esta solucion por ser simple y rapida de implementar pero seria una mejor opción implementar una paginación y filtros mediante base de datos.
3. **Token en cookie + localStorage**: permite que los Server Components reenvíen la autorización, pero al no ser `httpOnly` un XSS podría leerlo. Se mitiga con CSP estricta y ausencia de `dangerouslySetInnerHTML`.
4. **Token firmado con `itsdangerous` en vez de JWT estándar**: Se tomo esta desición por limites de tiempo de la prueba y seria mejor implementar una integracion con JWT estandar ya que permitiria que el token sea interoperable entre varias soluciones y tambien la revocación de este Token.
5. **Sin roles ni permisos**: Cualquier usuario que este registrado es capaz de hacer cualquier tipo de operacion dentro de la aplicación, para un entorno de producción se deberia introducir un sistema multi-tentant evitando el cruce de la información de las distintas empresas.
6. **XML de exógena en disco local**: Esta hace que el backend este atado a la instancia, para una solución mas robusta seria mejor un servidor de datos como un S3, esto tambien impide que se pueda hacer un load balancing.
7. **Quirk de errores en comprobantes**: `POST /comprobante/` relanza excepciones de negocio como HTTP 500 con prefijo `400: ` (y `PUT` lo hace con 400). El frontend mitiga esto, pero seria mejor reescribir partes del backend para evitar este problema.
8. **Sincronización UVT dentro del proceso de la API**: un hilo de fondo es suficiente para el alcance de esta prueba técnica, pero en producción es mucho mas seguro y confiable un worker/scheduler independiente (Celery, ARQ, cron) con reintentos y monitoreo propios.
9. **Frontend sin tests automatizados**: la verificación fue E2E manual scriptada contra la API real; faltan pruebas unitarias (vitest) y de interfaz (Playwright) para evitar regresiones.
10. **Sin capa de caché en el frontend**: los datos siempre están frescos a costa de más peticiones; con más carga convendría revalidación por segmento.

## Pendientes/Faltantes

- Test automatizados unitarios del backend (se verifico de forma manual toda la API, pero es posible que puedan haber casos limite que rompan la logica de algun modulo).
- Cacheo en las respuestas de la api, a largo plazo y con mas información es extremadamente importante para no impactar la experiencia de Usuario.

## Como llevaría esta solución a producción?

**Infraestructura y despliegue**
- Reverse proxy (Nginx/Traefik) con TLS terminado delante de backend y frontend.
- PostgreSQL administrado (RDS/Cloud SQL) con backups automáticos.
- XML de exógena en almacenamiento de objetos (S3/GCS) con URLs prefirmadas en vez de disco local.
- Frontend en CDN (Vercel), Esto permitiria que el backend escale horizontalmente.

**Autenticación y seguridad**
- Migrar a tokens de corta duración + refresh tokens, añadir roles/permisos por empresa y rate limit en el login.
- Rotación y gestión del `SECRET_KEY` en un gestor de secretos (Vault, SSM), no en un .env del repositorio.
- Creación de tabla de Auditoría de operaciones sensibles.

**Confiabilidad y observabilidad**
- Logging estructurado por petición, métricas (Prometheus/Grafana) y tracing distribuido (OpenTelemetry), alertas sobre errores 5xx, fallos de sincronización UVT y generaciones de exógena.
- Healthchecks reales (conectividad a DB, espacio del directorio de exógena) y readiness probes.
- Mover la sincronización UVT y la generación de exógena a workers independientes con cola (Celery/ARQ) para no cargar el proceso de la API.

**Calidad y entrega continua**
- CI/CD (GitHub Actions): lint + typecheck + pytest en cada PR; build y push de imágenes; despliegue blue/green o canary.
- Completar la pirámide de pruebas: unitarias de frontend (vitest) y E2E automatizadas (Playwright).
- Creación de un ambiente staging para hacer pruebas antes de pasar a producción.

**Rendimiento y datos**
- Ordenamiento/paginación en base de datos con índices sobre las columnas de consulta del libro mayor (cuenta, fecha de contabilización) y de comprobantes.
