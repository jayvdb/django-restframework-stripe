from django.conf.urls import include, url

from rest_framework import routers
from . import views

app_name = 'restframework_stripe'

router = routers.SimpleRouter()
router.register(r"cards", views.CardViewset, "card")
router.register(r"connected-accounts", views.ConnectedAccountViewset, "connected-account")
router.register(r"bank-accounts", views.BankAccountViewset, "bank-account")
router.register(r"subscriptions", views.SubscriptionViewset, "subscription")
router.register(r"customers", views.CustomerViewset, "customer")
router.register(r"charges", views.ChargeViewset, "charge")
router.register(r"transfers", views.TransferViewset, "transfer")
router.register(r"refunds", views.RefundViewset, "refund")

urlpatterns = []
urlpatterns += router.urls
