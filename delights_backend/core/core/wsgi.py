"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Ensure project root is discoverable when served by WSGI
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delights_backend.core.core.settings')

application = get_wsgi_application()
