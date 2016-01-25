from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from . import models, serializers, permissions


class StripeResourceViewset(ModelViewSet):
    """ a typical ModelViewSet that chooses its serializer based on the request type.
    this requires that the viewset has two additional parameters, namely
    `create_stripe_serializer` and `update_stripe_serializer`. these serializers will be
    used to handle create and update interactions with the stripe api resource.
    """
    permission_classes = (permissions.OwnerOnlyPermission,)

    def create(self, request, *args, **kwargs):
        """ since all stripe resource objects have a required `owner` foreign key, auto
        matically set the requesting users id to the `owner` field value
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

    @detail_route(methods=["get"])
    def refresh(self, request, *args, **kwargs):
        """ For whatever reason a model might need to be refreshed by a client a detail
        route /<resource>/<pk>/refresh/ is available.
        """
        instance = self.get_object()
        instance.refresh_from_stripe_api()
        instance.save()
        serializer = self.get_serializer_class(instance)
        return Response(serializer.data)


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
    """ Normal CRUD operations on the stripe BankAccount resource.

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
    """ Normal CRUD operations on the stripe Account resource.
    """
    model = models.ConnectedAccount
    queryset = models.ConnectedAccount.objects.all()
    serializer_class = serializers.ConnectedAccountSerializer
    create_stripe_serializer = serializers.CreateConnectedAccountResourceSerializer
    update_stripe_serializer = serializers.UpdateConnectedAccountResourceSerializer


class SubscriptionViewset(StripeResourceViewset):
    """ Normal CRUD operations on the stripe Subscription resource.

    a POST request expects a json document like this::

        {
            "plan": 2,  // primary key of local plan model
            "coupon": null  // primarty key of local coupon model
        }
    """
    model = models.Subscription
    queryset = models.Subscription.objects.all()
    serializer_class = serializers.SubscriptionSerializer
    create_stripe_serializer = serializers.CreateSubscriptionResourceSerializer
    update_stripe_serializer = serializers.UpdateSubscriptionResourceSerializer

    permission_classes = (permissions.CustomerOnlyPermission, )

    def create(self, request, *args, **kwargs):
        request.data["customer"] = request.user.stripe_customer.id
        return super().create(request, *args, **kwargs)
