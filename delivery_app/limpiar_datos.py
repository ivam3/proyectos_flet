import sqlite3
import os
import shutil

# Rutas importantes
DB_PATH = "backend_dona_soco.db"
UPLOADS_DIR = "app/src/assets"
ASSETS_TO_KEEP = ["favicon.png", "icon.png", "notify.mp3", "initial_data.db"]

def limpiar_base_datos():
    if not os.path.exists(DB_PATH):
        print(f"⚠️ Base de datos no encontrada en {DB_PATH}")
        return

    print("🧹 Conectando a la base de datos...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Borrar datos transaccionales (Pedidos)
        print("   - Eliminando historial de pedidos...")
        cursor.execute("DELETE FROM orden_detalle")
        cursor.execute("DELETE FROM historial_estados")
        cursor.execute("DELETE FROM ordenes")
        
        # 2. Borrar catálogo (Menú y Opciones)
        print("   - Eliminando menú y grupos de opciones...")
        cursor.execute("DELETE FROM menu")
        cursor.execute("DELETE FROM grupos_opciones")
        
        # 3. Resetear configuración (manteniendo la fila ID=1)
        print("   - Reseteando configuración del negocio...")
        # Dejamos campos vacíos o por defecto
        cursor.execute("""
            UPDATE configuracion SET 
                horario = 'Lunes a Domingo: 9:00 AM - 6:00 PM',
                codigos_postales = '',
                metodos_pago_activos = '{"efectivo": true, "terminal": false}',
                tipos_tarjeta = '[]',
                contactos = '{"telefono": "", "email": "", "whatsapp": "", "direccion": ""}',
                guisos_disponibles = '{}',
                salsas_disponibles = '{}'
            WHERE id = 1
        """)
        
        conn.commit()
        print("✅ Base de datos limpia.")
        
    except Exception as e:
        print(f"❌ Error limpiando DB: {e}")
    finally:
        conn.close()

def limpiar_imagenes():
    print(f"🧹 Limpiando carpeta de imágenes ({UPLOADS_DIR})...")
    if not os.path.exists(UPLOADS_DIR):
        print("   Carpeta no existe.")
        return

    archivos = os.listdir(UPLOADS_DIR)
    eliminados = 0
    
    for archivo in archivos:
        ruta_completa = os.path.join(UPLOADS_DIR, archivo)
        
        # Ignorar carpetas internas (como 'exports' si existe)
        if os.path.isdir(ruta_completa):
            continue
            
        # Borrar si no es archivo de sistema
        if archivo not in ASSETS_TO_KEEP:
            try:
                os.remove(ruta_completa)
                eliminados += 1
            except Exception as e:
                print(f"   ⚠️ No se pudo borrar {archivo}: {e}")
    
    print(f"✅ Se eliminaron {eliminados} imágenes antiguas.")

if __name__ == "__main__":
    print("==========================================")
    print("   HERRAMIENTA DE LIMPIEZA (FACTORY RESET)")
    print("==========================================")
    confirmacion = input("¿Estás seguro de borrar TODOS los datos y convertir esto en una plantilla limpia? (s/n): ")
    
    if confirmacion.lower() == 's':
        limpiar_base_datos()
        limpiar_imagenes()
        print("\n✨ ¡Proyecto listo para un nuevo negocio!")
        print("   1. Reinicia el backend: pkill -f uvicorn && ...")
        print("   2. Ejecuta 'python3 alimentar_db.py' o usa el panel admin para cargar datos nuevos.")
    else:
        print("Operación cancelada.")
