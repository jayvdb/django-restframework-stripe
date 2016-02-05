from django.conf import settings

import stripe

STRIPE = getattr(settings, "RESTFRAMEWORK_STRIPE", {})
STRIPE.setdefault("api_key", stripe.api_key)
STRIPE.setdefault("api_base", stripe.api_base)
STRIPE.setdefault("upload_api_base", stripe.upload_api_base)
STRIPE.setdefault("api_version", stripe.api_version)
STRIPE.setdefault("verify_ssl_certs", stripe.verify_ssl_certs)
STRIPE.setdefault("default_http_client", stripe.default_http_client)
STRIPE.setdefault("use_connect", False)
STRIPE.setdefault("project_title", None)

stripe.api_key = STRIPE["api_key"]
stripe.api_base = STRIPE["api_base"]
stripe.upload_api_base = STRIPE["upload_api_base"]
stripe.api_version = STRIPE["api_version"]
stripe.verify_ssl_certs = STRIPE["verify_ssl_certs"]
stripe.default_http_client = STRIPE["default_http_client"]

VERSION = "1.0"
