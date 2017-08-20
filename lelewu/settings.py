"""
Django settings for lelewu project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 't%w7p-95ksso!8_9rs)5ig&#-b6(7!7wy&gc2c3bg8_^b0u&=_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# add by tacy
# APPEND_SLASH = False
CORS_ORIGIN_ALLOW_ALL = True
# CSRF_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',  # DRF
    'rest_framework.authtoken',
    'django_filters',
    'stock',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lelewu.urls'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES':
    ('rest_framework.authentication.TokenAuthentication',
     'rest_framework.authentication.SessionAuthentication', ),
    'DEFAULT_PERMISSION_CLASSES':
    ('rest_framework.permissions.IsAuthenticated', ),  # AllowAny
    'DEFAULT_PAGINATION_CLASS':
    # 'rest_framework.pagination.PageNumberPagination',
    'stock.core.StockPagination',
    'PAGE_SIZE':
    10,
    'DEFAULT_RENDERER_CLASSES':
    ('rest_framework.renderers.JSONRenderer',
     'rest_framework.renderers.BrowsableAPIRenderer', )
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [],
        'DIRS': ['dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lelewu.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ymatou',
        'USER': 'root',
        'PASSWORD': '12345678',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

# Add for vuejs
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "dist/static"),
]

STATIC_URL = '/static/'

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1', )
    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware', )

    INSTALLED_APPS += ('debug_toolbar', )

    # DEBUG_TOOLBAR_PANELS = [
    #     'debug_toolbar.panels.versions.VersionsPanel',
    #     'debug_toolbar.panels.timer.TimerPanel',
    #     'debug_toolbar.panels.settings.SettingsPanel',
    #     'debug_toolbar.panels.headers.HeadersPanel',
    #     'debug_toolbar.panels.request.RequestPanel',
    #     'debug_toolbar.panels.sql.SQLPanel',
    #     'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    #     'debug_toolbar.panels.templates.TemplatesPanel',
    #     'debug_toolbar.panels.cache.CachePanel',
    #     'debug_toolbar.panels.signals.SignalsPanel',
    #     'debug_toolbar.panels.logging.LoggingPanel',
    #     'debug_toolbar.panels.redirects.RedirectsPanel',
    # ]

    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }
