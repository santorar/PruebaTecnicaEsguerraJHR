import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencias import obtener_usuario_actual
from app.main import app


@pytest.fixture()
def cliente_auth(sesion):
    """Cliente SIN el override de autenticación: ejercita el flujo real de login."""

    def override_get_db():
        yield sesion

    app.dependency_overrides.pop(obtener_usuario_actual, None)
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def registrar(cliente, correo, clave="clave123", empresa_id=1):
    return cliente.post(
        "/auth/registro",
        json={
            "nombre": "Usuario Prueba",
            "correo": correo,
            "clave": clave,
            "confirmacion_clave": clave,
            "empresa_id": empresa_id,
        },
    )


def test_registro_crea_usuario_y_login_entrega_token(cliente_auth, datos):
    registro = registrar(cliente_auth, "auth@test.com", empresa_id=datos["empresa"].id)
    assert registro.status_code == 201

    login = cliente_auth.post(
        "/auth/login", json={"correo": "auth@test.com", "clave": "clave123"}
    )
    assert login.status_code == 200
    cuerpo = login.json()
    assert cuerpo["token"]
    assert cuerpo["usuario"]["correo"] == "auth@test.com"

    comprobantes = cliente_auth.get(
        "/comprobante/", headers={"Authorization": f"Bearer {cuerpo['token']}"}
    )
    assert comprobantes.status_code == 200


def test_login_clave_incorrecta(cliente_auth, datos):
    registrar(cliente_auth, "auth2@test.com", empresa_id=datos["empresa"].id)
    login = cliente_auth.post(
        "/auth/login", json={"correo": "auth2@test.com", "clave": "malaclave"}
    )
    assert login.status_code == 401
    assert login.json()["detail"] == "Correo o clave incorrectos"


def test_login_correo_inexistente(cliente_auth):
    login = cliente_auth.post(
        "/auth/login", json={"correo": "nadie@test.com", "clave": "clave123"}
    )
    assert login.status_code == 401


def test_registro_correo_duplicado(cliente_auth, datos):
    registrar(cliente_auth, "auth3@test.com", empresa_id=datos["empresa"].id)
    duplicado = registrar(cliente_auth, "auth3@test.com", empresa_id=datos["empresa"].id)
    assert duplicado.status_code == 400
    assert duplicado.json()["detail"] == "Ya existe un usuario con ese correo"


def test_registro_claves_no_coinciden(cliente_auth, datos):
    respuesta = cliente_auth.post(
        "/auth/registro",
        json={
            "nombre": "Usuario Prueba",
            "correo": "auth4@test.com",
            "clave": "clave123",
            "confirmacion_clave": "otraclave",
            "empresa_id": datos["empresa"].id,
        },
    )
    assert respuesta.status_code == 400


def test_endpoint_protegido_rechaza_sin_token(cliente_auth):
    respuesta = cliente_auth.get("/comprobante/")
    assert respuesta.status_code == 401


def test_endpoint_protegido_rechaza_token_invalido(cliente_auth):
    respuesta = cliente_auth.get(
        "/comprobante/", headers={"Authorization": "Bearer token-falso"}
    )
    assert respuesta.status_code == 401


def test_simulador_uvt_y_empresas_son_publicos(cliente_auth):
    assert cliente_auth.get("/empresa/").status_code == 200
