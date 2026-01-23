import flet as ft

# Mantiene una referencia global al canal PubSub
pubsub_channel = None

def init_pubsub(page: ft.Page):
    """Inicializa el canal PubSub global."""
    global pubsub_channel
    if not pubsub_channel:
        pubsub_channel = page.pubsub
    return pubsub_channel
