import os

from sites.settings import *

SITE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
SECRET_KEY = 'fake'

# Data

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SITE_DIR, 'db.sqlite3'),
    }
}

# FlexiPages

FLEXIPAGES_CACHES = {
    'dbtemplates': {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "dbtemplates",
    },
    'flexipages': {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "flexipages",
    },
}
CACHES.update(FLEXIPAGES_CACHES)
FLEXIPAGES_PAGES_CACHE_ALIAS = 'flexipages'
