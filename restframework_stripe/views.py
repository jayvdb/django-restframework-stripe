from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response

from . import models, serializers, permissions


class StripeResourceViewset(ModelViewSet):
    """ a typical ModelViewSet that chooses its serializer based on the request type.
    this requires that the viewset has two additional parameters, namely
    `create_stripe_serializer` and `update_stripe_serializer`. these serializers will be
    used to handle create and update interactions with the stripe api resource.
    """
    permission_classes = (permissions.OwnerOnlyPermission,)

    def create(self, request, *args, **kwargs):
        """
        """
        request.data["owner"] = request.user.id
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        """ gets a serializer based on the request action type
        """
        if self.action == "create":
            return self.create_stripe_serializer
        elif self.action in ("update", "partialUpdate"):
            return self.update_stripe_serializer
        return super().get_serializer_class()

    def filter_queryset(self, queryset):
        """ no one can view objects that they do not own!
        """
        return queryset.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        stripe_instance = instance.retrieve_stripe_api_instance()
        stripe_instance.delete()
        instance.delete()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CardViewset(StripeResourceViewset):
    """ Normal CRUD operations on the stripe Card resource.

    a POST request expects a json document like this::

        {
            "token": "tok_fdsionNKO532N32nL",
            "card_type": "customer" or "merchant"
        }
    """
    model = models.Card
    queryset = models.Card.objects.all()
    serializer_class = serializers.CardSerializer
    create_stripe_serializer = serializers.CreateCardResourceSerializer
    update_stripe_serializer = serializers.UpdateCardResourceSerializer

    permission_classes = (permissions.PaymentTypePermission,)


class BankAccountViewset(StripeResourceViewset):
    """ Normal CRUD operations on the stripe Card resource.

    a POST request expects a json document like this::

        {
            "token": "tok_fdsionNKO532N32nL",
            "card_type": "customer" or "merchant"
        }
    """
    model = models.BankAccount
    queryset = models.BankAccount.objects.all()
    serializer_class = serializers.BankAccountSerializer
    create_stripe_serializer = serializers.CreateBankAccountResourceSerializer
    update_stripe_serializer = serializers.UpdateBankAccountResourceSerializer

    permission_classes = (permissions.PaymentTypePermission,)


class ConnectedAccountViewset(StripeResourceViewset):
    model = models.ConnectedAccount
    queryset = models.ConnectedAccount.objects.all()
    serializer_class = serializers.ConnectedAccountSerializer
    create_stripe_serializer = serializers.CreateConnectedAccountResourceSerializer
    update_stripe_serializer = serializers.UpdateConnectedAccountResourceSerializer
