import httpx
import json
import csv
import sys
import os
import cmd
from typing import Dict, Any, List

# Configurar el path para importar config.py
sys.path.append(os.path.join(os.getcwd(), "app/src"))
try:
    from config import API_URL, HEADERS, API_KEY
except ImportError:
    print("❌ No se pudo cargar config.py")
    sys.exit(1)

class DBManager:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, headers=HEADERS, timeout=30.0)

    # --- MENU ---
    def get_all_menu(self):
        r = self.client.get("/menu", params={"solo_activos": False})
        return r.json()

    def delete_item(self, item_id: int):
        r = self.client.delete(f"/menu/{item_id}")
        return r.status_code == 200

    def create_item(self, data: Dict[str, Any]):
        r = self.client.post("/menu", json=data)
        return r.status_code in [200, 201]

    def update_item(self, item_id: int, data: Dict[str, Any]):
        r = self.client.put(f"/menu/{item_id}", json=data)
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

    def create_group(self, nombre: str, opciones: List[str], multiple: int = 0, obligatorio: int = 0):
        data = {
            "nombre": nombre,
            "opciones": json.dumps(opciones),
            "seleccion_multiple": multiple,
            "obligatorio": obligatorio
        }
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

class AdminShell(cmd.Cmd):
    intro = '🛠️ Sistema de Administración Doña Soco. Escribe "help" o "?" para listar comandos.\n'
    prompt = '(ds-admin) '
    
    def __init__(self):
        super().__init__()
        self.mgr = DBManager()

    # --- GESTION DE IMAGENES ---
    def do_upload(self, arg):
        """Sube una imagen local al servidor: upload /ruta/a/la/imagen.jpg"""
        if not arg:
            print("❌ Uso: upload [ruta_local_imagen]")
            return
        
        print(f"🚀 Subiendo {arg}...")
        filename, error = self.mgr.upload_image(arg)
        if filename:
            print(f"✅ Imagen subida con éxito.")
            print(f"🔗 Nombre en servidor: {filename}")
            print(f"💡 Puedes usar este nombre al crear un platillo.")
        else:
            print(f"❌ Error al subir: {error}")

    def do_rmfile(self, arg):
        """Elimina un archivo del servidor: rmfile [nombre_archivo]"""
        if not arg:
            print("❌ Uso: rmfile [nombre_archivo]")
            return
        if self.mgr.delete_file(arg):
            print(f"🗑️ Archivo '{arg}' eliminado del servidor.")
        else:
            print(f"❌ No se pudo eliminar el archivo.")

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
                group_map = {g['nombre'].strip().lower(): g['id'] for g in current_groups}
                
                for g in data["grupos_extras"]:
                    name_clean = g['nombre'].strip().lower()
                    ops = json.loads(g['opciones']) if isinstance(g['opciones'], str) else g['opciones']
                    m = g.get('seleccion_multiple', 0)
                    o = g.get('obligatorio', 0)
                    
                    if name_clean in group_map:
                        if self.mgr.update_group(group_map[name_clean], g['nombre'], ops, m, o):
                            print(f" 🔄 Grupo '{g['nombre']}' actualizado.")
                        else:
                            print(f" ❌ Error actualizando grupo '{g['nombre']}'.")
                    else:
                        if self.mgr.create_group(g['nombre'], ops, m, o):
                            print(f" ✅ Grupo '{g['nombre']}' creado.")
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
                menu_map = {item['nombre'].strip().lower(): item['id'] for item in current_menu}

                print(f"📥 Procesando {len(items_to_import)} platillos...")
                for item in items_to_import:
                    nombre_clean = item['nombre'].strip().lower()
                    if "id" in item: del item["id"]
                    
                    if nombre_clean in menu_map:
                        item_id = menu_map[nombre_clean]
                        if self.mgr.update_item(item_id, item):
                            print(f" 🔄 {item['nombre']} actualizado.")
                        else:
                            print(f" ❌ Error actualizando {item['nombre']}.")
                    else:
                        if self.mgr.create_item(item):
                            print(f" ✅ {item['nombre']} creado.")
                        else:
                            print(f" ❌ Error creando {item['nombre']}.")
            
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
        print(f"{ 'ID':<5} | {'Nombre':<30} | {'Precio':<8} | {'Imagen'}")
        print("-" * 75)
        for i in items:
            img = i.get("imagen") or "---"
            print(f"{i['id']:<5} | {i['nombre'][:30]:<30} | ${i['precio']:<7.2f} | {img}")

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