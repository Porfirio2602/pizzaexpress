import re


_PATRON_CORREO = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def nombre_valido(valor):
    valor = valor.strip()
    return bool(valor) and any(caracter.isalpha() for caracter in valor) and all(
        caracter.isalpha() or caracter.isspace() or caracter in "-'’"
        for caracter in valor
    )


def correo_valido(valor):
    return bool(_PATRON_CORREO.fullmatch(valor.strip()))


def telefono_valido(valor):
    return bool(re.fullmatch(r"[0-9]{10}", valor.strip()))


def requisitos_contrasena_pendientes(valor):
    pendientes = []
    if len(valor) < 8:
        pendientes.append("al menos 8 caracteres")
    if not any(caracter.isupper() for caracter in valor):
        pendientes.append("una mayúscula")
    if not any(caracter.islower() for caracter in valor):
        pendientes.append("una minúscula")
    if not any(caracter.isdigit() for caracter in valor):
        pendientes.append("un número")
    if not any(
        not caracter.isalnum() and not caracter.isspace()
        for caracter in valor
    ):
        pendientes.append("un símbolo")
    return pendientes
