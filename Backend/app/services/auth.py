from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.config import get_settings

def generar_token(usuario_id: int) -> str:
    firmante = TimestampSigner(get_settings().secret_key)
    return firmante.sign(str(usuario_id).encode("utf-8")).decode("utf-8")

def verificar_token(token: str) -> int | None:
    try:
        crudo = TimestampSigner(get_settings().secret_key).unsign(
            token.encode("utf-8"), max_age=get_settings().token_segundos
        )
        return int(crudo.decode("utf-8"))
    except (BadSignature, SignatureExpired):
        return None
