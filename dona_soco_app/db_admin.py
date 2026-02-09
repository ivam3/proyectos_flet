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
        self.client = httpx.Client(base_url=API_URL, headers=HEADERS, timeout=15.0)

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

    # --- CONFIGURACION (Guisos y Salsas) ---
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

    def delete_group(self, group_id: int):
        r = self.client.delete(f"/opciones/{group_id}")
        return r.status_code == 200

class AdminShell(cmd.Cmd):
    intro = '🛠️ Sistema de Administración Doña Soco. Escribe "help" o "?" para listar comandos.\n'
    prompt = '(ds-admin) '
    
    def __init__(self):
        super().__init__()
        self.mgr = DBManager()

    # --- BACKUP & RESTORE ---
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
            print("✅ Backup completado con éxito.")
        except Exception as e:
            print(f"❌ Error: {e}")

    # --- MENU CRUD ---
    def do_ls(self, arg):
        """Lista todos los platillos: ls"""
        items = self.mgr.get_all_menu()
        print(f"{'ID':<5} | {'Nombre':<30} | {'Precio':<8} | {'Extras (G/S)'}")
        print("-" * 70)
        for i in items:
            g = "✅" if i.get("is_configurable") else "❌"
            s = "✅" if i.get("is_configurable_salsa") else "❌"
            print(f"{i['id']:<5} | {i['nombre'][:30]:<30} | ${i['precio']:<7.2f} | {g} / {s}")

    def do_rm(self, arg):
        """Elimina un platillo por ID: rm [id]"""
        if not arg: return
        if self.mgr.delete_item(int(arg)):
            print(f"🗑️ Item {arg} eliminado.")
        else:
            print(f"❌ No se pudo eliminar.")

    # --- GRUPOS DE OPCIONES (Extras) ---
    def do_groups(self, arg):
        """Lista grupos de opciones extras: groups"""
        groups = self.mgr.get_groups()
        print(f"{'ID':<5} | {'Nombre':<20} | {'Mult' :<4} | {'Obl' :<4} | {'Opciones'}")
        print("-" * 75)
        for g in groups:
            ops = json.loads(g['opciones'])
            m = "✅" if g.get('seleccion_multiple') else "❌"
            o = "✅" if g.get('obligatorio') else "❌"
            print(f"{g['id']:<5} | {g['nombre']:<20} | {m:<4} | {o:<4} | {', '.join(ops)}")

    def do_addgroup(self, arg):
        """Agrega un grupo: addgroup Nombre Op1,Op2 [-m] [-o]
        -m: Selección múltiple
        -o: Obligatorio
        Ej: addgroup Extras Queso,Tocino,Aguacate -m
        """
        import argparse
        import shlex
        
        try:
            # Usamos shlex para permitir nombres con espacios si se ponen entre comillas
            parts = shlex.split(arg)
            if len(parts) < 2:
                print("❌ Uso: addgroup [Nombre] [Op1,Op2...] [-m] [-o]")
                return
            
            nombre = parts[0]
            opciones = [o.strip() for o in parts[1].split(',')]
            multiple = 1 if "-m" in parts else 0
            obligatorio = 1 if "-o" in parts else 0
            
            if self.mgr.create_group(nombre, opciones, multiple, obligatorio):
                print(f"✅ Grupo '{nombre}' creado (Mult: {multiple}, Obl: {obligatorio}).")
            else:
                print("❌ Error al crear grupo.")
        except Exception as e:
            print(f"❌ Error al procesar comando: {e}")

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
            print("❌ Error al actualizar configuración.")

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
            print("❌ Error al actualizar configuración.")

    # --- UTILIDADES ---
    def do_ping(self, arg):
        """Verifica conexión con el API: ping"""
        try:
            r = httpx.get(API_URL, headers=HEADERS)
            print(f"📡 API Online: {API_URL} (Status: {r.status_code})")
        except Exception as e:
            print(f"🛑 Error de conexión: {e}")

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