# app/src/app_views/menu.py
import flet as ft
from database import obtener_menu, get_configuracion

def cargar_menu(page: ft.Page):
    """Carga y muestra los platillos del menú con una barra de búsqueda."""
    
    user_cart = page.session.cart
    main_content = ft.Container(expand=True)

    def update_menu_list(search_term=""):
        platillos = obtener_menu(solo_activos=True, search_term=search_term)
        platillos.sort(key=lambda x: x.get('descuento', 0) or 0, reverse=True)

        # Responsive: Ratio y Columnas
        if page.width < 600:
            current_ratio = 0.65  # Mucho más alto para móviles (evita encimado radicalmente)
            columns = 2
            img_height = 80       # Imagen más pequeña en móvil
        else:
            current_ratio = 0.8   # Ajustado para evitar superposición en Web/PC
            columns = 0           # Auto
            img_height = 110      # Imagen normal en web

        if not platillos:
            config = get_configuracion()
            horario = config['horario'] if config else "No disponible"
            main_content.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO_OUTLINED, size=40, color=ft.Colors.GREY_500),
                    ft.Text("Sin servicio", weight="bold", color=ft.Colors.BLACK),
                    ft.Text(horario, size=12, text_align="center", color=ft.Colors.BLACK),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0), expand=True
            )
        else:
            menu_grid = ft.GridView(
                expand=True,
                runs_count=columns,
                max_extent=250,
                child_aspect_ratio=current_ratio,
                spacing=10, run_spacing=10, padding=10
            )

            for platillo in platillos:
                pid = platillo['id']
                nombre = platillo['nombre']
                descripcion = platillo.get('descripcion', "")
                precio = platillo['precio']
                imagen = platillo.get('imagen')
                descuento = platillo.get('descuento', 0)
                is_configurable = platillo.get('is_configurable', 0)
                is_configurable_salsa = platillo.get('is_configurable_salsa', 0)
                piezas = platillo.get('piezas', 1)
                grupos_opciones_ids = platillo.get('grupos_opciones_ids', "[]")

                precio_final = precio * (1 - descuento / 100) if descuento > 0 else precio

                async def _on_add_clicked(e, item_id=pid, name=nombre, price=precio_final, img=imagen, is_conf=is_configurable, is_conf_salsa=is_configurable_salsa, pz=piezas, g_ids=grupos_opciones_ids):
                    user_cart.add_item(item_id, name, price, img, is_configurable=is_conf, is_configurable_salsa=is_conf_salsa, piezas=pz, grupos_opciones_ids=g_ids)
                    await page.push_route("/carrito") # Redirección directa al carrito vía ruteo unificado
                    page.update()

                p_display = ft.Column([
                    ft.Text(f"${precio:.0f}", size=10, color=ft.Colors.GREY, 
                            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH), 
                            visible=descuento > 0),
                    ft.Text(f"${precio_final:.0f}", weight="bold", size=14, color=ft.Colors.RED_700 if descuento > 0 else ft.Colors.ORANGE_800)
                ], spacing=0)

                                # Lógica para determinar el origen de la imagen
                                if imagen:
                                    if imagen.startswith(("http://", "https://")):
                                        img_src = imagen
                                    elif "." in imagen and not imagen.startswith("/"):
                                        # Si es una imagen subida por el API (nombre.jpg)
                                        # Opcional: Podrías usar API_URL directamente aquí si quieres forzar carga externa
                                        from config import API_URL
                                        img_src = f"{API_URL}/static/uploads/{imagen}"
                                    else:
                                        img_src = f"/{imagen}"
                                else:
                                    img_src = "/icon.png"
                
                                menu_grid.controls.append(
                                    ft.Card(
                                        elevation=3,
                                        content=ft.Container(
                                            padding=8,
                                            content=ft.Column(
                                                alignment=ft.MainAxisAlignment.START,
                                                spacing=4,
                                                controls=[
                                                    ft.Container(
                                                        content=ft.Stack([
                                                            ft.Image(src=img_src, fit="cover", width=1000, height=img_height),
                                                            ft.Container(
                                                                content=ft.Text(f"-{descuento:.0f}%", color="white", size=9, weight="bold"),                                                bgcolor=ft.Colors.RED, padding=4, border_radius=ft.BorderRadius.only(top_left=8, bottom_right=8),
                                                visible=descuento > 0
                                            )
                                        ]),
                                        height=img_height, border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                    ),
                                    ft.Text(nombre, weight=ft.FontWeight.BOLD, size=13, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.BLACK),
                                    ft.Text(descripcion or "", size=11, color=ft.Colors.GREY_800, max_lines=10, overflow=ft.TextOverflow.FADE),
                                    ft.Container(expand=True),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            p_display,
                                            ft.IconButton(
                                                icon=ft.Icons.ADD_SHOPPING_CART, icon_size=20,
                                                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, shape=ft.CircleBorder()),
                                                on_click=_on_add_clicked
                                            )
                                        ]
                                    )
                                ]
                            ),
                        )
                    )
                )
            main_content.content = menu_grid
        page.update()

    def on_page_resize(e):
        update_menu_list(search_bar.value)

    page.on_resized = on_page_resize

    def handle_search_change(e):
        update_menu_list(e.control.value)

    search_bar = ft.TextField(
        label="Buscar...", prefix_icon=ft.Icons.SEARCH,
        on_change=handle_search_change, border_radius=20, height=40,
        text_size=14, content_padding=10, filled=True,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.GREY_700)
    )

    update_menu_list()

    return ft.Column(
        expand=True,
        controls=[
            ft.Container(content=search_bar, padding=ft.Padding.only(left=15, right=15, top=10, bottom=5)),
            main_content
        ]
    )
