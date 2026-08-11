# =============================================================================
# SIH-DNK Mockup — frontend (placeholder)
# =============================================================================
# Minimal static placeholder served by nginx:alpine.
# Host port 8005 -> container port 80 (see root docker-compose.yml / COMPONENTS.md).
# =============================================================================
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
