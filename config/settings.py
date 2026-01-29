# config/settings.py
"""
Django settings for config project.
Editado para Arquitectura Limpia + Facturación SRI + Notificaciones Email.
Nivel: Producción Profesional.
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import dotenv  # pip install python-dotenv
import dj_database_url  # pip install dj-database-url

# ==============================================================================
# 0. FUNCIONES DE UTILIDAD (Best Practice)
# ==============================================================================
def get_env_bool(var_name, default=False):
    """Convierte variables de entorno 'True', 'true', '1' en booleanos reales."""
    return str(os.getenv(var_name, str(default))).lower() in ('true', '1', 'yes')

# ==============================================================================
# 1. CONFIGURACIÓN BÁSICA Y RUTAS
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env
dotenv_path = BASE_DIR / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path)
else:
    # En producción esto no es un error, ya que las variables pueden venir del sistema (Railway)
    print("ℹ️ INFO: No se encontró .env, usando variables del sistema.")

# ==============================================================================
# 2. SEGURIDAD (SECURITY HARDENING)
# ==============================================================================

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Fail Fast: Si no hay llave secreta en producción, que el sistema falle inmediatamente.
if not SECRET_KEY:
    if os.getenv('RAILWAY_ENVIRONMENT'): # Si estamos en Railway
        raise ValueError("❌ ERROR CRÍTICO: DJANGO_SECRET_KEY no está configurada.")
    SECRET_KEY = 'django-insecure-dev-key-only-for-local-testing'

# Uso de la función helper para evitar errores de string
DEBUG = get_env_bool('DEBUG', False)

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# --- Configuración HTTPS para Producción (Vital para certificaciones) ---
if not DEBUG:
    # Fuerza a usar HTTPS
    SECURE_SSL_REDIRECT = True
    # Evita que el navegador acceda a cookies por Javascript
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS: Le dice al navegador "Nunca entres aquí por HTTP normal" por 1 año
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Confianza en el Proxy de Railway (Load Balancer)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Orígenes confiables para CSRF (importante para API + Admin)
CSRF_TRUSTED_URLS = os.getenv('CSRF_TRUSTED_URLS', '')
if CSRF_TRUSTED_URLS:
    CSRF_TRUSTED_ORIGINS = [url.strip() for url in CSRF_TRUSTED_URLS.split(',')]

# ==============================================================================
# 3. APLICACIONES
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',

    # Local Apps (Arquitectura Limpia)
    'adapters.api.apps.ApiConfig',
    'adapters.infrastructure.apps.InfrastructureConfig',
    
    # Audit
    'simple_history',
]

# ==============================================================================
# 4. MIDDLEWARE
# ==============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS antes de todo lo demás
    'whitenoise.middleware.WhiteNoiseMiddleware', # WhiteNoise para estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware', # ✅ Audit Middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ==============================================================================
# 5. BASE DE DATOS (PROFESIONAL)
# ==============================================================================

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Ajuste fino para MySQL en Producción
if not DEBUG and 'mysql' in DATABASES['default']['ENGINE']:
    DATABASES['default']['OPTIONS'] = {
        # MySQL suele requerir configuración explícita si el servidor fuerza SSL
        # 'ssl': {'ca': '/path/to/ca-cert.pem'} # Descomentar si Railway te da un certificado CA específico
    }

# ==============================================================================
# 6. PASSWORD & AUTH
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 7. LOCALIZACIÓN
# ==============================================================================
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 8. ARCHIVOS ESTÁTICOS (MODERNIZADO DJANGO 5)
# ==============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Sintaxis moderna para Django 4.2+ y 5.x
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ==============================================================================
# 9. DRF & JWT
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ==============================================================================
# 10. CORS
# ==============================================================================
# En producción, NUNCA uses ALLOW_ALL_ORIGINS=True si manejas datos sensibles
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    # Lista explícita de dominios permitidos (Frontend)
    # Se leen de una variable de entorno separada por comas
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
    # Fallback por si la variable está vacía (Evita crash, pero bloquea acceso)
    if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == ['']:
        CORS_ALLOWED_ORIGINS = [] 

# ==============================================================================
# 11. CONFIGURACIÓN SRI (LIMPIA)
# ==============================================================================
SRI_FIRMA_PASS = os.getenv('SRI_FIRMA_PASS')
SRI_FIRMA_BASE64 = os.getenv('SRI_FIRMA_BASE64')
SRI_FIRMA_PATH = BASE_DIR / 'secrets' / 'el_arbolito.p12'
SRI_JAR_PATH = BASE_DIR / 'adapters' / 'infrastructure' / 'files' / 'jar' / 'sri.jar'

# Datos Emisor
SRI_EMISOR_RUC = os.getenv('SRI_EMISOR_RUC')
SRI_EMISOR_RAZON_SOCIAL = os.getenv('SRI_EMISOR_RAZON_SOCIAL')
SRI_EMISOR_DIRECCION_MATRIZ = os.getenv('SRI_EMISOR_DIRECCION_MATRIZ')
SRI_NOMBRE_COMERCIAL = os.getenv('SRI_NOMBRE_COMERCIAL')

# Configuración Técnica
SRI_SERIE_ESTABLECIMIENTO = os.getenv('SRI_SERIE_ESTABLECIMIENTO')
SRI_SERIE_PUNTO_EMISION = os.getenv('SRI_SERIE_PUNTO_EMISION')
SRI_AMBIENTE = int(os.getenv('SRI_AMBIENTE', '1'))
SRI_URL_RECEPCION = os.getenv('SRI_URL_RECEPCION')
SRI_URL_AUTORIZACION = os.getenv('SRI_URL_AUTORIZACION')
SRI_SECUENCIA_INICIO = 600

# Validación solo al arrancar el servidor "runserver" o Gunicorn
# Evitamos que falle al hacer collectstatic o migraciones
if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
    if not SRI_FIRMA_BASE64 and not SRI_FIRMA_PATH.exists():
        print("⚠️  ADVERTENCIA SRI: No se detectó firma electrónica (local o base64).")

# ==============================================================================
# 12. EMAIL
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ==============================================================================
# 13. CELERY & REDIS
# ==============================================================================
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ==============================================================================
# 14. LOGGING (Optimizado)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        # Tu logger personalizado para la Tesis
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# 15. CONFIGURACIÓN SWAGGER (DRF-YASG)
# ==============================================================================
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
}
