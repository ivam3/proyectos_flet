import httpx
import json
import csv
import os
import sys

API_URL = "http://localhost:8000"
JSON_FILE = "menu_maestro.json"
CSV_FILE = "reporte_analisis.csv"

def exportar_datos():
    print(f"🔄 Descargando base de datos de {API_URL}...")
    try:
        # 1. Obtener Menú
        r_menu = httpx.get(f"{API_URL}/menu?solo_activos=False")
        if r_menu.status_code != 200:
            print("❌ Error descargando menú")
            return
        menu = r_menu.json()

        # 2. Obtener Grupos (para referencia visual)
        r_grupos = httpx.get(f"{API_URL}/opciones")
        grupos = {g['id']: g['nombre'] for g in r_grupos.json()} if r_grupos.status_code == 200 else {}

        print(f"✅ Se descargaron {len(menu)} platillos.")

        # --- GUARDAR JSON MAESTRO (Para editar y re-subir) ---
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(menu, f, indent=4, ensure_ascii=False)
        print(f"📄 Archivo MAESTRO guardado: {JSON_FILE}")
        print("   -> Usa este archivo para agregar/editar platillos y luego importar.")

        # --- GUARDAR CSV (Para análisis humano en Excel) ---
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # Cabeceras
            writer.writerow(["ID", "Nombre", "Precio", "Descripción", "Piezas", "Configurable?", "Grupos IDs", "Nombres Grupos"])
            
            for p in menu:
                # Decodificar nombres de grupos
                g_ids_str = p.get('grupos_opciones_ids', "[]")
                g_names = []
                try:
                    g_ids = json.loads(g_ids_str)
                    g_names = [grupos.get(gid, f"ID:{gid}") for gid in g_ids]
                except: pass

                writer.writerow([
                    p['id'],
                    p['nombre'],
                    p['precio'],
                    p.get('descripcion', ''),
                    p.get('piezas', 1),
                    "SI" if p.get('is_configurable') else "NO",
                    g_ids_str,
                    ", ".join(g_names)
                ])
        print(f"📊 Reporte Excel guardado: {CSV_FILE}")
        print("   -> Abre este archivo para buscar duplicados o variantes visualmente.")

    except Exception as e:
        print(f"❌ Error fatal: {e}")

def importar_datos():
    if not os.path.exists(JSON_FILE):
        print(f"❌ No existe el archivo {JSON_FILE}. Primero ejecuta la opción Exportar.")
        return

    print(f"📖 Leyendo {JSON_FILE}...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        datos_locales = json.load(f)

    print(f"🔄 Iniciando sincronización de {len(datos_locales)} items...")
    
    creados = 0
    actualizados = 0
    errores = 0
    omitidos = 0

    # Obtener estado actual del servidor para comparar nombres si no hay ID
    r_actual = httpx.get(f"{API_URL}/menu?solo_activos=False")
    mapa_nombres = {p['nombre'].lower().strip(): p['id'] for p in r_actual.json()} if r_actual.status_code == 200 else {}

    for item in datos_locales:
        item_id = item.get('id')
        nombre_limpio = item['nombre'].lower().strip()
        
        # Limpiar datos para envio (la API no espera el ID en el body para crear, ni campos extra)
        payload = {
            "nombre": item['nombre'],
            "descripcion": item.get('descripcion'),
            "precio": item['precio'],
            "imagen": item.get('imagen'),
            "descuento": item.get('descuento', 0),
            "is_configurable": item.get('is_configurable', 0),
            "is_configurable_salsa": item.get('is_configurable_salsa', 0),
            "piezas": item.get('piezas', 1),
            "grupos_opciones_ids": item.get('grupos_opciones_ids', "[]"),
            "is_active": item.get('is_active', 1)
        }

        # CASO 1: TIENE ID (Actualizar)
        if item_id:
            try:
                r = httpx.put(f"{API_URL}/menu/{item_id}", json=payload)
                if r.status_code == 200:
                    actualizados += 1
                    print(f"   ✏️  Actualizado ID {item_id}: {item['nombre']}")
                else:
                    print(f"   ⚠️ Error actualizando ID {item_id}: {r.status_code}")
                    errores += 1
            except: errores += 1

        # CASO 2: NO TIENE ID, PERO EL NOMBRE YA EXISTE (Prevenir duplicado)
        elif nombre_limpio in mapa_nombres:
            existente_id = mapa_nombres[nombre_limpio]
            print(f"   ⏭️  Omitido (Ya existe por nombre): {item['nombre']} (ID: {existente_id})")
            omitidos += 1
            # Opcional: Podrías forzar actualización aquí si quisieras
        
        # CASO 3: NUEVO (Crear)
        else:
            try:
                r = httpx.post(f"{API_URL}/menu", json=payload)
                if r.status_code in [200, 201]:
                    creados += 1
                    print(f"   ✨ Creado nuevo: {item['nombre']}")
                else:
                    print(f"   ❌ Error creando {item['nombre']}: {r.text}")
                    errores += 1
            except: errores += 1

    print("\nResumen de Sincronización:")
    print(f"   ✨ Nuevos: {creados}")
    print(f"   ✏️  Actualizados: {actualizados}")
    print(f"   ⏭️  Omitidos (Duplicados): {omitidos}")
    print(f"   ❌ Errores: {errores}")

if __name__ == "__main__":
    print("--- GESTOR MASIVO DE MENÚ ---")
    print("1. EXPORTAR (Descargar DB a JSON y CSV)")
    print("2. IMPORTAR (Subir cambios desde JSON a la DB)")
    opcion = input("Elige una opción (1/2): ")

    if opcion == "1":
        exportar_datos()
    elif opcion == "2":
        importar_datos()
    else:
        print("Opción no válida")
