from unittest import mock

import pytest
from model_bakery import baker as mommy

from rest_framework.reverse import reverse

from restframework_stripe.test import get_mock_resource
from restframework_stripe import models


@mock.patch("stripe.Transfer.create")
@pytest.mark.django_db
def test_create_transfer(transfer_create, managed_account, bank_account):
    kwargs = {
        "amount": 1000,
        "currency": "usd",
        "destination": managed_account.stripe_id
        }
    transfer_create.return_value = get_mock_resource("Transfer",
        bank_account=bank_account.source,
        source_type="bank_account",
        type="account",
        **kwargs)

    stripe_object = models.Transfer.stripe_api_create(**kwargs)
    transfer = models.Transfer.stripe_object_to_model(stripe_object)
    transfer.owner = managed_account.owner
    transfer.save()

    assert transfer.succeeded


@pytest.mark.django_db
def test_transfer_retrieve(managed_account, transfer, api_client):
    api_client.force_authenticate(managed_account.owner)
    transfer.owner = managed_account.owner
    transfer.save()

    uri = reverse("rf_stripe:transfer-detail", kwargs={"pk": transfer.pk})
    response = api_client.get(uri)

    assert response.status_code == 200, response.data


@pytest.mark.django_db
def test_options(managed_account, api_client):
    api_client.force_authenticate(managed_account.owner)
    uri = reverse("rf_stripe:transfer-list")
    response = api_client.options(uri)
    assert response.status_code == 200, response.data
