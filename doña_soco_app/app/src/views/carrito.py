# src/views/carrito.py
import flet as ft
import json
from database import get_configuracion, get_grupos_opciones

def create_carrito_view(page: ft.Page, show_snackbar_func, nav):
    """
    Vista del carrito con lógica de actualización local.
    """
    
    # Contenedor principal que se actualizará
    main_column = ft.Column(scroll="auto", expand=True)

    def render_items():
        user_cart = page.session.cart
        items = user_cart.get_items()
        
        main_column.controls.clear()

        if not items:
            main_column.controls.append(
                ft.Container(
                    content=ft.Text("El carrito está vacío 🛒", size=18, color=ft.Colors.BLACK),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True
                )
            )
            page.update()
            return

        main_column.controls.append(ft.Text("Tu carrito", size=24, weight="bold", color=ft.Colors.BLACK))
        main_column.controls.append(ft.Divider())

        for idx, it in enumerate(items):
            nombre = it["nombre"]
            precio_unit = it["precio"]
            cantidad = it["cantidad"]
            imagen = it.get("imagen")
            subtotal = precio_unit * cantidad
            
            detalles = it.get("details", "")
            if detalles:
                nombre += f"\n({detalles})"

            card = ft.Card(
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
                                        content=ft.Row([ft.Icon(ft.Icons.COMMENT, size=16, color=ft.Colors.BROWN_500), ft.Text("Especificaciones", size=12, color=ft.Colors.BROWN_500)]),
                                        on_click=lambda e, item_id=it["id"]: _abrir_dialogo_comentario(e, item_id, page, show_snackbar_func, render_items)
                                    )
                                ],
                                expand=True
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.REMOVE,
                                        icon_color=ft.Colors.BLACK,
                                        on_click=lambda e, item_id=it["id"]: _decrement(item_id, page, show_snackbar_func, render_items)
                                    ),
                                    ft.Text(str(cantidad), color=ft.Colors.BLACK),
                                    ft.IconButton(
                                        icon=ft.Icons.ADD,
                                        icon_color=ft.Colors.BLACK,
                                        on_click=lambda e, item_id=it["id"]: _increment(item_id, page, show_snackbar_func, render_items)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED,
                                        tooltip="Eliminar",
                                        on_click=lambda e, index=idx: _eliminar(index, page, show_snackbar_func, render_items)
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
            main_column.controls.append(card)

        # Total y botón continuar
        main_column.controls.append(ft.Divider())
        main_column.controls.append(ft.Text(f"TOTAL: ${user_cart.get_total():.2f}", size=20, weight="bold", color=ft.Colors.BLACK))
        main_column.controls.append(
            ft.Row(
                [
                    ft.FilledButton(
                        content=ft.Text("Vaciar carrito"), 
                        on_click=lambda e: _vaciar(page, show_snackbar_func, render_items),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                    ),
                    ft.FilledButton(
                        content=ft.Text("Continuar a checkout"), 
                        on_click=lambda e: _iniciar_proceso_checkout(page, show_snackbar_func, nav),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )
        page.update()

    # Render inicial
    render_items()
    return main_column

# ---------- FUNCIONES AUXILIARES (Modificadas para recibir callback de renderizado) ----------

def _eliminar(index: int, page: ft.Page, show_snackbar_func, render_callback):
    user_cart = page.session.cart
    user_cart.remove_item_at(index)
    show_snackbar_func("Platillo eliminado")
    render_callback()

def _vaciar(page: ft.Page, show_snackbar_func, render_callback):
    user_cart = page.session.cart
    user_cart.clear_cart()
    show_snackbar_func("Carrito vaciado")
    render_callback()

def _increment(item_id: int, page: ft.Page, show_snackbar_func, render_callback):
    user_cart = page.session.cart
    items = user_cart.get_items()
    for it in items:
        if it["id"] == item_id:
            user_cart.update_quantity(item_id, it["cantidad"] + 1)
            break
    render_callback()

def _decrement(item_id: int, page: ft.Page, show_snackbar_func, render_callback):
    user_cart = page.session.cart
    items = user_cart.get_items()
    for it in items:
        if it["id"] == item_id:
            nueva = it["cantidad"] - 1
            user_cart.update_quantity(item_id, nueva)
            break
    render_callback()

def _abrir_dialogo_comentario(e, item_id, page, show_snackbar_func, render_callback):
    user_cart = page.session.cart
    item = next((it for it in user_cart.get_items() if it["id"] == item_id), None)
    if not item: return

    comentario_actual = item.get("comentario", "")
    text_field = ft.TextField(label="Ej: Sin mostaza, bien dorado...", value=comentario_actual, multiline=True) 

    def guardar_comentario(e):
        item["comentario"] = text_field.value.strip()
        dlg.open = False
        page.update()
        show_snackbar_func("Especificación guardada")
        render_callback()

    dlg = ft.AlertDialog(
        title=ft.Text(f"Especificaciones para {item['nombre']}"),
        content=text_field,
        actions=[
            ft.TextButton("Volver", on_click=lambda _: setattr(dlg, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700)),
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

def _iniciar_proceso_checkout(page: ft.Page, show_snackbar_func, nav):
    """
    Inicia el flujo de checkout. Verifica items configurables (guisos y salsas).
    """
    user_cart = page.session.cart
    items = user_cart.get_items()
    
    to_configure_guisos = [it for it in items if it.get("is_configurable")]
    to_configure_salsas = [it for it in items if it.get("is_configurable_salsa")]
    
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
    
    # --- PROCESO DE GRUPOS DINÁMICOS ---
    all_groups = get_grupos_opciones() # List of dicts {id, nombre, opciones, ...}
    
    # cola de pasos de configuración
    # Cada paso es una tupla: (grupo_obj, items_afectados)
    pasos_dinamicos = []
    
    for g in all_groups:
        items_in_this_group = []
        for it in items:
            g_ids_json = it.get("grupos_opciones_ids", "[]")
            try:
                g_ids = json.loads(g_ids_json)
                if g['id'] in g_ids:
                    items_in_this_group.append(it)
            except: pass
        
        if items_in_this_group:
            pasos_dinamicos.append((g, items_in_this_group))

    def final_step():
        # Ejecutar tarea asíncrona desde contexto síncrono
        page.run_task(page.push_route, "/checkout")

    # Ejecutor recursivo de pasos dinámicos
    def ejecutar_paso_dinamico(index):
        if index >= len(pasos_dinamicos):
            # Terminado los dinámicos, pasamos a los legacy (Guisos -> Salsas -> Fin)
            legacy_flow()
            return
            
        grupo, items_afectados = pasos_dinamicos[index]
        # Decodificar opciones del grupo
        try:
            opciones = json.loads(grupo['opciones'])
        except:
            opciones = [x.strip() for x in grupo['opciones'].split(",")]
            
        _mostrar_dialogo_generico(
            page, 
            grupo['nombre'], 
            opciones, 
            items_afectados, 
            0, 
            show_snackbar_func, 
            lambda: ejecutar_paso_dinamico(index + 1)
        )

    def legacy_flow():
        def step_salsas():
            if to_configure_salsas and salsas_activas:
                _mostrar_dialogo_salsas(page, to_configure_salsas, 0, salsas_activas, show_snackbar_func, final_callback=final_step)
            else:
                final_step()

        if to_configure_guisos and guisos_activos:
            _mostrar_dialogo_guisos(page, to_configure_guisos, 0, guisos_activos, show_snackbar_func, final_callback=step_salsas)
        else:
            step_salsas()

    # Iniciar flujo
    ejecutar_paso_dinamico(0)

def _mostrar_dialogo_generico(page, titulo_grupo, opciones_disponibles, items_to_configure, current_index, show_snackbar_func, final_callback):
    """
    Diálogo genérico para configurar opciones extras (ej: Termino, Verduras).
    Reutiliza la lógica de contadores.
    """
    if current_index >= len(items_to_configure):
        final_callback()
        return

    item = items_to_configure[current_index]
    # Por ahora asumimos 1 opción por pieza por defecto, o personalizable?
    # Para simplificar, asumimos que se elige 1 opción por cada pieza del producto.
    piezas_por_orden = item.get("piezas", 1)
    # Nota: Si piezas > 1 (ej: 3 tacos), el usuario elige X opciones total = cantidad * piezas
    cantidad_total = item["cantidad"] * piezas_por_orden
    
    counters = {op: 0 for op in opciones_disponibles}
    remaining_text = ft.Text(f"Faltan por elegir: {cantidad_total}", color=ft.Colors.BLACK)

    def update_remaining():
        selected = sum(counters.values())
        rem = cantidad_total - selected
        remaining_text.value = f"Faltan por elegir: {rem}"
        remaining_text.color = ft.Colors.RED if rem > 0 else ft.Colors.GREEN
        btn_confirmar.disabled = (rem != 0)
        page.update()

    def create_row(opcion):
        count_text = ft.Text("0", width=20, text_align="center", color=ft.Colors.BLACK)
        
        def change_count(e, delta):
            current_selected = sum(counters.values())
            # Limite superior
            if delta > 0 and current_selected >= cantidad_total: return 
            # Limite inferior
            if counters[opcion] + delta < 0: return
            
            counters[opcion] += delta
            count_text.value = str(counters[opcion])
            update_remaining()

        return ft.Row([
            ft.Text(opcion, expand=True, color=ft.Colors.BLACK),
            ft.IconButton(ft.Icons.REMOVE, icon_color=ft.Colors.BLACK, on_click=lambda e: change_count(e, -1)),
            count_text,
            ft.IconButton(ft.Icons.ADD, icon_color=ft.Colors.BLACK, on_click=lambda e: change_count(e, 1)),
        ])

    controls_list = [create_row(op) for op in opciones_disponibles]

    def confirmar_seleccion(e):
        detalles_list = []
        for op, c in counters.items():
            if c > 0: detalles_list.append(f"{op} x{c}")
        
        res_str = f"{titulo_grupo}: " + ", ".join(detalles_list)
        
        if item.get("details"):
            item["details"] = f"{item['details']} | {res_str}"
        else:
            item["details"] = res_str
            
        dlg.open = False
        page.update()
        _mostrar_dialogo_generico(page, titulo_grupo, opciones_disponibles, items_to_configure, current_index + 1, show_snackbar_func, final_callback)
    
    btn_confirmar = ft.Button(content=ft.Text("Confirmar"), on_click=confirmar_seleccion, disabled=True)
    # Cancelar solo cierra el dialogo actual y pasa al siguiente (skip) o cancela todo?
    # Mejor cancelar todo el checkout para evitar estados inconsistentes
    btn_cancelar = ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700))

    dlg = ft.AlertDialog(
        title=ft.Text(f"Elige {titulo_grupo} para: {item['nombre']}", color=ft.Colors.BLACK),
        content=ft.Column(
            [
                ft.Text(f"Cantidad a elegir: {cantidad_total}", color=ft.Colors.BLACK),
                remaining_text,
                ft.Divider(),
                ft.Column(controls_list, height=300, scroll="auto")
            ],
            width=400, height=400, tight=True
        ),
        actions=[btn_cancelar, btn_confirmar],
        modal=True
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

def _mostrar_dialogo_guisos(page, items_to_configure, current_index, guisos_disponibles, show_snackbar_func, final_callback):
    if current_index >= len(items_to_configure):
        final_callback()
        return

    item = items_to_configure[current_index]
    piezas_por_orden = item.get("piezas", 1)
    cantidad_total = item["cantidad"] * piezas_por_orden
    
    counters = {guiso: 0 for guiso in guisos_disponibles}
    remaining_text = ft.Text(f"Faltan por elegir: {cantidad_total}", color=ft.Colors.BLACK)

    def update_remaining():
        selected = sum(counters.values())
        rem = cantidad_total - selected
        remaining_text.value = f"Faltan por elegir: {rem}"
        remaining_text.color = ft.Colors.RED if rem > 0 else ft.Colors.GREEN
        btn_confirmar.disabled = (rem != 0)
        page.update()

    def create_guiso_row(guiso):
        count_text = ft.Text("0", width=20, text_align="center", color=ft.Colors.BLACK)
        
        def change_count(e, delta):
            current_selected = sum(counters.values())
            if delta > 0 and current_selected >= cantidad_total: return 
            if counters[guiso] + delta < 0: return
            counters[guiso] += delta
            count_text.value = str(counters[guiso])
            update_remaining()

        return ft.Row([
            ft.Text(guiso, expand=True, color=ft.Colors.BLACK),
            ft.IconButton(ft.Icons.REMOVE, icon_color=ft.Colors.BLACK, on_click=lambda e: change_count(e, -1)),
            count_text,
            ft.IconButton(ft.Icons.ADD, icon_color=ft.Colors.BLACK, on_click=lambda e: change_count(e, 1)),
        ])

    guiso_controls = [create_guiso_row(g) for g in guisos_disponibles]

    def confirmar_seleccion(e):
        detalles_list = []
        for g, c in counters.items():
            if c > 0: detalles_list.append(f"{g} x{c}")
        item["details"] = ", ".join(detalles_list)
        dlg.open = False
        page.update()
        _mostrar_dialogo_guisos(page, items_to_configure, current_index + 1, guisos_disponibles, show_snackbar_func, final_callback)
    
    def cancelar_seleccion(e):
        dlg.open = False
        page.update()

    btn_confirmar = ft.Button(content=ft.Text("Confirmar"), on_click=confirmar_seleccion, disabled=True)
    btn_cancelar = ft.TextButton("Cancelar", on_click=cancelar_seleccion, style=ft.ButtonStyle(color=ft.Colors.BROWN_700))

    dlg = ft.AlertDialog(
        title=ft.Text(f"Elige guisos para: {item['nombre']}", color=ft.Colors.BLACK),
        content=ft.Column(
            [
                ft.Text(f"Cantidad a elegir: {cantidad_total} (Ordenes: {item['cantidad']} x {piezas_por_orden} pz)", color=ft.Colors.BLACK),
                remaining_text,
                ft.Divider(),
                ft.Column(guiso_controls, height=300, scroll="auto")
            ],
            width=400, height=400, tight=True
        ),
        actions=[btn_cancelar, btn_confirmar],
        modal=True
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

def _mostrar_dialogo_salsas(page, items_to_configure, current_index, salsas_disponibles, show_snackbar_func, final_callback):
    if current_index >= len(items_to_configure):
        final_callback()
        return

    item = items_to_configure[current_index]
    piezas_por_orden = item.get("piezas", 1)
    cantidad_total = item["cantidad"] * piezas_por_orden
    
    counters = {salsa: 0 for salsa in salsas_disponibles}
    remaining_text = ft.Text(f"Faltan por elegir: {cantidad_total}", color=ft.Colors.BLACK)

    def update_remaining():
        selected = sum(counters.values())
        rem = cantidad_total - selected
        remaining_text.value = f"Faltan por elegir: {rem}"
        remaining_text.color = ft.Colors.RED if rem > 0 else ft.Colors.GREEN
        btn_confirmar.disabled = (rem != 0)
        page.update()

    def create_salsa_row(salsa):
        count_text = ft.Text("0", width=20, text_align="center", color=ft.Colors.BLACK)
        def change_count(e, delta):
            if delta > 0 and sum(counters.values()) >= cantidad_total: return 
            if counters[salsa] + delta < 0: return
            counters[salsa] += delta
            count_text.value = str(counters[salsa])
            update_remaining()
        return ft.Row([
            ft.Text(salsa, expand=True, color=ft.Colors.BLACK),
            ft.IconButton(ft.Icons.REMOVE, icon_color=ft.Colors.BLACK, on_click=lambda e: change_count(e, -1)),
            count_text,
            ft.IconButton(ft.Icons.ADD, icon_color=ft.Colors.BLACK, on_click=lambda e: change_count(e, 1)),
        ])

    salsa_controls = [create_salsa_row(s) for s in salsas_disponibles]

    def confirmar_seleccion(e):
        detalles_list = []
        for s, c in counters.items():
            if c > 0: detalles_list.append(f"{s} x{c}")
        salsa_str = "Salsas: " + ", ".join(detalles_list)
        if item.get("details"):
            item["details"] = f"{item['details']} | {salsa_str}"
        else:
            item["details"] = salsa_str
        dlg.open = False
        page.update()
        _mostrar_dialogo_salsas(page, items_to_configure, current_index + 1, salsas_disponibles, show_snackbar_func, final_callback)
    
    btn_confirmar = ft.Button(content=ft.Text("Confirmar"), on_click=confirmar_seleccion, disabled=True)
    btn_cancelar = ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700))

    dlg = ft.AlertDialog(
        title=ft.Text(f"Elige salsas para: {item['nombre']}", color=ft.Colors.BLACK),
        content=ft.Column(
            [
                ft.Text(f"Cantidad a elegir: {cantidad_total} (Ordenes: {item['cantidad']} x {piezas_por_orden} pz)", color=ft.Colors.BLACK), 
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
