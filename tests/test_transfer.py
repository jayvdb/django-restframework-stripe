from unittest import mock

import pytest
from model_mommy import mommy

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
