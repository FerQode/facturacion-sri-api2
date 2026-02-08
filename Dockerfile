# ==============================================================================
# Dockerfile Profesional - Django Production Ready (Con Soporte PDF & MySQL)
# Optimizado para Railway/Linux
# ==============================================================================

# 1. Base Image: Python 3.12 Slim (Pequeña y Segura)
FROM python:3.12-slim

# 2. Variables de Entorno para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 3. Instalar dependencias del sistema (OS Dependencies)
# CRÍTICO: build-essential y pkg-config para compilar mysqlclient
# CRÍTICO: librerías gráficas para WeasyPrint (PDFs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    libssl-dev \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    gdk-pixbuf2.0-0 \
    shared-mime-info \
    fonts-dejavu \
    fonts-liberation \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Instalar Dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copiar el Código Fuente
COPY . /app/

# 6. Generar Archivos Estáticos (Build Step)
# Truco: Usamos variables dummy para que Django no intente conectar a DB/Redis
RUN DJANGO_SECRET_KEY=build-mode-only \
    DATABASE_URL=sqlite://:memory: \
    ALLOWED_HOSTS=* \
    python manage.py collectstatic --noinput

# 7. Crear usuario no-root por seguridad
RUN addgroup --system appgroup && adduser --system --group appuser

# 8. Asignar permisos a carpetas críticas
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appgroup /app/

# 9. Cambiar al usuario seguro
USER appuser

# 10. Comando de Arranque (Gunicorn)
# --timeout 120: Para reportes PDF pesados
# --workers 3: Recomendado para instancias standard
CMD sh -c "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"