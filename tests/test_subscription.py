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
def test_create_subscription(create_sub, retrieve_customer, plan, customer, api_client):
    create_sub.return_value = get_mock_resource("Subscription", plan=plan.source)
    retrieve_customer.return_value = get_mock_resource("Customer")
    api_client.force_authenticate(customer.owner)

    data = {
        "plan": plan.id,
        "coupon": None
        }
    uri = reverse("rf_stripe:subscription-list")
    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201, response.data
    assert 0 < customer.owner.stripe_subscriptions.count()


@mock.patch("stripe.Customer.retrieve")
@mock.patch("stripe.ListObject.create")
@pytest.mark.django_db
def test_create_subscription_with_coupon(create_sub, retrieve_customer, plan, coupon,
                                            customer, api_client):
    create_sub.return_value = get_mock_resource("Subscription",
            plan=plan.source,
            discount={"coupon": coupon.source})
    retrieve_customer.return_value = get_mock_resource("Customer")
    api_client.force_authenticate(customer.owner)

    data = {
        "plan": plan.id,
        "coupon": coupon.id
        }
    uri = reverse("rf_stripe:subscription-list")
    response = api_client.post(uri, data=data, format="json")

    assert response.status_code == 201, response.data
    assert 0 < customer.owner.stripe_subscriptions.count()


@mock.patch("stripe.Subscription.save")
@mock.patch("stripe.Subscription.retrieve")
@pytest.mark.django_db
def test_update_subscription(sub_retrieve, sub_update, customer, subscription,
                                api_client, coupon):
    subscription.owner = customer.owner
    subscription.save()
    api_client.force_authenticate(customer.owner)

    data = {
        "coupon": coupon.id
        }

    sub_retrieve.return_value = get_mock_resource("Subscription",
                                                    plan=subscription.plan.source)
    sub_update.return_value = get_mock_resource("Subscription",
        plan=subscription.plan.source,
        discount={"coupon": coupon.source})

    uri = reverse("rf_stripe:subscription-detail", kwargs={"pk": subscription.pk})
    response = api_client.patch(uri, data=data, format="json")

    assert response.status_code == 200, response.data
