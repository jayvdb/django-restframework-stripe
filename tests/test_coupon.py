from unittest import mock
from django.utils import timezone
from django.core.exceptions import ValidationError

import pytest

from stripe.error import InvalidRequestError

from restframework_stripe import models
from restframework_stripe.test import get_mock_resource


@mock.patch("stripe.Coupon.create")
@pytest.mark.django_db
def test_create_coupon(create_coupon):
    kwargs = {
        "duration": models.Coupon.ONCE,
        "amount_off": 100,
        "currency": "usd",
        "redeem_by": timezone.now()
        }
    mock_kwargs = kwargs.copy()
    mock_kwargs.update({
        "duration": "once",
        "redeem_by": int(kwargs["redeem_by"].timestamp())
        })
    create_coupon.return_value = get_mock_resource("Coupon", **mock_kwargs)

    coupon = models.Coupon(**kwargs)
    coupon.save()

    assert coupon.is_created


@pytest.mark.parametrize("kwargs", [
    {"duration": 1},
    {"duration": 1, "percent_off": 10, "amount_off": 10},
    {"duration": 1, "amount_off": 10},
    {"duration": models.Coupon.REPEATING, "amount_off": 10, "currency": "usd"}
    ])
def test_clean_coupon(kwargs):
    coupon = models.Coupon(**kwargs)

    with pytest.raises(ValidationError) as err:
        coupon.clean()


@mock.patch("stripe.Coupon.create")
@pytest.mark.django_db
def test_create_coupon_error(create_coupon):
    kwargs = {
        "duration": models.Coupon.ONCE,
        "amount_off": 100,
        "currency": "usd",
        }
    create_coupon.side_effect = InvalidRequestError(param="foo", message="bar")

    coupon = models.Coupon(**kwargs)
    with pytest.raises(ValidationError):
        coupon.save()
