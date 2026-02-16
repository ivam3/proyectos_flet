FROM nginx:alpine

# Copiar el build del frontend
COPY build/web /usr/share/nginx/html

# Copiar la configuración de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Instalar 'gettext' para usar 'envsubst' y procesar el puerto dinámico
RUN apk add --no-cache gettext

# Comando para inyectar el puerto de Railway en la config y arrancar Nginx
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
