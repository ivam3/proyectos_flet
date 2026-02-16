import httpx
import json
import os
from config import API_URL, HEADERS

# Importar init_pubsub no es ideal aquí porque requiere 'page', 
# pero podemos simular un evento si tuviéramos acceso a la instancia.
# Como database.py es independiente de la UI, la notificación la debe gatillar 
# quien llama a guardar_pedido (checkout.py).
# Dejaremos este archivo limpio y modificaremos checkout.py.

# CONFIGURACIÓN DE CONEXIÓN
# En producción/nube, cambiar esto por la URL de tu servidor (ej: https://dona-soco-api.railway.app)
# Para pruebas locales en PC/Termux:
#API_URL = "https://dona-soco-app.onrender.com"

# Si estás en Android real y el servidor está en tu PC, usa la IP de tu PC (ej: http://192.168.1.50:8000)
# Si el servidor corre en el mismo Termux que la app, localhost está bien.

def conectar():
    """Ya no es necesario mantener una conexión persistente, pero dejamos la función por compatibilidad."""
    pass

def crear_tablas():
    """El backend se encarga de esto ahora."""
    pass

# --- AUTH ---
def verificar_admin_login(password):
    try:
        response = httpx.post(f"{API_URL}/admin/login", json={"password": password}, headers=HEADERS)
        return response.status_code == 200
    except Exception as e:
        print(f"Error login: {e}")
        return False

def subir_imagen(file_name, file_bytes):
    """Sube una imagen al backend y retorna el nombre del archivo guardado."""
    try:
        files = {"file": (file_name, file_bytes)}
        response = httpx.post(f"{API_URL}/upload", files=files, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("filename")
        print(f"Error subiendo imagen: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"Error en subir_imagen: {e}")
        return None

def cambiar_admin_password(new_password):
    try:
        response = httpx.post(f"{API_URL}/admin/change-password", json={"new_password": new_password}, headers=HEADERS)
        return response.status_code == 200
    except Exception as e:
        print(f"Error password: {e}")
        return False

# --- MENU ---
def agregar_platillo(nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1, grupos_opciones_ids="[]", printer_target="cocina"):
    data = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "imagen": imagen,
        "descuento": descuento,
        "is_configurable": is_configurable,
        "is_configurable_salsa": is_configurable_salsa,
        "piezas": piezas,
        "grupos_opciones_ids": grupos_opciones_ids,
        "printer_target": printer_target,
        "is_active": 1
    }
    try:
        r = httpx.post(f"{API_URL}/menu", json=data, headers=HEADERS)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Error agregar platillo: {e}")
        return False

def actualizar_platillo(platillo_id, nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1, grupos_opciones_ids="[]", printer_target="cocina"):
    data = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "imagen": imagen,
        "descuento": descuento,
        "is_configurable": is_configurable,
        "is_configurable_salsa": is_configurable_salsa,
        "piezas": piezas,
        "grupos_opciones_ids": grupos_opciones_ids,
        "printer_target": printer_target
    }
    try:
        httpx.put(f"{API_URL}/menu/{platillo_id}", json=data, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error actualizar platillo: {e}")
        return False

def eliminar_platillo(platillo_id):
    try:
        httpx.delete(f"{API_URL}/menu/{platillo_id}", headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error eliminar platillo: {e}")
        return False

# --- GRUPOS DE OPCIONES ---
def get_grupos_opciones():
    try:
        response = httpx.get(f"{API_URL}/opciones", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error obtener grupos: {e}")
        return []

def create_grupo_opciones(nombre, opciones, seleccion_multiple=0, obligatorio=0):
    # opciones debe ser un string JSON list: '["Op1", "Op2"]'
    data = {
        "nombre": nombre,
        "opciones": opciones,
        "seleccion_multiple": seleccion_multiple,
        "obligatorio": obligatorio
    }
    try:
        r = httpx.post(f"{API_URL}/opciones", json=data, headers=HEADERS)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Error crear grupo: {e}")
        return False

def delete_grupo_opciones(grupo_id):
    try:
        r = httpx.delete(f"{API_URL}/opciones/{grupo_id}", headers=HEADERS)
        return r.status_code == 200
    except Exception as e:
        print(f"Error borrar grupo: {e}")
        return False

def actualizar_visibilidad_platillo(platillo_id, is_active):
    try:
        httpx.put(f"{API_URL}/menu/{platillo_id}/visibilidad", params={"is_active": is_active}, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error visibilidad: {e}")
        return False

def ocultar_todos_los_platillos():
    try:
        httpx.put(f"{API_URL}/admin/menu/visibilidad-global", params={"is_active": 0}, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error ocultar todo: {e}")
        return False

def mostrar_todos_los_platillos():
    try:
        httpx.put(f"{API_URL}/admin/menu/visibilidad-global", params={"is_active": 1}, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error mostrar todo: {e}")
        return False

def obtener_menu(solo_activos=True, search_term=None):
    params = {"solo_activos": solo_activos}
    if search_term:
        params["search"] = search_term
    
    try:
        response = httpx.get(f"{API_URL}/menu", params=params, headers=HEADERS, timeout=10.0)
        if response.status_code == 200:
            return response.json() 
        return []
    except Exception as e:
        print(f"Error crítico obtener menu: {e}")
        return []

# --- CONFIGURACION ---
def get_configuracion():
    try:
        response = httpx.get(f"{API_URL}/configuracion", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"Error obtener config: {e}")
        return {}

def update_configuracion(horario, codigos_postales, metodos_pago_activos=None, tipos_tarjeta=None, contactos=None, guisos_disponibles=None, salsas_disponibles=None, costo_envio=20.0):
    data = {
        "horario": horario,
        "codigos_postales": codigos_postales,
        "metodos_pago_activos": metodos_pago_activos,
        "tipos_tarjeta": tipos_tarjeta,
        "contactos": contactos,
        "guisos_disponibles": guisos_disponibles,
        "salsas_disponibles": salsas_disponibles,
        "costo_envio": costo_envio
    }
    # Limpiar nones para no sobreescribir con null
    data = {k: v for k, v in data.items() if v is not None}
    
    try:
        httpx.put(f"{API_URL}/configuracion", json=data, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error update config: {e}")
        return False

# --- PEDIDOS ---
def guardar_pedido(nombre, telefono, direccion, referencias, total, items, metodo_pago, paga_con):
    # Formateo de items para la API del backend
    detalles_backend = []
    for item in items:
        # Estandarizar recuperación de detalles y notas
        detalles = item.get("details") or item.get("detalles") or ""
        comentario = item.get("comentario") or ""
        
        nombre_producto = item["nombre"]
        
        extras = []
        if detalles: extras.append(detalles)
        if comentario: extras.append(f"Nota: {comentario}")
        
        if extras:
             nombre_producto += f" ({' | '.join(extras)})"
             
        detalles_backend.append({
            "producto": nombre_producto,
            "cantidad": item["cantidad"],
            "precio_unitario": item["precio"]
        })

    orden_data = {
        "nombre_cliente": nombre,
        "telefono": telefono,
        "direccion": direccion,
        "referencias": referencias,
        "total": total,
        "metodo_pago": metodo_pago,
        "paga_con": paga_con,
        "items": detalles_backend
    }

    try:
        response = httpx.post(f"{API_URL}/pedidos", json=orden_data, headers=HEADERS)
        if response.status_code == 200:
            res_json = response.json()
            return True, res_json["codigo_seguimiento"]
        return False, None
    except Exception as e:
        print(f"Error guardar pedido: {e}")
        return False, None

def _formatear_pedido(pedido):
    """Añade el campo detalles_productos (string concatenado) para compatibilidad con el frontend."""
    if not pedido:
        return pedido
    
    detalles = pedido.get("detalles", [])
    items_strings = []
    for d in detalles:
        items_strings.append(f"{d['producto']} (x{d['cantidad']} - ${d['precio_unitario']:.2f})")
    
    pedido["detalles_productos"] = " | ".join(items_strings)
    return pedido

def obtener_pedido_por_codigo(telefono, codigo):
    try:
        response = httpx.get(f"{API_URL}/pedidos/seguimiento", params={"telefono": telefono, "codigo": codigo}, headers=HEADERS)
        if response.status_code == 200:
            pedido = response.json()
            return _formatear_pedido(pedido)
        return None
    except Exception as e:
        print(f"Error tracking: {e}")
        return None

def obtener_pedidos(limit=100, offset=0, start_date=None, end_date=None, search_term=None):
    # ...
    params = {"skip": offset, "limit": limit}
    if search_term:
        params["search"] = search_term
        
    try:
        response = httpx.get(f"{API_URL}/pedidos", params=params, headers=HEADERS)
        if response.status_code == 200:
            pedidos = response.json()
            return [_formatear_pedido(p) for p in pedidos]
        return []
    except Exception as e:
        print(f"Error obtener pedidos: {e}")
        return []

def obtener_total_pedidos(start_date=None, end_date=None, search_term=None):
    # Ineficiente: trae todos y cuenta. Fase 1 OK.
    pedidos = obtener_pedidos(limit=1000, start_date=start_date, end_date=end_date, search_term=search_term)
    return len(pedidos)

def obtener_datos_exportacion(search_term=None):
    """
    Simula la consulta SQL de exportación obteniendo todos los datos y desnormalizándolos.
    """
    try:
        # Pedir muchos pedidos con timeout extendido
        response = httpx.get(f"{API_URL}/pedidos", params={"limit": 5000, "search": search_term}, headers=HEADERS, timeout=30.0)
        if response.status_code != 200:
            return []
        
        pedidos = response.json()
        flat_data = []
        
        # Convertir estructura jerárquica (Orden -> Detalles) a tabla plana
        for o in pedidos:
            for d in o["detalles"]:
                row = {
                    "orden_id": o["id"],
                    "codigo_seguimiento": o["codigo_seguimiento"],
                    "fecha": o["fecha"],
                    "nombre_cliente": o["nombre_cliente"],
                    "telefono": o["telefono"],
                    "direccion": o["direccion"],
                    "referencias": o["referencias"],
                    "estado": o["estado"],
                    "metodo_pago": o["metodo_pago"],
                    "paga_con": o["paga_con"],
                    "total_orden": o["total"],
                    "motivo_cancelacion": o["motivo_cancelacion"],
                    "producto": d["producto"],
                    "cantidad": d["cantidad"],
                    "precio_unitario": d["precio_unitario"],
                    "subtotal_producto": d["cantidad"] * d["precio_unitario"]
                }
                flat_data.append(row)
                
        return flat_data
    except Exception as e:
        print(f"Error exportacion: {e}")
        return []

def obtener_pedidos_sin_paginacion(start_date=None, end_date=None, search_term=None):
    return obtener_pedidos(limit=5000, start_date=start_date, end_date=end_date, search_term=search_term)

def actualizar_estado_pedido(orden_id, nuevo_estado, motivo=None):
    params = {"nuevo_estado": nuevo_estado}
    if motivo: params["motivo"] = motivo
    
    try:
        httpx.put(f"{API_URL}/pedidos/{orden_id}/estado", params=params, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error estado: {e}")
        return False

def actualizar_pago_pedido(orden_id, metodo_pago, paga_con):
    data = {"metodo_pago": metodo_pago, "paga_con": paga_con}
    try:
        httpx.put(f"{API_URL}/pedidos/{orden_id}/pago", json=data, headers=HEADERS)
        return True
    except Exception as e:
        print(f"Error pago update: {e}")
        return False
