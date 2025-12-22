# src/views/carrito.py
import flet as ft
import json
from database import get_configuracion

def create_carrito_view(page: ft.Page, show_snackbar_func, nav):
    """
    Devuelve un ft.Column que representa la pantalla del carrito.
    Llamar esta función cada vez que necesites "refrescar" la vista.
    """
    user_cart = page.session.cart
    items = user_cart.get_items()

    if not items:
        return ft.Column(
            [
                ft.Text("El carrito está vacío 🛒", size=18, color=ft.Colors.BLACK),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )

    controls = [
        ft.Text("Tu carrito", size=24, weight="bold", color=ft.Colors.BLACK),
        ft.Divider(),
    ]

    # Lista de items con botones para - / + / eliminar
    for idx, it in enumerate(items):
        nombre = it["nombre"]
        precio_unit = it["precio"]
        cantidad = it["cantidad"]
        imagen = it.get("imagen")
        subtotal = precio_unit * cantidad
        
        detalles = it.get("details", "")
        if detalles:
            nombre += f"\n({detalles})"

        controls.append(
            ft.Card(
                content=ft.Container(
                    padding=8,
                    content=ft.Row(
                        [
                            ft.Image(src=f"/{imagen}" if imagen else "", width=60, height=60, fit="cover", border_radius=5) if imagen else ft.Container(width=60),
                            ft.Column(
                                [
                                    ft.Text(nombre, weight="bold", color=ft.Colors.BLACK, size=14),
                                    ft.Text(f"${precio_unit:.2f} c/u", color=ft.Colors.BLACK),
                                    ft.Text(f"Subtotal: ${subtotal:.2f}", size=12, color=ft.Colors.BLACK),
                                    ft.TextButton(
                                        content=ft.Row([ft.Icon(ft.Icons.COMMENT, size=16), ft.Text("Especificaciones", size=12)]),
                                        on_click=lambda e, item_id=it["id"]: _abrir_dialogo_comentario(e, item_id, page, show_snackbar_func, nav)
                                    )
                                ],
                                expand=True
                            ),
                            # Botones de cantidad
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.REMOVE,
                                        on_click=lambda e, item_id=it["id"]:
                                        _decrement(e, item_id, page, show_snackbar_func, nav)
                                    ),
                                    ft.Text(str(cantidad)),
                                    ft.IconButton(
                                        icon=ft.Icons.ADD,
                                        on_click=lambda e, item_id=it["id"]:
                                        _increment(e, item_id, page, show_snackbar_func, nav)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar",
                                        on_click=lambda e, index=idx:
                                        _eliminar(e, index, page, show_snackbar_func, nav)
                                    ),
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.END
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )
            )
        )

    # Total y botón continuar
    controls.append(ft.Divider())
    controls.append(ft.Text(f"TOTAL: ${user_cart.get_total():.2f}", size=20, weight="bold", color=ft.Colors.BLACK))
    controls.append(
        ft.Row(
            [
                ft.FilledButton(
                    content=ft.Text("Vaciar carrito"), 
                    on_click=lambda e: _vaciar(e, page, show_snackbar_func, nav),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                ),
                ft.FilledButton(
                    content=ft.Text("Continuar a checkout"), 
                    on_click=lambda e: _iniciar_proceso_checkout(e, page, show_snackbar_func, nav),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    )

    return ft.Column(controls, scroll="auto", expand=True)


# ---------- FUNCIONES AUXILIARES ----------
def _refrescar(page: ft.Page, show_snackbar_func, nav):
    # Asumiendo que el layout principal coloca la vista dentro de page.controls[1].content
    page.controls[1].content = create_carrito_view(page, show_snackbar_func, nav)
    page.update()

def _eliminar(e, index: int, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.cart
    user_cart.remove_item_at(index)
    show_snackbar_func("Platillo eliminado")
    _refrescar(page, show_snackbar_func, nav)

def _vaciar(e, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.cart
    user_cart.clear_cart()
    show_snackbar_func("Carrito vaciado")
    _refrescar(page, show_snackbar_func, nav)

def _increment(e, item_id: int, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.cart
    items = user_cart.get_items()
    for it in items:
        if it["id"] == item_id:
            user_cart.update_quantity(item_id, it["cantidad"] + 1)
            # Reset details if quantity changes to force re-selection? 
            # Or just keep it. Simplest is keep it, but logic suggests re-verification.
            # For now, let's keep it simple.
            break
    _refrescar(page, show_snackbar_func, nav)

def _decrement(e, item_id: int, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.cart
    items = user_cart.get_items()
    for it in items:
        if it["id"] == item_id:
            nueva = it["cantidad"] - 1
            user_cart.update_quantity(item_id, nueva)
            break
    _refrescar(page, show_snackbar_func, nav)

def _abrir_dialogo_comentario(e, item_id, page, show_snackbar_func, nav):
    user_cart = page.session.cart
    item = next((it for it in user_cart.get_items() if it["id"] == item_id), None)
    if not item: return

    # Usamos un campo persistente para el comentario si no existe
    comentario_actual = item.get("comentario", "")
    text_field = ft.TextField(label="Ej: Sin mostaza, bien dorado...", value=comentario_actual, multiline=True)

    def guardar_comentario(e):
        item["comentario"] = text_field.value.strip()
        # Actualizamos details para que se vea en el resumen
        # Si ya hay detalles (guisos), lo concatenamos
        # Pero mejor manejamos 'comentario' por separado en el backend al guardar el pedido
        dlg.open = False
        page.update()
        show_snackbar_func("Especificación guardada")
        _refrescar(page, show_snackbar_func, nav)

    dlg = ft.AlertDialog(
        title=ft.Text(f"Especificaciones para {item['nombre']}"),
        content=text_field,
        actions=[
            ft.TextButton("Volver", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
            ft.FilledButton(
                "Guardar", 
                on_click=guardar_comentario,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
            )
        ]
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

def _iniciar_proceso_checkout(e, page: ft.Page, show_snackbar_func, nav):
    """
    Inicia el flujo de checkout. Verifica items configurables (guisos y salsas).
    """
    user_cart = page.session.cart
    items = user_cart.get_items()
    
    # Lista de items que necesitan configuración (guisos o salsas)
    to_configure_guisos = [it for it in items if it.get("is_configurable")]
    to_configure_salsas = [it for it in items if it.get("is_configurable_salsa")]
    
    # 2. Cargar disponibilidades
    config = get_configuracion()
    
    def get_activos(key):
        if config and config[key]:
            try:
                mapping = json.loads(config[key])
                return [k for k, v in mapping.items() if v]
            except: pass
        return []

    guisos_activos = get_activos('guisos_disponibles')
    salsas_activas = get_activos('salsas_disponibles')

    # Iniciamos la cadena de diálogos
    # Primero guisos, luego salsas, luego checkout
    def step_salsas():
        if to_configure_salsas and salsas_activas:
            _mostrar_dialogo_salsas(page, to_configure_salsas, 0, salsas_activas, show_snackbar_func, nav, final_callback=lambda: _abrir_checkout(page, show_snackbar_func, nav))
        else:
            _abrir_checkout(page, show_snackbar_func, nav)

    if to_configure_guisos and guisos_activos:
        _mostrar_dialogo_guisos(page, to_configure_guisos, 0, guisos_activos, show_snackbar_func, nav, final_callback=step_salsas)
    else:
        step_salsas()

def _mostrar_dialogo_guisos(page, items_to_configure, current_index, guisos_disponibles, show_snackbar_func, nav, final_callback):
    if current_index >= len(items_to_configure):
        final_callback()
        return

    item = items_to_configure[current_index]
    # MULTIPLICAMOS POR PIEZAS PARA PERMITIR SELECCIÓN INDIVIDUAL
    piezas_por_orden = item.get("piezas", 1)
    cantidad_total = item["cantidad"] * piezas_por_orden
    
    # Contadores para cada guiso
    counters = {guiso: 0 for guiso in guisos_disponibles}
    remaining_text = ft.Text(f"Faltan por elegir: {cantidad_total}")

    def update_remaining():
        selected = sum(counters.values())
        rem = cantidad_total - selected
        remaining_text.value = f"Faltan por elegir: {rem}"
        remaining_text.color = ft.Colors.RED if rem > 0 else ft.Colors.GREEN
        btn_confirmar.disabled = (rem != 0)
        page.update()

    def create_guiso_row(guiso):
        count_text = ft.Text("0", width=20, text_align="center")
        
        def change_count(e, delta):
            current_selected = sum(counters.values())
            
            # Check upper limit
            if delta > 0 and current_selected >= cantidad_total:
                return 
            
            # Check lower limit
            if counters[guiso] + delta < 0:
                return

            counters[guiso] += delta
            count_text.value = str(counters[guiso])
            update_remaining()

        return ft.Row([
            ft.Text(guiso, expand=True),
            ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: change_count(e, -1)),
            count_text,
            ft.IconButton(ft.Icons.ADD, on_click=lambda e: change_count(e, 1)),
        ])

    guiso_controls = [create_guiso_row(g) for g in guisos_disponibles]

    def confirmar_seleccion(e):
        detalles_list = []
        for g, c in counters.items():
            if c > 0: detalles_list.append(f"{g} x{c}")
        
        # Guardar en details (limpiando previo si es necesario o acumulando)
        item["details"] = ", ".join(detalles_list)
        dlg.open = False
        page.update()
        _mostrar_dialogo_guisos(page, items_to_configure, current_index + 1, guisos_disponibles, show_snackbar_func, nav, final_callback)
    
    def cancelar_seleccion(e):
        dlg.open = False
        page.update()

    btn_confirmar = ft.Button(content=ft.Text("Confirmar"), on_click=confirmar_seleccion, disabled=True)
    btn_cancelar = ft.TextButton("Cancelar", on_click=cancelar_seleccion)

    dlg = ft.AlertDialog(
        title=ft.Text(f"Elige guisos para: {item['nombre']}"),
        content=ft.Column(
            [
                ft.Text(f"Cantidad a elegir: {cantidad_total} (Ordenes: {item['cantidad']} x {piezas_por_orden} pz)"),
                remaining_text,
                ft.Divider(),
                ft.Column(guiso_controls, height=300, scroll="auto")
            ],
            width=400,
            height=400,
            tight=True
        ),
        actions=[btn_cancelar, btn_confirmar],
        modal=True
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()

def _mostrar_dialogo_salsas(page, items_to_configure, current_index, salsas_disponibles, show_snackbar_func, nav, final_callback):
    if current_index >= len(items_to_configure):
        final_callback()
        return

    item = items_to_configure[current_index]
    # Salsas también se multiplican por piezas? Asumiremos que sí, para personalización máxima
    piezas_por_orden = item.get("piezas", 1)
    cantidad_total = item["cantidad"] * piezas_por_orden
    
    counters = {salsa: 0 for salsa in salsas_disponibles}
    remaining_text = ft.Text(f"Faltan por elegir: {cantidad_total}")

    def update_remaining():
        selected = sum(counters.values())
        rem = cantidad_total - selected
        remaining_text.value = f"Faltan por elegir: {rem}"
        remaining_text.color = ft.Colors.RED if rem > 0 else ft.Colors.GREEN
        btn_confirmar.disabled = (rem != 0)
        page.update()

    def create_salsa_row(salsa):
        count_text = ft.Text("0", width=20, text_align="center")
        def change_count(e, delta):
            if delta > 0 and sum(counters.values()) >= cantidad_total: return 
            if counters[salsa] + delta < 0: return
            counters[salsa] += delta
            count_text.value = str(counters[salsa])
            update_remaining()
        return ft.Row([
            ft.Text(salsa, expand=True),
            ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: change_count(e, -1)),
            count_text,
            ft.IconButton(ft.Icons.ADD, on_click=lambda e: change_count(e, 1)),
        ])

    salsa_controls = [create_salsa_row(s) for s in salsas_disponibles]

    def confirmar_seleccion(e):
        detalles_list = []
        for s, c in counters.items():
            if c > 0: detalles_list.append(f"{s} x{c}")
        
        # Acumular con guisos si ya existen detalles
        salsa_str = "Salsas: " + ", ".join(detalles_list)
        if item.get("details"):
            item["details"] = f"{item['details']} | {salsa_str}"
        else:
            item["details"] = salsa_str
            
        dlg.open = False
        page.update()
        _mostrar_dialogo_salsas(page, items_to_configure, current_index + 1, salsas_disponibles, show_snackbar_func, nav, final_callback)
    
    btn_confirmar = ft.Button(content=ft.Text("Confirmar"), on_click=confirmar_seleccion, disabled=True)
    btn_cancelar = ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update())

    dlg = ft.AlertDialog(
        title=ft.Text(f"Elige salsas para: {item['nombre']}"),
        content=ft.Column(
            [
                ft.Text(f"Cantidad a elegir: {cantidad_total} (Ordenes: {item['cantidad']} x {piezas_por_orden} pz)"), 
                remaining_text, 
                ft.Divider(), 
                ft.Column(salsa_controls, height=300, scroll="auto")
            ],
            width=400, height=400, tight=True
        ),
        actions=[btn_cancelar, btn_confirmar],
        modal=True
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

def _abrir_checkout(page: ft.Page, show_snackbar_func, nav):
    from views.checkout import create_checkout_view
    page.controls[1].content = create_checkout_view(page, show_snackbar_func, nav)
    page.update()