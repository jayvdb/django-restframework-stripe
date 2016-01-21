from unittest import mock

from django.utils import timezone

import pytest

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
