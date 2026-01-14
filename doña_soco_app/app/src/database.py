import httpx
import json
import os

# CONFIGURACIÓN DE CONEXIÓN
# En producción/nube, cambiar esto por la URL de tu servidor (ej: https://dona-soco-api.railway.app)
# Para pruebas locales en PC/Termux:
API_URL = "http://192.168.0.248:8000"

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
        response = httpx.post(f"{API_URL}/admin/login", json={"password": password})
        return response.status_code == 200
    except Exception as e:
        print(f"Error login: {e}")
        return False

def cambiar_admin_password(new_password):
    try:
        response = httpx.post(f"{API_URL}/admin/change-password", json={"new_password": new_password})
        return response.status_code == 200
    except Exception as e:
        print(f"Error password: {e}")
        return False

# --- MENU ---
def agregar_platillo(nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1):
    data = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "imagen": imagen,
        "descuento": descuento,
        "is_configurable": is_configurable,
        "is_configurable_salsa": is_configurable_salsa,
        "piezas": piezas,
        "is_active": 1
    }
    try:
        httpx.post(f"{API_URL}/menu", json=data)
        return True
    except Exception as e:
        print(f"Error agregar platillo: {e}")
        return False

def actualizar_platillo(platillo_id, nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1):
    data = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "imagen": imagen,
        "descuento": descuento,
        "is_configurable": is_configurable,
        "is_configurable_salsa": is_configurable_salsa,
        "piezas": piezas
    }
    try:
        httpx.put(f"{API_URL}/menu/{platillo_id}", json=data)
        return True
    except Exception as e:
        print(f"Error actualizar platillo: {e}")
        return False

def eliminar_platillo(platillo_id):
    try:
        httpx.delete(f"{API_URL}/menu/{platillo_id}")
        return True
    except Exception as e:
        print(f"Error eliminar platillo: {e}")
        return False

def actualizar_visibilidad_platillo(platillo_id, is_active):
    try:
        httpx.put(f"{API_URL}/menu/{platillo_id}/visibilidad", params={"is_active": is_active})
        return True
    except Exception as e:
        print(f"Error visibilidad: {e}")
        return False

def ocultar_todos_los_platillos():
    try:
        httpx.put(f"{API_URL}/admin/menu/visibilidad-global", params={"is_active": 0})
        return True
    except Exception as e:
        print(f"Error ocultar todo: {e}")
        return False

def mostrar_todos_los_platillos():
    try:
        httpx.put(f"{API_URL}/admin/menu/visibilidad-global", params={"is_active": 1})
        return True
    except Exception as e:
        print(f"Error mostrar todo: {e}")
        return False

def obtener_menu(solo_activos=True, search_term=None):
    params = {"solo_activos": solo_activos}
    if search_term:
        params["search"] = search_term
    
    try:
        response = httpx.get(f"{API_URL}/menu", params=params)
        if response.status_code == 200:
            return response.json() # Retorna lista de dicts
        return []
    except Exception as e:
        print(f"Error obtener menu: {e}")
        return []

# --- CONFIGURACION ---
def get_configuracion():
    try:
        response = httpx.get(f"{API_URL}/configuracion")
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"Error obtener config: {e}")
        return {}

def update_configuracion(horario, codigos_postales, metodos_pago_activos=None, tipos_tarjeta=None, contactos=None, guisos_disponibles=None, salsas_disponibles=None):
    data = {
        "horario": horario,
        "codigos_postales": codigos_postales,
        "metodos_pago_activos": metodos_pago_activos,
        "tipos_tarjeta": tipos_tarjeta,
        "contactos": contactos,
        "guisos_disponibles": guisos_disponibles,
        "salsas_disponibles": salsas_disponibles
    }
    # Limpiar nones para no sobreescribir con null
    data = {k: v for k, v in data.items() if v is not None}
    
    try:
        httpx.put(f"{API_URL}/configuracion", json=data)
        return True
    except Exception as e:
        print(f"Error update config: {e}")
        return False

# --- PEDIDOS ---
def guardar_pedido(nombre, telefono, direccion, referencias, total, items, metodo_pago, paga_con):
    # Formatear items para el backend
    detalles_backend = []
    for item in items:
        # Replicar lógica de formateo de nombre del producto
        detalles_txt = item.get("details") or item.get("detalles") or ""
        comentario = item.get("comentario") or ""
        nombre_producto = item["nombre"]
        
        extras = []
        if detalles_txt: extras.append(detalles_txt)
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
        response = httpx.post(f"{API_URL}/pedidos", json=orden_data)
        if response.status_code == 200:
            res_json = response.json()
            return True, res_json["codigo_seguimiento"]
        return False, None
    except Exception as e:
        print(f"Error guardar pedido: {e}")
        return False, None

def obtener_pedido_por_codigo(telefono, codigo):
    try:
        response = httpx.get(f"{API_URL}/pedidos/seguimiento", params={"telefono": telefono, "codigo": codigo})
        if response.status_code == 200:
            pedido = response.json()
            # Formatear detalles para el frontend (string concatenado)
            detalles_str = " | ".join([
                f"{d['producto']} (x{d['cantidad']} - ${d['precio_unitario']})" 
                for d in pedido["detalles"]
            ])
            # Simular objeto Row/Dict plano
            pedido["detalles_productos"] = detalles_str
            return pedido
        return None
    except Exception as e:
        print(f"Error tracking: {e} | DATA: {pedido if 'pedido' in locals() else 'No data'}")
        return None

def obtener_pedidos(limit=100, offset=0, start_date=None, end_date=None, search_term=None):
    # Nota: El backend tiene search, pero fecha aun no implementado en filtros simples, 
    # se puede agregar o filtrar en cliente. Por ahora pasamos search.
    params = {"skip": offset, "limit": limit}
    if search_term:
        params["search"] = search_term
        
    try:
        response = httpx.get(f"{API_URL}/pedidos", params=params)
        if response.status_code == 200:
            pedidos = response.json()
            # Aplanar detalles
            resultado = []
            for p in pedidos:
                detalles_str = " | ".join([
                    f"{d['producto']} (x{d['cantidad']} - ${d['precio_unitario']})" 
                    for d in p.get("detalles", [])
                ])
                p["detalles_productos"] = detalles_str
                resultado.append(p)
            
            # Filtro manual de fecha (si el backend no lo hace aun)
            # Esto es temporal hasta mejorar el backend
            if start_date or end_date:
                from datetime import datetime
                filtered = []
                for p in resultado:
                    p_date_str = p["fecha"].split("T")[0] # ISO format YYYY-MM-DD
                    keep = True
                    if start_date and p_date_str < start_date: keep = False
                    if end_date and p_date_str > end_date: keep = False
                    if keep: filtered.append(p)
                return filtered
                
            return resultado
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
        # Pedir muchos pedidos
        response = httpx.get(f"{API_URL}/pedidos", params={"limit": 5000, "search": search_term})
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
        httpx.put(f"{API_URL}/pedidos/{orden_id}/estado", params=params)
        return True
    except Exception as e:
        print(f"Error estado: {e}")
        return False

def actualizar_pago_pedido(orden_id, metodo_pago, paga_con):
    data = {"metodo_pago": metodo_pago, "paga_con": paga_con}
    try:
        httpx.put(f"{API_URL}/pedidos/{orden_id}/pago", json=data)
        return True
    except Exception as e:
        print(f"Error pago update: {e}")
        return False
