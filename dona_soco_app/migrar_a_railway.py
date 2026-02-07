import sqlite3
import httpx
import sys
import os

# Importamos la configuración directamente desde la carpeta app
# Para que el script funcione, necesitamos añadir el path de src
sys.path.append(os.path.join(os.getcwd(), "app/src"))
try:
    from config import API_URL, HEADERS
except ImportError:
    print("❌ No se pudo encontrar config.py. Asegúrate de estar en la raíz del proyecto.")
    # Fallback manual por si acaso
    API_URL = "https://dona-soco-api.up.railway.app"
    HEADERS = {"X-API-KEY": "ads2026_Ivam3byCinderella"}

# RUTA A TU DB LOCAL EN TERMUX
DB_LOCAL = "app/storage/data/dona_soco.db"

def migrar():
    if not os.path.exists(DB_LOCAL):
        print(f"❌ Error: No se encontró la base de datos en {DB_LOCAL}")
        return

    print(f"🚀 Iniciando migración hacia {API_URL}...")
    
    conn = sqlite3.connect(DB_LOCAL)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. MIGRAR PLATILLOS
    print("\n📦 Migrando platillos del menú...")
    cursor.execute("SELECT * FROM menu")
    platillos_raw = cursor.fetchall()
    
    for p_row in platillos_raw:
        p = dict(p_row) # Solución al AttributeError: convertimos Row a dict
        data = {
            "nombre": p["nombre"],
            "descripcion": p.get("descripcion", ""),
            "precio": p["precio"],
            "imagen": p.get("imagen", ""),
            "descuento": p.get("descuento", 0),
            "is_configurable": p.get("is_configurable", 0),
            "is_configurable_salsa": p.get("is_configurable_salsa", 0),
            "piezas": p.get("piezas", 1),
            "printer_target": "cocina", 
            "is_active": p.get("is_active", 1)
        }
        try:
            r = httpx.post(f"{API_URL}/menu", json=data, headers=HEADERS)
            if r.status_code in [200, 201]:
                print(f"✅ {p['nombre']} migrado.")
            else:
                print(f"❌ Error en {p['nombre']}: {r.text}")
        except Exception as e:
            print(f"💥 Error de conexión en platillo: {e}")

    # 2. MIGRAR CONFIGURACIÓN
    print("\n⚙️ Migrando configuración del sistema...")
    cursor.execute("SELECT * FROM configuracion WHERE id = 1")
    c_row = cursor.fetchone()
    if c_row:
        c = dict(c_row)
        config_data = {
            "horario": c["horario"],
            "codigos_postales": c["codigos_postales"],
            "metodos_pago_activos": c.get("metodos_pago_activos", '{"efectivo": true, "terminal": true}') ,
            "tipos_tarjeta": c.get("tipos_tarjeta", '["Visa", "Mastercard"]'),
            "contactos": c.get("contactos", '{"telefono": "", "email": "", "whatsapp": "", "direccion": ""}'),
            "guisos_disponibles": c.get("guisos_disponibles", '{}'),
            "salsas_disponibles": c.get("salsas_disponibles", '{}'),
            "costo_envio": 20.0
        }
        try:
            r = httpx.put(f"{API_URL}/configuracion", json=config_data, headers=HEADERS)
            if r.status_code == 200:
                print("✅ Configuración global migrada con éxito.")
            else:
                print(f"❌ Error en configuración: {r.text}")
        except Exception as e:
            print(f"💥 Error de conexión en configuración: {e}")

    conn.close()
    print("\n🏁 Migración finalizada. Ahora puedes abrir tu App conectada a Railway.")

if __name__ == "__main__":
    migrar()
