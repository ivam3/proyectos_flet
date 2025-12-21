# app/src/views/menu.py
import flet as ft
from database import obtener_menu, get_configuracion

def cargar_menu(page: ft.Page):
    """Carga y muestra los platillos del menú con una barra de búsqueda."""
    
    user_cart = page.session.cart
    
    # Contenedor principal que alternará entre el Grid y el Mensaje de Vacío
    main_content = ft.Container(expand=True)

    def update_menu_list(search_term=""):
        """Limpia y recarga la lista de platillos según el término de búsqueda."""
        platillos = obtener_menu(solo_activos=True, search_term=search_term)

        # Ordenar: primero los que tienen descuento (descendente), luego el resto
        platillos.sort(key=lambda x: x[6] if x[6] else 0, reverse=True)

        if not platillos:
            config = get_configuracion()
            horario = config['horario'] if config else "No disponible"
            
            main_content.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINED, size=40, color=ft.Colors.GREY_500),
                        ft.Text("Sin servicio", weight="bold"),
                        ft.Text(horario, size=12, text_align="center"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True
            )
        else:
            menu_grid = ft.GridView(
                expand=True,
                runs_count=2,          # Dos columnas
                max_extent=230,        # Ancho máximo aproximado de cada item
                child_aspect_ratio=0.9, # Relación de aspecto (Alto vs Ancho) para que quepa la info
                spacing=10,
                run_spacing=10,
                padding=10
            )

            for platillo in platillos:
                pid, nombre, descripcion, precio, imagen, _, descuento, is_configurable, is_configurable_salsa, piezas = platillo
                
                precio_final = precio
                if descuento > 0:
                    precio_final = precio * (1 - descuento / 100)

                def _on_add_clicked(e, item_id=pid, name=nombre, price=precio_final, img=imagen, is_conf=is_configurable, is_conf_salsa=is_configurable_salsa, pz=piezas):
                    user_cart.add_item(item_id, name, price, img, is_configurable=is_conf, is_configurable_salsa=is_conf_salsa, piezas=pz)
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"'{name}' agregado al carrito"),
                        bgcolor=ft.Colors.GREEN_700,
                    )
                    page.snack_bar.open = True
                    page.update()
                
                # Construir display de precio
                if descuento > 0:
                    precio_display = ft.Column([
                        ft.Text(f"${precio:.0f}", size=12, color=ft.Colors.GREY, decoration=ft.TextDecoration.LINE_THROUGH),
                        ft.Text(f"${precio_final:.0f}", weight="bold", size=15, color=ft.Colors.RED_700)
                    ], spacing=0)
                else:
                    precio_display = ft.Text(f"${precio:.0f}", weight="bold", size=15, color=ft.Colors.ORANGE_800)

                # Tarjeta de platillo optimizada para Grid
                menu_grid.controls.append(
                    ft.Card(
                        elevation=2,
                        content=ft.Container(
                            padding=10,
                            content=ft.Column(
                                spacing=5,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    # Imagen
                                    ft.Container(
                                        content=ft.Stack([
                                            ft.Image(
                                                src=f"/{imagen}" if imagen else "https://via.placeholder.com/150",
                                                fit="cover",
                                                border_radius=8,
                                                width=1000, # Fill width
                                                height=100
                                            ),
                                            ft.Container(
                                                content=ft.Text(f"-{descuento:.0f}%", color="white", size=10, weight="bold"),
                                                bgcolor=ft.Colors.RED,
                                                padding=ft.Padding.all(4),
                                                border_radius=ft.BorderRadius.only(top_left=8, bottom_right=8),
                                                visible=descuento > 0
                                            )
                                        ]),
                                        height=100, # Altura fija para la imagen
                                        border_radius=8,
                                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                    ),
                                    # Info
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(nombre, weight=ft.FontWeight.BOLD, size=13, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                            ft.Text(descripcion or "", size=9, color=ft.Colors.GREY_700, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                                        ]
                                    ),
                                    # Precio y Botón
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            precio_display,
                                            ft.IconButton(
                                                icon=ft.Icons.ADD_SHOPPING_CART,
                                                icon_size=20,
                                                style=ft.ButtonStyle(padding=5),
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

    def handle_search_change(e):
        update_menu_list(e.control.value)

    search_bar = ft.TextField(
        label="Buscar...",
        prefix_icon=ft.Icons.SEARCH,
        on_change=handle_search_change,
        border_radius=20,
        height=40,
        text_size=14,
        content_padding=10,
        filled=True,
    )

    # Carga inicial del menú
    update_menu_list()

    return ft.Column(
        expand=True,
        controls=[
            ft.Container(
                content=search_bar,
                padding=ft.Padding.only(left=15, right=15, top=10, bottom=5)
            ),
            main_content
        ]
    )
