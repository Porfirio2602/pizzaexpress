import hashlib
import hmac
import smtplib
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import string
import ssl
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Literal
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import FastAPI, Header, HTTPException, Request
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from components.validaciones import correo_valido, requisitos_contrasena_pendientes
import zxingcpp

logger = logging.getLogger("uvicorn.error")

DB_FOLDER = os.environ.get("DATA_DIR", "")
if DB_FOLDER:
    DATABASE_PATH = Path(DB_FOLDER) / "pizza_express.db"
else:
    DATABASE_PATH = Path(__file__).resolve().with_name("pizza_express.db")
SESSION_DURATION = timedelta(days=30)


class UsuarioLogin(BaseModel):
    correo: str
    contrasena: str


class SolicitudRestablecimiento(BaseModel):
    correo: str = Field(min_length=3, max_length=254)


class VerificarCodigoRestablecimiento(BaseModel):
    correo: str = Field(min_length=3, max_length=254)
    codigo: str = Field(min_length=6, max_length=6, pattern=r"^[A-Za-z]{6}$")


class ConfirmarRestablecimiento(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    nueva_contrasena: str = Field(min_length=8, max_length=256)


class UsuarioRegistro(BaseModel):
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    telefono: str
    correo: str
    contrasena: str = Field(min_length=8, max_length=256)


class ArticuloPedido(BaseModel):
    nombre_pizza: str = Field(min_length=1, max_length=250)
    cantidad: int = Field(gt=0, le=50)
    precio_unitario: float = Field(ge=0)


class NuevoPedido(BaseModel):
    nombre_contacto: str = Field(min_length=1, max_length=200)
    tipo_servicio: Literal["A Domicilio", "En Tienda"]
    direccion: str = Field(default="", max_length=500)
    referencias: str = Field(default="", max_length=500)
    hora_recoleccion: datetime | None = None
    subtotal: float = Field(ge=0)
    costo_envio: float = Field(ge=0)
    total: float = Field(ge=0)
    items: list[ArticuloPedido] = Field(min_length=1, max_length=50)


class CredencialesPersonal(BaseModel):
    correo: str = Field(min_length=3, max_length=254)
    contrasena: str = Field(min_length=1, max_length=256)
    rol: Literal["gerente", "vendedor", "cocinero"]


class NuevoVendedor(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    correo: str = Field(min_length=3, max_length=254)
    telefono: str = Field(min_length=10, max_length=20)
    contrasena: str = Field(min_length=8, max_length=256)


class EstadoVendedor(BaseModel):
    activo: bool


class EstadoPedidoVendedor(BaseModel):
    estado: Literal["Lista", "Finalizada"]


class ArticuloVenta(BaseModel):
    producto_id: int | str
    nombre_pizza: str | None = None
    cantidad: int = Field(gt=0, le=50)


class NuevoPedidoVendedor(BaseModel):
    nombre_contacto: str = Field(min_length=1, max_length=200)
    telefono_contacto: str = Field(default="", max_length=20)
    tipo_servicio: Literal["Comer en tienda", "Para recoger en tienda"]
    metodo_pago: Literal["Efectivo", "Tarjeta"]
    items: list[ArticuloVenta] = Field(min_length=1, max_length=50)


class ReporteIngredienteFaltante(BaseModel):
    ingrediente: str = Field(min_length=1, max_length=120)
    nota: str = Field(default="", max_length=300)


class DisponibilidadPizza(BaseModel):
    nombre_pizza: str = Field(min_length=1, max_length=150)
    disponible: bool


GERENTE_EMAIL = os.environ.get("GERENTE_EMAIL", "sajusa1@gmail.com").strip().lower()
GERENTE_NOMBRE = os.environ.get("GERENTE_NOMBRE", "Juan Alcudia Lopez").strip()
GERENTE_PASSWORD = os.environ.get("GERENTE_PASSWORD", "AdminPassword123!")
PASSWORD_RESET_DURATION = timedelta(minutes=3)
MAX_RESET_CODE_ATTEMPTS = 5
PBKDF2_ITERACIONES = 600_000

PRODUCTOS_VENTA = {
    1: ("Pizza Pepperoni", 180.00),
    2: ("Pizza Hawaiana", 170.00),
    3: ("Pizza Carnívora", 210.00),
    4: ("Pizza Mexicana", 195.00),
    5: ("Coca-Cola 2L", 45.00),
    6: ("Agua Fresa Natural 1L", 35.00),
    7: ("Te Manzanita 600ml", 28.00),
    8: ("Papas a la Francesa", 65.00),
    9: ("Alitas BBQ (6 pzas)", 95.00),
    10: ("Pan de Ajo con Queso", 55.00),
}

PRECIOS_TAMANOS_COMBINADOS = {
    "Individual (4 rebanadas)": (2, 110.00),
    "Chica (4 piezas)": (2, 140.00),
    "Mediana (6 piezas)": (2, 185.00),
    "Grande (8 piezas)": (2, 230.00),
    "Jumbo (12 rebanadas)": (4, 310.00),
    "Mega (24 piezas)": (4, 520.00),
    "Cuadripizza (24 reb.) (24 rebanadas)": (4, 540.00),
    "Cuadripizza (32 reb.) (32 rebanadas)": (4, 640.00),
}

INGREDIENTES_POR_PIZZA = {
    "Pizza Pepperoni": ["Masa", "Salsa de tomate", "Queso mozzarella", "Pepperoni"],
    "Pizza Hawaiana": ["Masa", "Salsa de tomate", "Queso mozzarella", "Jamón", "Piña"],
    "Pizza Carnívora": [
        "Masa",
        "Salsa de tomate",
        "Queso mozzarella",
        "Pepperoni",
        "Chorizo",
        "Carne molida",
        "Tocino",
    ],
    "Pizza Mexicana": [
        "Masa",
        "Salsa de tomate",
        "Queso mozzarella",
        "Chorizo",
        "Jalapeño",
        "Cebolla",
        "Pimiento",
    ],
}


def resolver_precio_y_validar_pizza(cursor, nombre_pizza):
    precios_catalogo = {nombre: precio for nombre, precio in PRODUCTOS_VENTA.values()}
    cursor.execute(
        "SELECT nombre_pizza, disponible FROM disponibilidad_pizzas"
    )
    mapa_disp = {fila["nombre_pizza"]: bool(fila["disponible"]) for fila in cursor.fetchall()}

    for sabor, disponible in mapa_disp.items():
        if sabor.casefold() in nombre_pizza.casefold() and not disponible:
            raise HTTPException(
                status_code=409,
                detail=f"{sabor} no está disponible temporalmente por falta de ingredientes.",
            )

    if nombre_pizza in precios_catalogo:
        return precios_catalogo[nombre_pizza]

    for prefijo, (max_comb, precio_fijo) in PRECIOS_TAMANOS_COMBINADOS.items():
        if nombre_pizza.startswith(f"{prefijo} - "):
            parte_sabores = nombre_pizza.split(" - ", 1)[1].removeprefix("Comb.: ")
            sabores = [s.strip() for s in parte_sabores.split(" + ") if s.strip()]
            if not 1 <= len(sabores) <= max_comb:
                raise HTTPException(
                    status_code=422,
                    detail=f"El tamaño {prefijo} permite máximo {max_comb} combinaciones.",
                )
            for s in sabores:
                if s not in INGREDIENTES_POR_PIZZA:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Sabor no reconocido en combinación: {s}",
                    )
            return precio_fijo

    raise HTTPException(
        status_code=422,
        detail=f"Producto no disponible: {nombre_pizza}",
    )


def conectar_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA journal_mode = WAL")
    return conexion


def inicializar_base_datos():
    conexion = conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                primer_apellido TEXT NOT NULL,
                segundo_apellido TEXT NOT NULL,
                telefono TEXT NOT NULL,
                correo TEXT NOT NULL,
                contrasena TEXT NOT NULL
            )
            """
        )

        sql_personal = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='personal'"
        ).fetchone()
        if sql_personal and "'cocinero'" not in sql_personal["sql"]:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute(
                """
                CREATE TABLE personal_nueva (
                    id_personal INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE,
                    telefono TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK (rol IN ('gerente', 'vendedor', 'cocinero')),
                    password_hash TEXT NOT NULL,
                    activo INTEGER NOT NULL DEFAULT 1,
                    creado_en TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO personal_nueva
                    (id_personal, nombre, correo, telefono, rol, password_hash, activo, creado_en)
                SELECT id_personal, nombre, correo, telefono, rol, password_hash, activo, creado_en
                FROM personal
                """
            )
            cursor.execute("DROP TABLE personal")
            cursor.execute("ALTER TABLE personal_nueva RENAME TO personal")
            cursor.execute("PRAGMA foreign_keys = ON")
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS personal (
                    id_personal INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE,
                    telefono TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK (rol IN ('gerente', 'vendedor', 'cocinero')),
                    password_hash TEXT NOT NULL,
                    activo INTEGER NOT NULL DEFAULT 1,
                    creado_en TEXT NOT NULL
                )
                """
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pedidos (
                id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                id_vendedor INTEGER,
                id_cocinero INTEGER,
                tipo_servicio TEXT NOT NULL,
                direccion TEXT,
                referencias TEXT,
                telefono_contacto TEXT,
                subtotal REAL NOT NULL,
                costo_envio REAL NOT NULL,
                total REAL NOT NULL,
                fecha TEXT NOT NULL,
                creado_en TEXT,
                estado TEXT NOT NULL,
                metodo_pago TEXT NOT NULL DEFAULT 'No especificado',
                FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
                FOREIGN KEY (id_vendedor) REFERENCES personal(id_personal),
                FOREIGN KEY (id_cocinero) REFERENCES personal(id_personal)
            )
            """
        )
        columnas_pedidos = {
            fila["name"]
            for fila in cursor.execute("PRAGMA table_info(pedidos)").fetchall()
        }
        if "nombre_contacto" not in columnas_pedidos:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN nombre_contacto TEXT")
        if "hora_recoleccion" not in columnas_pedidos:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN hora_recoleccion TEXT")
        if "id_vendedor" not in columnas_pedidos:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN id_vendedor INTEGER")
        if "id_cocinero" not in columnas_pedidos:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN id_cocinero INTEGER")
        if "telefono_contacto" not in columnas_pedidos:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN telefono_contacto TEXT")
        if "creado_en" not in columnas_pedidos:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN creado_en TEXT")
        if "metodo_pago" not in columnas_pedidos:
            cursor.execute(
                """
                ALTER TABLE pedidos
                ADD COLUMN metodo_pago TEXT NOT NULL DEFAULT 'No especificado'
                """
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS estado_reparto_cocina (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                ultimo_id_cocinero INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO estado_reparto_cocina (id, ultimo_id_cocinero)
            VALUES (1, 0)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reportes_ingredientes (
                id_reporte INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cocinero INTEGER NOT NULL,
                nombre_cocinero TEXT NOT NULL,
                ingrediente TEXT NOT NULL,
                nota TEXT,
                resuelto INTEGER NOT NULL DEFAULT 0,
                creado_en TEXT NOT NULL,
                FOREIGN KEY (id_cocinero) REFERENCES personal(id_personal)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS disponibilidad_pizzas (
                nombre_pizza TEXT PRIMARY KEY,
                disponible INTEGER NOT NULL DEFAULT 1,
                actualizado_por TEXT,
                actualizado_en TEXT
            )
            """
        )
        ahora_seed = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for nombre_pizza in INGREDIENTES_POR_PIZZA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO disponibilidad_pizzas
                    (nombre_pizza, disponible, actualizado_por, actualizado_en)
                VALUES (?, 1, 'Sistema', ?)
                """,
                (nombre_pizza, ahora_seed),
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detalle_pedido (
                id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                id_pedido INTEGER,
                nombre_pizza TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sesiones (
                token_hash TEXT PRIMARY KEY,
                id_cliente INTEGER NOT NULL,
                expira_en TEXT NOT NULL,
                FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sesiones_personal (
                token_hash TEXT PRIMARY KEY,
                id_personal INTEGER NOT NULL,
                expira_en TEXT NOT NULL,
                FOREIGN KEY (id_personal) REFERENCES personal(id_personal)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS restablecimientos_contrasena (
                token_hash TEXT PRIMARY KEY,
                id_cliente INTEGER NOT NULL,
                expira_en TEXT NOT NULL,
                FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS codigos_restablecimiento (
                id_cliente INTEGER PRIMARY KEY,
                codigo_hash TEXT NOT NULL,
                token_hash TEXT,
                expira_en TEXT NOT NULL,
                intentos INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
            )
            """
        )
        if GERENTE_PASSWORD:
            validar_contrasena_personal(GERENTE_PASSWORD)
            cursor.execute(
                "SELECT id_personal, rol FROM personal WHERE LOWER(correo) = ?",
                (GERENTE_EMAIL,),
            )
            gerente_existente = cursor.fetchone()
            if gerente_existente and gerente_existente["rol"] != "gerente":
                raise RuntimeError(
                    "El correo configurado para GERENTE_EMAIL ya pertenece a otro miembro del personal."
                )
            password_hash = hash_password(GERENTE_PASSWORD)
            ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
            cursor.execute(
                """
                INSERT INTO personal
                    (nombre, correo, telefono, rol, password_hash, activo, creado_en)
                VALUES (?, ?, '', 'gerente', ?, 1, ?)
                ON CONFLICT(correo) DO UPDATE SET
                    nombre = excluded.nombre,
                    password_hash = excluded.password_hash,
                    activo = 1
                """,
                (GERENTE_NOMBRE, GERENTE_EMAIL, password_hash, ahora),
            )
        conexion.commit()
    finally:
        conexion.close()


def asignar_siguiente_cocinero(cursor):
    cursor.execute(
        """
        SELECT id_personal
        FROM personal
        WHERE rol = 'cocinero' AND activo = 1
        ORDER BY id_personal ASC
        """
    )
    cocineros = [fila["id_personal"] for fila in cursor.fetchall()]
    if not cocineros:
        return None

    cursor.execute(
        "SELECT ultimo_id_cocinero FROM estado_reparto_cocina WHERE id = 1"
    )
    fila_estado = cursor.fetchone()
    ultimo_id = fila_estado["ultimo_id_cocinero"] if fila_estado else 0

    siguiente_id = next(
        (cid for cid in cocineros if cid > ultimo_id),
        cocineros[0],
    )
    cursor.execute(
        "UPDATE estado_reparto_cocina SET ultimo_id_cocinero = ? WHERE id = 1",
        (siguiente_id,),
    )
    return siguiente_id


SIN_EXPIRACION_CLIENTE = "9999-12-31T23:59:59+00:00"


def crear_sesion(cursor, id_cliente):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    cursor.execute(
        "INSERT INTO sesiones (token_hash, id_cliente, expira_en) VALUES (?, ?, ?)",
        (token_hash, id_cliente, SIN_EXPIRACION_CLIENTE),
    )
    return token


def autenticar_cliente(cursor, authorization):
    if not authorization:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar.")

    esquema, separador, token = authorization.partition(" ")
    if not separador or esquema.casefold() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="La sesión no es válida.")

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    cursor.execute(
        "SELECT id_cliente FROM sesiones WHERE token_hash = ?",
        (token_hash,),
    )
    sesion = cursor.fetchone()
    if not sesion:
        raise HTTPException(status_code=401, detail="La sesión no es válida.")

    return sesion["id_cliente"]


def validar_contrasena_personal(contrasena):
    if requisitos_contrasena_pendientes(contrasena):
        raise HTTPException(
            status_code=422,
            detail=(
                "La contraseña debe tener al menos 8 caracteres e incluir "
                "una mayúscula, una minúscula, un número y un símbolo."
            ),
        )


def validar_contrasena_cliente(contrasena):
    if requisitos_contrasena_pendientes(contrasena):
        raise HTTPException(
            status_code=422,
            detail=(
                "La contraseña debe tener al menos 8 caracteres e incluir "
                "una mayúscula, una minúscula, un número y un símbolo."
            ),
        )


def hash_password(contrasena):
    salt = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode("utf-8"),
        salt,
        PBKDF2_ITERACIONES,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERACIONES}${salt.hex()}${derivado.hex()}"


def verificar_password(contrasena, password_hash):
    try:
        algoritmo, iteraciones, salt_hex, hash_hex = password_hash.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        derivado = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iteraciones),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derivado.hex(), hash_hex)


def crear_sesion_personal(cursor, id_personal):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expira_en = (datetime.now(timezone.utc) + SESSION_DURATION).isoformat()
    cursor.execute(
        """
        INSERT INTO sesiones_personal (token_hash, id_personal, expira_en)
        VALUES (?, ?, ?)
        """,
        (token_hash, id_personal, expira_en),
    )
    return token


def autenticar_personal(cursor, authorization, rol_requerido=None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Inicia sesión como personal.")

    esquema, separador, token = authorization.partition(" ")
    if not separador or esquema.casefold() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="La sesión no es válida.")

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    cursor.execute(
        """
        SELECT p.id_personal, p.nombre, p.correo, p.telefono, p.rol,
               p.activo, s.expira_en
        FROM sesiones_personal s
        JOIN personal p ON p.id_personal = s.id_personal
        WHERE s.token_hash = ?
        """,
        (token_hash,),
    )
    personal = cursor.fetchone()
    if not personal:
        raise HTTPException(status_code=401, detail="La sesión no es válida.")
    if datetime.fromisoformat(personal["expira_en"]) <= datetime.now(timezone.utc):
        cursor.execute(
            "DELETE FROM sesiones_personal WHERE token_hash = ?",
            (token_hash,),
        )
        raise HTTPException(
            status_code=401,
            detail="La sesión expiró. Inicia sesión nuevamente.",
        )
    if not personal["activo"]:
        cursor.execute(
            "DELETE FROM sesiones_personal WHERE token_hash = ?",
            (token_hash,),
        )
        raise HTTPException(status_code=403, detail="La cuenta está desactivada.")
    if rol_requerido and personal["rol"] != rol_requerido:
        raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
    return personal


@asynccontextmanager
async def lifespan(app):
    inicializar_base_datos()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/registro")
def registrar_usuario(user: UsuarioRegistro):
    validar_contrasena_cliente(user.contrasena)
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        correo = user.correo.strip().lower()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            "SELECT id_cliente FROM clientes WHERE LOWER(TRIM(correo)) = ?",
            (correo,),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

        cursor.execute(
            """
            INSERT INTO clientes
                (nombre, primer_apellido, segundo_apellido, telefono, correo, contrasena)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.nombre,
                user.primer_apellido,
                user.segundo_apellido,
                user.telefono,
                correo,
                user.contrasena.strip(),
            ),
        )
        id_usuario = cursor.lastrowid
        token = crear_sesion(cursor, id_usuario)
        conexion.commit()
        return {"mensaje": "Usuario registrado con éxito", "id": id_usuario, "token": token}
    finally:
        conexion.close()


@app.post("/api/login")
def login_usuario(user: UsuarioLogin):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT id_cliente, nombre, primer_apellido
            FROM clientes
            WHERE LOWER(correo) = ? AND contrasena = ?
            """,
            (user.correo.strip().lower(), user.contrasena.strip()),
        )
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

        token = crear_sesion(cursor, resultado["id_cliente"])
        conexion.commit()
        return {
            "id": resultado["id_cliente"],
            "nombre": resultado["nombre"],
            "apellido": resultado["primer_apellido"],
            "token": token,
        }
    finally:
        conexion.close()


@app.post("/api/personal/login")
def login_personal(credenciales: CredencialesPersonal):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT id_personal, nombre, correo, rol, password_hash, activo
            FROM personal
            WHERE LOWER(correo) = ? AND rol = ?
            """,
            (credenciales.correo.strip().lower(), credenciales.rol),
        )
        personal = cursor.fetchone()
        if (
            not personal
            or not personal["activo"]
            or not verificar_password(credenciales.contrasena, personal["password_hash"])
        ):
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

        token = crear_sesion_personal(cursor, personal["id_personal"])
        conexion.commit()
        return {
            "id": personal["id_personal"],
            "nombre": personal["nombre"],
            "correo": personal["correo"],
            "rol": personal["rol"],
            "token": token,
        }
    finally:
        conexion.close()


@app.get("/api/gerencia/vendedores")
def listar_vendedores(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        cursor.execute(
            """
            SELECT id_personal, nombre, correo, telefono, activo, creado_en
            FROM personal
            WHERE rol = 'vendedor'
            ORDER BY nombre COLLATE NOCASE, id_personal
            """
        )
        return {"vendedores": [dict(fila) for fila in cursor.fetchall()]}
    finally:
        conexion.close()


@app.post("/api/gerencia/vendedores", status_code=201)
def crear_vendedor(
    vendedor: NuevoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        validar_contrasena_personal(vendedor.contrasena)
        correo = vendedor.correo.strip().lower()
        cursor.execute(
            """
            INSERT INTO personal
                (nombre, correo, telefono, rol, password_hash, activo, creado_en)
            VALUES (?, ?, ?, 'vendedor', ?, 1, ?)
            """,
            (
                vendedor.nombre.strip(),
                correo,
                vendedor.telefono.strip(),
                hash_password(vendedor.contrasena),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        id_vendedor = cursor.lastrowid
        conexion.commit()
        return {"id": id_vendedor, "mensaje": "Vendedor creado correctamente."}
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        if "UNIQUE constraint failed: personal.correo" in str(error):
            raise HTTPException(status_code=409, detail="Ya existe una cuenta de personal con ese correo.") from error
        raise
    finally:
        conexion.close()


@app.patch("/api/gerencia/vendedores/{id_vendedor}/estado")
def cambiar_estado_vendedor(
    id_vendedor: int,
    estado: EstadoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        cursor.execute(
            "UPDATE personal SET activo = ? WHERE id_personal = ? AND rol = 'vendedor'",
            (int(estado.activo), id_vendedor),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=404, detail="Vendedor no encontrado.")
        if not estado.activo:
            cursor.execute("DELETE FROM sesiones_personal WHERE id_personal = ?", (id_vendedor,))
        conexion.commit()
        return {"mensaje": "Estado del vendedor actualizado."}
    finally:
        conexion.close()


@app.get("/api/gerencia/cocineros")
def listar_cocineros(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        cursor.execute(
            """
            SELECT p.id_personal, p.nombre, p.correo, p.telefono, p.activo, p.creado_en,
                   COUNT(ped.id_pedido) AS pedidos_activos
            FROM personal p
            LEFT JOIN pedidos ped
                ON ped.id_cocinero = p.id_personal AND ped.estado = 'En Proceso'
            WHERE p.rol = 'cocinero'
            GROUP BY p.id_personal
            ORDER BY p.id_personal ASC
            """
        )
        return {"cocineros": [dict(fila) for fila in cursor.fetchall()]}
    finally:
        conexion.close()


@app.post("/api/gerencia/cocineros", status_code=201)
def crear_cocinero(
    cocinero: NuevoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        validar_contrasena_personal(cocinero.contrasena)
        correo = cocinero.correo.strip().lower()
        cursor.execute(
            """
            INSERT INTO personal
                (nombre, correo, telefono, rol, password_hash, activo, creado_en)
            VALUES (?, ?, ?, 'cocinero', ?, 1, ?)
            """,
            (
                cocinero.nombre.strip(),
                correo,
                cocinero.telefono.strip(),
                hash_password(cocinero.contrasena),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        id_cocinero = cursor.lastrowid
        conexion.commit()
        return {"id": id_cocinero, "mensaje": "Cocinero creado correctamente."}
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        if "UNIQUE constraint failed: personal.correo" in str(error):
            raise HTTPException(status_code=409, detail="Ya existe una cuenta de personal con ese correo.") from error
        raise
    finally:
        conexion.close()


@app.patch("/api/gerencia/cocineros/{id_cocinero}/estado")
def cambiar_estado_cocinero(
    id_cocinero: int,
    estado: EstadoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        cursor.execute(
            "UPDATE personal SET activo = ? WHERE id_personal = ? AND rol = 'cocinero'",
            (int(estado.activo), id_cocinero),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=404, detail="Cocinero no encontrado.")
        if not estado.activo:
            cursor.execute("DELETE FROM sesiones_personal WHERE id_personal = ?", (id_cocinero,))
        conexion.commit()
        return {"mensaje": "Estado del cocinero actualizado."}
    finally:
        conexion.close()


@app.post("/api/cocina/ingredientes/faltantes", status_code=201)
def reportar_ingrediente_faltante(
    reporte: ReporteIngredienteFaltante,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cocinero = autenticar_personal(cursor, authorization, "cocinero")
        ahora_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cursor.execute(
            """
            INSERT INTO reportes_ingredientes
                (id_cocinero, nombre_cocinero, ingrediente, nota, resuelto, creado_en)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                cocinero["id_personal"],
                cocinero["nombre"],
                reporte.ingrediente.strip(),
                reporte.nota.strip(),
                ahora_iso,
            ),
        )
        conexion.commit()
        return {"id_reporte": cursor.lastrowid, "mensaje": "Reporte enviado a vendedor y gerencia."}
    finally:
        conexion.close()


@app.get("/api/personal/ingredientes/faltantes")
def listar_reportes_ingredientes(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("gerente", "vendedor", "cocinero"):
            raise HTTPException(status_code=403, detail="No autorizado.")
        cursor.execute(
            """
            SELECT id_reporte, nombre_cocinero, ingrediente, nota, resuelto, creado_en
            FROM reportes_ingredientes
            ORDER BY resuelto ASC, id_reporte DESC
            LIMIT 100
            """
        )
        return {"reportes": [dict(fila) for fila in cursor.fetchall()]}
    finally:
        conexion.close()


@app.get("/api/pizzas/disponibilidad")
def obtener_disponibilidad_pizzas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT nombre_pizza, disponible, actualizado_por, actualizado_en
            FROM disponibilidad_pizzas
            ORDER BY nombre_pizza ASC
            """
        )
        return {
            "pizzas": [
                {
                    "nombre_pizza": fila["nombre_pizza"],
                    "disponible": bool(fila["disponible"]),
                    "ingredientes": INGREDIENTES_POR_PIZZA.get(fila["nombre_pizza"], []),
                    "actualizado_por": fila["actualizado_por"],
                    "actualizado_en": fila["actualizado_en"],
                }
                for fila in cursor.fetchall()
            ]
        }
    finally:
        conexion.close()


@app.patch("/api/personal/pizzas/disponibilidad")
def actualizar_disponibilidad_pizza(
    cambio: DisponibilidadPizza,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("gerente", "vendedor"):
            raise HTTPException(
                status_code=403,
                detail="Solo vendedor o gerencia pueden cambiar la disponibilidad en el menú.",
            )
        ahora_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cursor.execute(
            """
            INSERT INTO disponibilidad_pizzas
                (nombre_pizza, disponible, actualizado_por, actualizado_en)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(nombre_pizza) DO UPDATE SET
                disponible = excluded.disponible,
                actualizado_por = excluded.actualizado_por,
                actualizado_en = excluded.actualizado_en
            """,
            (
                cambio.nombre_pizza.strip(),
                int(cambio.disponible),
                f"{personal['nombre']} ({personal['rol']})",
                ahora_iso,
            ),
        )
        if cambio.disponible:
            for ing in INGREDIENTES_POR_PIZZA.get(cambio.nombre_pizza.strip(), []):
                cursor.execute(
                    """
                    UPDATE reportes_ingredientes
                    SET resuelto = 1
                    WHERE LOWER(ingrediente) = ? AND resuelto = 0
                    """,
                    (ing.casefold(),),
                )
        conexion.commit()
        return {
            "nombre_pizza": cambio.nombre_pizza.strip(),
            "disponible": cambio.disponible,
            "mensaje": "Disponibilidad actualizada en todas las presentaciones.",
        }
    finally:
        conexion.close()


@app.get("/api/cocina/pedidos")
def listar_pedidos_cocina(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cocinero = autenticar_personal(cursor, authorization, "cocinero")
        cursor.execute(
            """
            SELECT id_pedido, nombre_contacto, tipo_servicio, fecha,
                   creado_en, hora_recoleccion, estado,
                   CASE
                       WHEN id_cliente IS NOT NULL AND id_vendedor IS NULL
                           THEN 'App'
                       ELSE 'Mostrador'
                   END AS origen
            FROM pedidos
            WHERE id_cocinero = ? AND estado IN ('En Proceso', 'Lista')
            ORDER BY julianday(creado_en) ASC, id_pedido ASC
            """,
            (cocinero["id_personal"],),
        )
        pedidos = [dict(fila) for fila in cursor.fetchall()]
        for pedido in pedidos:
            pedido["codigo"] = f"PE-{pedido['id_pedido']:06d}"
            cursor.execute(
                """
                SELECT nombre_pizza, cantidad
                FROM detalle_pedido
                WHERE id_pedido = ?
                ORDER BY id_detalle
                """,
                (pedido["id_pedido"],),
            )
            detalles = []
            for fila in cursor.fetchall():
                item_dict = dict(fila)
                ings = list(INGREDIENTES_POR_PIZZA.get(item_dict["nombre_pizza"], []))
                if not ings:
                    for clave, lista_ing in INGREDIENTES_POR_PIZZA.items():
                        if clave.casefold() in item_dict["nombre_pizza"].casefold():
                            for ing in lista_ing:
                                if ing not in ings:
                                    ings.append(ing)
                item_dict["ingredientes"] = ings
                detalles.append(item_dict)
            pedido["detalles"] = detalles
        return {"pedidos": pedidos}
    finally:
        conexion.close()


@app.patch("/api/cocina/pedidos/{id_pedido}/listo")
def marcar_pedido_listo_cocina(
    id_pedido: int,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cocinero = autenticar_personal(cursor, authorization, "cocinero")
        cursor.execute(
            "SELECT estado FROM pedidos WHERE id_pedido = ? AND id_cocinero = ?",
            (id_pedido, cocinero["id_personal"]),
        )
        pedido = cursor.fetchone()
        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        if pedido["estado"] != "En Proceso":
            raise HTTPException(status_code=409, detail="Este pedido ya fue marcado como listo o finalizado.")

        cursor.execute(
            """
            UPDATE pedidos
            SET estado = 'Lista'
            WHERE id_pedido = ? AND id_cocinero = ? AND estado = 'En Proceso'
            """,
            (id_pedido, cocinero["id_personal"]),
        )
        conexion.commit()
        return {"mensaje": "Pedido marcado como listo.", "estado": "Lista"}
    finally:
        conexion.close()


@app.post("/api/personal/pedidos", status_code=201)
def crear_pedido_vendedor(
    pedido: NuevoPedidoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        vendedor = autenticar_personal(cursor, authorization, "vendedor")
        nombre_contacto = pedido.nombre_contacto.strip()
        telefono = pedido.telefono_contacto.strip()
        if pedido.tipo_servicio == "Para recoger en tienda":
            if len("".join(c for c in telefono if c.isdigit())) != 10:
                raise HTTPException(status_code=422, detail="Para recoger en tienda se requiere un teléfono de 10 dígitos.")
        elif telefono:
            raise HTTPException(status_code=422, detail="Comer en tienda no requiere teléfono.")

        productos = []
        subtotal = 0.0
        for item in pedido.items:
            if isinstance(item.producto_id, int) and item.producto_id in PRODUCTOS_VENTA:
                nombre, _ = PRODUCTOS_VENTA[item.producto_id]
            elif item.nombre_pizza:
                nombre = item.nombre_pizza.strip()
            else:
                raise HTTPException(status_code=422, detail="El pedido incluye un producto no disponible.")
            precio = resolver_precio_y_validar_pizza(cursor, nombre)
            productos.append((nombre, item.cantidad, precio))
            subtotal += item.cantidad * precio

        subtotal = round(subtotal, 2)
        ahora = datetime.now().astimezone()
        cursor.execute("BEGIN IMMEDIATE")
        id_cocinero = asignar_siguiente_cocinero(cursor)
        cursor.execute(
            """
            INSERT INTO pedidos (
                id_cliente, id_vendedor, id_cocinero, nombre_contacto, tipo_servicio,
                direccion, referencias, telefono_contacto, subtotal,
                costo_envio, total, fecha, creado_en, estado, hora_recoleccion,
                metodo_pago
            )
            VALUES (
                NULL, ?, ?, ?, ?, '', '', ?, ?, 0, ?, ?, ?, 'En Proceso', NULL, ?
            )
            """,
            (
                vendedor["id_personal"],
                id_cocinero,
                nombre_contacto,
                pedido.tipo_servicio,
                telefono,
                subtotal,
                subtotal,
                ahora.strftime("%d/%m/%Y - %H:%M"),
                ahora.isoformat(timespec="seconds"),
                pedido.metodo_pago,
            ),
        )
        id_pedido = cursor.lastrowid
        cursor.executemany(
            """
            INSERT INTO detalle_pedido
                (id_pedido, nombre_pizza, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
            """,
            [(id_pedido, nombre, cantidad, precio) for nombre, cantidad, precio in productos],
        )
        conexion.commit()
        return {
            "id_pedido": id_pedido,
            "codigo": f"PE-{id_pedido:06d}",
            "subtotal": subtotal,
            "total": subtotal,
            "metodo_pago": pedido.metodo_pago,
            "id_cocinero": id_cocinero,
        }
    except HTTPException:
        conexion.rollback()
        raise
    finally:
        conexion.close()


@app.post("/api/pedidos", status_code=201)
def crear_pedido(pedido: NuevoPedido, authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        id_cliente = autenticar_cliente(cursor, authorization)
        items_validados = []
        subtotal_calculado = 0.0
        for item in pedido.items:
            precio_real = resolver_precio_y_validar_pizza(cursor, item.nombre_pizza)
            items_validados.append((item.nombre_pizza, item.cantidad, precio_real))
            subtotal_calculado += item.cantidad * precio_real

        subtotal_calculado = round(subtotal_calculado, 2)
        costo_envio_calculado = 35.0 if pedido.tipo_servicio == "A Domicilio" else 0.0
        total_calculado = round(subtotal_calculado + costo_envio_calculado, 2)

        if pedido.tipo_servicio == "En Tienda":
            if pedido.hora_recoleccion is None:
                raise HTTPException(status_code=422, detail="Selecciona una hora de recolección.")
            hora_recoleccion_guardada = pedido.hora_recoleccion.isoformat(timespec="minutes")
        else:
            hora_recoleccion_guardada = None

        cursor.execute("BEGIN IMMEDIATE")
        id_cocinero = asignar_siguiente_cocinero(cursor)
        cursor.execute(
            """
            INSERT INTO pedidos (
                id_cliente, id_cocinero, nombre_contacto, tipo_servicio, direccion,
                referencias, subtotal, costo_envio, total, fecha, estado,
                hora_recoleccion, telefono_contacto, creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'En Proceso', ?, ?, ?)
            """,
            (
                id_cliente,
                id_cocinero,
                pedido.nombre_contacto.strip(),
                pedido.tipo_servicio,
                pedido.direccion.strip(),
                pedido.referencias.strip(),
                subtotal_calculado,
                costo_envio_calculado,
                total_calculado,
                datetime.now().strftime("%d/%m/%Y - %H:%M"),
                hora_recoleccion_guardada,
                "",
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
        id_pedido = cursor.lastrowid
        cursor.executemany(
            """
            INSERT INTO detalle_pedido
                (id_pedido, nombre_pizza, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
            """,
            [(id_pedido, nombre, cantidad, precio) for nombre, cantidad, precio in items_validados],
        )
        conexion.commit()
        return {
            "id_pedido": id_pedido,
            "codigo": f"PE-{id_pedido:06d}",
            "id_cocinero": id_cocinero,
        }
    except HTTPException:
        conexion.rollback()
        raise
    finally:
        conexion.close()

def _resolver_filtro_fecha(fecha_texto: str | None):
    if fecha_texto:
        try:
            fecha_obj = date.fromisoformat(fecha_texto.strip())
        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail="Formato de fecha inválido. Usa AAAA-MM-DD.",
            ) from error
    else:
        fecha_obj = datetime.now().astimezone().date()
    return fecha_obj.isoformat(), f"{fecha_obj.strftime('%d/%m/%Y')}%"


def _extraer_id_desde_codigo(codigo: str) -> int:
    limpio = codigo.strip().upper().removeprefix("PE-").lstrip("0") or "0"
    if not limpio.isdigit() or int(limpio) <= 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    return int(limpio)


def _cargar_detalles_pedido(cursor, id_pedido: int):
    cursor.execute(
        """
        SELECT nombre_pizza, cantidad, precio_unitario
        FROM detalle_pedido
        WHERE id_pedido = ?
        ORDER BY id_detalle ASC
        """,
        (id_pedido,),
    )
    return [dict(fila) for fila in cursor.fetchall()]


@app.get("/api/gerencia/reporte")
def obtener_reporte_gerencia(
    fecha: str | None = None,
    authorization: str | None = Header(default=None),
):
    fecha_iso, fecha_like = _resolver_filtro_fecha(fecha)
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        filtro = (
            "(substr(COALESCE(p.creado_en, ''), 1, 10) = ? OR p.fecha LIKE ?) "
            "AND p.estado != 'Cancelada'"
        )
        cursor.execute(
            f"""
            SELECT COALESCE(SUM(p.total), 0.0) AS ingresos,
                   COUNT(*) AS cantidad_pedidos
            FROM pedidos p
            WHERE {filtro}
            """,
            (fecha_iso, fecha_like),
        )
        totales = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT p.tipo_servicio,
                   COUNT(*) AS cantidad,
                   COALESCE(SUM(p.total), 0.0) AS ingresos
            FROM pedidos p
            WHERE {filtro}
            GROUP BY p.tipo_servicio
            ORDER BY ingresos DESC
            """,
            (fecha_iso, fecha_like),
        )
        por_servicio = [
            {
                "tipo_servicio": fila["tipo_servicio"],
                "cantidad": int(fila["cantidad"]),
                "ingresos": round(float(fila["ingresos"]), 2),
            }
            for fila in cursor.fetchall()
        ]

        cursor.execute(
            f"""
            SELECT COALESCE(v.nombre, 'App') AS vendedor,
                   COUNT(*) AS cantidad,
                   COALESCE(SUM(p.total), 0.0) AS ingresos
            FROM pedidos p
            LEFT JOIN personal v ON v.id_personal = p.id_vendedor
            WHERE {filtro}
            GROUP BY COALESCE(v.nombre, 'App')
            ORDER BY ingresos DESC
            """,
            (fecha_iso, fecha_like),
        )
        por_vendedor = [
            {
                "vendedor": fila["vendedor"],
                "cantidad": int(fila["cantidad"]),
                "ingresos": round(float(fila["ingresos"]), 2),
            }
            for fila in cursor.fetchall()
        ]

        return {
            "fecha": fecha_iso,
            "ingresos": round(float(totales["ingresos"]), 2),
            "cantidad_pedidos": int(totales["cantidad_pedidos"]),
            "por_servicio": por_servicio,
            "por_vendedor": por_vendedor,
        }
    finally:
        conexion.close()


@app.get("/api/gerencia/pedidos")
def listar_pedidos_gerencia(
    fecha: str | None = None,
    authorization: str | None = Header(default=None),
):
    fecha_iso, fecha_like = _resolver_filtro_fecha(fecha)
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        cursor.execute(
            """
            SELECT p.id_pedido, p.nombre_contacto, p.tipo_servicio,
                   p.telefono_contacto, p.subtotal, p.costo_envio, p.total,
                   p.fecha, p.creado_en, p.estado, p.metodo_pago,
                   COALESCE(v.nombre, 'App') AS vendedor,
                   COALESCE(c.nombre, 'Sin asignar') AS cocinero
            FROM pedidos p
            LEFT JOIN personal v ON v.id_personal = p.id_vendedor
            LEFT JOIN personal c ON c.id_personal = p.id_cocinero
            WHERE substr(COALESCE(p.creado_en, ''), 1, 10) = ?
               OR p.fecha LIKE ?
            ORDER BY COALESCE(julianday(p.creado_en), 0) DESC, p.id_pedido DESC
            """,
            (fecha_iso, fecha_like),
        )
        pedidos = []
        for fila in cursor.fetchall():
            pedido = dict(fila)
            pedido["codigo"] = f"PE-{pedido['id_pedido']:06d}"
            pedido["detalles"] = _cargar_detalles_pedido(cursor, pedido["id_pedido"])
            pedidos.append(pedido)
        return {"pedidos": pedidos}
    finally:
        conexion.close()


@app.patch("/api/gerencia/pedidos/{id_pedido}/cancelar")
def cancelar_pedido_gerencia(
    id_pedido: int,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        cursor.execute(
            "SELECT estado FROM pedidos WHERE id_pedido = ?",
            (id_pedido,),
        )
        pedido = cursor.fetchone()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        if pedido["estado"] == "Cancelada":
            raise HTTPException(status_code=409, detail="El pedido ya está cancelado.")
        cursor.execute(
            "UPDATE pedidos SET estado = 'Cancelada' WHERE id_pedido = ?",
            (id_pedido,),
        )
        conexion.commit()
        return {"mensaje": "Pedido cancelado.", "estado": "Cancelada"}
    finally:
        conexion.close()


@app.get("/api/personal/pedidos")
def listar_pedidos_personal(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("vendedor", "gerente"):
            raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
        cursor.execute(
            """
            SELECT p.id_pedido, p.id_vendedor, p.nombre_contacto, p.tipo_servicio,
                   p.telefono_contacto, p.subtotal, p.costo_envio, p.total,
                   p.fecha, p.creado_en, p.estado, p.metodo_pago,
                   CASE
                       WHEN p.id_cliente IS NOT NULL AND p.id_vendedor IS NULL
                           THEN 'App'
                       ELSE 'Mostrador'
                   END AS origen
            FROM pedidos p
            ORDER BY COALESCE(julianday(p.creado_en), 0) DESC, p.id_pedido DESC
            LIMIT 200
            """
        )
        pedidos = []
        for fila in cursor.fetchall():
            pedido = dict(fila)
            pedido["codigo"] = f"PE-{pedido['id_pedido']:06d}"
            pedido["detalles"] = _cargar_detalles_pedido(cursor, pedido["id_pedido"])
            pedidos.append(pedido)
        return {"pedidos": pedidos}
    finally:
        conexion.close()


@app.get("/api/personal/pedidos/codigo/{codigo}")
def buscar_pedido_por_codigo_api(
    codigo: str,
    authorization: str | None = Header(default=None),
):
    id_pedido = _extraer_id_desde_codigo(codigo)
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("vendedor", "gerente"):
            raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
        cursor.execute(
            """
            SELECT p.id_pedido, p.id_vendedor, p.nombre_contacto, p.tipo_servicio,
                   p.telefono_contacto, p.subtotal, p.costo_envio, p.total,
                   p.fecha, p.creado_en, p.estado, p.metodo_pago,
                   CASE
                       WHEN p.id_cliente IS NOT NULL AND p.id_vendedor IS NULL
                           THEN 'App'
                       ELSE 'Mostrador'
                   END AS origen
            FROM pedidos p
            WHERE p.id_pedido = ?
            """,
            (id_pedido,),
        )
        fila = cursor.fetchone()
        if not fila:
            raise HTTPException(status_code=404, detail="No se encontró el pedido.")
        pedido = dict(fila)
        pedido["codigo"] = f"PE-{pedido['id_pedido']:06d}"
        pedido["detalles"] = _cargar_detalles_pedido(cursor, pedido["id_pedido"])
        return pedido
    finally:
        conexion.close()


@app.patch("/api/personal/pedidos/codigo/{codigo}/entregar")
def entregar_pedido_por_codigo(
    codigo: str,
    authorization: str | None = Header(default=None),
):
    id_pedido = _extraer_id_desde_codigo(codigo)
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("vendedor", "gerente"):
            raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
        cursor.execute(
            "SELECT estado FROM pedidos WHERE id_pedido = ?",
            (id_pedido,),
        )
        pedido = cursor.fetchone()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        if pedido["estado"] == "Cancelada":
            raise HTTPException(
                status_code=409,
                detail="No se puede entregar un pedido cancelado.",
            )
        if pedido["estado"] == "Finalizada":
            raise HTTPException(
                status_code=409,
                detail="Este pedido ya fue entregado.",
            )
        cursor.execute(
            "UPDATE pedidos SET estado = 'Finalizada' WHERE id_pedido = ?",
            (id_pedido,),
        )
        conexion.commit()
        return {"mensaje": "Pedido entregado y finalizado.", "estado": "Finalizada"}
    finally:
        conexion.close()


@app.patch("/api/personal/pedidos/{id_pedido}/estado")
def actualizar_estado_pedido_personal(
    id_pedido: int,
    cambio: EstadoPedidoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("vendedor", "gerente"):
            raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
        cursor.execute(
            "SELECT estado FROM pedidos WHERE id_pedido = ?",
            (id_pedido,),
        )
        pedido = cursor.fetchone()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        if pedido["estado"] == "Cancelada":
            raise HTTPException(
                status_code=409,
                detail="No se puede modificar un pedido cancelado.",
            )
        cursor.execute(
            "UPDATE pedidos SET estado = ? WHERE id_pedido = ?",
            (cambio.estado, id_pedido),
        )
        conexion.commit()
        return {"mensaje": "Estado del pedido actualizado.", "estado": cambio.estado}
    finally:
        conexion.close()


@app.post("/api/personal/pedidos/leer-codigo")
async def leer_codigo_pedido_imagen(
    request: Request,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        personal = autenticar_personal(cursor, authorization)
        if personal["rol"] not in ("vendedor", "gerente"):
            raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
    finally:
        conexion.close()

    datos = await request.body()
    if not datos:
        raise HTTPException(status_code=400, detail="No se recibió ninguna imagen.")

    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen = ImageOps.exif_transpose(imagen)
    except UnidentifiedImageError as error:
        raise HTTPException(status_code=400, detail="La imagen enviada no es válida.") from error

    variantes = [
        imagen,
        ImageOps.grayscale(imagen),
        ImageOps.autocontrast(ImageOps.grayscale(imagen)),
        ImageEnhance.Contrast(ImageOps.grayscale(imagen)).enhance(2.0),
    ]
    for variante in variantes:
        for resultado in zxingcpp.read_barcodes(variante):
            texto = (resultado.text or "").strip().upper()
            coincidencia = re.search(r"PE-\d+", texto)
            if coincidencia:
                return {"codigo": coincidencia.group(0)}
            if texto.isdigit():
                return {"codigo": f"PE-{int(texto):06d}"}

    raise HTTPException(
        status_code=422,
        detail="No se detectó ningún código en la imagen.",
    )


@app.get("/api/pedidos")
def listar_pedidos_cliente(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        id_cliente = autenticar_cliente(cursor, authorization)
        cursor.execute(
            """
            SELECT id_pedido, nombre_contacto, tipo_servicio, direccion,
                   referencias, telefono_contacto, subtotal, costo_envio,
                   total, fecha, creado_en, estado, hora_recoleccion,
                   metodo_pago
            FROM pedidos
            WHERE id_cliente = ?
            ORDER BY COALESCE(julianday(creado_en), 0) DESC, id_pedido DESC
            """,
            (id_cliente,),
        )
        pedidos = []
        for fila in cursor.fetchall():
            pedido = dict(fila)
            pedido["codigo"] = f"PE-{pedido['id_pedido']:06d}"
            pedido["detalles"] = _cargar_detalles_pedido(cursor, pedido["id_pedido"])
            pedidos.append(pedido)
        return {"pedidos": pedidos}
    finally:
        conexion.close()

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("PIZZAEXPRESS_HOST", "0.0.0.0")
    port = int(os.environ.get("PIZZAEXPRESS_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)