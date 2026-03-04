# PROD-006: Nginx Reverse Proxy + Docker Compose

## Status: Done

## Summary
Production-ready Nginx config with SSL, WebSocket upgrade, static file serving, and Docker Compose with 6 services.

## Implementation
- Nginx: reverse proxy to Django/Daphne, SSL termination, WebSocket upgrade for `/ws/`
- Static/media files served directly by Nginx with long cache headers
- Gzip compression for text assets
- Content Security Policy headers
- Docker Compose services: postgres, redis, web (Django/Daphne), celery-worker, celery-beat, nginx
- SSL certificate generation scripts for both Linux and Windows
- Health check on each Docker service

## Files Modified/Created
- `deployment/nginx.conf` — full Nginx configuration
- `deployment/generate-ssl.sh` — self-signed SSL cert generation (Linux/macOS)
- `deployment/generate-ssl.ps1` — self-signed SSL cert generation (Windows)
- `docker-compose.yml` — 6-service production stack
- `.gitignore` — added SSL cert paths and Docker volumes

## Configuration
- `NGINX_HOST` — server name (default: `localhost`)
- SSL certs expected at `deployment/ssl/cert.pem` and `deployment/ssl/key.pem`
- PostgreSQL, Redis connection strings configured via environment in docker-compose

## Verification
- Run `docker-compose up -d` and verify all 6 services start healthy
- Access `https://localhost` and verify SSL, static files, and WebSocket upgrade
- Run `deployment/generate-ssl.sh` or `.ps1` and verify certs are created
