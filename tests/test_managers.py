from unittest import mock

from django.core.exceptions import ValidationError

import pytest
from stripe.error import InvalidRequestError

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("requests.post")
@mock.patch("stripe.Account.retrieve")
@pytest.mark.django_db
def test_register_standalone_account(retrieve_account_mock, post_mock, user):
    data = {
        "token_type": "bearer",
        "stripe_publishable_key": "pub_89jIOH23NUNhjs3",
        "scope": "read_write",
        "livemode": True,
        "stripe_user_id": "acct_djio33fnioN",
        "refresh_token": "tok_234jkods9J",
        "access_token": "tok_fdjIOfj389hFho3"
        }
    post_mock.return_value = mock.Mock(json=mock.Mock(return_value=data))
    retrieve_account_mock.return_value = get_mock_resource("Account",
            id=data["stripe_user_id"])
    connected = models.ConnectedAccount.objects.connect_standalone_account(user, "jjj")

    assert connected.stripe_id == data["stripe_user_id"]
    assert connected.publishable_key == data["stripe_publishable_key"]
    assert connected.refresh_token == data["refresh_token"]
    assert connected.access_token == data["access_token"]
    assert connected in models.ConnectedAccount.objects.standalone_accounts()


@mock.patch("requests.post")
@pytest.mark.django_db
def test_register_standalone_account_access_token_failure(post_mock, user):
    data = {
        "error": "invalid_grant",
        "error_description": "Authorization code does not exist: jjj"
        }
    post_mock.return_value = mock.Mock(json=mock.Mock(return_value=data))

    with pytest.raises(InvalidRequestError) as err:
        models.ConnectedAccount.objects.connect_standalone_account(user, "jjj")
        assert err.param == data["error"]
        assert err._message == data["error_description"]


@mock.patch("stripe.Plan.create")
@pytest.mark.django_db
def test_plan_manager_create(plan_create_mock):
    plan_create_mock.return_value = get_mock_resource("Plan", id="Gold Plan")
    plan = models.Plan(
        name="Gold Plan",
        amount=100,
        interval=models.Plan.MONTHLY,
        name_on_invoice="Gold Plan Subscription",
        statement_descriptor="GOLDPLANSUB",
        )
    plan.save()

    assert plan.stripe_id is not None
    assert plan.source is not None


@mock.patch("stripe.Plan.create")
@pytest.mark.django_db
def test_plan_manager_error(plan_create_mock):
    plan_create_mock.side_effect = InvalidRequestError(param="id", message="no!")
    plan = models.Plan(
        name="Gold Plan",
        amount=100,
        interval=models.Plan.MONTHLY,
        name_on_invoice="Gold Plan Subscription",
        statement_descriptor="GOLDPLANSUB",
        )

    with pytest.raises(ValidationError) as err:
        plan.save()
    assert err.value.message_dict == {"id": ["no!"]}
