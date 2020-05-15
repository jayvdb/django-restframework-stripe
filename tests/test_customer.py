from unittest import mock

import pytest
import stripe
from model_mommy import mommy

from rest_framework.reverse import reverse

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("stripe.Customer.save")
@mock.patch("stripe.Customer.retrieve")
@pytest.mark.django_db
def test_customer_update_bank_acct(customer_retrieve, customer_update, customer,
                                    bank_account, api_client):
    bank_account.owner = customer.owner
    bank_account.save()
    api_client.force_authenticate(customer.owner)
    data = {
        "default_source": bank_account.id,
        "default_source_type": "bank_account"
        }

    customer_retrieve.return_value = get_mock_resource("Customer")
    customer_update.return_value = get_mock_resource("Customer", default_source=bank_account.source)

    uri = reverse("rf_stripe:customer-detail", kwargs={"pk": customer.pk})
    response = api_client.patch(uri, data=data, format="json")

    customer.refresh_from_db()
    assert response.status_code == 200, response.data
    if customer.default_source:
        assert customer.default_source.id == bank_account.id
    else:
        assert customer.source['default_source']['id'] == bank_account.stripe_id


@mock.patch("stripe.Customer.save")
@mock.patch("stripe.Customer.retrieve")
@pytest.mark.django_db
def test_customer_update_card(customer_retrieve, customer_update, customer, card, api_client):
    card.owner = customer.owner
    card.save()
    api_client.force_authenticate(customer.owner)
    data = {
        "default_source": card.id,
        "default_source_type": "card"
        }

    customer_retrieve.return_value = get_mock_resource("Customer")
    customer_update.return_value = get_mock_resource("Customer", default_source=card.source)

    uri = reverse("rf_stripe:customer-detail", kwargs={"pk": customer.pk})
    response = api_client.patch(uri, data=data, format="json")

    customer.refresh_from_db()
    assert response.status_code == 200, response.data
    if customer.default_source:
        assert customer.default_source.id == card.id
    else:
        assert customer.source['default_source']['id'] == card.stripe_id


@pytest.mark.django_db
def test_customer_to_record_with_card_as_source(card):
    stripe_object = get_mock_resource("Customer", default_source=card.source)
    record = models.Customer.stripe_object_to_record(stripe_object)
    print(record)
    if record.get("default_source", None):
        assert record["default_source"].id == card.id
    else:
        assert record["source"]["default_source"].id == card.stripe_id


@pytest.mark.django_db
def test_customer_to_record_with_bank_account_as_source(bank_account):
    stripe_object = get_mock_resource("Customer", default_source=bank_account.source)
    record = models.Customer.stripe_object_to_record(stripe_object)
    print(record)
    if record.get("default_source", None):
        assert record["default_source"].id == bank_account.id
    else:
        assert record["source"]["default_source"].id == bank_account.stripe_id


@pytest.mark.django_db
def test_customer_to_record_with_string_as_source():
    stripe_object = get_mock_resource("Customer", default_source="bjkldjkfd532")
    record = models.Customer.stripe_object_to_record(stripe_object)
    assert record.get("default_source", None) is None
    if record.get("source", None):
        assert record["source"].get("defailt_source", None) is None


@mock.patch("stripe.ListObject.create")
@mock.patch("stripe.Customer.save")
@mock.patch("stripe.Customer.retrieve")
@pytest.mark.django_db
def test_customer_add_payment_method(a_retrieve, a_update, l_create, customer, api_client):
    api_client.force_authenticate(customer.owner)
    data = {
        "source": "fkdsla;jfioewni3o2ndsa",
        "email": "test@test.com",
        }
    new_card = get_mock_resource("Card")

    updated_data = data.copy()
    updated_data.pop("source")
    updated_data["default_source"] = new_card

    a_retrieve.return_value = get_mock_resource("Customer")
    l_create.return_value = new_card
    a_update.return_value = get_mock_resource("Customer", **updated_data)

    uri = reverse("rf_stripe:customer-detail", kwargs={"pk": customer.pk})
    response = api_client.patch(uri, data=data, format="json")

    customer.refresh_from_db()
    assert response.status_code == 200, response.data
    assert 0 < models.Card.objects.filter(owner=customer.owner).count()
    assert customer.source["email"] == data["email"]


@pytest.mark.django_db
def test_options(customer, api_client):
    api_client.force_authenticate(customer.owner)
    uri = reverse("rf_stripe:customer-list")
    response = api_client.options(uri)
    assert response.status_code == 200, response.data
