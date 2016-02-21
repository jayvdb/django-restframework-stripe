from django.conf import settings

import stripe

STRIPE = getattr(settings, "RESTFRAMEWORK_STRIPE", {})
STRIPE.setdefault("api_key", getattr(stripe, "api_key", None))
STRIPE.setdefault("api_base", getattr(stripe, "api_base", None))
STRIPE.setdefault("upload_api_base", getattr(stripe, "upload_api_base", None))
STRIPE.setdefault("api_version", getattr(stripe, "api_version", None))
STRIPE.setdefault("verify_ssl_certs", getattr(stripe, "verify_ssl_certs", None))
STRIPE.setdefault("default_http_client", getattr(stripe, "default_http_client", None))
STRIPE.setdefault("use_connect", False)
STRIPE.setdefault("project_title", None)

stripe.api_key = STRIPE["api_key"]
stripe.api_base = STRIPE["api_base"]
stripe.upload_api_base = STRIPE["upload_api_base"]
stripe.api_version = STRIPE["api_version"]
stripe.verify_ssl_certs = STRIPE["verify_ssl_certs"]
stripe.default_http_client = STRIPE["default_http_client"]

VERSION = "1.0"

default_app_config = "restframework_stripe.apps.RFStripeConfig"
