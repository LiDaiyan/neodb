import os
from .settings import *
import getpass
import sys
import dj_database_url


if ENABLE_NEW_MODEL:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': sys.stderr,
            },
        },
        'loggers': {
            'catalog': {
                'propagate': True,
                'level': 'INFO' if not DEBUG else 'DEBUG',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}
RQ_QUEUES = {
    'mastodon': {
        'URL': os.getenv('REDIS_URL')
    },
    'export': {
        'URL': os.getenv('REDIS_URL')
    },
    'doufen': {
        'URL': os.getenv('REDIS_URL')
    }
}

SITE_INFO['site_name'] = '[Test] NeoDB'
APP_WEBSITE = 'federleicht.neodb.social'
REDIRECT_URIS = "https://federleicht.neodb.social/users/OAuth2_login/\nhttp://federleicht.neodb.social/users/OAuth2_login/\nhttps://neodb.fly.dev/users/OAuth2_login/\nhttp://neodb.fly.dev/users/OAuth2_login/"

THUMBNAIL_DEBUG = True

SEARCH_BACKEND = 'TYPESENSE'  # None # 'TYPESENSE' # 'MEILISEARCH'
# SEARCH_BACKEND = 'MEILISEARCH'  # None # 'TYPESENSE'

DOWNLOADER_SAVEDIR = '/tmp'
