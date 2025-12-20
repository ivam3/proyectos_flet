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
                ft.Button(content=ft.Text("Vaciar carrito"), on_click=lambda e: _vaciar(e, page, show_snackbar_func, nav)),
                ft.Button(content=ft.Text("Continuar a checkout"), on_click=lambda e: _iniciar_proceso_checkout(e, page, show_snackbar_func, nav))
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

def _iniciar_proceso_checkout(e, page: ft.Page, show_snackbar_func, nav):
    """
    Inicia el flujo de checkout. Primero verifica si hay items configurables sin configurar.
    """
    user_cart = page.session.cart
    items = user_cart.get_items()
    
    # 1. Obtener items configurables
    configurable_items = [it for it in items if it.get("is_configurable")]
    
    if not configurable_items:
        _abrir_checkout(page, show_snackbar_func, nav)
        return

    # 2. Cargar guisos disponibles
    config = get_configuracion()
    guisos_activos = []
    if config and config['guisos_disponibles']:
        try:
            guisos_map = json.loads(config['guisos_disponibles'])
            guisos_activos = [k for k, v in guisos_map.items() if v]
        except:
            pass
    
    if not guisos_activos:
         # Si no hay guisos configurados pero hay items configurables, advertir o dejar pasar?
         # Dejamos pasar con advertencia o asumimos "sin guiso"
         _abrir_checkout(page, show_snackbar_func, nav)
         return

    # 3. Iniciar Wizard de Selección
    _mostrar_dialogo_guisos(page, configurable_items, 0, guisos_activos, show_snackbar_func, nav)

def _mostrar_dialogo_guisos(page, items_to_configure, current_index, guisos_disponibles, show_snackbar_func, nav):
    if current_index >= len(items_to_configure):
        _abrir_checkout(page, show_snackbar_func, nav)
        return

    item = items_to_configure[current_index]
    cantidad_total = item["cantidad"]
    
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
        # Generar string de detalles
        detalles_list = []
        for g, c in counters.items():
            if c > 0:
                detalles_list.append(f"{g} x{c}")
        
        item["details"] = ", ".join(detalles_list)
        dlg.open = False
        page.update()
        # Siguiente item
        _mostrar_dialogo_guisos(page, items_to_configure, current_index + 1, guisos_disponibles, show_snackbar_func, nav)
    
    def cancelar_seleccion(e):
        dlg.open = False
        page.update()

    btn_confirmar = ft.Button(content=ft.Text("Confirmar"), on_click=confirmar_seleccion, disabled=True)
    btn_cancelar = ft.TextButton("Cancelar", on_click=cancelar_seleccion)

    dlg = ft.AlertDialog(
        title=ft.Text(f"Elige guisos para: {item['nombre']}"),
        content=ft.Column(
            [
                ft.Text(f"Cantidad a elegir: {cantidad_total}"),
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

def _abrir_checkout(page: ft.Page, show_snackbar_func, nav):
    from views.checkout import create_checkout_view
    page.controls[1].content = create_checkout_view(page, show_snackbar_func, nav)
    page.update()