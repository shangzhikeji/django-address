"""
WSGI config for example_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_site.settings")

from django.core.wsgi import get_wsgi_application  # noqa

application = get_wsgi_application()
