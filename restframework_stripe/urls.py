from django.conf.urls import include, url

from rest_framework import routers
from . import views

router = routers.SimpleRouter()
router.register(r"cards", views.CardViewset, base_name="card")
router.register(r"connected-accounts", views.ConnectedAccountViewset,
        base_name="connected-account")
router.register(r"bank-accounts", views.BankAccountViewset, base_name="bank-account")
router.register(r"subscriptions", views.SubscriptionViewset, base_name="subscription")

urlpatterns = []
urlpatterns += router.urls
