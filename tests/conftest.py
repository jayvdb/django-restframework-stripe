from django.conf import settings

import pytest
from rest_framework.test import APIClient

from model_mommy import mommy

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@pytest.fixture
def user(request):
    user = mommy.make(settings.AUTH_USER_MODEL, username="testman", password="testing")
    user.set_password("testing")
    user.is_active = True
    user.save()
    def fin():
        user.delete()
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
def api_client():
    return APIClient()
