from unittest import mock

import pytest
import stripe
from stripe.error import StripeError

from model_mommy import mommy

from rest_framework.reverse import reverse

from restframework_stripe.test import get_mock_resource
from restframework_stripe import models
from restframework_stripe.webhooks import webhooks


@mock.patch("stripe.Event.retrieve")
@pytest.mark.django_db
def test_verify_event(event_retrieve, event):
    event_retrieve.return_value = get_mock_resource("Event")
    event.verify()
    assert event.verified is True


@mock.patch("stripe.Event.retrieve")
@pytest.mark.django_db
def test_verify_event_error(event_retrieve, event):
    event_retrieve.side_effect = StripeError(message="Could not find event.")
    event.verify()
    assert event.verified is False
    assert 0 < event.processing_errors.count()


@mock.patch("stripe.Event.retrieve")
@pytest.mark.django_db
def test_process_event(event_retrieve, event):
    event_retrieve.return_value = get_mock_resource("Event")
    handler = mock.Mock()
    event_type, event_subtype = event.event_type.split(".", 1)
    webhooks.register(event_type)(handler)

    event.process()

    assert event.verified is True
    assert event.processed is True
    handler.assert_called_with(event, event.source["data"], event_subtype)


@mock.patch("stripe.Event.retrieve")
@pytest.mark.django_db
def test_process_event_error(event_retrieve, event):
    event_retrieve.return_value = get_mock_resource("Event")
    handler = mock.Mock()
    handler.side_effect = StripeError(message="Bad Request")
    event_type, event_subtype = event.event_type.split(".", 1)
    webhooks.register(event_type)(handler)

    event.process()

    assert event.verified is True
    assert event.processed is False
    handler.assert_called_with(event, event.source["data"], event_subtype)
