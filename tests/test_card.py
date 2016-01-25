from unittest import mock

import pytest
import stripe
from model_mommy import mommy

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
    card_create.side_effect = stripe.InvalidRequestError("invalid token!", "token")

    response = api_client.post(uri, data=data, format="json")
    assert response.status_code == 400
    assert response.data["token"] == "invalid token!"


@mock.patch("stripe.Card.delete")
@mock.patch("stripe.Card.retrieve")
@pytest.mark.django_db
def test_card_delete(card_retrieve, card_delete, user, api_client):
    api_client.force_authenticate(user)
    card_retrieve.return_value = get_mock_resource("Card")
    card_delete.return_value = None  # no one cares about this value... EVER
    card = mommy.make(models.Card, owner=user, source=get_mock_resource("Card"))

    uri = reverse("rf_stripe:card-detail", kwargs={"pk": card.pk})
    response = api_client.delete(uri)

    assert response.status_code == 204
    assert not models.Card.objects.filter(id=card.id).exists()
