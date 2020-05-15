#!/usr/bin/env python
import os
import sys

try:
    import django
    django
except ImportError as e:
    raise ImportError(
        "Couldn't import Django. Are you sure it's installed and "
        'available on your PYTHONPATH environment variable? Did you '
        'forget to activate a virtual environment?'
        '{0}'.format(e)
    )

from django.core.management import execute_from_command_line


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
