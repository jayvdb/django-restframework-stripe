from unittest import mock

import pytest
import stripe
from model_bakery import baker as mommy

from rest_framework.reverse import reverse

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("stripe.Charge.create")
@pytest.mark.django_db
def test_create_stripe_charge(create_charge, card):
    kwargs = {
        "amount": 1000,
        "currency": "usd",
        "source": card.stripe_id,
        }
    create_charge.return_value = get_mock_resource("Charge",
            status="succeeded",
            source=card.source,
            amount=1000,
            currency="usd")
    stripe_object = models.Charge.stripe_api_create(**kwargs)
    charge_model = models.Charge.stripe_object_to_model(stripe_object)
    charge_model.owner = card.owner
    charge_model.save()

    assert charge_model.succeeded
    assert charge_model.retrieve_payment_source().id == card.id


@mock.patch("stripe.Charge.create")
@pytest.mark.django_db
def test_create_stripe_bank_account_charge(create_charge, bank_account):
    kwargs = {
        "amount": 1000,
        "currency": "usd",
        "source": bank_account.stripe_id,
        }
    create_charge.return_value = get_mock_resource("Charge",
            status="succeeded",
            source=bank_account.source,
            amount=1000,
            currency="usd")
    stripe_object = models.Charge.stripe_api_create(**kwargs)
    charge_model = models.Charge.stripe_object_to_model(stripe_object)
    charge_model.owner = bank_account.owner
    charge_model.save()

    assert charge_model.succeeded
    assert charge_model.retrieve_payment_source().id == bank_account.id


@pytest.mark.django_db
def test_transfer_retrieve(customer, charge, api_client):
    api_client.force_authenticate(customer.owner)
    charge.owner = customer.owner
    charge.save()

    uri = reverse("rf_stripe:charge-detail", kwargs={"pk": charge.pk})
    response = api_client.get(uri)

    assert response.status_code == 200, response.data


@pytest.mark.django_db
def test_options(customer, api_client):
    api_client.force_authenticate(customer.owner)
    uri = reverse("rf_stripe:charge-list")
    response = api_client.options(uri)
    assert response.status_code == 200, response.data
