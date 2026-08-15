import flet as ft
import asyncio

# Mantiene la referencia al handler suscrito por sesión para evitar acumular
# closures que apuntan a vistas destruidas al recrearlas (navegación).
_subscribed_handlers = {}  # session_id -> view_key

def init_pubsub(page: ft.Page):
    """Devuelve el canal PubSub de la sesión ACTUAL.
    
    Cada sesión de navegador tiene su propio PubSubClient con su session_id.
    No se cachea globalmente: cachear el de la primera sesión rompía el
    aislamiento entre clientes web (todos suscribían bajo el mismo session_id).
    """
    return page.pubsub

def subscribe_view_handler(page: ft.Page, view_key: str, handler):
    """Suscribe un handler de vista reemplazando el anterior de la misma sesión.

    Evita acumulación: si la vista se recrea (navegación /admin, /seguimiento),
    se desuscribe el handler previo antes de suscribir el nuevo, de modo que
    nunca se apile más de un handler por sesión.
    """
    session_id = str(page.session.id)
    pubsub = init_pubsub(page)
    if session_id in _subscribed_handlers:
        try:
            pubsub.unsubscribe()
        except Exception:
            pass
    _subscribed_handlers[session_id] = view_key
    pubsub.subscribe(handler)

def show_notification(page: ft.Page, text: str, color=ft.Colors.GREEN):
    """Muestra un SnackBar de forma robusta."""
    snack = ft.SnackBar(
        content=ft.Text(text, color=ft.Colors.WHITE),
        bgcolor=color,
        action="Cerrar",
        duration=3000
    )
    snack.open = True
    page.overlay.append(snack)
    page.update()

def play_notification_sound(page: ft.Page):
    """Reproduce sonido inyectando un componente de audio HTML temporal."""
    try:
        # Truco: Insertamos un Markdown con HTML habilitado que contiene el tag audio
        # El random query param evita caché
        sound_html = ft.Markdown(
            value='<audio src="notify.mp3" autoplay style="display:none;"></audio>',
            extension_set="html"
        )
        
        # Agregamos al overlay (invisible)
        page.overlay.append(sound_html)
        page.update()
        
        # Función para limpiar el elemento después de un tiempo
        # Se ejecuta en el event loop de la página (no en un thread), porque
        # page.update()/overlay no son seguros desde hilos de fondo.
        async def cleanup():
            await asyncio.sleep(3)  # Duración del audio + margen
            try:
                if sound_html in page.overlay:
                    page.overlay.remove(sound_html)
                    page.update()
            except Exception:
                pass

        # Programar limpieza en el event loop de la página
        page.run_task(cleanup)
        
    except Exception as e:
        print(f"Error playing sound (HTML hack): {e}")
