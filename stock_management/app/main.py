import flet as ft
import os
import sys

try:
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    if APP_ROOT not in sys.path:
        sys.path.insert(0, APP_ROOT)
    if os.getcwd() not in sys.path:
        sys.path.insert(1, os.getcwd())
except: pass

from config import APP_NAME
from api_client import APIClient

def main(page: ft.Page):
    # Paleta de Colores Basada en el Logo
    THEME_COLOR = ft.Colors.ORANGE_700
    BG_COLOR = ft.Colors.GREY_100
    ACCENT_COLOR = ft.Colors.BLACK

    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = BG_COLOR
    
    # Configuración de Tema
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=THEME_COLOR,
            secondary=ACCENT_COLOR,
        )
    )

    api = APIClient()
    page.session.api = api

    # Contenedor principal con imagen de fondo
    # Usamos un Stack para poner la imagen detrás del contenido
    content_area = ft.Container(expand=True)
    
    main_stack = ft.Stack(
        [
            # Imagen de Fondo con Opacidad
            ft.Image(
                src="stockman.webp",
                width=float("inf"),
                height=float("inf"),
                fit="cover",
                opacity=0.08, # Muy sutil para no distraer
            ),
            content_area
        ],
        expand=True
    )

    main_container = ft.Container(content=main_stack, expand=True, padding=15)

    def update_responsive_layout(e=None):
        # Aumentamos el ancho máximo para aprovechar mejor pantallas grandes
        MAX_CONTENT_WIDTH = 1600 
        if page.width > MAX_CONTENT_WIDTH:
            side_padding = (page.width - MAX_CONTENT_WIDTH) / 2
            main_container.padding = ft.Padding.only(left=side_padding, right=side_padding, top=10, bottom=10)
        else:
            # Reducimos la sangría lateral mínima a 5px para móviles/tablets
            main_container.padding = ft.Padding.only(left=5, right=5, top=10, bottom=10)
        page.update()

    page.on_resized = update_responsive_layout

    def global_file_picker_handler(e):
        if not e.files: return
        ctx = getattr(page.session, "file_picker_ctx", None)
        if not ctx: return
        try:
            # Soporte para múltiples archivos
            if ctx.get("multi", False):
                callback_files = e.files
            else:
                callback_files = e.files[0]
                
            import inspect
            if inspect.iscoroutinefunction(ctx["callback"]):
                page.run_task(ctx["callback"], callback_files)
            else:
                ctx["callback"](callback_files)
        except Exception as ex:
            print(f"Error en file_picker: {ex}")

    global_file_picker = ft.FilePicker()
    global_file_picker.on_result = global_file_picker_handler
    export_file_picker = ft.FilePicker()
    
    # Envoltorios de seguridad para evitar "Unknown control: FilePicker" (franja roja)
    fp_container = ft.Container(content=global_file_picker, width=1, height=1, opacity=0)
    ex_container = ft.Container(content=export_file_picker, width=1, height=1, opacity=0)

    page.overlay.append(fp_container)
    page.overlay.append(ex_container)
    
    page.session.file_picker = global_file_picker
    page.session.export_picker = export_file_picker

    def change_tab(e):
        idx = e.control.selected_index if hasattr(e, "control") else e
        nav.selected_index = idx
        if idx == 0:
            from views.inventory_view import inventory_view
            content_area.content = inventory_view(page)
        elif idx == 1:
            from views.register_view import register_view
            content_area.content = register_view(page)
        elif idx == 2:
            from views.history_view import history_view
            content_area.content = history_view(page)
        page.update()

    page.session.switch_tab = change_tab

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label="Inventario"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.Icons.ADD_CIRCLE, label="Registro"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, selected_icon=ft.Icons.HISTORY, label="Historial"),
        ],
        on_change=change_tab,
        bgcolor=ft.Colors.WHITE,
        indicator_color=THEME_COLOR,
    )

    app_bar = ft.AppBar(
        leading=ft.Container(content=ft.Image(src="logo.webp", fit="contain"), padding=5),
        leading_width=60,
        title=ft.Text(APP_NAME, color=ft.Colors.WHITE, weight="bold", size=22),
        bgcolor=ACCENT_COLOR,
        center_title=False,
    )

    from views.inventory_view import inventory_view
    content_area.content = inventory_view(page)
    
    update_responsive_layout()

    page.add(
        ft.SafeArea(
            ft.Column(
                [
                    app_bar,
                    main_container,
                    nav
                ],
                expand=True,
                spacing=0
            ),
            expand=True
        )
    )

if __name__ == "__main__":
    assets_path = os.path.join(os.path.dirname(__file__), "assets")
    ft.run(main, view=ft.AppView.FLET_APP, web_renderer="canvaskit", assets_dir=assets_path)
