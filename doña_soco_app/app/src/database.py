import sqlite3
import json
import os

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

def crear_tablas():
    """Creates database tables from the schema.sql file."""
    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.executescript(schema)
        conn.commit()
        print("Tablas creadas exitosamente desde schema.sql.")
    except sqlite3.Error as e:
        print(f"Error al crear las tablas: {e}")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo schema.sql en {SCHEMA_PATH}")
    finally:
        if conn:
            conn.close()

def agregar_platillo(nombre, descripcion, precio, imagen):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO menu (nombre, descripcion, precio, imagen) VALUES (?,?,?,?)",
                   (nombre, descripcion, precio, imagen))
    conn.commit()
    conn.close()

def actualizar_platillo(platillo_id, nombre, descripcion, precio, imagen):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE menu 
        SET nombre = ?, descripcion = ?, precio = ?, imagen = ?
        WHERE id = ?
    """, (nombre, descripcion, precio, imagen, platillo_id))
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

def guardar_pedido(nombre, telefono, direccion, referencias, total, items):
    """Guarda una orden y sus productos en la base de datos."""
    conn = conectar()
    cursor = conn.cursor()

    try:
        # Guardar encabezado de orden
        cursor.execute("""
            INSERT INTO ordenes (nombre_cliente, telefono, direccion, referencias, total)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, telefono, direccion, referencias, total))
        orden_id = cursor.lastrowid

        # Guardar cada producto
        for item in items:
            cursor.execute("""
                INSERT INTO orden_detalle (orden_id, producto, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (orden_id, item["nombre"], item["cantidad"], item["precio"]))

        conn.commit()
        return True

    except Exception as e:
        print("Error al guardar pedido:", e)
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def obtener_menu(solo_activos=True):
    """Devuelve la lista de platillos del menú."""
    conn = conectar()
    cursor = conn.cursor()
    query = "SELECT id, nombre, descripcion, precio, imagen, is_active FROM menu"
    if solo_activos:
        query += " WHERE is_active = 1"
    cursor.execute(query)
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
            o.id, o.nombre_cliente, o.telefono, o.direccion, o.referencias, o.total, o.fecha, o.estado,
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

def actualizar_estado_pedido(orden_id, nuevo_estado):
    """Actualiza el estado de un pedido y registra el cambio en el historial."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        # Actualizar el estado en la tabla de ordenes
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

