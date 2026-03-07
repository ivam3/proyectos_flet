import httpx
import json
import csv
import sys
import os
import cmd
import shlex
import glob
import shutil
from typing import Dict, Any, List

# Configurar el path para importar config.py
tenant = sys.argv[1] if len(sys.argv) > 1 else print("❌ Por favor, especifica el tenant como argumento: python db_admin.py [tenant]") or sys.exit(1)
sys.path.append(os.path.join(os.getcwd(), f"{tenant}/app/src"))
try:
    from config import API_URL, HEADERS, API_KEY, TENANT_ID
except ImportError:
    print("❌ No se pudo cargar config.py")
    # Intentar diagnóstico de ruta
    print(f"🔍 Ruta buscada: {os.path.join(os.getcwd(), f'{tenant}/app/src')}")
    sys.exit(1)

class DBManager:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, headers=HEADERS, timeout=30.0)

    # --- MENU ---
    def get_all_menu(self):
        try:
            r = self.client.get("/menu", params={"solo_activos": False})
            if r.status_code != 200:
                print(f"❌ Error del API ({r.status_code}): {r.text}")
                return []
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"🛑 Error de conexión: {e}")
            return []

    def delete_item(self, item_id: int):
        r = self.client.delete(f"/menu/{item_id}")
        if r.status_code != 200:
            print(f"❌ Error al borrar: {r.text}")
        return r.status_code == 200

    def create_item(self, data: Dict[str, Any]):
        r = self.client.post("/menu", json=data)
        if r.status_code not in [200, 201]:
            print(f"    ⚠️ Detalle error: {r.text}")
        return r.status_code in [200, 201]

    def update_item(self, item_id: int, data: Dict[str, Any]):
        r = self.client.put(f"/menu/{item_id}", json=data)
        if r.status_code != 200:
            print(f"    ⚠️ Detalle error: {r.text}")
        return r.status_code == 200

    # --- UPLOAD ---
    def upload_image(self, file_path: str):
        """Sube una imagen al servidor y devuelve el nombre guardado."""
        if not os.path.exists(file_path):
            return None, "Archivo no encontrado"
        
        files = {'file': (os.path.basename(file_path), open(file_path, 'rb'), 'image/jpeg')}
        r = self.client.post("/upload", files=files)
        if r.status_code == 200:
            return r.json().get("filename"), None
        return None, r.text

    def delete_file(self, filename: str):
        """Elimina un archivo del servidor."""
        r = self.client.delete(f"/upload/{filename}")
        return r.status_code == 200

    # --- CONFIGURACION ---
    def get_config(self):
        r = self.client.get("/configuracion")
        return r.json()

    def update_config(self, data: Dict[str, Any]):
        r = self.client.put("/configuracion", json=data)
        return r.status_code == 200

    # --- GRUPOS DE OPCIONES ---
    def get_groups(self):
        r = self.client.get("/opciones")
        return r.json()

    def create_group(self, nombre: str, opciones: List[str], multiple: int = 0, obligatorio: int = 0, group_id: int = None):
        data = {
            "nombre": nombre,
            "opciones": json.dumps(opciones),
            "seleccion_multiple": multiple,
            "obligatorio": obligatorio
        }
        if group_id:
            data["id"] = group_id
        r = self.client.post("/opciones", json=data)
        return r.status_code in [200, 201]

    def update_group(self, group_id: int, nombre: str, opciones: List[str], multiple: int = 0, obligatorio: int = 0):
        data = {
            "nombre": nombre,
            "opciones": json.dumps(opciones),
            "seleccion_multiple": multiple,
            "obligatorio": obligatorio
        }
        r = self.client.put(f"/opciones/{group_id}", json=data)
        return r.status_code == 200

    def delete_group(self, group_id: int):
        r = self.client.delete(f"/opciones/{group_id}")
        return r.status_code == 200

    # --- PEDIDOS ---
    def get_pedidos(self, limit: int = 50):
        r = self.client.get("/pedidos", params={"limit": limit})
        return r.json()

    def delete_pedido(self, orden_id: int):
        r = self.client.delete(f"/pedidos/{orden_id}")
        return r.status_code == 200

    def get_upload_list(self):
        r = self.client.get("/upload/list")
        return r.json().get("files", [])

    # --- SHORT LINKS ---
    def get_short_links(self):
        try:
            r = self.client.get("/shortlinks")
            if r.status_code != 200:
                print(f"❌ Error del API ({r.status_code}): {r.text}")
                return []
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"🛑 Error de conexión: {e}")
            return []

    def create_short_link(self, code: str, url: str):
        data = {"short_code": code, "destination_url": url}
        r = self.client.post("/shortlinks", json=data)
        return r.status_code in [200, 201]

    def delete_short_link(self, link_id: int):
        r = self.client.delete(f"/shortlinks/{link_id}")
        return r.status_code == 200

    def purge_root_webp(self):
        r = self.client.post("/admin/maintenance/purge-root-webp")
        return r.json()

    def reset_password(self, new_password: str):
        """Reestablece la contraseña administrativa del tenant."""
        r = self.client.post("/admin/reset-password", json={"password": new_password})
        return r.status_code == 200

class AdminShell(cmd.Cmd):
    intro = f'🛠️_Sistema de Administración {tenant}\n📡 API_URL: {API_URL}\n🆔 TENANT_ID: {TENANT_ID}\n🔑 HEADERS: {json.dumps(HEADERS, indent=2)}\n❓ Escribe "help" o "?" para listar comandos.\n'
    prompt = f'(db-admin-{TENANT_ID})\n╰─➤ '
    
    def __init__(self):
        super().__init__()
        self.mgr = DBManager()

    # --- GESTION DE IMAGENES ---
    def do_upload(self, arg):
        """Sube una o varias imágenes locales al servidor: 
        upload imagen.jpg 
        upload imagen1.jpg imagen2.png
        upload "carpeta con espacios/*.jpg"
        """
        if not arg:
            print("❌ Uso: upload [ruta_local_imagen1] [ruta_local_imagen2] ...")
            return
        
        try:
            # Separar argumentos respetando comillas
            patterns = shlex.split(arg)
            files_to_upload = []
            
            # Expandir globs (ej: *.jpg)
            for p in patterns:
                expanded = glob.glob(p)
                if expanded:
                    files_to_upload.extend(expanded)
                else:
                    # Si no es un glob, añadir tal cual para que el manager maneje el error de "no encontrado"
                    files_to_upload.append(p)

            if not files_to_upload:
                print("⚠️ No se encontraron archivos para subir.")
                return

            print(f"🚀 Iniciando carga de {len(files_to_upload)} archivos...")
            
            success_count = 0
            for file_path in files_to_upload:
                if os.path.isdir(file_path):
                    continue
                    
                filename, error = self.mgr.upload_image(file_path)
                if filename:
                    print(f" ✅ {os.path.basename(file_path)} -> {filename}")
                    success_count += 1
                else:
                    print(f" ❌ {os.path.basename(file_path)}: {error}")
            
            print(f"🏁 Proceso finalizado. Subidos con éxito: {success_count}/{len(files_to_upload)}")
            
        except Exception as e:
            print(f"❌ Error procesando comando: {e}")

    def do_rmupload(self, arg):
        """Elimina una imagen del servidor: rmupload [nombre_archivo.webp]"""
        if not arg:
            print("❌ Uso: rmupload [nombre_archivo]")
            return
        if self.mgr.delete_file(arg):
            print(f"🗑️ Archivo '{arg}' eliminado del servidor.")
        else:
            print(f"❌ No se pudo eliminar el archivo.")

    def do_migrate_webp(self, arg):
        """Automatiza la migración de TODO el menú a WebP:
        1. Descarga imágenes actuales (JPG/PNG).
        2. Las resube (el servidor las convierte a WebP).
        3. Actualiza el Menú con los nuevos nombres.
        """
        print("🔍 Iniciando migración masiva a WebP...")
        menu = self.mgr.get_all_menu()
        count = 0
        
        # Carpeta temporal para la migración
        tmp_dir = "tmp_migration"
        os.makedirs(tmp_dir, exist_ok=True)

        for item in menu:
            img_name = item.get("imagen")
            if img_name and not img_name.endswith(".webp"):
                print(f"📦 Procesando: {item['nombre']} ({img_name})")
                
                try:
                    # 1. Descargar
                    img_url = f"{API_URL}/static/uploads/{img_name}"
                    r_img = httpx.get(img_url)
                    if r_img.status_code != 200:
                        print(f"  ❌ No se pudo descargar {img_name}")
                        continue
                    
                    local_path = os.path.join(tmp_dir, img_name)
                    with open(local_path, "wb") as f:
                        f.write(r_img.content)
                    
                    # 2. Resubir (activará la conversión automática en el backend)
                    new_name, error = self.mgr.upload_image(local_path)
                    
                    if new_name:
                        # 3. Actualizar Item en DB
                        item["imagen"] = new_name
                        # Limpiar campos de SQLAlchemy si existen
                        item_payload = {k: v for k, v in item.items() if k not in ["id", "historial", "detalles"]}
                        if self.mgr.update_item(item["id"], item_payload):
                            print(f"  ✅ DB Actualizada para {item['nombre']} -> {new_name}")
                            # Eliminar el viejo del servidor
                            if new_name != img_name:
                                if self.mgr.delete_file(img_name):
                                    print(f"  🗑️ Original '{img_name}' eliminado del servidor.")
                                else:
                                    print(f"  ⚠️ No se pudo eliminar '{img_name}' del servidor (posiblemente ya no existía).")
                            count += 1
                        else:
                            print(f"  ❌ Error actualizando base de datos para {item['nombre']}")
                    else:
                        print(f"  ❌ Error al subir/convertir: {error}")
                        
                except Exception as ex:
                    print(f"  ❌ Error crítico: {ex}")

        print(f"🏁 Migración finalizada. {count} imágenes optimizadas.")
        # Limpiar carpeta temporal
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def do_ls_uploads(self, arg):
        """Lista todos los archivos de imagen en el servidor: ls_uploads"""
        files = self.mgr.get_upload_list()
        menu = self.mgr.get_all_menu()
        print(f"📦 Items en el menú de este tenant: {len(menu)}")
        print(f"📂 Archivos en el espacio del servidor ({len(files)}):")
        for f in sorted(files):
            print(f"  - {f}")

    def do_purge_root(self, arg):
        """⚠️ ELIMINA ARCHIVOS .WEBP DE LA RAÍZ DEL SERVIDOR: purge_root"""
        confirm = input("❗ ¿Estás seguro de eliminar todos los .webp de la RAÍZ (fuera de carpetas)? (s/n): ")
        if confirm.lower() == 's':
            res = self.mgr.purge_root_webp()
            if res.get("ok"):
                print(f"✅ Limpieza completada. Archivos borrados: {res['deleted_count']}")
                if res.get("errors"):
                    print(f"⚠️ Algunos errores: {res['errors']}")
            else:
                print(f"❌ Error en el servidor: {res}")

    def do_wipe_uploads(self, arg):
        """Elimina archivos del servidor que no están en el menú o no son WebP: wipe_uploads"""
        print("🧹 Iniciando limpieza de archivos huérfanos...")
        
        # 1. Obtener lista de archivos en el servidor
        server_files = self.mgr.get_upload_list()
        
        # 2. Obtener lista de imágenes usadas en el menú
        menu = self.mgr.get_all_menu()
        used_images = {item.get("imagen") for item in menu if item.get("imagen")}
        
        # 3. Identificar archivos a eliminar
        to_delete = []
        for f in server_files:
            # Ignorar archivos de sistema
            if f == "lost+found" or f.startswith("."):
                continue
            # Si no es webp O no está en el menú, se va
            if not f.endswith(".webp") or f not in used_images:
                to_delete.append(f)
        
        if not to_delete:
            print("✨ El servidor ya está limpio. No hay archivos huérfanos.")
            return

        print(f"Se encontraron {len(to_delete)} archivos para eliminar.")
        confirm = input(f"¿Deseas eliminar estos {len(to_delete)} archivos permanentemente? (s/n): ")
        
        if confirm.lower() == 's':
            success = 0
            for f in to_delete:
                if self.mgr.delete_file(f):
                    print(f"  🗑️ {f} eliminado.")
                    success += 1
                else:
                    print(f"  ❌ Falló eliminación de {f}.")
            print(f"🏁 Limpieza completada. {success} archivos borrados.")
        else:
            print("🚫 Operación cancelada.")

    def do_backupimg(self, arg):
        """Descarga todas las imágenes del servidor a una carpeta local: backupimg [nombre_carpeta]"""
        target_dir = arg if arg else "backup_images"
        print(f"📥 Iniciando backup de imágenes en '{target_dir}'...")
        
        try:
            # 1. Obtener lista de archivos
            files = self.mgr.get_upload_list()
            if not files:
                print("📭 No hay archivos en el servidor para respaldar.")
                return

            # 2. Crear carpeta local
            os.makedirs(target_dir, exist_ok=True)
            print(f"📦 Se encontraron {len(files)} archivos en el servidor.")
            
            success = 0
            for f in files:
                url = f"{API_URL}/static/uploads/{f}"
                try:
                    # Usamos un timeout amplio por si hay imágenes pesadas
                    r = httpx.get(url, timeout=60.0)
                    if r.status_code == 200:
                        with open(os.path.join(target_dir, f), "wb") as img_file:
                            img_file.write(r.content)
                        print(f"  ✅ Descargado: {f}")
                        success += 1
                    else:
                        print(f"  ❌ Error {r.status_code} al descargar: {f}")
                except Exception as e:
                    print(f"  ❌ Fallo en {f}: {e}")
            
            print(f"🏁 Proceso finalizado. Se respaldaron {success}/{len(files)} archivos en '{os.path.abspath(target_dir)}'.")
            
        except Exception as e:
            print(f"❌ Error crítico durante el backup: {e}")

    def do_importar(self, arg):
        """Importa/Sincroniza TODO desde un JSON (Menú, Configuración, Grupos): importar [archivo.json]"""
        if not arg:
            print("❌ Uso: importar [archivo.json]")
            return
        try:
            with open(arg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. IMPORTAR CONFIGURACION
            if isinstance(data, dict) and "configuracion" in data:
                print("⚙️  Sincronizando configuración...")
                cfg = data["configuracion"]
                # Limpiar campos no deseados
                cfg_payload = {k: v for k, v in cfg.items() if k not in ["id", "admin_password"]}
                if self.mgr.update_config(cfg_payload):
                    print(" ✅ Configuración actualizada.")
                else:
                    print(" ❌ Error al actualizar configuración.")

            # 2. IMPORTAR GRUPOS DE EXTRAS
            if isinstance(data, dict) and "grupos_extras" in data:
                print("➕ Sincronizando grupos de extras...")
                current_groups = self.mgr.get_groups()
                if not isinstance(current_groups, list): current_groups = []
                
                group_id_map = {int(g['id']): g['id'] for g in current_groups if isinstance(g, dict) and g.get('id') is not None}
                group_name_map = {g['nombre'].strip().lower(): g['id'] for g in current_groups if isinstance(g, dict)}
                
                print(f"📦 Grupos actuales en DB: {len(group_id_map)}")
                
                for g in data["grupos_extras"]:
                    name_clean = g['nombre'].strip().lower()
                    try:
                        item_id = int(g.get("id")) if g.get("id") is not None else None
                    except (ValueError, TypeError):
                        item_id = None
                    ops = json.loads(g['opciones']) if isinstance(g['opciones'], str) else g['opciones']
                    m = g.get('seleccion_multiple', 0)
                    o = g.get('obligatorio', 0)
                    
                    # Payload limpio
                    g_payload = {
                        "nombre": g['nombre'],
                        "opciones": json.dumps(ops),
                        "seleccion_multiple": m,
                        "obligatorio": o
                    }
                    if item_id:
                        g_payload["id"] = item_id

                    target_id = None
                    if item_id and item_id in group_id_map:
                        target_id = item_id
                    elif name_clean in group_name_map:
                        target_id = group_name_map[name_clean]
                    
                    if target_id:
                        if self.mgr.update_group(target_id, g['nombre'], ops, m, o):
                            print(f" 🔄 Grupo '{g['nombre']}' (ID: {target_id}) actualizado.")
                        else:
                            print(f" ❌ Error actualizando grupo '{g['nombre']}'.")
                    else:
                        # Para creación, usamos el payload que puede incluir el ID
                        # Pero el método create_group actual no acepta el payload completo
                        # Vamos a usar una versión que sí lo haga si es necesario, 
                        # o simplemente dejar que el manager lo maneje.
                        # El manager actual: create_group(self, nombre, opciones, multiple=0, obligatorio=0)
                        # Necesito actualizar el manager también.
                        if self.mgr.create_group(g['nombre'], ops, m, o, item_id):
                            print(f" ✅ Grupo '{g['nombre']}' (ID: {item_id or 'auto'}) creado.")
                        else:
                            print(f" ❌ Error creando grupo '{g['nombre']}'.")

            # 3. IMPORTAR MENU
            items_to_import = []
            if isinstance(data, dict) and "menu" in data:
                items_to_import = data["menu"]
            elif isinstance(data, list):
                items_to_import = data

            if items_to_import:
                print("🔍 Sincronizando menú...")
                current_menu = self.mgr.get_all_menu()
                if not isinstance(current_menu, list): 
                    print(f" ⚠️ Error: El API no devolvió una lista de menú ({type(current_menu)})")
                    current_menu = []
                
                # Asegurar que los IDs en el mapa sean enteros para comparación robusta
                menu_id_map = {int(item['id']): item['id'] for item in current_menu if isinstance(item, dict) and item.get('id') is not None}
                menu_name_map = {item['nombre'].strip().lower(): item['id'] for item in current_menu if isinstance(item, dict)}

                print(f"📦 Registros actuales en DB para este tenant: {len(menu_id_map)}")
                print(f"📥 Procesando {len(items_to_import)} platillos del JSON...")
                
                for item in items_to_import:
                    nombre_clean = item['nombre'].strip().lower()
                    try:
                        item_id = int(item.get("id")) if item.get("id") is not None else None
                    except (ValueError, TypeError):
                        item_id = None
                    
                    # --- FILTRADO ESTRICTO DE CAMPOS ---
                    campos_validos = [
                        "id", "nombre", "descripcion", "precio", "descuento", "imagen", 
                        "is_active", "is_configurable", "is_configurable_salsa", 
                        "piezas", "printer_target", "grupos_opciones_ids", "categoria_id"
                    ]
                    item_clean = {k: v for k, v in item.items() if k in campos_validos}
                    
                    # --- AUTO-CORRECCIÓN DE DATOS ---
                    # 1. Forzar extensión .webp
                    img = item_clean.get("imagen", "")
                    if img and not img.endswith(".webp") and "." in img:
                        item_clean["imagen"] = os.path.splitext(img)[0] + ".webp"
                    
                    # 2. Asegurar campos obligatorios con valores por defecto
                    if "printer_target" not in item_clean: item_clean["printer_target"] = "cocina"
                    if "grupos_opciones_ids" not in item_clean: item_clean["grupos_opciones_ids"] = "[]"
                    if "piezas" not in item_clean: item_clean["piezas"] = 1
                    if "is_active" not in item_clean: item_clean["is_active"] = 1
                    if "is_configurable" not in item_clean: item_clean["is_configurable"] = 0
                    if "is_configurable_salsa" not in item_clean: item_clean["is_configurable_salsa"] = 0
                    if "descuento" not in item_clean: item_clean["descuento"] = 0.0
                    
                    target_id = None
                    if item_id and item_id in menu_id_map:
                        target_id = item_id
                    elif nombre_clean in menu_name_map:
                        target_id = menu_name_map[nombre_clean]

                    if target_id:
                        if self.mgr.update_item(target_id, item_clean):
                            print(f" 🔄 {item_clean['nombre']} (ID: {target_id}) actualizado.")
                        else:
                            print(f" ❌ Error actualizando {item_clean['nombre']}.")
                    else:
                        if self.mgr.create_item(item_clean):
                            print(f" ✅ {item_clean['nombre']} (ID: {item_id or 'auto'}) creado.")
                        else:
                            print(f" ❌ Error creando {item_clean['nombre']}.")
            
            print("🏁 Importación finalizada.")
        except Exception as e:
            print(f"❌ Error en importación: {e}")

    # --- MENU CRUD ---
    def do_additem(self, arg):
        """Agrega un platillo manualmente: additem "Nombre" Precio "Imagen" "Desc" """
        import shlex
        try:
            parts = shlex.split(arg)
            if len(parts) < 2:
                print("❌ Uso: additem [Nombre] [Precio] [Imagen] [Descripcion]")
                return
            
            data = {
                "nombre": parts[0],
                "precio": float(parts[1]),
                "imagen": parts[2] if len(parts) > 2 else "",
                "descripcion": parts[3] if len(parts) > 3 else "",
                "is_active": 1
            }
            if self.mgr.create_item(data):
                print(f"✅ Platillo '{data['nombre']}' creado.")
            else:
                print("❌ Error al crear platillo.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_ls(self, arg):
        """Lista todos los platillos: ls"""
        items = self.mgr.get_all_menu()
        if not items or not isinstance(items, list):
            print("📭 No hay platillos que mostrar o hubo un error en la consulta.")
            return

        print(f"{ 'ID':<5} | {'Nombre':<30} | {'Precio':<8} | {'Imagen'}")
        print("-" * 75)
        for i in items:
            if isinstance(i, dict):
                img = i.get("imagen") or "---"
                print(f"{i.get('id', '??'):<5} | {i.get('nombre', 'Sin nombre')[:30]:<30} | ${i.get('precio', 0.0):<7.2f} | {img}")
            else:
                print(f"⚠️ Item inesperado: {i}")

    def do_rm(self, arg):
        """Elimina un platillo por ID: rm [id]"""
        if not arg: return
        if self.mgr.delete_item(int(arg)):
            print(f"🗑️ Item {arg} eliminado.")
        else:
            print(f"❌ No se pudo eliminar.")

    def do_wipe(self, arg):
        """⚠️ BORRA TODO EL MENÚ: wipe"""
        confirm = input("❗ ¿ESTÁS SEGURO? Esto borrará TODO el menú del servidor (s/n): ")
        if confirm.lower() == 's':
            items = self.mgr.get_all_menu()
            for i in items:
                self.mgr.delete_item(i["id"])
            print("🧹 Servidor vaciado por completo.")

    # --- GRUPOS DE OPCIONES (Extras) ---
    def do_groups(self, arg):
        """Lista grupos de opciones extras: groups"""
        groups = self.mgr.get_groups()
        print(f"{ 'ID':<5} | {'Nombre':<20} | {'Mult' :<4} | {'Obl' :<4} | {'Opciones'}")
        print("-" * 75)
        for g in groups:
            ops = json.loads(g['opciones'])
            m = "✅" if g.get('seleccion_multiple') else "❌"
            o = "✅" if g.get('obligatorio') else "❌"
            print(f"{g['id']:<5} | {g['nombre']:<20} | {m:<4} | {o:<4} | {', '.join(ops)}")

    def do_addgroup(self, arg):
        """Agrega un grupo: addgroup Nombre Op1,Op2 [-m] [-o]"""
        import shlex
        try:
            parts = shlex.split(arg)
            if len(parts) < 2:
                print("❌ Uso: addgroup [Nombre] [Op1,Op2...] [-m] [-o]")
                return
            nombre = parts[0]
            opciones = [o.strip() for o in parts[1].split(',')]
            multiple = 1 if "-m" in parts else 0
            obligatorio = 1 if "-o" in parts else 0
            if self.mgr.create_group(nombre, opciones, multiple, obligatorio):
                print(f"✅ Grupo '{nombre}' creado.")
            else:
                print("❌ Error al crear grupo.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_rmgroup(self, arg):
        """Elimina un grupo por ID: rmgroup [id]"""
        if not arg: return
        if self.mgr.delete_group(int(arg)):
            print(f"🗑️ Grupo {arg} eliminado.")
        else:
            print(f"❌ Error al eliminar grupo.")

    # --- CONFIGURACION (Guisos y Salsas Legacy) ---
    def do_guisos(self, arg):
        """Gestiona guisos: guisos (lista), guisos add Nombre, guisos rm Nombre"""
        config = self.mgr.get_config()
        guisos = json.loads(config.get("guisos_disponibles", "{}"))
        if not arg:
            print(f"🥘 Guisos actuales: {', '.join(guisos.keys())}")
            return
        parts = arg.split(' ', 1)
        cmd_type = parts[0].lower()
        if cmd_type == "add" and len(parts) > 1:
            guisos[parts[1].strip()] = True
        elif cmd_type == "rm" and len(parts) > 1:
            guisos.pop(parts[1].strip(), None)
        if self.mgr.update_config({"guisos_disponibles": json.dumps(guisos)}):
            print("✅ Guisos actualizados.")
        else:
            print("❌ Error.")

    def do_salsas(self, arg):
        """Gestiona salsas: salsas (lista), salsas add Nombre, salsas rm Nombre"""
        config = self.mgr.get_config()
        salsas = json.loads(config.get("salsas_disponibles", "{}"))
        if not arg:
            print(f"🌶️ Salsas actuales: {', '.join(salsas.keys())}")
            return
        parts = arg.split(' ', 1)
        cmd_type = parts[0].lower()
        if cmd_type == "add" and len(parts) > 1:
            salsas[parts[1].strip()] = True
        elif cmd_type == "rm" and len(parts) > 1:
            salsas.pop(parts[1].strip(), None)
        if self.mgr.update_config({"salsas_disponibles": json.dumps(salsas)}):
            print("✅ Salsas actualizadas.")
        else:
            print("❌ Error.")

    # --- GESTION DE PEDIDOS ---
    def do_pedidos(self, arg):
        """Lista el historial de pedidos: pedidos [limite]"""
        limit = int(arg) if arg and arg.isdigit() else 50
        pedidos = self.mgr.get_pedidos(limit=limit)
        
        if not pedidos:
            print("📭 No hay pedidos en el historial.")
            return

        print(f"{ 'ID':<5} | {'Cliente':<20} | {'Total':<8} | {'Estado':<12} | {'Fecha'}")
        print("-" * 80)
        for p in pedidos:
            # Formatear fecha simple: 2024-05-20T10:00:00 -> 20/05 10:00
            fecha_raw = p.get("fecha", "")
            fecha_fmt = fecha_raw[8:10] + "/" + fecha_raw[5:7] + " " + fecha_raw[11:16] if len(fecha_raw) > 16 else "---"
            
            print(f"{p['id']:<5} | {p['nombre_cliente'][:20]:<20} | ${p['total']:<7.2f} | {p['estado']:<12} | {fecha_fmt}")

    def do_rmpedido(self, arg):
        """Elimina un pedido por ID: rmpedido [id]"""
        if not arg:
            print("❌ Uso: rmpedido [id]")
            return
        if self.mgr.delete_pedido(int(arg)):
            print(f"🗑️ Pedido {arg} eliminado.")
        else:
            print(f"❌ No se pudo eliminar el pedido.")

    def do_wipe_pedidos(self, arg):
        """⚠️ BORRA TODO EL HISTORIAL DE PEDIDOS: wipe_pedidos"""
        confirm = input("❗ ¿ESTÁS SEGURO? Esto borrará TODO el historial de pedidos (s/n): ")
        if confirm.lower() == 's':
            pedidos = self.mgr.get_pedidos(limit=1000)
            count = 0
            for p in pedidos:
                if self.mgr.delete_pedido(p["id"]):
                    count += 1
            print(f"🧹 Historial vaciado: {count} pedidos eliminados.")

    # --- ENLACES CORTOS (REDICCIONAMIENTO) ---
    def do_links(self, arg):
        """Lista todos los enlaces de redirección: links"""
        links = self.mgr.get_short_links()
        if not links:
            print("📭 No hay enlaces configurados.")
            return
        print(f"{ 'ID':<5} | {'Código':<15} | {'URL de Destino'}")
        print("-" * 75)
        for l in links:
            print(f"{l['id']:<5} | {l['short_code']:<15} | {l['destination_url']}")

    def do_addlink(self, arg):
        """Crea o actualiza un enlace de redirección: addlink codigo url"""
        import shlex
        try:
            parts = shlex.split(arg)
            if len(parts) < 2:
                print("❌ Uso: addlink [codigo] [url]")
                return
            if self.mgr.create_short_link(parts[0], parts[1]):
                print(f"✅ Redirección para '{parts[0]}' configurada -> {parts[1]}")
            else:
                print("❌ Error al crear enlace.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_rmlink(self, arg):
        """Elimina un enlace de redirección por ID o Código: rmlink [id|codigo]"""
        if not arg:
            print("❌ Uso: rmlink [id|codigo]")
            return
        
        target_id = None
        # Si es un número, lo usamos directamente como ID
        if arg.isdigit():
            target_id = int(arg)
        else:
            # Si es texto (ej: "apk"), buscamos el ID correspondiente en este tenant
            print(f"🔍 Buscando enlace con código '{arg}'...")
            links = self.mgr.get_short_links()
            if isinstance(links, list):
                for l in links:
                    if l.get('short_code') == arg:
                        target_id = l['id']
                        break
        
        if target_id is not None:
            if self.mgr.delete_short_link(target_id):
                print(f"🗑️ Enlace '{arg}' eliminado con éxito.")
            else:
                print(f"❌ No se pudo eliminar el enlace en el servidor.")
        else:
            print(f"❌ No se encontró ningún enlace con el código o ID: {arg}")

    def do_passwd(self, arg):
        """Reestablece la contraseña del panel administrativo: passwd [nueva_contraseña]"""
        if not arg:
            print("❌ Uso: passwd [nueva_contraseña]")
            return
        
        confirm = input(f"❗ ¿Estás seguro de reestablecer la contraseña para el tenant '{TENANT_ID}'? (s/n): ")
        if confirm.lower() == 's':
            if self.mgr.reset_password(arg):
                print(f"✅ Contraseña para '{TENANT_ID}' reestablecida con éxito.")
            else:
                print(f"❌ Error al reestablecer la contraseña en el servidor.")
        else:
            print("🚫 Operación cancelada.")

    def do_backup(self, arg):
        """Genera un backup local total en JSON: backup [nombre_archivo]"""
        filename = arg if arg else "backup_full.json"
        print(f"📦 Generando backup en {filename}...")
        try:
            data = {
                "menu": self.mgr.get_all_menu(),
                "configuracion": self.mgr.get_config(),
                "grupos_extras": self.mgr.get_groups()
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("✅ Backup completado.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_ping(self, arg):
        """Verifica conexión con el API: ping"""
        try:
            r = self.mgr.client.get("/")
            print(f"📡 API Online (Status: {r.status_code})")
        except Exception as e:
            print(f"🛑 Error: {e}")

    def do_exit(self, arg):
        """Salir de la shell: exit"""
        print("👋 Adiós.")
        return True

    def do_EOF(self, arg):
        """Salir usando el atajo de teclado Ctrl+D"""
        print()
        return self.do_exit(arg)

if __name__ == "__main__":
    AdminShell().cmdloop()
