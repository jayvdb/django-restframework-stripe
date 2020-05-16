from unittest import mock
from django.conf import settings

import pytest
from rest_framework.test import APIClient

from model_bakery import baker as mommy

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@pytest.fixture
def refund(charge, request):
    source = get_mock_resource("Refund", charge=charge.stripe_id,
            amount=charge.source["amount"])
    refund = mommy.make(models.Refund,
            owner=charge.owner, is_created=True, charge=charge,
            reason=models.Refund.DUPLICATE, amount=source["amount"],
            stripe_id=source["id"], source=source)

    def fin():
        refund.delete()
    request.addfinalizer(fin)

    return refund


@pytest.fixture
def subscription(plan, request):
    source = get_mock_resource("Subscription", plan=plan.stripe_id)
    subscription = mommy.make(models.Subscription, stripe_id=source["id"],
            source=source, plan=plan)

    def fin():
        subscription.delete()
    request.addfinalizer(fin)

    return subscription


@pytest.fixture
def charge(request):
    source = get_mock_resource("Charge")
    charge = mommy.make(models.Charge, stripe_id=source["id"], source=source)

    def fin():
        charge.delete()
    request.addfinalizer(fin)

    return charge


@pytest.fixture
def transfer(request):
    source = get_mock_resource("Transfer")
    transfer = mommy.make(models.Transfer, stripe_id=source["id"], source=source)

    def fin():
        transfer.delete()
    request.addfinalizer(fin)

    return transfer


@pytest.fixture
def event(request):
    source = get_mock_resource("Event")
    event = mommy.make(models.Event, source=source, stripe_id=source["id"],
                        verified=False, processed=False, event_type=source["type"])

    def fin():
        event.delete()
    request.addfinalizer(fin)

    return event


@pytest.fixture
def coupon(request):
    source = get_mock_resource("Coupon")
    coupon = mommy.make(models.Coupon,
        duration=models.Coupon.ONCE,
        percent_off=75,
        stripe_id=source["id"],
        source=source,
        is_created=True)

    @mock.patch("stripe.Coupon.delete")
    @mock.patch("stripe.Coupon.retrieve")
    def fin(ret_plan, del_plan):
        ret_plan.return_value = get_mock_resource("Coupon")
        del_plan.return_value = None
        coupon.delete()
    request.addfinalizer(fin)

    return coupon


@pytest.fixture
def plan(request):
    source = get_mock_resource("Plan")
    plan = mommy.make(models.Plan, stripe_id=source["id"], source=source, is_created=True)

    @mock.patch("stripe.Plan.delete")
    @mock.patch("stripe.Plan.retrieve")
    def fin(ret_plan, del_plan):
        ret_plan.return_value = get_mock_resource("Plan")
        del_plan.return_value = None
        plan.delete()
    request.addfinalizer(fin)

    return plan


@pytest.fixture
def card(request):
    source = get_mock_resource("Card")
    card = mommy.make(models.Card, stripe_id=source["id"], source=source)
    def fin():
        card.delete()
    request.addfinalizer(fin)
    return card


@pytest.fixture
def user(request):
    user = mommy.make(settings.AUTH_USER_MODEL, username="testman", password="testing")
    user.set_password("testing")
    user.is_active = True
    user.save()
    def fin():
        user.delete()
    request.addfinalizer(fin)
    return user

@pytest.fixture
def customer(request):
    source = get_mock_resource("Customer")
    customer = mommy.make(models.Customer,
        stripe_id=source["id"],
        source=source
        )
    def fin():
        customer.delete()
    request.addfinalizer(fin)
    return customer


@pytest.fixture
def managed_account(request):
    source = get_mock_resource("Account", managed=True)
    account = mommy.make(models.ConnectedAccount,
        stripe_id=source["id"],
        managed=True,
        source=source
        )
    def fin():
        account.delete()
    request.addfinalizer(fin)
    return account


@pytest.fixture
def bank_account(request):
    source = get_mock_resource("BankAccount")
    bank_account = mommy.make(models.BankAccount,
        stripe_id=source["id"],
        source=source
        )
    def fin():
        bank_account.delete()
    request.addfinalizer(fin)
    return bank_account


@pytest.fixture
def api_client():
    return APIClient()
