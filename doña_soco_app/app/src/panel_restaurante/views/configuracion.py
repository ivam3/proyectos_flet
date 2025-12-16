import flet as ft
from database import get_configuracion, update_configuracion

class ConfiguracionView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/admin/configuracion", padding=20)
        self._page = page
        
        # --- Controles de la UI ---
        self.horario_field = ft.TextField(label="Horario de Atención", border_radius=10)
        self.codigos_postales_field = ft.TextField(
            label="Códigos Postales Permitidos",
            hint_text="Separados por comas, ej: 12345,54321",
            border_radius=10
        )
        self.guardar_button = ft.Button(
            content=ft.Text("Guardar Cambios"),
            on_click=self.guardar_cambios,
            icon="save_outlined",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=15
            )
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Configuración de la Plataforma", size=24, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=20),
                        self.horario_field,
                        self.codigos_postales_field,
                        ft.Container(height=10), # Espaciador
                        self.guardar_button,
                    ],
                    spacing=15,
                ),
                padding=20,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=15,
            )
        ]
        
        self.cargar_datos_actuales()

    def cargar_datos_actuales(self):
        """Carga la configuración actual desde la base de datos y la muestra en los campos."""
        config = get_configuracion()
        if config:
            self.horario_field.value = config['horario']
            self.codigos_postales_field.value = config['codigos_postales']
            self._page.update()

    def guardar_cambios(self, e):
        """Guarda los nuevos valores en la base de datos y muestra una notificación."""
        horario = self.horario_field.value.strip()
        codigos = self.codigos_postales_field.value.strip()
        
        if not horario or not codigos:
            self.mostrar_notificacion("Ambos campos son obligatorios.", ft.Colors.ERROR)
            return

        if update_configuracion(horario, codigos):
            self.mostrar_notificacion("Configuración guardada exitosamente.", ft.Colors.GREEN_700)
        else:
            self.mostrar_notificacion("Error al guardar la configuración.", ft.Colors.ERROR)

    def mostrar_notificacion(self, mensaje, color):
        """Muestra un SnackBar con un mensaje."""
        self._page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=color,
            duration=4000
        )
        self._page.snack_bar.open = True
        self._page.update()

# Para probar esta vista de forma aislada
if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Prueba de Configuración"
        page.window_width = 500
        page.window_height = 600
        
        # Se necesita inicializar la DB para la prueba
        from database import crear_tablas
        crear_tablas()
        
        config_view = ConfiguracionView(page)
        page.add(config_view)

    ft.run(target=main)
