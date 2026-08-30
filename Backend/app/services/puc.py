from sqlalchemy.orm import Session
from app.repositories import puc as puc_repository


class PucValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validar_codigo(codigo: str) -> None:
    if not codigo:
        raise PucValidationError("Código no puede estar vacío")
    if not codigo.isdigit() and len(codigo) > 1:
        raise PucValidationError("Código debe ser numérico o de un solo carácter")


def validar_naturaleza(naturaleza: str) -> None:
    if naturaleza not in ['D', 'C']:
        raise PucValidationError("Naturaleza debe ser 'D' o 'C'")


def crear_cuenta(db: Session, codigo: str, nombre: str, naturaleza: str, activo: bool = True):
    validar_codigo(codigo)
    validar_naturaleza(naturaleza)

    if puc_repository.get_cuenta(db, codigo):
        raise PucValidationError("Cuenta ya existe")

    return puc_repository.create_cuenta(db, codigo, nombre, naturaleza, activo)


def actualizar_cuenta(db: Session, codigo: str, nombre: str, naturaleza: str, activo: bool):
    validar_codigo(codigo)
    validar_naturaleza(naturaleza)

    db_cuenta = puc_repository.get_cuenta(db, codigo)
    if db_cuenta is None:
        raise PucValidationError("Cuenta no encontrada")

    return puc_repository.update_cuenta(db, db_cuenta, nombre, naturaleza, activo)


def eliminar_cuenta(db: Session, codigo: str):
    db_cuenta = puc_repository.get_cuenta(db, codigo)
    if db_cuenta is None:
        raise PucValidationError("Cuenta no encontrada")

    return puc_repository.delete_cuenta(db, db_cuenta)
