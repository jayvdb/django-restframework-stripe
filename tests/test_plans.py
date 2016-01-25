from unittest import mock

import pytest

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("stripe.Plan.create")
@pytest.mark.django_db
def test_create_plan(create_plan):
    kwargs = {
        "name": "test plan",
        "amount": 1000,
        "interval": models.Plan.MONTHLY,
        "name_on_invoice": "test plan monthly charge",
        "statement_descriptor": "TESTPLANCHARGE",
        }
    mocked_plan =  get_mock_resource("Plan",
        id="test plan",
        amount=1000,
        interval="month",
        name="test plan monthly charge",
        statement_descriptor= "TESTPLANCHARGE")

    create_plan.return_value = mocked_plan
    plan = models.Plan(**kwargs)
    plan.save()

    assert plan.is_created
    assert plan.stripe_id == mocked_plan["id"]
    assert plan.source["interval"] == "month"
