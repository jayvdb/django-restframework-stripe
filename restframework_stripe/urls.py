from django.conf.urls import include, url

from rest_framework import routers
from . import views

router = routers.SimpleRouter()
router.register(r"cards", views.CardViewset, base_name="card")
router.register(r"connected-account", views.ConnectedAccountViewset,
        base_name="connected-account")
router.register(r"bank-accounts", views.BankAccountViewset, base_name="bank-account")

patterns = []
patterns += router.urls

urlpatterns = [
    url(r"^", include(patterns, namespace="rf_stripe"))
    ]
