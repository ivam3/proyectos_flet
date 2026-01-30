import flet as ft

# Mantiene una referencia global al canal PubSub
pubsub_channel = None

def init_pubsub(page: ft.Page):
    """Inicializa el canal PubSub global."""
    global pubsub_channel
    if not pubsub_channel:
        pubsub_channel = page.pubsub
    return pubsub_channel

import time
import threading

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
        def cleanup():
            time.sleep(3) # Duración del audio + margen
            try:
                if sound_html in page.overlay:
                    page.overlay.remove(sound_html)
                    page.update()
            except:
                pass

        # Ejecutar limpieza en segundo plano
        threading.Thread(target=cleanup, daemon=True).start()
        
    except Exception as e:
        print(f"Error playing sound (HTML hack): {e}")
