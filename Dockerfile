# ==============================================================================
# Dockerfile Profesional - Django Production Ready
# ==============================================================================

# 1. Base Image: Usamos Python 3.12 Slim para menor tamaño y mayor seguridad
FROM python:3.12-slim

# 2. Variables de Entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 3. Directorio de Trabajo
WORKDIR /app

# 4. Instalar dependencias del sistema (OS Dependencies)
# mysqlclient requiere headers de C y librerías de MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalar Dependencias de Python
# Copiamos primero el requirements.txt para aprovechar caché de Docker
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copiar el Código Fuente
COPY . /app/

# 7. Crear usuario no-root por seguridad
RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

# 8. Comando por defecto (Será sobreescrito por docker-compose o Railway)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
