# 🚀 Guía de Ejecución en Producción - Legajo Digital DIRESA

## Opción Recomendada: Waitress WSGI

Waitress es un servidor WSGI puro de Python que es **mucho más seguro y estable que Flask** para producción.

### Uso Básico

```bash
# Ejecutar con puerto por defecto (5001)
python run_production.py

# Ejecutar con puerto personalizado
python run_production.py 8080

# Ejecutar con host y puerto personalizados
python run_production.py 192.168.1.100 8080
```

### En Windows (Batch)

Hemos creado `run_production.bat` que automatiza todo:

```batch
# Ejecutar con configuración por defecto
run_production.bat

# Ejecutar con puerto personalizado
run_production.bat 8080

# Ejecutar con host y puerto personalizados
run_production.bat 192.168.1.100 8080
```

### Configuración Recomendada para Producción

En `run_production.py`, Waitress se configura con:

- **Threads**: 8 (ajusta según la carga esperada)
- **Channel Timeout**: 300 segundos (5 minutos)
- **Host**: 0.0.0.0 (escucha en todas las interfaces)

### Con Nginx (Proxy Reverso Recomendado)

Para producción real, es **recomendado usar Nginx como proxy reverso** para:

1. ✅ Manejar SSL/TLS
2. ✅ Balanceo de carga
3. ✅ Cacheo
4. ✅ Compresión
5. ✅ Seguridad adicional

**Ejemplo de configuración Nginx:**

```nginx
upstream legajo_app {
    server localhost:5001;
}

server {
    listen 80;
    server_name tu-dominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    
    # Certificados SSL
    ssl_certificate /ruta/a/tu/certificado.crt;
    ssl_certificate_key /ruta/a/tu/certificado.key;
    
    # Configuraciones SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://legajo_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Diferencias: Flask Development vs Waitress

| Aspecto | Flask Dev | Waitress |
|---------|-----------|----------|
| **Estabilidad** | ❌ Inestable | ✅ Muy Estable |
| **Concurrencia** | ❌ Single-threaded | ✅ Multi-threaded |
| **Seguridad** | ⚠️ Solo dev | ✅ Producción |
| **Performance** | ❌ Muy lento | ✅ ~10x más rápido |
| **Logs SSL** | ❌ Mensajes de error | ✅ Sin errores |
| **Debugging** | ✅ Sí | ⚠️ Limitado |

### Notas Importantes

1. **No uses Flask dev en producción**: El servidor de desarrollo de Flask NO es seguro ni escalable.

2. **Rate Limiting en Producción**: Actualmente usa almacenamiento en memoria. Para producción con múltiples servidores, considera:
   - Redis (recomendado)
   - Memcached
   - Base de datos

3. **Monitoreo**: Usa herramientas como:
   - Supervisor (reiniciar si cae)
   - SystemD (en Linux)
   - Task Scheduler (en Windows)

4. **Logs**: Configura rotación de logs en production

5. **Variables de Entorno**: 
   - Asegúrate que `.env` esté configurado correctamente
   - Usa valores seguros para producción
   - Nunca commits `.env` al repositorio

### Ejecutar en Segundo Plano (Windows)

Para ejecutar sin que se cierre cuando cierres la terminal:

```batch
start "" python run_production.py 5001
```

O con Supervisor:
```bash
pip install supervisor
```

Crea `/etc/supervisor/conf.d/legajo.conf`:
```ini
[program:legajo]
command=/ruta/al/venv/bin/python /ruta/a/run_production.py 5001
directory=/ruta/a/legajo_digital
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/legajo.log
```

### Verificar que está corriendo

```bash
# En otra terminal
curl http://localhost:5001
```

Deberías ver el HTML de login.

---

**Última actualización**: Noviembre 20, 2025
**Versión**: Production Ready v1.0
