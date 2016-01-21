import os
import argparse

import django
from django.conf import settings
from django.core.management import call_command

import pytest

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJ_DIR = os.path.join(BASE_DIR, "restframework_stripe")
TEST_DIR = os.path.join(BASE_DIR, "tests")

# Test Settings
SETTINGS = {
    "DEBUG": True,
    "INSTALLED_APPS": [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.sites",
        "restframework_stripe",
        ],
    "DATABASES": {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "restframework_stripe",
            "USER": "postgres"
            }
        },
    "RESTFRAMEWORK_STRIPE": {
        "api_key": "xxxTESTINGxxx",
        "api_version": "2015-10-16"
        },
    "ROOT_URLCONF": "tests.urls",
    "SITE_ID": 1
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrations", action="store_true")
    return parser.parse_args()


def main():
    settings.configure(**SETTINGS)
    django.setup()
    args = parse_args()
    if args.migrations:
        call_command("makemigrations")

    coverage = "--cov=restframework_stripe"
    pytest.main(["-x", "-s", "tests", coverage, "--cov-report", "term",
        "--cov-report", "html"])


if __name__ == "__main__":
    main()
