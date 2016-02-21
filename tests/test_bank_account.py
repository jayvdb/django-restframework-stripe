from unittest import mock

import pytest
from model_mommy import mommy

from rest_framework.reverse import reverse

from restframework_stripe.test import get_mock_resource
from restframework_stripe import models


@mock.patch("stripe.ListObject.create")
@mock.patch("stripe.Account.retrieve")
@pytest.mark.django_db
def test_managed_account_adding_bank_account(account_retrieve_mock, ba_create_mock,
                                                managed_account, api_client):

    api_client.force_authenticate(managed_account.owner)
    account_retrieve_mock.return_value = get_mock_resource("Account", managed=True)
    ba_create_mock.return_value = get_mock_resource("BankAccount")
    data = {
        "token": "tok_dfsjio23jhOFio23",
        "type": "merchant"
        }
    uri = reverse("rf_stripe:bank-account-list")

    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201, response.data
    assert response.data["owner"] == managed_account.owner.id


@mock.patch("stripe.ListObject.create")
@mock.patch("stripe.Customer.retrieve")
@pytest.mark.django_db
def test_customer_adding_bank_account(customer_retrieve_mock, ba_create_mock,
                                                customer, api_client):

    api_client.force_authenticate(customer.owner)
    customer_retrieve_mock.return_value = get_mock_resource("Customer")
    ba_create_mock.return_value = get_mock_resource("BankAccount")
    data = {
        "token": "tok_dfsjio23jhOFio23",
        "type": "customer"
        }
    uri = reverse("rf_stripe:bank-account-list")

    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201, response.data
    assert response.data["owner"] == customer.owner.id
    ba = models.BankAccount.objects.get(id=response.data["id"])
    assert ba.is_usable


@mock.patch("stripe.Account.retrieve")
@mock.patch("stripe.BankAccount.save")
@mock.patch("stripe.ListObject.retrieve")
@pytest.mark.django_db
def test_bank_account_update(
        bank_account_retrieve,
        bank_account_update,
        account_retrieve,
        bank_account,
        managed_account,
        api_client):

    bank_account.owner = managed_account.owner
    bank_account.save()

    api_client.force_authenticate(bank_account.owner)
    data = {
        "default_for_currency": True,
        }

    bank_account_retrieve.return_value = bank_account.source
    bank_account_update.return_value = get_mock_resource("BankAccount", **data)
    account_retrieve.return_value = managed_account.source

    uri = reverse("rf_stripe:bank-account-detail", kwargs={"pk": bank_account.pk})
    response = api_client.patch(uri, data=data, format="json")

    bank_account.refresh_from_db()
    assert response.status_code == 200, response.data
    assert bank_account.source["default_for_currency"] is True


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.BankAccount.delete")
@mock.patch("stripe.ListObject.retrieve")
@pytest.mark.django_db
def test_bank_account_delete(
        bank_account_retrieve,
        bank_account_delete,
        customer_retrieve,
        bank_account,
        customer,
        api_client):

    bank_account.owner = customer.owner
    bank_account.source.pop("account", None)
    bank_account.source["customer"] = customer.stripe_id
    bank_account.save()

    api_client.force_authenticate(bank_account.owner)
    bank_account_retrieve.return_value = bank_account.source
    customer_retrieve.return_value = customer.source
    bank_account_delete.return_value = None  # no one cares about this value... EVER

    uri = reverse("rf_stripe:bank-account-detail", kwargs={"pk": bank_account.pk})
    response = api_client.delete(uri)

    assert response.status_code == 204
    assert not models.BankAccount.objects.filter(id=bank_account.id).exists()


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.ListObject.retrieve")
@pytest.mark.django_db
def test_bank_account_refresh(
        bank_account_retrieve,
        customer_retrieve,
        customer,
        bank_account,
        api_client):

    bank_account.owner = customer.owner
    bank_account.source.pop("account", None)
    bank_account.source["customer"] = customer.stripe_id
    bank_account.save()

    api_client.force_authenticate(bank_account.owner)
    customer_retrieve.return_value = customer.source
    bank_account_retrieve.return_value = get_mock_resource("BankAccount",
                                                            status="verification_failed")
    uri = reverse("rf_stripe:bank-account-refresh", kwargs={"pk": bank_account.pk})
    response = api_client.get(uri)

    bank_account.refresh_from_db()
    assert bank_account.status == "verification_failed"
    assert bank_account.is_usable is False
