FROM nginx:alpine

# Instalar gettext para envsubst
RUN apk add --no-cache gettext

# Copiar el build del frontend
COPY build/web /usr/share/nginx/html

# Copiar la configuración como plantilla
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Comando para inyectar el PORT y arrancar
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
