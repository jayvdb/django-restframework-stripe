from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

import stripe

from . import models
from . import util
from . import STRIPE


class ReturnSerializerMixin:
    """ a mixin class for serializers which return a different serializers data when
    when validated. two fields are required on the Meta class: `model` and
    `return_serializer`. the model variable must be and instance of StripeModel and
    the return serializer must be the model serializer of the model variable.
    """
    @staticmethod
    def reraise_stripe_error(error):  # pragma: no cover
        if hasattr(error, "param"):
            body = {error.param: error._message}
        else:
            body = error._message
        raise ValidationError(detail=body)

    @classmethod
    def get_return_serializer(cls, *args, **kwargs):  # pragma: no cover
        return cls.Meta.return_serializer(*args, **kwargs)

    @classmethod
    def get_model_class(cls):  # pragma: no cover
        return cls.Meta.model

    @property
    def data(self):
        if self.instance is not None and not getattr(self, "_errors", None):
            return self.get_return_serializer(self.instance).data
        return super().data  # pragma: no cover


class StripeResourceSerializer(ReturnSerializerMixin, serializers.Serializer):
    """ a serializer that mocks a ModelSerializer by validating client data, making the
    update or create request to the stripe api then creating or updating the local
    redux of the stripe resource.

    .. code-block:: python

        class CustomerSerializer(StripeResourceSerializer):
            account_balance = serializers.IntegerField(required=False)
            coupon = serializers.CharField(required=False)
            description = serializers.CharField(required=False)
            email = serializers.EmailField(required=False)
            metadata = serializers.DictField(required=False)
            plan = serializers.CharField(required=False)
            quantity = serializers.IntegerField(required=False)
            shipping = serializers.DictField(required=False)

            class Meta:
                model = models.Customer
                return_serializer = CustomerSerializer
    """
    def create(self, validated_data):  # pragma: no cover
        instance = self.get_model_class().stripe_object_to_model(validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        instance.stripe_object_sync(validated_data)
        instance.save()
        return instance

    def run_validation(self, data=empty):
        """ extends the default serializer validation to include validation via the
        stripe api.
        """
        # prescreen fields from the client
        validated_data = super().run_validation(data)
        _instance = None
        if self.instance is not None:
            _instance = self.instance.api_retrieve()
        # validate clients data with stripe
        return self.validate_stripe(validated_data, _instance)

    def validate_stripe(self, data, instance=None):
        """ send the clients data to stripe for creation or updating
        """
        if instance is None:
            return self._stripe_instance_create(data)
        return self._stripe_instance_update(instance, data)

    def _stripe_instance_create(self, data):
        try:
            instance = self.get_model_class().stripe_api_create(**data)
        except stripe.StripeError as err:
            self.reraise_stripe_error(err)
        else:
            return instance

    def _stripe_instance_update(self, instance, data):
        """ raise a validation error if stripe id was not included
        """
        # update the retrieved stripe instance
        instance = util.recursive_mapping_update(instance, **data)
        try:
            instance = instance.save()
        except stripe.StripeError as err:
            self.reraise_stripe_error(err)
        else:
            return instance


class StripeTokenResourceSerializer(ReturnSerializerMixin, serializers.Serializer):
    """
    """
    token = serializers.CharField()
    owner = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())


class CardSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.Card


class CreateCardResourceSerializer(StripeTokenResourceSerializer):
    """
    """
    type = serializers.CharField(required=False, default="customer")

    class Meta:
        model = models.Card
        return_serializer = CardSerializer

    def create(self, validated_data):
        """
        """
        owner = validated_data.get("owner")
        token = validated_data.get("token")
        type_ = validated_data.get("type")

        if type_ not in ("customer", "merchant"):
            message = "Invalid type {}. Valid choices are 'customer' or "\
                                                        "'merchant'".format(card_type)
            raise ValidationError(detail={"type": message})

        try:

            # try to connect the card instance with the users connected account or
            # customer resource. if a stripe error is raised, the token is invalid or
            # has been used and the client will need to submit a new token for security
            # purposes.
            if type_ == "merchant":
                instance = owner.stripe_account.add_payment_source(token)
            elif type_ == "customer":
                instance = owner.stripe_customer.add_payment_source(token)

        except stripe.StripeError as err:  # raise a validation error, return to client
            self.reraise_stripe_error(err)
        else:
            return instance


class UpdateCardResourceSerializer(StripeResourceSerializer):
    """
    """
    address_city = serializers.CharField(required=False)
    address_country = serializers.CharField(required=False)
    address_line1 = serializers.CharField(required=False)
    address_line2 = serializers.CharField(required=False)
    address_state = serializers.CharField(required=False)
    address_zip = serializers.CharField(required=False)
    exp_month = serializers.IntegerField(required=False)
    exp_year = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    default_for_currency = serializers.BooleanField(required=False)

    class Meta:
        model = models.Card
        return_serializer = CardSerializer


class BankAccountSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.BankAccount


class CreateBankAccountResourceSerializer(CreateCardResourceSerializer):
    """
    """
    class Meta:
        model = models.BankAccount
        return_serializer = BankAccountSerializer


class UpdateBankAccountResourceSerializer(StripeResourceSerializer):
    """
    """
    class Meta:
        model = models.BankAccount
        return_serializer = BankAccountSerializer


class ConnectedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConnectedAccount


class CreateConnectedAccountResourceSerializer(StripeResourceSerializer):
    country = serializers.CharField()
    managed = serializers.BooleanField()
    legal_entity = serializers.DictField()
    tos_acceptance = serializers.DictField()

    class Meta:
        model = models.ConnectedAccount
        return_serializer = ConnectedAccountSerializer

    def create(self, validated_data):  # pragma: no cover
        owner = validated_data.pop("owner")
        instance = self.get_model_class().stripe_object_to_model(validated_data)
        instance.owner = owner
        instance.save()
        return instance


class UpdateConnectedAccountResourceSerializer(StripeResourceSerializer):

    class Meta:
        model = models.ConnectedAccount
        return_serializer = ConnectedAccountSerializer
