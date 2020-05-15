from unittest import mock

from django.core.exceptions import ValidationError

import pytest
from model_mommy import mommy
import stripe

from rest_framework.reverse import reverse

from stripe.error import InvalidRequestError

from restframework_stripe.test import get_mock_resource
from restframework_stripe import models


@mock.patch("stripe.Refund.create")
@pytest.mark.django_db
def test_creating_refund(create_refund, charge):
    create_refund.return_value = get_mock_resource("Refund",
            amount=charge.source["amount"], charge=charge.stripe_id)
    refund = models.Refund(
        charge=charge,
        amount=charge.source["amount"],
        reason=models.Refund.DUPLICATE
        )
    refund.save()


@mock.patch("stripe.Refund.create")
@pytest.mark.django_db
def test_creating_refund_error(create_refund, charge):
    create_refund.side_effect = InvalidRequestError(param="charge", message="no")
    refund = models.Refund(
        charge=charge,
        amount=charge.source["amount"],
        reason=models.Refund.DUPLICATE
        )

    with pytest.raises(ValidationError) as err:
        refund.save()

    assert err.value.message_dict == {"charge": ["no"]}


@pytest.mark.django_db
def test_customer_viewing_refund(refund, customer, api_client):
    refund.owner = customer.owner
    refund.save()
    api_client.force_authenticate(customer.owner)

    uri = reverse("rf_stripe:refund-detail", kwargs={"pk": refund.pk})
    response = api_client.get(uri)

    assert response.status_code == 200, response.data


@pytest.mark.django_db
def test_options(customer, api_client):
    api_client.force_authenticate(customer.owner)
    uri = reverse("rf_stripe:refund-list")
    response = api_client.options(uri)
    assert response.status_code == 200, response.data
