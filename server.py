import hashlib
import hmac
import io
import os
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import zxingcpp

# Permite definir una carpeta persistente en la nube o usar la local por defecto
DB_FOLDER = os.environ.get("DATA_DIR", "")
if DB_FOLDER:
    DATABASE_PATH = Path(DB_FOLDER) / "pizza_express.db"
else:
    DATABASE_PATH = Path(__file__).resolve().with_name("pizza_express.db")
SESSION_DURATION = timedelta(days=30)


class UsuarioLogin(BaseModel):
    correo: str
    contrasena: str


class UsuarioRegistro(BaseModel):
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    telefono: str
    correo: str
    contrasena: str


class ArticuloPedido(BaseModel):
    nombre_pizza: str = Field(min_length=1, max_length=150)
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
    rol: Literal["gerente", "vendedor"]


class NuevoVendedor(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    correo: str = Field(min_length=3, max_length=254)
    telefono: str = Field(min_length=10, max_length=20)
    contrasena: str = Field(min_length=12, max_length=256)


class EstadoVendedor(BaseModel):
    activo: bool


class EstadoPedidoVendedor(BaseModel):
    estado: Literal["Lista", "Finalizada"]


class ArticuloVenta(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=50)


class NuevoPedidoVendedor(BaseModel):
    nombre_contacto: str = Field(min_length=1, max_length=200)
    telefono_contacto: str = Field(default="", max_length=20)
    tipo_servicio: Literal["Comer en tienda", "Para recoger en tienda"]
    metodo_pago: Literal["Efectivo", "Tarjeta"]
    items: list[ArticuloVenta] = Field(min_length=1, max_length=50)


GERENTE_EMAIL = os.environ.get("GERENTE_EMAIL", "sajusa1@gmail.com").strip().lower()
GERENTE_NOMBRE = os.environ.get("GERENTE_NOMBRE", "Juan Alcudia Lopez").strip()
GERENTE_PASSWORD = os.environ.get("GERENTE_PASSWORD", "AdminPassword123!")
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


def conectar_db():
    conexion = sqlite3.connect(DATABASE_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS personal (
                id_personal INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                telefono TEXT NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('gerente', 'vendedor')),
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
                FOREIGN KEY (id_vendedor) REFERENCES personal(id_personal)
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
        pedidos_legacy = cursor.execute(
            """
            SELECT id_pedido, fecha
            FROM pedidos
            WHERE creado_en IS NULL OR creado_en = ''
            """
        ).fetchall()
        for pedido_legacy in pedidos_legacy:
            fecha_legacy = datetime.strptime(
                pedido_legacy["fecha"],
                "%d/%m/%Y - %H:%M",
            ).astimezone()
            cursor.execute(
                "UPDATE pedidos SET creado_en = ? WHERE id_pedido = ?",
                (
                    fecha_legacy.isoformat(timespec="seconds"),
                    pedido_legacy["id_pedido"],
                ),
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
        if GERENTE_PASSWORD:
            validar_contrasena_personal(GERENTE_PASSWORD)
            cursor.execute(
                "SELECT id_personal, rol FROM personal WHERE LOWER(correo) = ?",
                (GERENTE_EMAIL,),
            )
            gerente_existente = cursor.fetchone()
            if gerente_existente and gerente_existente["rol"] != "gerente":
                raise RuntimeError(
                    "El correo configurado para GERENTE_EMAIL ya pertenece a un vendedor."
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
            cursor.execute(
                """
                DELETE FROM sesiones_personal
                WHERE id_personal = (
                    SELECT id_personal FROM personal
                    WHERE LOWER(correo) = ? AND rol = 'gerente'
                )
                """,
                (GERENTE_EMAIL,),
            )
        else:
            cursor.execute(
                """
                UPDATE personal
                SET activo = 0
                WHERE LOWER(correo) = ? AND rol = 'gerente'
                """,
                (GERENTE_EMAIL,),
            )
            cursor.execute(
                """
                DELETE FROM sesiones_personal
                WHERE id_personal IN (
                    SELECT id_personal FROM personal
                    WHERE LOWER(correo) = ? AND rol = 'gerente'
                )
                """,
                (GERENTE_EMAIL,),
            )
        conexion.commit()
    finally:
        conexion.close()


def crear_sesion(cursor, id_cliente):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expira_en = (datetime.now(timezone.utc) + SESSION_DURATION).isoformat()
    cursor.execute(
        "INSERT INTO sesiones (token_hash, id_cliente, expira_en) VALUES (?, ?, ?)",
        (token_hash, id_cliente, expira_en),
    )
    return token


def validar_contrasena_personal(contrasena):
    if (
        len(contrasena) < 12
        or not any(caracter.isupper() for caracter in contrasena)
        or not any(caracter.islower() for caracter in contrasena)
        or not any(caracter.isdigit() for caracter in contrasena)
        or not any(not caracter.isalnum() for caracter in contrasena)
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "La contraseña debe tener 12 caracteres e incluir "
                "mayúsculas, minúsculas, números y símbolos."
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


def autenticar_cliente(cursor, authorization):
    if not authorization:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar.")

    esquema, separador, token = authorization.partition(" ")
    if not separador or esquema.casefold() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="La sesión no es válida.")

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    cursor.execute(
        "SELECT id_cliente, expira_en FROM sesiones WHERE token_hash = ?",
        (token_hash,),
    )
    sesion = cursor.fetchone()
    if not sesion:
        raise HTTPException(status_code=401, detail="La sesión no es válida.")

    if datetime.fromisoformat(sesion["expira_en"]) <= datetime.now(timezone.utc):
        cursor.execute("DELETE FROM sesiones WHERE token_hash = ?", (token_hash,))
        raise HTTPException(
            status_code=401,
            detail="La sesión expiró. Inicia sesión nuevamente.",
        )
    return sesion["id_cliente"]


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
            raise HTTPException(
                status_code=409,
                detail="Ya existe una cuenta con ese correo",
            )

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
        return {
            "mensaje": "Usuario registrado con éxito",
            "id": id_usuario,
            "token": token,
        }
    except HTTPException:
        conexion.rollback()
        raise
    except sqlite3.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una cuenta con ese correo",
        )
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
            raise HTTPException(
                status_code=401,
                detail="Correo o contraseña incorrectos",
            )

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
        if credenciales.rol == "gerente" and not GERENTE_PASSWORD:
            raise HTTPException(
                status_code=503,
                detail="La cuenta gerencial no está configurada en el servidor.",
            )
        if (
            not personal
            or not personal["activo"]
            or not verificar_password(
                credenciales.contrasena,
                personal["password_hash"],
            )
        ):
            raise HTTPException(
                status_code=401,
                detail="Correo o contraseña incorrectos.",
            )

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
            raise HTTPException(
                status_code=409,
                detail="Ya existe una cuenta de personal con ese correo.",
            ) from error
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
            """
            UPDATE personal
            SET activo = ?
            WHERE id_personal = ? AND rol = 'vendedor'
            """,
            (int(estado.activo), id_vendedor),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=404, detail="Vendedor no encontrado.")
        if not estado.activo:
            cursor.execute(
                """
                DELETE FROM sesiones_personal
                WHERE id_personal = ?
                """,
                (id_vendedor,),
            )
        conexion.commit()
        return {"mensaje": "Estado del vendedor actualizado."}
    except HTTPException:
        conexion.rollback()
        raise
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
            if len("".join(caracter for caracter in telefono if caracter.isdigit())) != 10:
                raise HTTPException(
                    status_code=422,
                    detail="Para recoger en tienda se requiere un teléfono de 10 dígitos.",
                )
        elif telefono:
            raise HTTPException(
                status_code=422,
                detail="Comer en tienda no requiere teléfono.",
            )

        productos = []
        subtotal = 0.0
        for item in pedido.items:
            producto = PRODUCTOS_VENTA.get(item.producto_id)
            if producto is None:
                raise HTTPException(
                    status_code=422,
                    detail="El pedido incluye un producto no disponible.",
                )
            nombre, precio = producto
            productos.append((item.producto_id, nombre, item.cantidad, precio))
            subtotal += item.cantidad * precio
        subtotal = round(subtotal, 2)
        ahora = datetime.now().astimezone()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            """
            INSERT INTO pedidos (
                id_cliente, id_vendedor, nombre_contacto, tipo_servicio,
                direccion, referencias, telefono_contacto, subtotal,
                costo_envio, total, fecha, creado_en, estado, hora_recoleccion,
                metodo_pago
            )
            VALUES (
                NULL, ?, ?, ?, '', '', ?, ?, 0, ?, ?, ?, 'En Proceso', NULL, ?
            )
            """,
            (
                vendedor["id_personal"],
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
            [
                (id_pedido, nombre, cantidad, precio)
                for _, nombre, cantidad, precio in productos
            ],
        )
        conexion.commit()
        return {
            "id_pedido": id_pedido,
            "codigo": f"PE-{id_pedido:06d}",
            "subtotal": subtotal,
            "total": subtotal,
            "metodo_pago": pedido.metodo_pago,
        }
    except HTTPException:
        conexion.rollback()
        raise
    except sqlite3.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


@app.get("/api/personal/pedidos")
def listar_pedidos_vendedor(
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        vendedor = autenticar_personal(cursor, authorization, "vendedor")
        cursor.execute(
            """
            SELECT id_pedido, id_vendedor, nombre_contacto, telefono_contacto, tipo_servicio,
                   fecha, creado_en, total, estado, metodo_pago,
                   'Mostrador' AS origen
            FROM pedidos
            WHERE id_vendedor = ?
            ORDER BY julianday(creado_en) DESC, id_pedido DESC
            LIMIT 200
            """,
            (vendedor["id_personal"],),
        )
        pedidos = [dict(fila) for fila in cursor.fetchall()]
        for pedido in pedidos:
            cursor.execute(
                """
                SELECT nombre_pizza, cantidad, precio_unitario
                FROM detalle_pedido
                WHERE id_pedido = ?
                ORDER BY id_detalle
                """,
                (pedido["id_pedido"],),
            )
            pedido["detalles"] = [dict(fila) for fila in cursor.fetchall()]
        return {"pedidos": pedidos}
    finally:
        conexion.close()


@app.patch("/api/personal/pedidos/{id_pedido}/estado")
def cambiar_estado_pedido_vendedor(
    id_pedido: int,
    estado: EstadoPedidoVendedor,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        vendedor = autenticar_personal(cursor, authorization, "vendedor")
        cursor.execute(
            """
            SELECT tipo_servicio, estado
            FROM pedidos
            WHERE id_pedido = ? AND id_vendedor = ?
            """,
            (id_pedido, vendedor["id_personal"]),
        )
        pedido = cursor.fetchone()
        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        if pedido["estado"] in ("Cancelada", "Finalizada"):
            raise HTTPException(
                status_code=409,
                detail="El pedido ya no admite cambios de estado.",
            )
        if (
            estado.estado == "Lista"
            and pedido["tipo_servicio"] != "Para recoger en tienda"
        ):
            raise HTTPException(
                status_code=422,
                detail="Solo los pedidos para recoger pueden marcarse como listos.",
            )
        if estado.estado == "Lista" and pedido["estado"] != "En Proceso":
            raise HTTPException(
                status_code=409,
                detail="El pedido ya avanzó a otro estado.",
            )
        if estado.estado == "Finalizada" and pedido["estado"] not in (
            "En Proceso",
            "Lista",
        ):
            raise HTTPException(
                status_code=409,
                detail="El pedido ya avanzó a otro estado.",
            )
        estados_previos = (
            ("En Proceso",)
            if estado.estado == "Lista"
            else ("En Proceso", "Lista")
        )
        marcadores = ", ".join("?" for _ in estados_previos)
        cursor.execute(
            f"""
            UPDATE pedidos
            SET estado = ?
            WHERE id_pedido = ? AND id_vendedor = ?
              AND estado IN ({marcadores})
            """,
            (
                estado.estado,
                id_pedido,
                vendedor["id_personal"],
                *estados_previos,
            ),
        )
        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=409,
                detail="El pedido ya avanzó a otro estado.",
            )
        conexion.commit()
        return {"mensaje": "Estado del pedido actualizado.", "estado": estado.estado}
    except HTTPException:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def obtener_id_pedido_codigo(codigo):
    coincidencia = re.fullmatch(r"(?:PE-)?(\d{1,10})", codigo.strip().upper())
    if coincidencia is None:
        raise HTTPException(
            status_code=422,
            detail="Usa un código válido, por ejemplo PE-000019.",
        )
    return int(coincidencia.group(1))


def obtener_pedido_para_entrega(cursor, id_pedido):
    cursor.execute(
        """
        SELECT p.id_pedido, p.nombre_contacto, p.tipo_servicio,
               p.telefono_contacto, p.fecha, p.total, p.estado, p.metodo_pago,
               COALESCE(v.nombre, 'Cliente de la app') AS vendedor,
               CASE
                   WHEN p.id_cliente IS NOT NULL AND p.id_vendedor IS NULL
                       THEN 'App'
                   ELSE 'Mostrador'
               END AS origen
        FROM pedidos p
        LEFT JOIN personal v ON v.id_personal = p.id_vendedor
        WHERE p.id_pedido = ?
        """,
        (id_pedido,),
    )
    pedido = cursor.fetchone()
    if pedido is None:
        raise HTTPException(status_code=404, detail="No se encontró ese pedido.")
    cursor.execute(
        """
        SELECT nombre_pizza, cantidad, precio_unitario
        FROM detalle_pedido
        WHERE id_pedido = ?
        ORDER BY id_detalle
        """,
        (id_pedido,),
    )
    resultado = dict(pedido)
    resultado["codigo"] = f"PE-{id_pedido:06d}"
    resultado["detalles"] = [dict(fila) for fila in cursor.fetchall()]
    return resultado


def decodificar_codigo_pedido(imagen):
    imagen = ImageOps.exif_transpose(imagen)
    escala = min(1, 2000 / max(imagen.size))
    if escala < 1:
        imagen = imagen.resize(
            (round(imagen.width * escala), round(imagen.height * escala)),
            Image.Resampling.LANCZOS,
        )
    gris = ImageOps.autocontrast(imagen.convert("L"), cutoff=1)
    candidatos = (
        imagen,
        gris,
        ImageEnhance.Sharpness(gris).enhance(2),
        gris.point(lambda pixel: 255 if pixel >= 160 else 0),
    )
    for candidato in candidatos:
        codigos = zxingcpp.read_barcodes(
            candidato,
            formats=zxingcpp.BarcodeFormat.Code128,
            try_invert=True,
        )
        for codigo in codigos:
            try:
                id_pedido = obtener_id_pedido_codigo(codigo.text)
            except HTTPException:
                continue
            return f"PE-{id_pedido:06d}"
    return None


@app.post("/api/personal/pedidos/leer-codigo")
async def leer_codigo_pedido(
    request: Request,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "vendedor")
    finally:
        conexion.close()

    tipo_contenido = request.headers.get("content-type", "").split(";", 1)[0]
    if tipo_contenido not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=415,
            detail="Envía una captura de cámara en formato JPEG o PNG.",
        )
    if request.headers.get("content-length", "").isdigit() and int(
        request.headers["content-length"]
    ) > 5_000_000:
        raise HTTPException(status_code=413, detail="La imagen excede el tamaño permitido.")

    contenido = bytearray()
    async for fragmento in request.stream():
        contenido.extend(fragmento)
        if len(contenido) > 5_000_000:
            raise HTTPException(
                status_code=413,
                detail="La imagen excede el tamaño permitido.",
            )
    if not contenido:
        raise HTTPException(status_code=400, detail="La captura está vacía.")

    try:
        with Image.open(io.BytesIO(contenido)) as imagen:
            if imagen.width * imagen.height > 12_000_000:
                raise HTTPException(
                    status_code=413,
                    detail="La resolución de la imagen excede el límite permitido.",
                )
            imagen.load()
            codigo = decodificar_codigo_pedido(imagen)
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="No se pudo leer la captura.")

    if codigo:
        return {"codigo": codigo}

    raise HTTPException(
        status_code=422,
        detail="No se detectó un código de pedido de PizzaExpress. "
        "Asegúrate de enfocar el código de barras completo.",
    )


@app.get("/api/personal/pedidos/codigo/{codigo}")
def consultar_pedido_por_codigo(
    codigo: str,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "vendedor")
        id_pedido = obtener_id_pedido_codigo(codigo)
        return obtener_pedido_para_entrega(cursor, id_pedido)
    finally:
        conexion.close()


@app.patch("/api/personal/pedidos/codigo/{codigo}/entregar")
def entregar_pedido_por_codigo(
    codigo: str,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "vendedor")
        id_pedido = obtener_id_pedido_codigo(codigo)
        pedido = obtener_pedido_para_entrega(cursor, id_pedido)
        if pedido["estado"] in ("Cancelada", "Finalizada"):
            raise HTTPException(
                status_code=409,
                detail="El pedido ya fue cancelado o entregado.",
            )
        cursor.execute(
            """
            UPDATE pedidos
            SET estado = 'Finalizada'
            WHERE id_pedido = ?
              AND estado IN ('En Proceso', 'Lista')
            """,
            (id_pedido,),
        )
        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=409,
                detail="El estado del pedido cambió. Actualiza la búsqueda.",
            )
        conexion.commit()
        return {
            "codigo": pedido["codigo"],
            "estado": "Finalizada",
            "mensaje": "Pedido entregado y finalizado.",
        }
    except HTTPException:
        conexion.rollback()
        raise
    finally:
        conexion.close()


@app.get("/api/gerencia/pedidos")
def listar_pedidos_gerencia(
    fecha: date | None = None,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        fecha_consulta = fecha or datetime.now().astimezone().date()
        cursor.execute(
            """
            SELECT p.id_pedido, p.nombre_contacto, p.telefono_contacto,
                   p.tipo_servicio, p.fecha, p.creado_en, p.total, p.estado,
                   p.metodo_pago,
                   COALESCE(v.nombre, 'Cliente de la app') AS vendedor
            FROM pedidos p
            LEFT JOIN personal v ON v.id_personal = p.id_vendedor
            WHERE date(p.creado_en, 'localtime') = ?
            ORDER BY julianday(p.creado_en) DESC, p.id_pedido DESC
            LIMIT 500
            """,
            (fecha_consulta.isoformat(),),
        )
        pedidos = [dict(fila) for fila in cursor.fetchall()]
        for pedido in pedidos:
            cursor.execute(
                """
                SELECT nombre_pizza, cantidad, precio_unitario
                FROM detalle_pedido
                WHERE id_pedido = ?
                ORDER BY id_detalle
                """,
                (pedido["id_pedido"],),
            )
            pedido["detalles"] = [dict(fila) for fila in cursor.fetchall()]
        return {"fecha": fecha_consulta.isoformat(), "pedidos": pedidos}
    finally:
        conexion.close()


@app.get("/api/gerencia/reporte")
def reporte_gerencia(
    fecha: date | None = None,
    authorization: str | None = Header(default=None),
):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        autenticar_personal(cursor, authorization, "gerente")
        fecha_consulta = fecha or datetime.now().astimezone().date()
        cursor.execute(
            """
            SELECT COUNT(*) AS cantidad,
                   COALESCE(SUM(total), 0) AS ingresos
            FROM pedidos
            WHERE date(creado_en, 'localtime') = ? AND estado != 'Cancelada'
            """,
            (fecha_consulta.isoformat(),),
        )
        resumen = dict(cursor.fetchone())
        cursor.execute(
            """
            SELECT p.id_vendedor, COALESCE(v.nombre, 'Cliente de la app') AS vendedor,
                   COUNT(*) AS cantidad, COALESCE(SUM(p.total), 0) AS ingresos
            FROM pedidos p
            LEFT JOIN personal v ON v.id_personal = p.id_vendedor
            WHERE date(p.creado_en, 'localtime') = ? AND p.estado != 'Cancelada'
            GROUP BY p.id_vendedor, v.nombre
            ORDER BY ingresos DESC, vendedor COLLATE NOCASE
            """,
            (fecha_consulta.isoformat(),),
        )
        por_vendedor = [dict(fila) for fila in cursor.fetchall()]
        cursor.execute(
            """
            SELECT tipo_servicio, COUNT(*) AS cantidad,
                   COALESCE(SUM(total), 0) AS ingresos
            FROM pedidos
            WHERE date(creado_en, 'localtime') = ? AND estado != 'Cancelada'
            GROUP BY tipo_servicio
            ORDER BY tipo_servicio
            """,
            (fecha_consulta.isoformat(),),
        )
        por_servicio = [dict(fila) for fila in cursor.fetchall()]
        return {
            "fecha": fecha_consulta.isoformat(),
            "cantidad_pedidos": resumen["cantidad"],
            "ingresos": resumen["ingresos"],
            "por_vendedor": por_vendedor,
            "por_servicio": por_servicio,
        }
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
            """
            UPDATE pedidos
            SET estado = 'Cancelada'
            WHERE id_pedido = ? AND estado != 'Cancelada'
            """,
            (id_pedido,),
        )
        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Pedido no encontrado o ya cancelado.",
            )
        conexion.commit()
        return {"mensaje": "Pedido cancelado."}
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
        if pedido.tipo_servicio == "En Tienda":
            if pedido.hora_recoleccion is None:
                raise HTTPException(
                    status_code=422,
                    detail="Selecciona una hora de recolección.",
                )
            hora_recoleccion = pedido.hora_recoleccion
            if hora_recoleccion.tzinfo is None:
                raise HTTPException(
                    status_code=422,
                    detail="La hora de recolección debe incluir zona horaria.",
                )
            ahora_local = datetime.now().astimezone()
            hora_recoleccion_local = hora_recoleccion.astimezone()
            cierre_local = ahora_local.replace(
                hour=22,
                minute=0,
                second=0,
                microsecond=0,
            )
            if hora_recoleccion_local.date() != ahora_local.date():
                raise HTTPException(
                    status_code=422,
                    detail="La hora de recolección debe ser para hoy.",
                )
            ahora_minuto = ahora_local.replace(second=0, microsecond=0)
            if hora_recoleccion_local < ahora_minuto + timedelta(minutes=30):
                raise HTTPException(
                    status_code=422,
                    detail="La hora de recolección debe ser al menos 30 minutos después.",
                )
            if (
                hora_recoleccion_local >= cierre_local
                or hora_recoleccion_local.second
                or hora_recoleccion_local.microsecond
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La recolección debe programarse antes del cierre "
                        "de las 10:00 p. m."
                    ),
                )
            hora_recoleccion_guardada = hora_recoleccion.isoformat(
                timespec="minutes"
            )
        else:
            hora_recoleccion_guardada = None

        cursor.execute("BEGIN IMMEDIATE")
        # Se omite el UPDATE masivo para no cancelar pedidos abiertos en otros dispositivos del mismo cliente
        cursor.execute(
            """
            INSERT INTO pedidos (
                id_cliente, nombre_contacto, tipo_servicio, direccion,
                referencias, subtotal, costo_envio, total, fecha, estado,
                hora_recoleccion, telefono_contacto, creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'En Proceso', ?, ?, ?)
            """,
            (
                id_cliente,
                pedido.nombre_contacto.strip(),
                pedido.tipo_servicio,
                pedido.direccion.strip(),
                pedido.referencias.strip(),
                pedido.subtotal,
                pedido.costo_envio,
                pedido.total,
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
            [
                (id_pedido, item.nombre_pizza, item.cantidad, item.precio_unitario)
                for item in pedido.items
            ],
        )
        conexion.commit()
        return {
            "id_pedido": id_pedido,
            "codigo": f"PE-{id_pedido:06d}",
        }
    except HTTPException:
        conexion.rollback()
        raise
    except sqlite3.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


@app.get("/api/pedidos")
def consultar_pedidos(authorization: str | None = Header(default=None)):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        id_cliente = autenticar_cliente(cursor, authorization)
        cursor.execute(
            """
            SELECT id_pedido, nombre_contacto, tipo_servicio, direccion,
                   referencias, fecha, total, hora_recoleccion
            FROM pedidos
            WHERE id_cliente = ? AND estado = 'En Proceso'
            ORDER BY id_pedido DESC
            LIMIT 1
            """,
            (id_cliente,),
        )
        pedido_activo_row = cursor.fetchone()
        pedido_activo = dict(pedido_activo_row) if pedido_activo_row else None
        if pedido_activo:
            cursor.execute(
                """
                SELECT nombre_pizza, cantidad, precio_unitario
                FROM detalle_pedido
                WHERE id_pedido = ?
                ORDER BY id_detalle
                """,
                (pedido_activo["id_pedido"],),
            )
            pedido_activo["detalles"] = [
                dict(fila) for fila in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT id_pedido, fecha, total, estado
                FROM pedidos
                WHERE id_cliente = ? AND id_pedido != ?
                ORDER BY id_pedido DESC
                """,
                (id_cliente, pedido_activo["id_pedido"]),
            )
        else:
            cursor.execute(
                """
                SELECT id_pedido, fecha, total, estado
                FROM pedidos
                WHERE id_cliente = ?
                ORDER BY id_pedido DESC
                """,
                (id_cliente,),
            )
        historial = [dict(fila) for fila in cursor.fetchall()]
        return {"pedido_activo": pedido_activo, "historial": historial}
    finally:
        conexion.close()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("PIZZAEXPRESS_HOST", "0.0.0.0")
    port = int(os.environ.get("PIZZAEXPRESS_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
