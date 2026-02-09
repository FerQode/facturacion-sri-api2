# config/settings.py
"""
Django settings for config project.
Enterprise Grade: Production Ready (Railway + S3 Tigris + WhiteNoise).
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import dotenv
import dj_database_url

# ==============================================================================
# 0. UTILITIES & ENV
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env si existe (Local Development)
dotenv_path = BASE_DIR / '.env'
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path)

def get_env_bool(var_name, default=False):
    """Convierte variables de entorno 'True', '1' en booleanos reales."""
    return str(os.getenv(var_name, str(default))).lower() in ('true', '1', 'yes')

def get_env_list(var_name, default=''):
    """Convierte string separado por comas en lista."""
    val = os.getenv(var_name, default)
    if not val:
        return []
    return [x.strip() for x in val.split(',') if x.strip()]

# ==============================================================================
# 1. CORE & SECURITY (FAIL FAST)
# ==============================================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Build Safety: Si estamos construyendo el contenedor, usamos una llave falsa
IS_BUILD_PROCESS = os.getenv('DJANGO_SECRET_KEY') == 'build-mode-only'

if not SECRET_KEY:
    if get_env_bool('RAILWAY_ENVIRONMENT'):
        raise ValueError("❌ CRITICAL: DJANGO_SECRET_KEY missing in Production.")
    SECRET_KEY = 'django-insecure-local-dev-key' 

DEBUG = get_env_bool('DEBUG', False)

ALLOWED_HOSTS = get_env_list('ALLOWED_HOSTS', '*')

# HTTPS & Proxies (Railway)
if not DEBUG and not IS_BUILD_PROCESS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF Trusted Origins (Vital para Admin Panel en Prod)
CSRF_TRUSTED_ORIGINS = get_env_list('CSRF_TRUSTED_URLS')

# ==============================================================================
# 2. APPS & MIDDLEWARE
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'simple_history',
    'storages', # AWS S3 Support

    # Local Apps
    'core',
    'adapters.api.apps.ApiConfig',
    'adapters.infrastructure.apps.InfrastructureConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Static Files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

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

# ==============================================================================
# 3. DATABASE (Build Safe)
# ==============================================================================
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # MySQL Fine-tuning
    if not DEBUG and 'mysql' in DATABASES['default']['ENGINE']:
        DATABASES['default']['OPTIONS'] = {'charset': 'utf8mb4'}
else:
    # Fallback para build de Docker (collectstatic) o dev sin DB
    print("ℹ️  INFO: Usando SQLite en memoria (Build Mode).")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# ==============================================================================
# 4. STORAGE & STATIC FILES (S3 + WhiteNoise)
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

USE_S3 = get_env_bool('USE_S3', False)

if USE_S3:
    # Tigris / AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'auto')
    
    # Compatibilidad Tigris
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_QUERYSTRING_AUTH = True 
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            # WhiteNoise es mejor para estáticos incluso usando S3 para media
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# ==============================================================================
# 5. PASSWORD & AUTH
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 6. DRF & API
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}



SPECTACULAR_SETTINGS = {
    'TITLE': 'API ERP El Arbolito',
    'DESCRIPTION': 'Sistema de Facturación SRI y Gestión de Agua Potable',
    'VERSION': '5.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# ==============================================================================
# 7. CORS
# ==============================================================================
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = get_env_list('CORS_ALLOWED_ORIGINS')
    # HYBRID TESTING: Allow localhost explicitly for local frontend dev against prod backend
    CORS_ALLOWED_ORIGINS.extend(["http://localhost:4200", "http://127.0.0.1:4200"])
    CORS_ALLOW_CREDENTIALS = True
    # CORS Hardening
    from corsheaders.defaults import default_headers
    CORS_ALLOW_HEADERS = list(default_headers) + [
        'Authorization',
    ]

# ==============================================================================
# 8. SRI & BUSINESS LOGIC
# ==============================================================================
SRI_CONFIG = {
    'FIRMA_PASS': os.getenv('SRI_FIRMA_PASS'),
    'FIRMA_BASE64': os.getenv('SRI_FIRMA_BASE64'),
    'FIRMA_PATH': BASE_DIR / 'secrets' / 'el_arbolito.p12',
    'EMISOR_RUC': os.getenv('SRI_EMISOR_RUC'),
    'AMBIENTE': int(os.getenv('SRI_AMBIENTE', '1')),
    'URL_RECEPCION': os.getenv('SRI_URL_RECEPCION'),
    'URL_AUTORIZACION': os.getenv('SRI_URL_AUTORIZACION'),
}

# ==============================================================================
# 9. LOGGING & OBSERVABILITY
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
        'core': { # Tu aplicación
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# 10. ENDURECIMIENTO DE SEGURIDAD (Compliance Bancario)
# ==============================================================================

# Backend (Django Admin)
SESSION_COOKIE_AGE = 1200  # 20 min de inactividad estricta
SESSION_SAVE_EVERY_REQUEST = True  # Reiniciar contador si hay actividad
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Cerrar navegador = Kill Session

# APIs (DRF SimpleJWT)
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=12),  # Jornada laboral
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
