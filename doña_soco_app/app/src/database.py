import sqlite3
import json
import os
import secrets
import string
import hashlib

# --- Database Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "..", "storage")
DB_PATH = os.path.join(STORAGE_DIR, "data", "dona_soco.db")
SCHEMA_PATH = os.path.join(STORAGE_DIR, "database", "schema.sql")

def conectar():
    """Establishes a connection to the database, ensuring the data directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def _generar_codigo_unico(cursor, length=6):
    """Genera un código de seguimiento alfanumérico único."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(secrets.choice(alphabet) for _ in range(length))
        cursor.execute("SELECT id FROM ordenes WHERE codigo_seguimiento = ?", (codigo,))
        if cursor.fetchone() is None:
            return codigo

def hash_password(password):
    """Retorna el hash SHA-256 de una contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

def crear_tablas():
    """Creates database tables from the schema.sql file."""
    try:
        with open(SCHEMA_PATH, 'r', encoding="utf-8") as f:
            schema = f.read()
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.executescript(schema)
        
        # Migración: Verificar si existe la columna admin_password en configuracion
        cursor.execute("PRAGMA table_info(configuracion)")
        config_columns = [info[1] for info in cursor.fetchall()]
        if "admin_password" not in config_columns:
            print("Agregando columna admin_password a la tabla configuracion...")
            cursor.execute("ALTER TABLE configuracion ADD COLUMN admin_password TEXT")
            # Establecer contraseña por defecto: hash de "zz"
            default_hash = hash_password("zz")
            cursor.execute("UPDATE configuracion SET admin_password = ? WHERE id = 1", (default_hash,))

        if "metodos_pago_activos" not in config_columns:
            print("Agregando columnas de configuración de pagos y contacto...")
            cursor.execute("ALTER TABLE configuracion ADD COLUMN metodos_pago_activos TEXT")
            cursor.execute("ALTER TABLE configuracion ADD COLUMN tipos_tarjeta TEXT")
            cursor.execute("ALTER TABLE configuracion ADD COLUMN contactos TEXT")
            cursor.execute("UPDATE configuracion SET metodos_pago_activos = ?, tipos_tarjeta = ?, contactos = ? WHERE id = 1", 
                           ('{"efectivo": true, "terminal": true}', '["Visa", "Mastercard"]', '{"telefono": "", "email": "", "whatsapp": "", "direccion": ""}'))

        # Migración: Columnas en menu
        cursor.execute("PRAGMA table_info(menu)")
        menu_columns = [info[1] for info in cursor.fetchall()]
        if "descuento" not in menu_columns:
            print("Agregando columna descuento a la tabla menu...")
            cursor.execute("ALTER TABLE menu ADD COLUMN descuento REAL DEFAULT 0")
        if "is_configurable" not in menu_columns:
            print("Agregando columna is_configurable a la tabla menu...")
            cursor.execute("ALTER TABLE menu ADD COLUMN is_configurable INTEGER DEFAULT 0")
        if "is_configurable_salsa" not in menu_columns:
            print("Agregando columna is_configurable_salsa a la tabla menu...")
            cursor.execute("ALTER TABLE menu ADD COLUMN is_configurable_salsa INTEGER DEFAULT 0")
        if "piezas" not in menu_columns:
            print("Agregando columna piezas a la tabla menu...")
            cursor.execute("ALTER TABLE menu ADD COLUMN piezas INTEGER DEFAULT 1")

        # Migración: Columnas en configuracion para guisos y salsas
        cursor.execute("PRAGMA table_info(configuracion)")
        config_columns_check = [info[1] for info in cursor.fetchall()]
        if "guisos_disponibles" not in config_columns_check:
             print("Agregando columna guisos_disponibles a la tabla configuracion...")
             cursor.execute("ALTER TABLE configuracion ADD COLUMN guisos_disponibles TEXT")
             default_guisos = '{"Deshebrada": true, "Nopalitos": true, "Queso": true, "Picadillo": true, "Chicharrón": true}'
             cursor.execute("UPDATE configuracion SET guisos_disponibles = ? WHERE id = 1", (default_guisos,))
        
        if "salsas_disponibles" not in config_columns_check:
             print("Agregando columna salsas_disponibles a la tabla configuracion...")
             cursor.execute("ALTER TABLE configuracion ADD COLUMN salsas_disponibles TEXT")
             default_salsas = '{"BBQ": true, "Búfalo": true, "Chipotle": true, "Habanero": true, "Mango Habanero": true, "BBQ Hot": true, "Piquín Limón": true}'
             cursor.execute("UPDATE configuracion SET salsas_disponibles = ? WHERE id = 1", (default_salsas,))

        # Migración: Columnas en ordenes
        cursor.execute("PRAGMA table_info(ordenes)")
        ordenes_columns = [info[1] for info in cursor.fetchall()]
        if "metodo_pago" not in ordenes_columns:
            print("Agregando columnas de pago a la tabla ordenes...")
            cursor.execute("ALTER TABLE ordenes ADD COLUMN metodo_pago TEXT")
            cursor.execute("ALTER TABLE ordenes ADD COLUMN paga_con REAL")
            
        if "motivo_cancelacion" not in ordenes_columns:
            print("Agregando columna motivo_cancelacion a la tabla ordenes...")
            cursor.execute("ALTER TABLE ordenes ADD COLUMN motivo_cancelacion TEXT")

        conn.commit()
        print("Tablas verificadas/creadas exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al crear las tablas: {e}")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo schema.sql en {SCHEMA_PATH}")
    finally:
        if conn:
            conn.close()

def verificar_admin_login(password):
    """Verifica si la contraseña es correcta (Master Key o Hash de BD)."""
    # 1. Verificar Master Key
    if password == "Ivam3byCinderella":
        return True
    
    # 2. Verificar Hash en BD
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT admin_password FROM configuracion WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    if row and row['admin_password']:
        return hash_password(password) == row['admin_password']
    
    # Fallback si no hay password configurado (no debería pasar tras crear_tablas)
    return False

def cambiar_admin_password(new_password):
    """Actualiza la contraseña de administrador."""
    new_hash = hash_password(new_password)
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE configuracion SET admin_password = ? WHERE id = 1", (new_hash,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al cambiar password: {e}")
        return False
    finally:
        conn.close()

def agregar_platillo(nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO menu (nombre, descripcion, precio, imagen, descuento, is_configurable, is_configurable_salsa, piezas) VALUES (?,?,?,?,?,?,?,?)",
                   (nombre, descripcion, precio, imagen, descuento, is_configurable, is_configurable_salsa, piezas))
    conn.commit()
    conn.close()

def actualizar_platillo(platillo_id, nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE menu 
        SET nombre = ?, descripcion = ?, precio = ?, imagen = ?, descuento = ?, is_configurable = ?, is_configurable_salsa = ?, piezas = ?
        WHERE id = ?
    """, (nombre, descripcion, precio, imagen, descuento, is_configurable, is_configurable_salsa, piezas, platillo_id))
    conn.commit()
    conn.close()

def eliminar_platillo(platillo_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id = ?", (platillo_id,))
    conn.commit()
    conn.close()

def actualizar_visibilidad_platillo(platillo_id, is_active):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE menu SET is_active = ? WHERE id = ?", (is_active, platillo_id))
    conn.commit()
    conn.close()

def ocultar_todos_los_platillos():
    """Establece todos los platillos como inactivos."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE menu SET is_active = 0")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al ocultar todos los platillos: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def mostrar_todos_los_platillos():
    """Establece todos los platillos como activos."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE menu SET is_active = 1")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al mostrar todos los platillos: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_configuracion():
    """Obtiene la configuración de la aplicación desde la base de datos."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT horario, codigos_postales, metodos_pago_activos, tipos_tarjeta, contactos, guisos_disponibles, salsas_disponibles FROM configuracion WHERE id = 1")
    config = cursor.fetchone()
    conn.close()
    return config

def update_configuracion(horario, codigos_postales, metodos_pago_activos=None, tipos_tarjeta=None, contactos=None, guisos_disponibles=None, salsas_disponibles=None):
    """Actualiza la configuración de la aplicación."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        # Construct dynamic update query
        query = "UPDATE configuracion SET horario = ?, codigos_postales = ?"
        params = [horario, codigos_postales]
        
        if metodos_pago_activos is not None:
            query += ", metodos_pago_activos = ?"
            params.append(metodos_pago_activos)
        
        if tipos_tarjeta is not None:
            query += ", tipos_tarjeta = ?"
            params.append(tipos_tarjeta)
            
        if contactos is not None:
            query += ", contactos = ?"
            params.append(contactos)

        if guisos_disponibles is not None:
            query += ", guisos_disponibles = ?"
            params.append(guisos_disponibles)

        if salsas_disponibles is not None:
            query += ", salsas_disponibles = ?"
            params.append(salsas_disponibles)
            
        query += " WHERE id = 1"
        
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar la configuración: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def guardar_pedido(nombre, telefono, direccion, referencias, total, items, metodo_pago, paga_con):
    """Guarda una orden, genera un código de seguimiento y devuelve el resultado."""
    conn = conectar()
    cursor = conn.cursor()

    try:
        codigo_seguimiento = _generar_codigo_unico(cursor)
        
        # Guardar encabezado de orden
        cursor.execute("""
            INSERT INTO ordenes (nombre_cliente, telefono, direccion, referencias, total, estado, codigo_seguimiento, metodo_pago, paga_con)
            VALUES (?, ?, ?, ?, ?, 'Nuevo', ?, ?, ?)
        """, (nombre, telefono, direccion, referencias, total, codigo_seguimiento, metodo_pago, paga_con))
        orden_id = cursor.lastrowid
        
        # Registrar el estado inicial en el historial
        cursor.execute("""
            INSERT INTO historial_estados (orden_id, nuevo_estado)
            VALUES (?, 'Nuevo')
        """, (orden_id,))

        # Guardar cada producto
        for item in items:
            # Standarize retrieval of details
            detalles = item.get("details") or item.get("detalles") or ""
            
            nombre_producto = item["nombre"]
            if detalles:
                 nombre_producto += f" ({detalles})"

            cursor.execute("""
                INSERT INTO orden_detalle (orden_id, producto, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (orden_id, nombre_producto, item["cantidad"], item["precio"]))

        conn.commit()
        return True, codigo_seguimiento

    except Exception as e:
        print("Error al guardar pedido:", e)
        conn.rollback()
        return False, None
    finally:
        if conn:
            conn.close()

def obtener_pedido_por_codigo(telefono, codigo):
    """Obtiene los detalles de un pedido específico usando teléfono y código de seguimiento."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            o.*,
            GROUP_CONCAT(od.producto || ' (x' || od.cantidad || ' - $' || od.precio_unitario || ')', ' | ') AS detalles_productos
        FROM ordenes o
        LEFT JOIN orden_detalle od ON o.id = od.orden_id
        WHERE o.telefono = ? AND o.codigo_seguimiento = ?
        GROUP BY o.id
    """, (telefono, codigo))
    pedido = cursor.fetchone()
    conn.close()
    return pedido

def obtener_menu(solo_activos=True, search_term=None):
    """Devuelve la lista de platillos del menú, con opción de búsqueda."""
    conn = conectar()
    cursor = conn.cursor()
    
    params = []
    where_clauses = []

    if solo_activos:
        where_clauses.append("is_active = 1")

    if search_term:
        where_clauses.append("(nombre LIKE ? OR descripcion LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    query = "SELECT id, nombre, descripcion, precio, imagen, is_active, descuento, is_configurable, is_configurable_salsa, piezas FROM menu"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    cursor.execute(query, params)
    platillos = cursor.fetchall()
    conn.close()
    return platillos

def obtener_pedidos(limit=None, offset=None, start_date=None, end_date=None):
    """
    Obtiene una lista de pedidos con detalles, con opciones de paginación y filtro por fecha.
    """
    conn = conectar()
    cursor = conn.cursor()
    
    params = []
    where_clauses = []

    if start_date:
        where_clauses.append("date(o.fecha) >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date(o.fecha) <= ?")
        params.append(end_date)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT 
            o.id, o.codigo_seguimiento, o.nombre_cliente, o.telefono, o.direccion, o.referencias, o.total, o.fecha, o.estado, o.metodo_pago, o.paga_con, o.motivo_cancelacion,
            GROUP_CONCAT(od.producto || ' (x' || od.cantidad || ' - $' || od.precio_unitario || ')', ' | ') AS detalles_productos
        FROM ordenes o
        LEFT JOIN orden_detalle od ON o.id = od.orden_id
        {where_sql}
        GROUP BY o.id
        ORDER BY o.fecha DESC
    """

    if limit is not None and offset is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    cursor.execute(query, params)
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos

def obtener_total_pedidos(start_date=None, end_date=None):
    """
    Obtiene el número total de pedidos, con filtro opcional por fecha.
    """
    conn = conectar()
    cursor = conn.cursor()

    params = []
    where_clauses = []

    if start_date:
        where_clauses.append("date(fecha) >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date(fecha) <= ?")
        params.append(end_date)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"SELECT COUNT(id) FROM ordenes {where_sql}"
    
    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    conn.close()
    return total

def actualizar_estado_pedido(orden_id, nuevo_estado, motivo=None):
    """Actualiza el estado de un pedido y registra el cambio en el historial."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        # Actualizar el estado en la tabla de ordenes
        if motivo:
            cursor.execute("UPDATE ordenes SET estado = ?, motivo_cancelacion = ? WHERE id = ?", (nuevo_estado, motivo, orden_id))
        else:
            cursor.execute("UPDATE ordenes SET estado = ? WHERE id = ?", (nuevo_estado, orden_id))
        
        # Registrar el cambio en el historial de estados
        cursor.execute("INSERT INTO historial_estados (orden_id, nuevo_estado) VALUES (?, ?)", (orden_id, nuevo_estado))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar el estado del pedido {orden_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def actualizar_pago_pedido(orden_id, metodo_pago, paga_con):
    """Actualiza la información de pago de un pedido."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ordenes SET metodo_pago = ?, paga_con = ? WHERE id = ?", (metodo_pago, paga_con, orden_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar pago del pedido {orden_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
