import httpx
import json
import sys
import os
import cmd
import shlex
from typing import Dict, Any, List
from datetime import datetime

# Configurar el path para importar config.py desde la carpeta app
sys.path.append(os.path.join(os.getcwd(), "app"))
try:
    from config import API_URL, HEADERS, TENANT_ID
except ImportError:
    print("❌ No se pudo cargar config.py desde la carpeta 'app'")
    sys.exit(1)

class DBManager:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, headers=HEADERS, timeout=30.0)

    def get_all_products(self):
        try:
            r = self.client.get("/products")
            return r.json() if r.status_code == 200 else None
        except Exception as e:
            print(f"🛑 Error de conexión: {e}")
            return None

    def create_product(self, data: Dict[str, Any]):
        try:
            r = self.client.post("/products", json=data)
            if r.status_code in [200, 201]:
                return True, r.json()
            return False, r.text
        except Exception as e:
            return False, str(e)

    def delete_product(self, product_id: int):
        try:
            r = self.client.delete(f"/products/{product_id}")
            return r.status_code == 200
        except: return False

    def wipe_products(self):
        try:
            r = self.client.post("/admin/maintenance/wipe")
            return r.status_code == 200
        except: return False

    def recreate_tables(self):
        try:
            r = self.client.post("/admin/maintenance/recreate-tables")
            return r.status_code == 200
        except: return False

    def upload_photo(self, product_id: int, file_path: str):
        if not os.path.exists(file_path):
            return None, "Archivo local no encontrado"
        try:
            files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
            r = self.client.post(f"/photos/upload/{product_id}", files=files)
            return (r.json(), None) if r.status_code == 200 else (None, r.text)
        except Exception as e:
            return None, str(e)

    def get_upload_list(self):
        try:
            r = self.client.get("/upload/list")
            return r.json().get("files", [])
        except: return []

    def get_movements(self):
        try:
            r = self.client.get("/movements")
            return r.json() if r.status_code == 200 else []
        except: return []

class StockAdminShell(cmd.Cmd):
    intro = f'👟 Sistema de Administración (Risk Shoes Stock)\n📡 API: {API_URL}\n🆔 TENANT: {TENANT_ID}\n'
    prompt = f'(db-admin-{TENANT_ID})\n╰─➤ '
    
    def __init__(self):
        super().__init__()
        self.mgr = DBManager()

    def do_ls(self, arg):
        """Lista los productos: ls"""
        products = self.mgr.get_all_products()
        if products is None:
            print("❌ Error: No se pudo conectar con la API.")
            return
        if not products:
            print("📭 El inventario está vacío.")
            return
        
        print(f"\n{'ID':<4} | {'Modelo':<22} | {'Marca':<12} | {'SKU':<12} | {'Precio':<9} | {'Stock'}")
        print("-" * 85)
        for p in products:
            total_stock = sum(s['stock'] for s in p.get('sizes', []))
            print(f"{p['id']:<4} | {p['model_name'][:22]:<22} | {p.get('brand','-')[:12]:<12} | {p['sku']:<12} | ${p['price']:<8.2f} | {total_stock}")
        print()

    def do_ping(self, arg):
        """Verifica conexión: ping"""
        try:
            r = self.mgr.client.get("/")
            print(f"📡 API Status {r.status_code}: {r.json().get('message')}")
        except Exception as e:
            print(f"🛑 Error: {e}")

    def do_addproduct(self, arg):
        """Añade un producto: addproduct \"Modelo\" SKU \"Marca\" Precio \"Tallas\" \"Colores\" \"Cantidades\"
        Ej: addproduct \"Jordan 1\" J1-001 Nike 2500 \"7 8\" \"Rojo Negro\" \"5 10\"
        """
        try:
            args = shlex.split(arg)
            if len(args) < 7:
                print("❌ Faltan parámetros.")
                print("👉 Uso: addproduct \"Modelo\" SKU \"Marca\" Precio \"Tallas\" \"Colores\" \"Cantidades\"")
                return

            model, sku, brand, price, sizes, colors, stocks = args
            
            raw_sizes = sizes.split()
            raw_colors = colors.split()
            raw_stocks = stocks.split()
            
            initial_sizes = []
            for i, s in enumerate(raw_sizes):
                # Mapeo 1:1 similar al frontend
                c = raw_colors[i] if len(raw_colors) > i else (raw_colors[0] if raw_colors else "N/A")
                q = int(raw_stocks[i]) if len(raw_stocks) > i else (int(raw_stocks[0]) if raw_stocks else 0)
                initial_sizes.append({"size": s, "color": c, "stock": q})

            data = {
                "model_name": model,
                "sku": sku,
                "brand": brand,
                "price": float(price),
                "initial_sizes": initial_sizes
            }
            
            ok, res = self.mgr.create_product(data)
            if ok: print(f"✅ Producto '{model}' creado.")
            else: print(f"⚠️ Fallo: {res}")
        except Exception as e:
            print(f"❌ Error de parsing: {e}")

    def do_rmproduct(self, arg):
        """Elimina un producto por ID: rmproduct [ID]"""
        if not arg:
            print("❌ Falta el ID del producto. Uso: rmproduct [id]")
            return
        if self.mgr.delete_product(int(arg)):
            print(f"🗑️ Producto {arg} eliminado.")
        else:
            print("❌ No se pudo eliminar (verifique el ID).")

    def do_ls_img(self, arg):
        """Lista imágenes en el servidor: ls_img"""
        files = self.mgr.get_upload_list()
        print(f"📂 Imágenes en servidor ({len(files)}):")
        for f in sorted(files): print(f"  - {f}")

    def do_upimg(self, arg):
        """Sube imagen a un producto: upimg [prod_id] [ruta_archivo]"""
        args = shlex.split(arg)
        if len(args) < 2:
            print("❌ Faltan parámetros. Uso: upimg [id_producto] [ruta_archivo]")
            return
        res, err = self.mgr.upload_photo(int(args[0]), args[1])
        if res: print("✅ Imagen subida y vinculada.")
        else: print(f"❌ Error: {err}")

    def do_backup(self, arg):
        """Genera backup integral: backup [nombre_archivo.json]"""
        filename = arg if arg else f"backup_{TENANT_ID}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        print(f"📦 Generando backup en '{filename}'...")
        try:
            data = {
                "products": self.mgr.get_all_products(),
                "movements": self.mgr.get_movements(),
                "timestamp": datetime.now().isoformat(),
                "tenant": TENANT_ID
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("✅ Backup completado.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_importar(self, arg):
        """Importa datos desde JSON: importar [archivo.json]"""
        if not arg or not os.path.exists(arg):
            print("❌ Archivo no encontrado. Uso: importar [archivo.json]")
            return
        try:
            with open(arg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            products = data.get("products", [])
            print(f"📥 Importando {len(products)} productos...")
            for p in products:
                p_data = {
                    "model_name": p['model_name'],
                    "sku": p['sku'],
                    "brand": p.get('brand'),
                    "category": p.get('category'),
                    "price": p['price'],
                    "cost": p.get('cost', 0),
                    "initial_sizes": [{"size": s['size'], "color": s.get('color','N/A'), "stock": s['stock']} for s in p.get('sizes', [])]
                }
                self.mgr.create_product(p_data)
            print("🏁 Proceso de importación finalizado.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_reset_schema(self, arg):
        """⚠️ RECREA LAS TABLAS (BORRA TODO)"""
        confirm = input("❗ ADVERTENCIA: Se borrarán TODOS los datos. ¿Continuar? (s/n): ")
        if confirm.lower() == 's':
            if self.mgr.recreate_tables(): print("✅ Tablas recreadas.")
            else: print("❌ Error en el servidor.")

    def do_exit(self, arg):
        """Salir: exit"""
        print("👋 Saliendo...")
        return True

    def do_EOF(self, arg):
        print()
        return self.do_exit(arg)

if __name__ == "__main__":
    StockAdminShell().cmdloop()
