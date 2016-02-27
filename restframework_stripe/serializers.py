""" this module confronts many issues involving the validation of client side data and
the multiple serializer types necessary for creating, updating and retrieving stripe
resources for a client. some resources for instance have different allowed parameters
for creating and updating, for instance bank accounts have such dramatically different
serializers for creating and updating that it would be impossible to compress them into
a single serializer. the solution that restframework_stripe proposes is to include 3
serializers per model, a serializer for creating, updating and retrieving these
resources.

at the base of each of these triads is a simple model serializer for the model instance.
no matter what the method, the model serializer will always return data back to the
client. used in conjunction with the `views.StripeResourceViewset` it is easy to perform
CRUD operatons with these serializers without very verbose views.
"""
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

    def update(self, instance, validated_data):  # pragma: no cover
        instance.stripe_object_sync(validated_data)
        instance.save()
        return instance

    def retrieve_stripe_api_instance(self):
        return self.instance.retrieve_stripe_api_instance()

    def run_validation(self, data=empty):
        """ extends the default serializer validation to include validation via the
        stripe api.
        """
        # prescreen fields from the client
        validated_data = super().run_validation(data)
        _instance = None

        if self.instance is not None:
            try:
                _instance = self.retrieve_stripe_api_instance()
            # an error due to an object not existing, invalid api key, or network outage
            except stripe.StripeError as err:  # pragma: no cover
                self.reraise_stripe_error(err)

        # validate clients data with stripe
        return self.validate_stripe(validated_data, _instance)

    def validate_stripe(self, data, instance=None):
        """ send the clients data to stripe for creation or updating
        """
        if instance is None:
            return self._stripe_instance_create(data)
        return self._stripe_instance_update(instance, data)

    def _stripe_instance_create(self, data):
        data = self._process_data_for_stripe(data)
        try:
            instance = self.get_model_class().stripe_api_create(**data)
        except stripe.StripeError as err:
            self.reraise_stripe_error(err)
        else:
            return instance

    def _stripe_instance_update(self, instance, data):
        """ raise a validation error if stripe id was not included
        """
        data = self._process_data_for_stripe(data)
        # update the retrieved stripe instance
        instance = util.recursive_mapping_update(instance, **data)
        try:
            instance = instance.save()
        except stripe.StripeError as err:
            self.reraise_stripe_error(err)
        else:
            return instance

    def _process_data_for_stripe(self, data):
        """ simply flatten StripeModels down to their id only
        """
        _data = {}
        for key, value in data.items():
            if isinstance(value, models.StripeModel):
                value = value.stripe_id
            if value not in ("", None):
                _data[key] = value
        _data = _clean_dict(_data)
        return _data
        
def _clean_dict(d):
    _dict = {}
    for key, value in d.items():
        if isinstance(value, dict):
            _clean_dict(d)
        elif value not in (None, ""):
            _dict[key] = value
    return _dict


class StripeListObjectSerializer(StripeResourceSerializer):
    """
    """
    def _get_related_field_name(self):
        return self.Meta.parent_model_field_name

    def _get_list_object_name(self):
        return self.Meta.list_object_name

    def _stripe_instance_create(self, data):
        """
        """
        relation = data.pop(self._get_related_field_name())
        parent_object = relation.retrieve_stripe_api_instance()

        list_object = getattr(parent_object, self._get_list_object_name())
        data = self._process_data_for_stripe(data)

        try:
            stripe_object = list_object.create(**data)
        # an error due to an object not existing, invalid api key, or network outage
        except stripe.StripeError as err:  # pragma: no cover
            self.reraise_stripe_error(err)
        else:
            return stripe_object


class StripeTokenResourceSerializer(ReturnSerializerMixin, serializers.Serializer):
    """ A serializer base class for creating objects from tokens returned by Stripe.js.
    """
    token = serializers.CharField()
    owner = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())


class DefaultSourceRelatedField(serializers.RelatedField):
    """ A Field type for representing payment & payout accounts for merchants and
    customers
    """
    def to_representation(self, value):
        if isinstance(value, models.BankAccount):
            return BankAccountSerializer(value).data
        elif isinstance(value, models.Card):
            return CardSerializer(value).data
        raise NotImplementedError(value.__class__.__name__)


class CardSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.Card
        exclude = ("stripe_id", )


class CreateCardResourceSerializer(StripeTokenResourceSerializer):
    """
    """
    TYPE_CHOICES = (
        ("customer", "customer"),
        ("merchant", "merchant")
        )
    type = serializers.ChoiceField(TYPE_CHOICES, required=False, default="customer")

    class Meta:
        model = models.Card
        return_serializer = CardSerializer

    def create(self, validated_data):
        """
        """
        owner = validated_data.get("owner")
        token = validated_data.get("token")
        type_ = validated_data.get("type")

        try:

            # try to connect the card instance with the users connected account or
            # customer resource. if a stripe error is raised, the token is invalid or
            # has been used and the client will need to submit a new token for security
            # purposes.
            if type_ == "merchant":
                instance = owner.stripe_account.add_payment_source(token)
            elif type_ == "customer":  # pragma: no branch
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
        exclude = ("stripe_id", )


class CreateBankAccountResourceSerializer(CreateCardResourceSerializer):
    """
    """
    class Meta:
        model = models.BankAccount
        return_serializer = BankAccountSerializer


class UpdateBankAccountResourceSerializer(StripeResourceSerializer):
    """
    """
    default_for_currency = serializers.NullBooleanField(required=False)

    class Meta:
        model = models.BankAccount
        return_serializer = BankAccountSerializer


class ConnectedAccountSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.ConnectedAccount
        exclude = ("stripe_id", )


class CreateConnectedAccountResourceSerializer(StripeResourceSerializer):
    """
    """
    country = serializers.CharField()
    managed = serializers.BooleanField()
    legal_entity = serializers.DictField()
    tos_acceptance = serializers.DictField()

    class Meta:
        model = models.ConnectedAccount
        return_serializer = ConnectedAccountSerializer

    def create(self, validated_data):
        owner = validated_data.pop("owner")
        instance = self.get_model_class().stripe_object_to_model(validated_data)
        instance.owner = owner
        instance.save()
        return instance


class LegalEntitySerializer(serializers.Serializer):
    """
    """
    address = serializers.DictField(required=False, allow_null=True)
    business_name = serializers.CharField(required=False, allow_null=True)
    business_tax_id = serializers.CharField(required=False, allow_null=True)
    business_vat_id = serializers.CharField(required=False, allow_null=True)
    dob = serializers.DictField(required=False, allow_null=True)
    first_name = serializers.CharField(required=False, allow_null=True)
    last_name = serializers.CharField(required=False, allow_null=True)
    personal_address = serializers.DictField(required=False, allow_null=True)
    personal_id_number = serializers.CharField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_null=True)
    ssn_last_4 = serializers.CharField(required=False, allow_null=True)


class UpdateConnectedAccountResourceSerializer(StripeResourceSerializer):
    """
    """
    business_logo = serializers.ImageField(required=False, allow_null=True)
    business_name = serializers.CharField(required=False, allow_null=True)
    business_primary_color = serializers.CharField(required=False, allow_null=True)
    business_url = serializers.URLField(required=False, allow_null=True)
    default_currency = serializers.CharField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)
    legal_entity = LegalEntitySerializer(required=False, allow_null=True)
    product_description = serializers.CharField(required=False, allow_null=True)
    statement_descriptor = serializers.CharField(required=False, allow_null=True)
    support_email = serializers.EmailField(required=False, allow_null=True)
    support_phone = serializers.CharField(required=False, allow_null=True)
    # external account will make THIS account the default payout method. this field
    # is a token returned by stripe.js or similar sdk
    external_account = serializers.CharField(required=False)

    class Meta:
        model = models.ConnectedAccount
        return_serializer = ConnectedAccountSerializer

    def _stripe_instance_update(self, instance, data):
        """ overrides the default behavior of the Stripe API which deletes the old
        external_account (default payout method), such that you are not required to
        clean up stale objects that are recorded locally.
        """
        new_ext = data.pop("external_account", None)
        if new_ext is not None:
            self.instance.add_payment_source(new_ext)
        instance = super()._stripe_instance_update(instance, data)
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.Subscription
        exclude = ("stripe_id", )


class CreateSubscriptionResourceSerializer(StripeListObjectSerializer):
    """
    """
    plan = serializers.PrimaryKeyRelatedField(queryset=models.Plan.objects.all())
    coupon = serializers.PrimaryKeyRelatedField(queryset=models.Coupon.objects.all(),
                                                required=False, allow_null=True)
    # though its not part of the model it is necessary for adding the subscription to
    # the customer instance
    customer = serializers.PrimaryKeyRelatedField(queryset=models.Customer.objects.all())

    class Meta:
        model = models.Subscription
        return_serializer = SubscriptionSerializer
        parent_model_field_name = "customer"
        list_object_name = "subscriptions"

    def create(self, validated_data):
        owner = validated_data.pop("owner")
        subscription = models.Subscription.stripe_object_to_model(validated_data)
        subscription.owner = owner
        subscription.save()
        return subscription


class UpdateSubscriptionResourceSerializer(StripeResourceSerializer):
    """
    """
    plan = serializers.PrimaryKeyRelatedField(queryset=models.Plan.objects.all(),
                                                required=False)
    coupon = serializers.PrimaryKeyRelatedField(queryset=models.Coupon.objects.all(),
                                                required=False, allow_null=True)

    class Meta:
        model = models.Subscription
        return_serializer = SubscriptionSerializer


# Customers can not be created by clients, this should be explicitly handled on the
# server side with an event hook after an account has been created.
class CustomerSerializer(serializers.ModelSerializer):
    """
    """
    default_source = DefaultSourceRelatedField(allow_null=True, read_only=True)

    class Meta:
        model = models.Customer
        exclude = ("stripe_id", )


class CustomerShippingSerializer(serializers.Serializer):
    """
    """
    address = serializers.DictField()
    name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_null=True)


class UpdateCustomerResourceSerializer(StripeResourceSerializer):
    """
    """
    TYPE_CHOICES = (
        ("bank_account", "bank_account"),
        ("card", "card")
        )

    coupon = serializers.CharField(required=False)
    default_source = serializers.IntegerField(required=False, allow_null=True)
    default_source_type = serializers.ChoiceField(choices=TYPE_CHOICES, required=False,
                                                    allow_null=True)
    email = serializers.EmailField(required=False)
    shipping = CustomerShippingSerializer(required=False)
    source = serializers.CharField(required=False)

    class Meta:
        model = models.Customer
        return_serializer = CustomerSerializer

    def _stripe_instance_update(self, instance, data):
        new_src = data.pop("source", None)
        default_src = data.pop("default_source", None)
        src_type = data.pop("default_source_type", None)

        if default_src and src_type == "bank_account":
            default_src = models.BankAccount.objects.get(id=default_src).stripe_id
        elif default_src and src_type == "card":  # pragma: no branch
            default_src = models.Card.objects.get(id=default_src).stripe_id

        data["default_source"] = default_src
        if new_src is not None:
            self.instance.add_payment_source(new_src)
        instance = super()._stripe_instance_update(instance, data)
        return instance


# READ ONLY OWNED RESOURCES #

class ChargeSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.Charge
        exclude = ("stripe_id", )


class TransferSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.Transfer
        exclude = ("stripe_id", )


class RefundSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = models.Refund
        exclude = ("stripe_id", )
