DEBUG = True

SECRET_KEY = "unguessable"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "restframework_stripe",
    ]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "restframework_stripe",
        "USER": "postgres"
        }
    }

RESTFRAMEWORK_STRIPE = {
    "api_key": "xxxTESTINGxxx",
    "api_version": "2015-10-16"
    }

ROOT_URLCONF ="urls",
SITE_ID = 1
