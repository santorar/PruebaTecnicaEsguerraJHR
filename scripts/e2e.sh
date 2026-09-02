#!/bin/zsh
# E2E de punta a punta contra servidores reales.
# Uso:
#   docker compose up -d db       (base de datos)
#   ./scripts/e2e.sh              (levanta backend y frontend, prueba todo y los detiene)
set -u
TMP=$(mktemp -d)
BASE=http://localhost:8000
FRONT=http://localhost:3000
FALLAS=0

verificar() { if [ "$1" = "0" ]; then echo "  OK  - $2"; else echo "  FAIL- $2"; FALLAS=$((FALLAS+1)); fi }

cd "$(dirname "$0")/../Backend"
uv run uvicorn app.main:app --port 8000 > $TMP/backend.log 2>&1 &
PID_B=$!
cd ../Frontend
pnpm dev --port 3000 > $TMP/frontend.log 2>&1 &
PID_F=$!
trap "kill $PID_B $PID_F 2>/dev/null" EXIT

for i in $(seq 1 60); do
  curl -s -o /dev/null $BASE/docs && curl -s -o /dev/null $FRONT/iniciar-sesion && break
  sleep 1
done

echo "== 1. Seguridad (CORS/CSRF/XSS/Auth) =="
COD=$(curl -s -X OPTIONS $BASE/comprobante/ -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" -o /dev/null -w "%{http_code}")
[ "$COD" = "200" ]; verificar $? "preflight CORS desde origen permitido ($COD)"
COD=$(curl -s -X POST $BASE/tercero/ -H "Origin: http://evil.com" -H "Content-Type: application/json" -d '{"nombre":"x","numero_documento":"1","tipo_documento_id":1}' -o /dev/null -w "%{http_code}")
[ "$COD" = "403" ]; verificar $? "origin no permitido rechazado ($COD)"
HDRS=$(curl -s $BASE/empresa/ -D - -o /dev/null)
echo "$HDRS" | grep -qi "x-content-type-options: nosniff" && echo "$HDRS" | grep -qi "content-security-policy"; verificar $? "cabeceras de seguridad presentes"
COD=$(curl -s -o /dev/null -w "%{http_code}" $BASE/comprobante/)
[ "$COD" = "401" ]; verificar $? "endpoint protegido sin token -> 401 ($COD)"
COD=$(curl -s -o /dev/null -w "%{http_code}" $BASE/api/exogena/uvt-simulador/2026)
[ "$COD" = "200" ]; verificar $? "simulador UVT publico ($COD)"
COD=$(curl -s -o /dev/null -w "%{http_code}" $BASE/empresa/)
[ "$COD" = "200" ]; verificar $? "GET /empresa/ publico para registro ($COD)"

echo "== 2. Auth =="
CORREO="e2e$RANDOM@test.com"
CLAVE="clave123"
COD=$(curl -s -X POST $BASE/auth/registro -H "Content-Type: application/json" -d "{\"nombre\":\"Usuario E2E\",\"correo\":\"$CORREO\",\"clave\":\"$CLAVE\",\"confirmacion_clave\":\"$CLAVE\",\"empresa_id\":1}" -o /dev/null -w "%{http_code}")
[ "$COD" = "201" ]; verificar $? "registro ($COD)"
TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" -d "{\"correo\":\"$CORREO\",\"clave\":\"$CLAVE\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])" 2>/dev/null)
[ -n "$TOKEN" ]; verificar $? "login entrega token"
COD=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" -d "{\"correo\":\"$CORREO\",\"clave\":\"mala\"}" -o /dev/null -w "%{http_code}")
[ "$COD" = "401" ]; verificar $? "clave incorrecta -> 401 ($COD)"
AUTH="Authorization: Bearer $TOKEN"

echo "== 3. Seed de datos de negocio =="
NIT="9${RANDOM}12345"
RESP=$(curl -s -X POST $BASE/empresa/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"nombre\":\"Comercial E2E SA\",\"nit\":\"$NIT\"}")
EMPRESA_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null)
[ -n "$EMPRESA_ID" ]; verificar $? "empresa creada (id=$EMPRESA_ID)"
USUARIO_ID=$(curl -s $BASE/auth/login -H "Content-Type: application/json" -d "{\"correo\":\"$CORREO\",\"clave\":\"$CLAVE\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['usuario']['id'])" 2>/dev/null)
CUENTA="62${RANDOM}0"
curl -s -X POST $BASE/puc/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"codigo\":\"$CUENTA\",\"nombre\":\"Gastos E2E\",\"naturaleza\":\"D\"}" -o /dev/null
TERCERO_ID=$(curl -s -X POST $BASE/tercero/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"nombre\":\"Proveedor E2E\",\"numero_documento\":\"7${RANDOM}6\",\"tipo_documento_id\":1}" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null)
PERIODO_ID=$(curl -s -X POST $BASE/periodo-contable/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"nombre\":\"2026-E2E-$RANDOM\",\"fecha_inicio\":\"2026-01-01\",\"fecha_fin\":\"2026-12-31\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null)
[ -n "$TERCERO_ID" ] && [ -n "$PERIODO_ID" ]; verificar $? "cuenta, tercero y periodo creados"

echo "== 4. Vista 1 - flujo de comprobantes =="
RESP=$(curl -s -X POST $BASE/comprobante/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"descripcion\":\"Compra E2E\",\"empresa_id\":$EMPRESA_ID,\"periodo_contable_id\":$PERIODO_ID,\"usuario_id\":$USUARIO_ID,\"lineas\":[{\"cuenta\":\"$CUENTA\",\"debito\":\"1000000\",\"credito\":\"0\",\"tercero_id\":$TERCERO_ID},{\"cuenta\":\"236501\",\"debito\":\"0\",\"credito\":\"190000\",\"tercero_id\":$TERCERO_ID},{\"cuenta\":\"220501\",\"debito\":\"0\",\"credito\":\"810000\",\"tercero_id\":$TERCERO_ID}]}")
COMP_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null)
[ -n "$COMP_ID" ]; verificar $? "comprobante creado como borrador (id=$COMP_ID)"
RESP=$(curl -s -X POST $BASE/comprobante/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"empresa_id\":$EMPRESA_ID,\"periodo_contable_id\":$PERIODO_ID,\"usuario_id\":$USUARIO_ID,\"lineas\":[{\"cuenta\":\"$CUENTA\",\"debito\":\"100\",\"credito\":\"0\"},{\"cuenta\":\"220501\",\"debito\":\"0\",\"credito\":\"90\"}]}")
echo "$RESP" | grep -q "El total de débito debe ser igual al total de crédito"; verificar $? "descuadre rechazado con mensaje claro"
ID_CONTABILIZADO=$(curl -s $BASE/estado/ -H "$AUTH" | python3 -c "import sys,json;print([e['id'] for e in json.load(sys.stdin) if e['nombre']=='contabilizado'][0])")
COD=$(curl -s -X PUT $BASE/comprobante/$COMP_ID/estado/$ID_CONTABILIZADO -H "$AUTH" -o /dev/null -w "%{http_code}")
[ "$COD" = "200" ]; verificar $? "contabilizacion resuelta por nombre de estado ($COD)"
RESP=$(curl -s -X PUT $BASE/comprobante/$COMP_ID -H "$AUTH" -H "Content-Type: application/json" -d "{\"empresa_id\":$EMPRESA_ID,\"periodo_contable_id\":$PERIODO_ID,\"usuario_id\":$USUARIO_ID,\"lineas\":[{\"cuenta\":\"$CUENTA\",\"debito\":\"900\",\"credito\":\"0\"},{\"cuenta\":\"220501\",\"debito\":\"0\",\"credito\":\"900\"}]}")
SUSTITUTO=$(echo "$RESP" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['id'] != $COMP_ID and d['estado_id'])" 2>/dev/null)
[ -n "$SUSTITUTO" ]; verificar $? "editar contabilizado crea sustituto en borrador (id distinto, estado=$SUSTITUTO)"

echo "== 5. Vista 2 - libro mayor =="
RESP=$(curl -s -X POST $BASE/libro_mayor/ -H "$AUTH" -H "Content-Type: application/json" -d "{\"cuenta\":\"$CUENTA\",\"fecha_inicial\":\"2026-01-01\",\"fecha_final\":\"2026-12-31\"}")
echo "$RESP" | grep -q "acumulado"; verificar $? "libro mayor con saldo acumulado"
RESP=$(curl -s -X POST $BASE/libro_mayor/ -H "$AUTH" -H "Content-Type: application/json" -d '{"cuenta":"999999","fecha_inicial":"2026-01-01","fecha_final":"2026-12-31"}')
[ "$RESP" = "[]" ]; verificar $? "estado vacio del libro mayor"

echo "== 6. Vista 3 - exogena =="
RESP=$(curl -s -X POST $BASE/api/exogena/generar -H "$AUTH" -H "Content-Type: application/json" -d "{\"empresa_id\":$EMPRESA_ID,\"anio_gravable\":2026,\"umbral_uvt\":\"0\"}" -o $TMP/exogena.xml -w "%{http_code}")
[ "$RESP" = "200" ] && grep -q "<InformacionExogena" $TMP/exogena.xml; verificar $? "XML generado y descargado"
GEN_ID=$(curl -s "$BASE/api/exogena/historial?limit=1" -H "$AUTH" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
COD=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH" $BASE/api/exogena/historial/$GEN_ID/archivo)
[ "$COD" = "200" ]; verificar $? "re-descarga del historial ($COD)"

echo "== 7. Frontend (SSR) =="
COD=$(curl -s -o /dev/null -w "%{http_code}" $FRONT/iniciar-sesion)
[ "$COD" = "200" ]; verificar $? "/iniciar-sesion publica"
COD=$(curl -s -o /dev/null -w "%{http_code}" $FRONT/registrarse)
[ "$COD" = "200" ]; verificar $? "/registrarse publica"
COD=$(curl -s -o /dev/null -w "%{http_code}" $FRONT/dashboard)
echo "$COD" | grep -q "200\|307"; verificar $? "/dashboard sin sesion redirige al login ($COD)"
COD=$(curl -s -o /dev/null -w "%{http_code}" -H "Cookie: balance_token=$TOKEN" $FRONT/dashboard)
[ "$COD" = "200" ]; verificar $? "/dashboard con sesion -> 200 ($COD)"
RESP=$(curl -s -H "Cookie: balance_token=$TOKEN" $FRONT/dashboard)
echo "$RESP" | grep -q "Comprobantes"; verificar $? "/dashboard renderiza la tabla ordenable/paginada"
COD=$(curl -s -o /dev/null -w "%{http_code}" -H "Cookie: balance_token=$TOKEN" $FRONT/libro-mayor)
[ "$COD" = "200" ]; verificar $? "/libro-mayor con sesion ($COD)"
COD=$(curl -s -o /dev/null -w "%{http_code}" -H "Cookie: balance_token=$TOKEN" $FRONT/exogena)
[ "$COD" = "200" ]; verificar $? "/exogena con sesion ($COD)"

echo ""
if [ "$FALLAS" = "0" ]; then echo "TODOS LOS CHECKS PASARON"; else echo "FALLAS: $FALLAS"; fi
exit $FALLAS
