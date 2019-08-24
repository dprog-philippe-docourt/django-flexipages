"""
WSGI config for MyGym project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

SITE_NAME = os.environ.get("SITE_NAME")
default_settings_module = "sites.local_dev.settings"
if SITE_NAME:
    default_settings_module = "sites.%s.settings" % SITE_NAME
os.environ.setdefault("DJANGO_SETTINGS_MODULE", default_settings_module)

application = get_wsgi_application()
