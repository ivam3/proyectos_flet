import http.server
import socketserver
import os
import sys

# Configuración
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
DIRECTORY = "build/web"

class SPARequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Intentar obtener el archivo solicitado
        path = self.translate_path(self.path)
        
        # Si el archivo no existe y no tiene extensión (es una ruta de la app)
        # o si simplemente no existe, servimos index.html
        if not os.path.exists(path) or os.path.isdir(path):
            print(f"DEBUG: Ruta '{self.path}' no encontrada, sirviendo index.html")
            self.path = "/index.html"
            
        return super().do_GET()

# Asegurar que el directorio existe antes de empezar
if not os.path.exists(DIRECTORY):
    print(f"ERROR: El directorio {DIRECTORY} no existe. Asegúrate de ejecutar 'flet build web' primero.")
    sys.exit(1)

print(f"Servidor SPA iniciado en el puerto {PORT} sirviendo {DIRECTORY}")
with socketserver.TCPServer(("", PORT), SPARequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
