import flet as ft
import os
import re
import markdown
from xhtml2pdf import pisa

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MDS_PATH = os.path.join(APP_DIR, "storage", "mds")
PDFS_PATH = os.path.join(APP_DIR, "storage", "pdfs")


def main(page: ft.Page):
    # ---------------- PAGE ----------------
    page.title = "Ivam3byCinderella - Markdown Viewer"
    page.padding = 0
    page.expand = True
    page.theme_mode = ft.ThemeMode.DARK

    # Diálogo persistente para notificaciones (Solución definitiva para invisibilidad)
    notification_dlg = ft.AlertDialog(
        title=ft.Text(""),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Cerrar", on_click=lambda _: setattr(notification_dlg, "open", False) or page.update()),
        ],
    )
    page.overlay.append(notification_dlg)

    all_md_files = []
    original_md_content = ""
    current_file_name = ""

    # ---------------- REFS ----------------
    files_list_ref = ft.Ref[ft.Column]()
    md_view_ref = ft.Ref[ft.Markdown]()
    search_text_ref = ft.Ref[ft.TextField]()
    status_text_ref = ft.Ref[ft.Text]()
    left_panel_ref = ft.Ref[ft.Container]()

    # ---------------- DATA ----------------
    def load_markdown_files():
        all_md_files.clear()
        if not os.path.exists(MDS_PATH):
            os.makedirs(MDS_PATH, exist_ok=True)
        for root, _, files in os.walk(MDS_PATH):
            for f in files:
                if f.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, f), MDS_PATH)
                    all_md_files.append(rel.replace("\\", "/"))
        all_md_files.sort()

    # ---------------- PDF CONVERSION ----------------
    def convert_to_pdf(e):
        def notify(title, message):
            notification_dlg.title.value = title
            notification_dlg.content.value = message
            notification_dlg.open = True
            page.update()

        if not original_md_content:
            notify("Aviso", "No hay contenido para convertir")
            return

        try:
            notify("Procesando", "Generando archivo PDF...")
            
            # Crear HTML simple desde Markdown
            html_body = markdown.markdown(original_md_content, extensions=['extra', 'codehilite'])
            html_content = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: sans-serif; padding: 20px; }}
                    pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                    code {{ font-family: monospace; }}
                </style>
            </head>
            <body>
                {html_body}
            </body>
            </html>
            """
            
            # Definir nombre de salida
            pdf_base_name = current_file_name.replace(".md", ".pdf")
            pdf_file_path = os.path.join(PDFS_PATH, pdf_base_name)
            
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)
            
            # Convertir a PDF
            with open(pdf_file_path, "wb") as f:
                pisa_status = pisa.CreatePDF(html_content, dest=f)
            
            if not pisa_status.err:
                notify("¡Éxito!", f"PDF guardado en:\nsrc/storage/pdfs/{pdf_base_name}")
            else:
                notify("Error", "Error al generar el PDF")
                
        except Exception as ex:
            notify("Error Crítico", f"{str(ex)}")

    # ---------------- FILE OPEN ----------------
    def open_markdown_file(e):
        nonlocal original_md_content, current_file_name
        current_file_name = e.control.data
        file_path = os.path.join(MDS_PATH, current_file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_md_content = f.read()

            if search_text_ref.current:
                search_text_ref.current.value = ""

            md_view_ref.current.value = original_md_content
            md_view_ref.current.update()

            if page.width < 700:
                page.drawer.open = False
                page.update()

        except Exception as ex:
            md_view_ref.current.value = f"Error:\n{ex}"
            md_view_ref.current.update()

    # ---------------- FILE LIST ----------------
    def update_file_list(term=""):
        files_list_ref.current.controls.clear()

        filtered = [
            f for f in all_md_files
            if term.lower() in f.lower()
        ]

        for f in filtered:
            files_list_ref.current.controls.append(
                ft.ListTile(
                    title=ft.Text(f, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    leading=ft.Icon(ft.Icons.DESCRIPTION),
                    data=f,
                    on_click=open_markdown_file,
                    height=40,
                )
            )

        files_list_ref.current.update()
        status_text_ref.current.value = f"{len(filtered)} archivos"
        status_text_ref.current.update()

    # ---------------- SEARCH ----------------
    def search_files(e):
        update_file_list(e.control.value)

    def search_in_file(e):
        term = e.control.value
        if not term:
            md_view_ref.current.value = original_md_content
        else:
            matches = len(re.findall(re.escape(term), original_md_content, re.I))
            highlighted = re.sub(
                f"({re.escape(term)})",
                r"<mark>\1</mark>",
                original_md_content,
                flags=re.IGNORECASE,
            )
            md_view_ref.current.value = f"**Coincidencias:** {matches}\n\n{highlighted}"
        md_view_ref.current.update()

    # ---------------- THEME ----------------
    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        page.update()

    # ---------------- SIDEBAR ----------------
    def build_sidebar():
        return ft.Container(
            ref=left_panel_ref,
            width=260,
            padding=10,
            bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Archivos", weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                icon=ft.Icons.DARK_MODE,
                                on_click=toggle_theme,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),

                    ft.TextField(
                        label="Buscar archivo",
                        prefix_icon=ft.Icons.SEARCH,
                        on_change=search_files,
                        border_radius=20,
                    ),

                    ft.Text(ref=status_text_ref, size=10),

                    ft.Column(
                        ref=files_list_ref,
                        expand=True,
                        scroll=ft.ScrollMode.ADAPTIVE,
                    ),
                ],
                expand=True,
                spacing=8,
            ),
        )

    sidebar = build_sidebar()

    # ---------------- DRAWER (MOBILE) ----------------
    page.drawer = ft.NavigationDrawer(
        controls=[sidebar],
    )

    # ---------------- CONTENT ----------------
    content = ft.Column(
        [
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.MENU,
                        on_click=lambda _: setattr(page.drawer, "open", True),
                    ),
                    ft.TextField(
                        ref=search_text_ref,
                        label="Buscar en el texto",
                        prefix_icon=ft.Icons.FIND_IN_PAGE,
                        on_change=search_in_file,
                        expand=True,
                        border_radius=20,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PICTURE_AS_PDF,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Exportar a PDF",
                        on_click=convert_to_pdf,
                    ),
                ],
            ),

            ft.Container(
                expand=True,
                padding=10,
                content=ft.Column(
                    [
                        ft.Markdown(
                            ref=md_view_ref,
                            value="**Selecciona un archivo**",
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            on_tap_link=lambda e: page.launch_url(e.data),
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True,
                ),
            ),
        ],
        expand=True,
    )

    # ---------------- RESPONSIVE ----------------
    def build_layout():
        page.controls.clear()

        if page.width >= 700:
            page.add(
                ft.Row(
                    [sidebar, content],
                    expand=True,
                )
            )
        else:
            page.add(content)

        page.update()

    page.on_resize = lambda e: build_layout()

    # ---------------- START ----------------
    build_layout()
    load_markdown_files()
    update_file_list()


if __name__ == "__main__":
    # En Termux puro, usar rutas relativas para evitar PermissionError del motor Starlette/Flet
    assets_path = "assets" if os.path.exists(os.path.join(APP_DIR, "assets")) else None

    ft.run(
        main,
        assets_dir=assets_path,
        web_renderer=ft.WebRenderer.CANVAS_KIT,
    )
