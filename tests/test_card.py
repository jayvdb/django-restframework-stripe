from unittest import mock

import pytest
import stripe
from stripe.error import InvalidRequestError

from model_bakery import baker as mommy

from rest_framework.reverse import reverse

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.ListObject.create")
@pytest.mark.django_db
def test_create_stripe_card(card_create, customer_retrieve, customer,
                            api_client):
    api_client.force_authenticate(customer.owner)
    uri = reverse("rf_stripe:card-list")
    data = {
        "token": "jflkd;sajfdksa;"
        }

    card_create.return_value = get_mock_resource("Card")
    customer_retrieve.return_value = get_mock_resource("Customer")

    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201, "Request failed!"
    assert 0 < customer.owner.stripe_cards.count()


@mock.patch("stripe.Account.retrieve")
@mock.patch("stripe.ListObject.create")
@pytest.mark.django_db
def test_create_merchant_stripe_card(card_create, account_retrieve,
                                        managed_account, api_client):
    api_client.force_authenticate(managed_account.owner)
    uri = reverse("rf_stripe:card-list")
    data = {
        "token": "jflkd;sajfdksa;",
        "type": "merchant"
        }

    card_create.return_value = get_mock_resource("Card")
    account_retrieve.return_value = get_mock_resource("Account", managed=True)

    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201, "Request failed!"
    assert 0 < managed_account.owner.stripe_cards.count()


@pytest.mark.django_db
def test_retrieve_card(customer, api_client):
    api_client.force_authenticate(customer.owner)
    card = mommy.make(models.Card, owner=customer.owner, cvc_check="fail",
            source=get_mock_resource("Card", cvc_check="fail"))
    uri = reverse("rf_stripe:card-detail", kwargs={"pk": card.pk})
    response = api_client.get(uri)

    assert response.status_code == 200
    assert response.data["id"] == card.id
    assert response.data["owner"] == customer.owner.id
    assert response.data["cvc_check"] == "fail"
    assert card.is_usable is False


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.ListObject.create")
@pytest.mark.django_db
def test_card_create_error(card_create, customer_retrieve, customer, api_client):
    api_client.force_authenticate(customer.owner)
    uri = reverse("rf_stripe:card-list")
    data = {
        "token": "jflkd;sajfdksa;",
        "type": "customer"
        }
    customer_retrieve.return_value = get_mock_resource("Customer")
    card_create.side_effect = InvalidRequestError("invalid token!", "token")

    response = api_client.post(uri, data=data, format="json")
    assert response.status_code == 400
    assert response.data["token"] == "invalid token!"


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.Card.save")
@mock.patch("stripe.ListObject.retrieve")
@pytest.mark.django_db
def test_card_update(
        card_retrieve,
        card_update,
        customer_retrieve,
        customer,
        card,
        api_client):

    card.owner = customer.owner
    card.source.pop("account", None)
    card.source["customer"] = customer.stripe_id
    card.save()

    api_client.force_authenticate(card.owner)
    data = {
        "name": "Hans Solo",
        "exp_month": 1,
        "exp_year": 2019
        }

    customer_retrieve.return_value = customer.source
    card_retrieve.return_value = card.source
    card_update.return_value = get_mock_resource("Card", **data)

    uri = reverse("rf_stripe:card-detail", kwargs={"pk": card.pk})
    response = api_client.patch(uri, data=data, format="json")

    card.refresh_from_db()
    assert response.status_code == 200
    assert card.source["name"] == data["name"]
    assert card.source["exp_month"] == data["exp_month"]
    assert card.source["exp_year"] == data["exp_year"]


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.Card.delete")
@mock.patch("stripe.ListObject.retrieve")
@pytest.mark.django_db
def test_card_delete(
        card_retrieve,
        card_delete,
        customer_retrieve,
        customer,
        card,
        api_client):

    card.owner = customer.owner
    card.source.pop("account", None)
    card.source["customer"] = customer.stripe_id
    card.save()

    api_client.force_authenticate(card.owner)

    customer_retrieve = customer.source
    card_retrieve.return_value = card.source
    card_delete.return_value = None  # no one cares about this value... EVER

    uri = reverse("rf_stripe:card-detail", kwargs={"pk": card.pk})
    response = api_client.delete(uri)

    assert response.status_code == 204
    assert not models.Card.objects.filter(id=card.id).exists()


@pytest.mark.django_db
def test_options(user, api_client):
    api_client.force_authenticate(user)
    uri = reverse("rf_stripe:card-list")
    response = api_client.options(uri)
    assert response.status_code == 200, response.data
