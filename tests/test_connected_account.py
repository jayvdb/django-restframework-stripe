from unittest import mock

from django.utils import timezone

import pytest
import stripe
from stripe.error import InvalidRequestError

from model_mommy import mommy

from rest_framework.reverse import reverse

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("stripe.Account.create")
@pytest.mark.django_db
def test_register_managed_account(account_create_mock, user, api_client):
    data = {
        "country": "US",
        "managed": True,
        "legal_entity": {
            "first_name": "test",
            "last_name": "man",
            "type": "individual",
            "dob": {
                "day": 9,
                "month": 1,
                "year": 1980
                }
            },
        "tos_acceptance": {
            "ip": "192.168.1.1",
            "date": int(timezone.now().timestamp())
            }
        }
    mock_keys = {"private": "sec_43ioJIO32", "publishable": "pub_jkJIJ390jF90"}
    api_client.force_authenticate(user)
    account_create_mock.return_value = get_mock_resource("Account",
        keys=mock_keys,
        verification={"fields_needed": ["external_account"]},
        **data
        )
    uri = reverse("rf_stripe:connected-account-list")

    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201
    assert response.data["owner"] == user.id
    assert response.data["managed"] == True
    assert response.data["secret_key"] == mock_keys["private"]
    assert response.data["publishable_key"] == mock_keys["publishable"]
    assert user.stripe_account in models.ConnectedAccount.objects.managed_accounts()


@mock.patch("stripe.Account.create")
@pytest.mark.django_db
def test_register_managed_account_error(account_create, user, api_client):
    data = {
        "country": "US",
        "managed": True,
        "legal_entity": {
            "first_name": "test",
            "last_name": "man",
            "type": "individual",
            "dob": {
                "day": 9,
                "month": 1,
                "year": 1980
                }
            },
        "tos_acceptance": {
            "ip": "192.168.1.1",
            "date": int(timezone.now().timestamp())
            }
        }
    mock_keys = {"private": "sec_43ioJIO32", "publishable": "pub_jkJIJ390jF90"}
    api_client.force_authenticate(user)
    account_create.side_effect = InvalidRequestError(param="dob",
            message="invalid date of birth")
    uri = reverse("rf_stripe:connected-account-list")

    response = api_client.post(uri, data=data, format="json")
    assert response.status_code == 400, response.data
    assert response.data["dob"] == "invalid date of birth"


@mock.patch("stripe.Account.delete")
@mock.patch("stripe.Account.retrieve")
@pytest.mark.django_db
def test_account_delete(account_retrieve, account_delete, user, api_client):
    api_client.force_authenticate(user)
    account_retrieve.return_value = get_mock_resource("Account", managed=True)
    account_delete.return_value = None  # no one cares about this value... EVER
    account = mommy.make(models.ConnectedAccount, owner=user, managed=True,
            source=get_mock_resource("Account", managed=True))

    uri = reverse("rf_stripe:connected-account-detail", kwargs={"pk": account.pk})
    response = api_client.delete(uri)

    assert response.status_code == 204
    assert not models.ConnectedAccount.objects.filter(id=account.id).exists()


@mock.patch("stripe.Account.save")
@mock.patch("stripe.Account.retrieve")
@pytest.mark.django_db
def test_update_connected_account(account_retrieve, account_update, managed_account,
                                    api_client):
    api_client.force_authenticate(managed_account.owner)
    data = managed_account.source
    data.update({
        "business_name": "targus"
        })
    account_retrieve.return_value = get_mock_resource("Account", managed=True)
    account_update.return_value = get_mock_resource("Account", **data)

    uri = reverse("rf_stripe:connected-account-detail", kwargs={"pk": managed_account.pk})
    response = api_client.put(uri, data=data, format="json")

    assert response.status_code == 200, response.data
    assert response.data["owner"] == managed_account.owner.id
    assert response.data["source"]["business_name"] == data["business_name"]


@mock.patch("stripe.Account.save")
@mock.patch("stripe.Account.retrieve")
@pytest.mark.django_db
def test_update_connected_account_error(account_retrieve, account_update, managed_account,
                                    api_client):
    api_client.force_authenticate(managed_account.owner)
    data = managed_account.source
    data.update({
        "business_name": "targus"
        })
    account_retrieve.return_value = get_mock_resource("Account", managed=True)
    account_update.side_effect = InvalidRequestError(param="business_name",
        message="no targuses allowed!")

    uri = reverse("rf_stripe:connected-account-detail", kwargs={"pk": managed_account.pk})
    response = api_client.put(uri, data=data, format="json")

    assert response.status_code == 400, response.data
    assert response.data["business_name"] == "no targuses allowed!"


@mock.patch("stripe.ListObject.create")
@mock.patch("stripe.Account.save")
@mock.patch("stripe.Account.retrieve")
@pytest.mark.django_db
def test_connected_account_add_payment_method(a_retrieve, a_update, l_create,
                                                managed_account, api_client):
    api_client.force_authenticate(managed_account.owner)
    data = {
        "external_account": "fkdsla;jfioewni3o2ndsa",
        "email": "test@test.com",
        "legal_entity": {
            "first_name": "ted",
            "last_name": "bed"
            }
        }
    updated_data = data.copy()
    updated_data.pop("external_account")

    a_retrieve.return_value = get_mock_resource("Account", managed=True)
    a_update.return_value = get_mock_resource("Account", managed=True, **updated_data)
    l_create.return_value = get_mock_resource("BankAccount")

    uri = reverse("rf_stripe:connected-account-detail", kwargs={"pk": managed_account.pk})
    response = api_client.patch(uri, data=data, format="json")

    assert response.status_code == 200, response.data
    assert 0 < models.BankAccount.objects.filter(owner=managed_account.owner).count()


@pytest.mark.django_db
def test_options(user, api_client):
    api_client.force_authenticate(user)
    uri = reverse("rf_stripe:connected-account-list")
    response = api_client.options(uri)
    assert response.status_code == 200, response.data
