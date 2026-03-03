import httpx
import json
import os
from config import API_URL, HEADERS, TENANT_ID

def get_auth_headers(page=None):
    """
    Genera los headers dinámicamente. 
    Si hay un token JWT en la sesión, lo usa. Si no, usa los HEADERS base (que traen la API_KEY local).
    """
    headers = HEADERS.copy()
    if page and page.session.get("auth_token"):
        headers["Authorization"] = f"Bearer {page.session.get('auth_token')}"
    return headers

# --- AUTH ---
def verificar_admin_login(password, page=None):
    try:
        # Petición inicial de login
        response = httpx.post(f"{API_URL}/admin/login", json={"password": password}, headers=HEADERS)
        if response.status_code == 200:
            token_data = response.json()
            # Guardamos el JWT en la sesión de Flet (seguro en el navegador)
            if page:
                page.session["auth_token"] = token_data["access_token"]
            return True
        return False
    except Exception as e:
        print(f"Error login: {e}")
        return False

def subir_imagen(file_name, file_bytes, page=None):
    try:
        files = {"file": (file_name, file_bytes)}
        response = httpx.post(f"{API_URL}/upload", files=files, headers=get_auth_headers(page))
        if response.status_code == 200:
            return response.json().get("filename")
        return None
    except Exception as e:
        return None

def cambiar_admin_password(new_password, page=None):
    try:
        response = httpx.post(f"{API_URL}/admin/change-password", json={"new_password": new_password}, headers=get_auth_headers(page))
        return response.status_code == 200
    except Exception as e:
        return False

# --- MENU ---
def agregar_platillo(nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1, grupos_opciones_ids="[]", printer_target="cocina", categoria_id=None, page=None):
    data = {
        "nombre": nombre, "descripcion": descripcion, "precio": precio, "imagen": imagen,
        "descuento": descuento, "is_configurable": is_configurable, "is_configurable_salsa": is_configurable_salsa,
        "piezas": piezas, "grupos_opciones_ids": grupos_opciones_ids, "printer_target": printer_target,
        "categoria_id": categoria_id, "is_active": 1
    }
    try:
        r = httpx.post(f"{API_URL}/menu", json=data, headers=get_auth_headers(page))
        return r.status_code in [200, 201]
    except Exception as e:
        return False

def actualizar_platillo(platillo_id, nombre, descripcion, precio, imagen, descuento=0, is_configurable=0, is_configurable_salsa=0, piezas=1, grupos_opciones_ids="[]", printer_target="cocina", categoria_id=None, page=None):
    data = {
        "nombre": nombre, "descripcion": descripcion, "precio": precio, "imagen": imagen,
        "descuento": descuento, "is_configurable": is_configurable, "is_configurable_salsa": is_configurable_salsa,
        "piezas": piezas, "grupos_opciones_ids": grupos_opciones_ids, "printer_target": printer_target,
        "categoria_id": categoria_id
    }
    try:
        r = httpx.put(f"{API_URL}/menu/{platillo_id}", json=data, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def eliminar_platillo(platillo_id, page=None):
    try:
        r = httpx.delete(f"{API_URL}/menu/{platillo_id}", headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def get_grupos_opciones(page=None):
    try:
        response = httpx.get(f"{API_URL}/opciones", headers=get_auth_headers(page))
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        return []

def create_grupo_opciones(nombre, opciones, seleccion_multiple=0, obligatorio=0, page=None):
    data = {"nombre": nombre, "opciones": opciones, "seleccion_multiple": seleccion_multiple, "obligatorio": obligatorio}
    try:
        r = httpx.post(f"{API_URL}/opciones", json=data, headers=get_auth_headers(page))
        return r.status_code in [200, 201]
    except Exception as e:
        return False

def delete_grupo_opciones(grupo_id, page=None):
    try:
        r = httpx.delete(f"{API_URL}/opciones/{grupo_id}", headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def actualizar_visibilidad_platillo(platillo_id, is_active, page=None):
    try:
        r = httpx.put(f"{API_URL}/menu/{platillo_id}/visibilidad", params={"is_active": is_active}, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def ocultar_todos_los_platillos(page=None):
    try:
        r = httpx.put(f"{API_URL}/admin/menu/visibilidad-global", params={"is_active": 0}, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def mostrar_todos_los_platillos(page=None):
    try:
        r = httpx.put(f"{API_URL}/admin/menu/visibilidad-global", params={"is_active": 1}, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def obtener_menu(solo_activos=True, search_term=None, page=None):
    params = {"solo_activos": solo_activos}
    if search_term: params["search"] = search_term
    try:
        response = httpx.get(f"{API_URL}/menu", params=params, headers=get_auth_headers(page), timeout=10.0)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        return []

def get_configuracion(page=None):
    try:
        response = httpx.get(f"{API_URL}/configuracion", headers=get_auth_headers(page))
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        return {}

def update_configuracion(horario, codigos_postales, metodos_pago_activos=None, tipos_tarjeta=None, contactos=None, guisos_disponibles=None, salsas_disponibles=None, costo_envio=20.0, categorias_disponibles=None, page=None):
    data = {
        "horario": horario, "codigos_postales": codigos_postales, "metodos_pago_activos": metodos_pago_activos,
        "tipos_tarjeta": tipos_tarjeta, "contactos": contactos, "guisos_disponibles": guisos_disponibles,
        "salsas_disponibles": salsas_disponibles, "categorias_disponibles": categorias_disponibles, "costo_envio": costo_envio
    }
    data = {k: v for k, v in data.items() if v is not None}
    try:
        r = httpx.put(f"{API_URL}/configuracion", json=data, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def guardar_pedido(nombre, telefono, direccion, referencias, total, items, metodo_pago, paga_con, page=None):
    detalles_backend = []
    for item in items:
        detalles = item.get("details") or item.get("detalles") or ""
        comentario = item.get("comentario") or ""
        nombre_producto = item["nombre"]
        extras = []
        if detalles: extras.append(detalles)
        if comentario: extras.append(f"Nota: {comentario}")
        if extras: nombre_producto += f" ({' | '.join(extras)})"
        detalles_backend.append({"producto": nombre_producto, "cantidad": item["cantidad"], "precio_unitario": item["precio"]})

    orden_data = {
        "nombre_cliente": nombre, "telefono": telefono, "direccion": direccion, "referencias": referencias,
        "total": total, "metodo_pago": metodo_pago, "paga_con": paga_con, "items": detalles_backend
    }
    try:
        response = httpx.post(f"{API_URL}/pedidos", json=orden_data, headers=get_auth_headers(page))
        if response.status_code == 200:
            return True, response.json()["codigo_seguimiento"]
        return False, None
    except Exception as e:
        return False, None

def _formatear_pedido(pedido):
    if not pedido: return pedido
    detalles = pedido.get("detalles", [])
    items_strings = [f"{d['producto']} (x{d['cantidad']} - ${d['precio_unitario']:.2f})" for d in detalles]
    pedido["detalles_productos"] = " | ".join(items_strings)
    return pedido

def obtener_pedido_por_codigo(telefono, codigo, page=None):
    try:
        response = httpx.get(f"{API_URL}/pedidos/seguimiento", params={"telefono": telefono, "codigo": codigo}, headers=get_auth_headers(page))
        return _formatear_pedido(response.json()) if response.status_code == 200 else None
    except Exception as e:
        return None

def obtener_pedidos(limit=100, offset=0, search_term=None, page=None):
    params = {"skip": offset, "limit": limit}
    if search_term: params["search"] = search_term
    try:
        response = httpx.get(f"{API_URL}/pedidos", params=params, headers=get_auth_headers(page))
        return [_formatear_pedido(p) for p in response.json()] if response.status_code == 200 else []
    except Exception as e:
        return []

def obtener_total_pedidos(search_term=None, page=None):
    pedidos = obtener_pedidos(limit=1000, search_term=search_term, page=page)
    return len(pedidos)

def obtener_pedidos_sin_paginacion(search_term=None, page=None):
    return obtener_pedidos(limit=5000, search_term=search_term, page=page)

def obtener_datos_exportacion(search_term=None, page=None):
    try:
        response = httpx.get(f"{API_URL}/pedidos", params={"limit": 5000, "search": search_term}, headers=get_auth_headers(page), timeout=30.0)
        if response.status_code != 200: return []
        pedidos = response.json()
        flat_data = []
        for o in pedidos:
            for d in o["detalles"]:
                flat_data.append({
                    "orden_id": o["id"], "codigo_seguimiento": o["codigo_seguimiento"], "fecha": o["fecha"],
                    "nombre_cliente": o["nombre_cliente"], "telefono": o["telefono"], "direccion": o["direccion"],
                    "referencias": o["referencias"], "estado": o["estado"], "metodo_pago": o["metodo_pago"],
                    "paga_con": o["paga_con"], "total_orden": o["total"], "motivo_cancelacion": o["motivo_cancelacion"],
                    "producto": d["producto"], "cantidad": d["cantidad"], "precio_unitario": d["precio_unitario"],
                    "subtotal_producto": d["cantidad"] * d["precio_unitario"]
                })
        return flat_data
    except Exception as e:
        return []

def actualizar_estado_pedido(orden_id, nuevo_estado, motivo=None, page=None):
    params = {"nuevo_estado": nuevo_estado}
    if motivo: params["motivo"] = motivo
    try:
        r = httpx.put(f"{API_URL}/pedidos/{orden_id}/estado", params=params, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def actualizar_pago_pedido(orden_id, metodo_pago, paga_con, page=None):
    data = {"metodo_pago": metodo_pago, "paga_con": paga_con}
    try:
        r = httpx.put(f"{API_URL}/pedidos/{orden_id}/pago", json=data, headers=get_auth_headers(page))
        return r.status_code == 200
    except Exception as e:
        return False

def conectar(): pass
def crear_tablas(): pass
