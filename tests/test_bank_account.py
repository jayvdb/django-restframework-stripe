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


@mock.patch("stripe.BankAccount.delete")
@mock.patch("stripe.BankAccount.retrieve")
@pytest.mark.django_db
def test_bank_account_delete(bank_account_retrieve, bank_account_delete, user, api_client):
    api_client.force_authenticate(user)
    bank_account_retrieve.return_value = get_mock_resource("BankAccount")
    bank_account_delete.return_value = None  # no one cares about this value... EVER
    bank_account = mommy.make(models.BankAccount, owner=user,
            source=get_mock_resource("BankAccount"))

    uri = reverse("rf_stripe:bank-account-detail", kwargs={"pk": bank_account.pk})
    response = api_client.delete(uri)

    assert response.status_code == 204
    assert not models.BankAccount.objects.filter(id=bank_account.id).exists()
