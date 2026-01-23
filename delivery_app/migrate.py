import sqlite3
import httpx
import json
import os

DB_PATH = "app/storage/data/restaurante.db"
API_URL = "http://localhost:8000"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"No se encontró base de datos antigua en {DB_PATH}")
        return

    print(f"Iniciando migración desde {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Migrar MENU
    try:
        cursor.execute("SELECT * FROM menu")
        platillos = cursor.fetchall()
        print(f"Encontrados {len(platillos)} platillos.")
        
        for p in platillos:
            data = {
                "nombre": p["nombre"],
                "descripcion": p["descripcion"],
                "precio": p["precio"],
                "descuento": p["descuento"],
                "imagen": p["imagen"],
                "is_active": p["is_active"],
                # Manejar columnas nuevas que podrían no existir en la DB vieja vieja
                "is_configurable": p["is_configurable"] if "is_configurable" in p.keys() else 0,
                "is_configurable_salsa": p["is_configurable_salsa"] if "is_configurable_salsa" in p.keys() else 0,
                "piezas": p["piezas"] if "piezas" in p.keys() else 1
            }
            # Verificar si existe categoria_id
            if "categoria_id" in p.keys() and p["categoria_id"]:
                 data["categoria_id"] = p["categoria_id"]

            try:
                r = httpx.post(f"{API_URL}/menu", json=data)
                if r.status_code == 200:
                    print(f"Migrado: {p['nombre']}")
                else:
                    print(f"Error migrando {p['nombre']}: {r.text}")
            except Exception as e:
                print(f"Error HTTP {p['nombre']}: {e}")
                
    except Exception as e:
        print(f"Error leyendo menu: {e}")

    # 2. Migrar CONFIGURACION
    try:
        cursor.execute("SELECT * FROM configuracion WHERE id = 1")
        config = cursor.fetchone()
        if config:
            print("Migrando configuración...")
            # Convertir JSON strings si es necesario, pero la API espera JSON objects si definí Pydantic models con str? 
            # En schemas.py definí 'metodos_pago_activos' como str (Optional[str]), así que pasamos el string directo.
            
            data = {
                "horario": config["horario"],
                "codigos_postales": config["codigos_postales"]
            }
            
            # Campos opcionales que pueden no estar en viejas DBs
            keys = config.keys()
            if "metodos_pago_activos" in keys: data["metodos_pago_activos"] = config["metodos_pago_activos"]
            if "tipos_tarjeta" in keys: data["tipos_tarjeta"] = config["tipos_tarjeta"]
            if "contactos" in keys: data["contactos"] = config["contactos"]
            if "guisos_disponibles" in keys: data["guisos_disponibles"] = config["guisos_disponibles"]
            if "salsas_disponibles" in keys: data["salsas_disponibles"] = config["salsas_disponibles"]
            # admin_password lo migramos? Sí, para no perder el login
            if "admin_password" in keys: 
                # OJO: La API no tiene endpoint directo para setear password hasheada via PUT config?
                # En crud.py update_configuracion SÍ actualiza todo lo que venga en el modelo.
                # En schemas.py ConfiguracionUpdate NO tiene admin_password.
                # Tendremos que usar el endpoint change-password si queremos, pero ese pide new_password y lo hashea de nuevo.
                # Si ya tenemos el hash, no podemos usar change-password.
                # Hack: Update directo a base de datos del backend o ignorar password y usar default.
                # Por seguridad, mejor que el usuario resetee o use la Master Key.
                pass
            
            httpx.put(f"{API_URL}/configuracion", json=data)
            print("Configuración migrada.")
            
    except Exception as e:
        print(f"Error configuracion: {e}")

    conn.close()
    print("Migración finalizada.")

if __name__ == "__main__":
    migrate()
