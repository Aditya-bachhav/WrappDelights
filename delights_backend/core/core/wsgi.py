"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
import logging
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Setup logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(asctime)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure project root is discoverable when served by WSGI
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delights_backend.core.core.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    logger.critical(f"Failed to load WSGI application: {e}", exc_info=True)
    raise
