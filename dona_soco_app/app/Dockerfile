FROM nginx:alpine

# Copiar el build del frontend
COPY build/web /usr/share/nginx/html

# Copiar la configuración
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Nginx Alpine ya incluye soporte para plantillas en /etc/nginx/templates/*.template
# Automáticamente procesará el puerto ${PORT} si existe la variable de entorno
ENV PORT=8080

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
