# src/views/carrito.py
import flet as ft

def create_carrito_view(page: ft.Page, show_snackbar_func, nav):
    """
    Devuelve un ft.Column que representa la pantalla del carrito.
    Llamar esta función cada vez que necesites "refrescar" la vista.
    """
    user_cart = page.session.get("cart")
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
        subtotal = precio_unit * cantidad

        controls.append(
            ft.Card(
                content=ft.Container(
                    padding=8,
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(nombre, weight="bold", color=ft.Colors.BLACK),
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
                                        on_click=lambda e, item_id=it["id"]: _decrement(e, item_id, page, show_snackbar_func, nav)
                                    ),
                                    ft.Text(str(cantidad)),
                                    ft.IconButton(
                                        icon=ft.Icons.ADD,
                                        on_click=lambda e, item_id=it["id"]: _increment(e, item_id, page, show_snackbar_func, nav)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar",
                                        on_click=lambda e, index=idx: _eliminar(e, index, page, show_snackbar_func, nav)
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
                ft.ElevatedButton("Vaciar carrito", on_click=lambda e: _vaciar(e, page, show_snackbar_func, nav)),
                ft.ElevatedButton("Continuar a checkout", on_click=lambda e: _abrir_checkout(e, page, show_snackbar_func, nav))
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
    user_cart = page.session.get("cart")
    user_cart.remove_item_at(index)
    show_snackbar_func("Platillo eliminado")
    _refrescar(page, show_snackbar_func, nav)

def _vaciar(e, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.get("cart")
    user_cart.clear_cart()
    show_snackbar_func("Carrito vaciado")
    _refrescar(page, show_snackbar_func, nav)

def _increment(e, item_id: int, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.get("cart")
    items = user_cart.get_items()
    for it in items:
        if it["id"] == item_id:
            user_cart.update_quantity(item_id, it["cantidad"] + 1)
            break
    _refrescar(page, show_snackbar_func, nav)

def _decrement(e, item_id: int, page: ft.Page, show_snackbar_func, nav):
    user_cart = page.session.get("cart")
    items = user_cart.get_items()
    for it in items:
        if it["id"] == item_id:
            nueva = it["cantidad"] - 1
            user_cart.update_quantity(item_id, nueva)
            break
    _refrescar(page, show_snackbar_func, nav)

def _abrir_checkout(e, page: ft.Page, show_snackbar_func, nav):
    from views.checkout import create_checkout_view
    page.controls[1].content = create_checkout_view(page, show_snackbar_func, nav)
    page.update()
