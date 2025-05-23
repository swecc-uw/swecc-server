import os
from pathlib import Path

DJANGO_DEBUG = DEBUG = os.environ["DJANGO_DEBUG"].lower() == "true"
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_PORT = os.environ["DB_PORT"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
# use for storage client only
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
# use for accessing metric from chronos
METRIC_SERVER_URL = os.environ["METRIC_SERVER_URL"]
JWT_SECRET = os.environ["JWT_SECRET"]
AWS_BUCKET_NAME = os.environ["AWS_BUCKET_NAME"]
VERIFICATION_EMAIL_ADDR = os.environ.get("VERIFICATION_EMAIL_ADDR", "swecc@uw.edu")

print(
    {
        "DJANGO_DEBUG": DJANGO_DEBUG,
        "DB_HOST": DB_HOST,
        "DB_NAME": DB_NAME,
        "DB_PORT": DB_PORT,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "SENDGRID_API_KEY": SENDGRID_API_KEY,
        "METRIC_SERVER_URL": METRIC_SERVER_URL,
    }
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ehylqtrwm(8+eq!m#*3fq3(m6j9jfvm6bzb8=f-uz=l@4$l&^g"

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = False

ALLOWED_HOSTS = ["*"]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        # 'rest_framework.renderers.AdminRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer'
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "questions.apps.QuestionsConfig",
    "members.apps.MembersConfig",
    "custom_auth.apps.AuthConfig",
    "interview.apps.InterviewConfig",
    "report.apps.ReportConfig",
    "leaderboard.apps.LeaderboardConfig",
    "engagement.apps.EngagementConfig",
    "contentManage.apps.ContentManageConfig",
    "metasync.apps.MetasyncConfig",
    "metrics.apps.MetricsConfig",
    "cohort.apps.CohortConfig",
    "resume_review.apps.ResumeReviewConfig",
    "corsheaders",
    "rest_framework_api_key",
]

if DJANGO_DEBUG:
    print("DEBUG is enabled, adding debug apps")
    INSTALLED_APPS += [
        "silk",
    ]

    SILKY_PYTHON_PROFILER = True  # Enable Python profiler
    SILKY_ANALYZE_QUERIES = True  # Analyze SQL queries
    SILKY_MAX_RECORDED_REQUESTS = 10000  # Max number of recorded requests to store


FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DJANGO_DEBUG:
    print("DEBUG is enabled, adding debug middleware")
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "members.User"
CORS_ALLOWED_ORIGINS = [
    "https://interview.swecc.org",
    "https://leaderboard.swecc.org",
    "https://engagement.swecc.org",
    "https://admin.swecc.org",
    "https://dashboard.swecc.org",
    "https://template.swecc.org",
    "https://rooms.swecc.org",
]
CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]
CORS_ALLOW_CREDENTIALS = True

# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True

CSRF_COOKIE_SAMESITE = "None" if not DJANGO_DEBUG else "Lax"
SESSION_COOKIE_SAMESITE = "None" if not DJANGO_DEBUG else "Lax"
CSRF_COOKIE_HTTPONLY = not DJANGO_DEBUG
SESSION_COOKIE_HTTPONLY = not DJANGO_DEBUG
CSRF_TRUSTED_ORIGINS = [
    "https://interview.swecc.org",
    "https://leaderboard.swecc.org",
    "https://engagement.swecc.org",
    "https://admin.swecc.org",
    "https://dashboard.swecc.org",
    "https://template.swecc.org",
    "https://rooms.swecc.org",
]

devclient = "http://localhost:5173"

if DJANGO_DEBUG:
    CORS_ALLOWED_ORIGINS.append(devclient)
    CSRF_TRUSTED_ORIGINS.append(devclient)


# PROD ONLY
CSRF_COOKIE_SECURE = not DJANGO_DEBUG
SESSION_COOKIE_SECURE = not DJANGO_DEBUG

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {process:d} {thread:d} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(PROJECT_ROOT, "logs", "django.log"),
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "server": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://swecc-redis-instance:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Django will keep running if redis isn't available
            "IGNORE_EXCEPTIONS": True,
        },
    }
}
