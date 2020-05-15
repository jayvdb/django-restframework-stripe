from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError as DJValidationError

import stripe
try:
    from stripe import convert_to_stripe_object
except ImportError:
    from stripe.util import convert_to_stripe_object

from . import managers
from .webhooks import webhooks


def _get_class_name(obj):
    try:
        return obj.class_name()
    except Exception:
        return obj.__class__.__name__.lower()


class StripeModel(models.Model):
    """ The abstract base model for all local representations of stripe resources. it
    provides methods for normal CRUD operations with corresponding stripe resources and
    stores the source stripe object retrieved from the api.

    ``STRIPE_API_NAME`` the corresponding name of the stripe resource, for instance
    *Account*.

    ``stripe_id`` the id that was returned by creating a stripe resource or retrieving
    the resource from a stripe Token instance.

    ``source`` the return value from stripe. it is important to set this attribute after
    creating, and updating a resource -- doing so gives a client an accurate account of
    the resource without requiring a round trip to stripe. this attribute should also be
    updated on any corresponding webhooks.
    """
    STRIPE_API_NAME = None

    stripe_id = models.CharField(max_length=100, unique=True)
    source = JSONField()

    class Meta:
        abstract = True

    def __str__(self):
        info = {
            "label": self._meta.label,
            "pk": self.pk,
            "stripe_resource": self.STRIPE_API_NAME,
            "stripe_id": self.stripe_id,
            }
        return "<{label}({pk}) :: {stripe_resource}({stripe_id})>".format(**info)

    @classmethod
    def get_stripe_api(cls):
        return getattr(stripe, cls.STRIPE_API_NAME)

    @classmethod
    def get_stripe_api_instance(cls, stripe_id):
        stripe_resource = cls.get_stripe_api()
        return stripe_resource.retrieve(stripe_id)

    @classmethod
    def stripe_api_create(cls, **kwargs):
        return cls.get_stripe_api().create(**kwargs)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = {
            "stripe_id": stripe_object.pop("id"),
            "source": stripe_object
            }
        return record

    @classmethod
    def stripe_object_to_model(cls, stripe_object):
        return cls(**cls.stripe_object_to_record(stripe_object))

    def stripe_object_sync(self, stripe_object):
        record = self.stripe_object_to_record(stripe_object)
        for key, value in record.items():
            setattr(self, key, value)
        return self

    def retrieve_stripe_api_instance(self):
        return self.get_stripe_api_instance(self.stripe_id)

    def refresh_from_stripe_api(self):
        stripe_object = self.retrieve_stripe_api_instance()
        self.stripe_object_sync(stripe_object)


class DefaultPaymentMixin(models.Model):
    """
    """
    currency = models.CharField(max_length=3, null=True, blank=True)
    default_for_currency = models.NullBooleanField()

    class Meta:
        abstract = True

    def retrieve_stripe_api_instance(self):
        """ The process for updating payment / payout methods for stripe objects is
        a bit different than other api objects. The steps involved are as follows.
        1) Determine if this object is owned by an Account or a Customer
        2) Retrieve the Account or Customer instace
        3) Retrieve the payment method instance using the `sources` or `external_account`
            parameter
        4) Perform Updates
        5) Call the `.save` method
        """
        owner = self.owner
        if self.source.get("account"):
            owner_param, source_param = "stripe_account", "external_accounts"
        else:
            owner_param, source_param = "stripe_customer", "sources"
        stripe_owner = getattr(owner, owner_param)
        stripe_owner = stripe_owner.retrieve_stripe_api_instance()
        instance = stripe_owner[source_param].retrieve(self.stripe_id)
        return instance

    def save(self, *args, **kwargs):
        if self.default_for_currency is True and self.currency:
            qs = type(self).objects.filter(owner=self.owner, currency=self.currency)
            if self.id is not None:  # pragma: no branch
                qs = qs.exclude(id=self.id)
            qs.update(default_for_currency=False)
        return super().save(*args, **kwargs)


class Customer(StripeModel):
    """ Each project will need Customer objects in order to add payment methods and
    make reoccuring charges to those payment methods. There are many attributes of the
    Customer object that a client can update that a specific project may be interested
    in. For instance, if your use case is a marketplace application that ships parcels to
    their customers you will want to fill out the ``Customer.shipping`` object to
    hold a record of their primary shipping address.

    A Customer resource can be created with no attributes. This enables you to create
    the record and collect more information on your customer as you go. For instance you
    can subscribe a customer to a Plan by setting the ``Customer.plan`` field to the id
    of a Plan you have setup with stripe. With a Plan and Card set for the Customer you
    can charge the customer on a reoccuring basis.

    Another field of interest is ``Customer.source``. This field is your Customers
    primary payment method. Your Customer can create as many BankAccounts or Cards as she
    wishes but this value will not change unless explicitly set. By default all Charges
    will make a charge to the customers primary source unless otherwise stated.

    For more information about the Customer resource see `Stripe Customer`_.

    .. _Stripe Customer:: https://stripe.com/docs/api/python#customer_object
    """
    STRIPE_API_NAME = "Customer"

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="stripe_customer")

    source_type = models.ForeignKey(ContentType, null=True)
    source_id = models.PositiveIntegerField(null=True)
    default_source = GenericForeignKey("source_type", "source_id")

    def add_payment_source(self, token):
        stripe_object = self.retrieve_stripe_api_instance()
        new_source = stripe_object.sources.create(source=token)

        class_name = _get_class_name(new_source)
        if class_name == "bankaccount":
            source = BankAccount.stripe_object_to_model(new_source)
        elif class_name == "card":
            source = Card.stripe_object_to_model(new_source)
        else:
            raise NotImplementedError(class_name)

        source.owner = self.owner
        source.save()
        return source

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        default_source = stripe_object.get("default_source", None)
        if default_source is not None and isinstance(default_source, stripe.error.StripeError):
            class_name = _get_class_name(default_source)
            if class_name == "bankaccount":
                default_source = BankAccount.objects.get(stripe_id=default_source["id"])
                record["default_source"] = default_source
            elif class_name == "card":  # pragma: no branch
                default_source = Card.objects.get(stripe_id=default_source["id"])
                record["default_source"] = default_source
        return record

    @classmethod
    def get_stripe_api_instance(cls, stripe_id):
        stripe_resource = cls.get_stripe_api()
        return stripe_resource.retrieve(stripe_id, expand=["default_source"])


class Card(DefaultPaymentMixin, StripeModel):
    """ While BankAccounts and other options are available Cards (credit / debit) are a
    primary source of payment for most projects. Luckily with stripe Cards are easy to
    register and verify, all it takes is document like this::

        {
            "number": "532280852315",
            "exp_month": 12,
            "exp_year": 1970,
            "cvc": "123",
            "name": "Simon Says"
        }

    It is best practice to create & validate cards on the client side and to send a
    single use token to a server to retrieve and store the non-sensative information. The
    Stripe.js library provides client side validation to check that a credit card number
    is infact valid before sending it to stripe in exchange for a Token.

    Cards can also be a primary source for ConnectedAccounts to collect payments. These
    must be debit cards and can only belong to a ConnectedAccount or Customer *not both*.

    For more information see `Stripe Card`_.

    .. _Stripe Card:: https://stripe.com/docs/api/python#card_object
    """
    STRIPE_API_NAME = "Card"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="stripe_cards")
    cvc_check = models.CharField(max_length=20, null=True, blank=True)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        record["cvc_check"] = stripe_object["cvc_check"]
        record["currency"] = stripe_object.get("currency")
        record["default_for_currency"] = stripe_object.get("default_for_currency")
        return record

    @property
    def is_usable(self):
        return self.cvc_check != "fail"


class Charge(StripeModel):
    """ A Charge is a read only resource for a client, allowing them to review the amount
    charged to their primary payment method. Creating a charge is handled on the server
    side and has associated webhooks confirming if the charge succeeded.

    The most basic Charge can be created like this::

        {
            "amount": 1000,
            "currency": "usd",
            "source": "tok_4j15JK4jkPdsa"  // token obtained with Stripe.js
        }

    A more thourough Charge will include the Customer and a source associated with that
    Customer::

        {
            "amount": 1000,
            "currency": "usd",
            "customer": "cus_JJio23JIO23HJInda",
            "source": "card_dION32nio90Nf"
        }

    A charge that is paid to a merchant (i.e. ConnectedAccount) also includes an
    application fee (a fee your platform gathers from the charge) and a destination (the
    id of a ConnectedAccount)::

        {
            "amount": 1000,
            "currency": "usd",
            "customer": "cus_JJio23JIO23HJInda",
            "source": "card_dION32nio90Nf",
            "destination": "acct_IJojifo23jIOjP"
        }

    It is also best practice to include an up to 22 character statement descriptor that
    will be displayed on your Customers credit/debit card statement.

    For more information see `Stripe Charge`_.

    .. _Stripe Charge:: https://stripe.com/docs/api/python#charge_object
    """
    STRIPE_API_NAME = "Charge"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="stripe_charges")
    status = models.CharField(max_length=25)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        record["status"] = stripe_object["status"]
        return record

    def retrieve_payment_source(self):
        """
        """
        source = convert_to_stripe_object(self.source["source"], None, None)
        class_name = _get_class_name(source)
        if class_name == "card":
            s = Card.objects.get(stripe_id=source["id"])
        elif class_name == "bankaccount":
            s = BankAccount.objects.get(stripe_id=source["id"])
        else:
            raise NotImplementedError(class_name)
        return s

    @property
    def succeeded(self):
        return self.status == "succeeded"


class ConnectedAccount(StripeModel):
    """ This is the base representation of a stripe Account resource that is either
    registered with or managed by your platform. ConnectedAccounts are semantically
    equivalent to merchants in a marketplace application. These merchants receive payment
    through your platform via the `destination` attribute of a Charge or through the
    destination attribute of Transfers.

    Many fields are required to confirm a clients identity, but the number of fields
    scales proportionately with the amount of funds the merchant is earning through your
    platform. As more fields are required to ensure the merchants identity, webhooks are
    sent to your platform asking for additional fields in the
    `Account.verification.fields_needed` dict. Stripe states that it is a best practice
    to get a minimum of the following fields when registering a managed ConnectedAccount:

    * legal_entity.type
    * legal_entity.first_name
    * legal_entity.last_name
    * legal_entity.dob
    * tos_acceptance.ip
    * tos_acceptance.date

    With this information your managed account can begin to earn up to a few thousand
    dollars before needing to supply additional identity verification materials.

    Registering your platform with a *standalone* Account is a two step oauth procedure
    part two of which can be handled by the ConnectedAccounts manager. Essentially, like
    any oauth account, the client is directed to stripe to confirm your platform then
    redirected back to your platform with some important pieces of information that are
    stored in this model -- namely `access_token` and `refresh_token`. Unlike managed
    Accounts, you will have to include the access token in any request from your platform
    that updates your clients stripe Account, otherwise the Account is read-only.

    For more information on Accounts see `Stripe Account`_.
    For best practices with managed Accounts see `Managed Accounts`_.
    For more information on connecting standalone accounts see `Standalone Accounts`_.

    .. _Stripe Account:: https://stripe.com/docs/api/python#account_object
    .. _Managed Accounts:: https://stripe.com/docs/connect/best-practices
    .. _Standalone Accounts:: https://stripe.com/docs/connect/standalone-accounts
    """
    STRIPE_API_NAME = "Account"

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="stripe_account")
    managed = models.BooleanField()

    secret_key = models.CharField(max_length=120, null=True, blank=True)
    publishable_key = models.CharField(max_length=120, null=True, blank=True)
    access_token = models.CharField(max_length=120, null=True, blank=True)
    refresh_token = models.CharField(max_length=120, null=True, blank=True)

    objects = managers.ConnectedAccountManager()

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        keys = stripe_object.pop("keys", None)

        record = super().stripe_object_to_record(stripe_object)
        record["managed"] = stripe_object["managed"]

        if keys is not None:
            record["publishable_key"] = keys.get("publishable")
            record["secret_key"] = keys.get("private")
            record["access_token"] = keys.get("access_token")
            record["refresh_token"] = keys.get("refresh_token")
        return record

    def add_payment_source(self, token):
        stripe_object = self.retrieve_stripe_api_instance()
        new_source = stripe_object.external_accounts.create(external_account=token)

        class_name = _get_class_name(new_source)
        if class_name == "bankaccount":
            source = BankAccount.stripe_object_to_model(new_source)
        elif class_name == "card":
            source = Card.stripe_object_to_model(new_source)
        else:
            raise NotImplementedError(class_name)

        source.owner = self.owner
        source.save()
        return source


class BankAccount(DefaultPaymentMixin, StripeModel):
    """ BankAccounts are resources specifically for distributing payments to
    ConnectedAccounts; If a merchant would like to have their earnings deposited directly
    to their bank account rather than a debit card. BankAccounts are created on the
    client side using Stripe.js and retrieved with the stripe Token resource on the
    server side where they can be added as a payment source to a ConnectedAccount.

    BankAccounts can also be added as a payment source for a Customer, though I can't be
    certain that many customers would prefer to use their bank account over a credit card
    for making payments.

    For more information on BankAccounts see `Stripe BankAccount`_.

    .. _Stripe BankAccount:: https://stripe.com/docs/api/python#bank_account_object
    """
    STRIPE_API_NAME = "BankAccount"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name="stripe_bank_accounts")
    status = models.CharField(max_length=20)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        record["status"] = stripe_object["status"]
        record["currency"] = stripe_object.get("currency")
        record["default_for_currency"] = stripe_object.get("default_for_currency")
        return record

    @property
    def is_usable(self):
        return self.status not in ("verification_failed", "errored")


class Transfer(StripeModel):
    """ A Transfer resource is used to move money from your platform to a
    ConnectedAccount. This is one of two ways to pay the merchants connected to your
    platform, the other being the `destination` parameter of a Charge resource.

    To create a transfer you will need a document like this::

        {
            "amount": 1000,
            "currency": "usd",
            "destination": "bank_Djfif3892hChjkLf"
        }

    Where `distination` is an id of a ConnectedAccount, BankAccount or Card to transfer
    funds to.

    It is also best to include a `description` and `statement_descriptor` so the receiver
    of the Transfer knows exactly what it is. In most cases, complying with Stripe, a
    Transfer is not meant to be explicitly created by your platform. So most transfers
    **MUST** be directly link to an incoming charge through the `source_transaction`
    parameter. For more information on special case transfers see `Custom Transfers`_.

    .. _Custom Transfers:: https://stripe.com/docs/connect/special-case-transfers

    For more information on the Transfer resource see `Stripe Transfer`_.

    .. _Stripe Transfer:: https://stripe.com/docs/api/python#transfer_object
    """
    STRIPE_API_NAME = "Transfer"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="stripe_transfers")
    status = models.CharField(max_length=20)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        record["status"] = stripe_object["status"]
        return record

    @property
    def succeeded(self):
        return self.status not in ("canceled", "failed")


class Subscription(StripeModel):
    """ A subscription is a resource used to create reoccuring charges to customers based
    on a Plan.

    For more information on the Subscription resource see `Stripe Subscription`_.

    .. _Stripe Subscription:: https://stripe.com/docs/api/python#subscription_object
    """
    STRIPE_API_NAME = "Subscription"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name="stripe_subscriptions")

    plan = models.ForeignKey("Plan", related_name="subscriptions")
    coupon = models.ForeignKey("Coupon", null=True, related_name="subscriptions")
    canceled = models.BooleanField(default=False)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        record["plan"] = Plan.objects.get(stripe_id=stripe_object["plan"]["id"])
        if stripe_object.get("discount", None) is not None:
            coupon = stripe_object["discount"]["coupon"]["id"]
            record["coupon"] = Coupon.objects.get(stripe_id=coupon)
        return record

    def retrieve_stripe_api_instance(self):
        customer = self.owner.stripe_customer
        customer = customer.retrieve_stripe_api_instance()
        instance = customer.subscriptions.retrieve(self.stripe_id)
        return instance


class Event(StripeModel):
    """
    """
    STRIPE_API_NAME = "Event"

    event_type = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)
    # since a webhook is an open uri we need to verify the existance of the Event with
    # stripe before doing anything with it.
    verified = models.BooleanField(default=False)

    @classmethod
    def stripe_object_to_record(cls, stripe_object):
        record = super().stripe_object_to_record(stripe_object)
        record["event_type"] = stripe_object["type"]
        return record

    def process(self):
        """ process the stripe event by distributing this object and its source to all
        *registered* webhook handlers.
        """
        if self.processed:  # pragma: no cover
            return

        verified = self.verify()
        if not verified:  # pragma: no cover
            return

        event_type, event_subtype = self.event_type.split(".", 1)
        try:
            webhooks.call_handlers(self, self.source["data"], event_type, event_subtype)
            self.processed = True
            self.save()
        except stripe.error.StripeError as err:
            EventProcessingError.objects.create(
                event=self,
                message=err._message,
                )

    def verify(self):
        """ try to verify the existance of the event with stripe. if the event doesn't
        exist, then it is likely some hacker is attempting to send fake events to the
        open webhook endpoint.
        """
        try:
            stripe_object = self.retrieve_stripe_api_instance()
            self.stripe_object_sync(stripe_object)
            self.verified = True
            self.save()
        except stripe.error.StripeError as err:
            EventProcessingError.objects.create(
                error_type=EventProcessingError.VALIDATING,
                event=self,
                message=err._message
                )
        return self.verified


class EventProcessingError(models.Model):
    """ this is a helper model specifically for capturing errors encountered while
    validating or processing a stripe Event.
    """
    PROCESSING = 0
    VALIDATING = 1
    ERROR_TYPES = (
        (PROCESSING, "processing"),
        (VALIDATING, "validating"),
        )

    error_type = models.SmallIntegerField(choices=ERROR_TYPES, default=PROCESSING)
    event = models.ForeignKey(Event, related_name="processing_errors")
    message = models.TextField()
    datetime_created = models.DateTimeField(auto_now_add=True)


class Plan(StripeModel):
    """ The Plan resource, unlike many of the client editable resources, is read-only to
    end users. A Plan should be created by admin users (likely using the Django admin
    interface). Also, unlike client editable resources, this model is created in a
    local database before creating the resource with Stripe.

    Plans are used to setup reoccuring charges through Subscriptions

    ``name`` the unique identifier for this Plan, such as 'gold'.
    ``amount`` the total amount to charge per interval in cents.
    ``currency`` the 3 character ISO code for the country.
    ``name_on_invoice`` the name of the plan to be displayed on invoices in the Stripe
    web interface.
    ``interval`` the interval at which to charge a subscriber (per day, month, week or
    year).
    ``statement_descriptor`` a 22 character max description that will be displayed on a
    subscribers credit card statement.
    ``interval_count`` the number of intervals between each subscription billing.
    ``trial_period_days`` the number of days in which this plan is free.

    .. note::

        Plan.objects.create_resource_from_model() should be called **BEFORE** saving the
        model instance. If `.save()` is called before then an integrity error will be
        raised because the `stripe_id` field is blank.
    """
    STRIPE_API_NAME = "Plan"

    DAILY = 0
    WEEKLY = 1
    MONTHLY = 2
    YEARLY = 3
    INTERVAL_CHOICES = (
        (DAILY, "day"),
        (WEEKLY, "week"),
        (MONTHLY, "month"),
        (YEARLY, "year")
        )

    name = models.CharField(max_length=120, unique=True)
    amount = models.PositiveIntegerField()
    interval = models.PositiveSmallIntegerField(choices=INTERVAL_CHOICES)
    name_on_invoice = models.CharField(max_length=50)
    statement_descriptor = models.CharField(max_length=22)
    interval_count = models.PositiveSmallIntegerField(default=1)
    trial_period_days = models.PositiveIntegerField(null=True)

    is_created = models.BooleanField(default=False)

    objects = managers.PlanManager()

    def save(self, *args, **kwargs):
        """
        :raises: django.core.exceptions.ValidationError
        """
        if not self.is_created:
            type(self).objects.create_resource_from_model(self)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        stripe_object = self.retrieve_stripe_api_instance()
        stripe_object.delete()
        return super().delete(*args, **kwargs)


class Coupon(StripeModel):
    """
    """
    STRIPE_API_NAME = "Coupon"

    FOREVER = 0
    ONCE = 1
    REPEATING = 2
    DURATION_CHOICES = (
        (FOREVER, "forever"),
        (ONCE, "once"),
        (REPEATING, "repeating")
        )

    duration = models.PositiveSmallIntegerField(choices=DURATION_CHOICES)
    amount_off = models.PositiveIntegerField(null=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    duration_in_months = models.PositiveSmallIntegerField(null=True)
    max_redemptions = models.PositiveIntegerField(null=True)
    percent_off = models.PositiveSmallIntegerField(null=True)
    redeem_by = models.DateTimeField(null=True)

    is_created = models.BooleanField(default=False)

    objects = managers.CouponManager()

    def clean(self, *args, **kwargs):
        if not any([self.amount_off, self.percent_off]):
            raise DJValidationError(message="One of `amount_off`, `percent_off` must be set.")
        elif all([self.amount_off, self.percent_off]):
            raise DJValidationError(message="Both `amount_off` and `percent_off` can not be set.")

        if self.amount_off and not self.currency:
            raise DJValidationError(message={"currency": "This field can not be null."})

        if self.duration == self.REPEATING and not self.duration_in_months:
            raise DJValidationError(message={"duration_in_months": "This field can not be null."})

    def save(self, *args, **kwargs):
        """
        :raises: django.core.exceptions.ValidationError
        """
        self.clean()
        if not self.is_created:
            type(self).objects.create_resource_from_model(self)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        stripe_object = self.retrieve_stripe_api_instance()
        stripe_object.delete()
        return super().delete(*args, **kwargs)


class Refund(StripeModel):
    """
    """
    STRIPE_API_NAME = "Refund"

    DUPLICATE = 0
    FRAUDULENT = 1
    REQUESTED = 2
    REFUND_REASON_CHOICES = (
        (DUPLICATE, "duplicate"),
        (FRAUDULENT, "fraudulent"),
        (REQUESTED, "requested_by_customer")
        )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="stripe_refunds")

    charge = models.ForeignKey("Charge", related_name="refunds")
    amount = models.PositiveIntegerField()
    reason = models.PositiveSmallIntegerField(choices=REFUND_REASON_CHOICES)
    refund_application_fee = models.NullBooleanField()
    reverse_transfer = models.NullBooleanField()

    is_created = models.BooleanField(default=False)

    objects = managers.RefundManager()

    def save(self, *args, **kwargs):
        """
        :raises: django.core.exceptions.ValidationError
        """
        if not self.is_created:
            type(self).objects.create_resource_from_model(self)
        super().save(*args, **kwargs)
