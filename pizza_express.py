import sqlite3
import sqlite3

def verificar_credenciales(correo, contrasena):
    conexion = sqlite3.connect("pizza_express.db")
    cursor = conexion.cursor()
    
    cursor.execute(
        "SELECT id_cliente, nombre, primer_apellido FROM clientes WHERE correo = ? AND contrasena = ?", 
        (correo, contrasena)
    )
    usuario = cursor.fetchone()
    conexion.close()
    
    if usuario:
        return {"id": usuario[0], "nombre": usuario[1], "apellido": usuario[2]}
    return None

def inicializar_base_datos():
    conexion = sqlite3.connect("pizza_express.db")
    cursor = conexion.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            primer_apellido TEXT NOT NULL,
            segundo_apellido TEXT NOT NULL,
            telefono TEXT NOT NULL,
            correo TEXT NOT NULL,
            contrasena TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER,
            nombre_contacto TEXT,
            tipo_servicio TEXT NOT NULL,
            direccion TEXT,
            referencias TEXT,
            subtotal REAL NOT NULL,
            costo_envio REAL NOT NULL,
            total REAL NOT NULL,
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
        )
    """)

    cursor.execute("PRAGMA table_info(pedidos)")
    columnas_pedidos = {columna[1] for columna in cursor.fetchall()}
    if "nombre_contacto" not in columnas_pedidos:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN nombre_contacto TEXT")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_pedido (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pedido INTEGER,
            nombre_pizza TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
        )
    """)
    
    conexion.commit()
    conexion.close()