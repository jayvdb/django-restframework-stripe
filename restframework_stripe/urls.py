from django.conf.urls import include, url

from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r"cards", views.CardViewset, base_name="card")
router.register(r"connected-accounts", views.ConnectedAccountViewset,
        base_name="connected-account")
router.register(r"bank-accounts", views.BankAccountViewset, base_name="bank-account")
router.register(r"subscriptions", views.SubscriptionViewset, base_name="subscription")
router.register(r"customers", views.CustomerViewset, base_name="customer")
router.register(r"charges", views.ChargeViewset, base_name="charge")
router.register(r"transfers", views.TransferViewset, base_name="transfer")
router.register(r"refunds", views.RefundViewset, base_name="refund")

urlpatterns = []
urlpatterns += router.urls
