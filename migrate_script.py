import os
import sys

# Add the project directory to sys.path
sys.path.append(os.path.abspath('delights_backend'))

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delights_backend.core.core.settings')

import django
from django.core.management import call_command

django.setup()
call_command('makemigrations')
call_command('migrate')
print("Migrations applied successfully.")