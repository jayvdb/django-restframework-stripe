from unittest import mock
from restframework_stripe.webhooks import webhooks


def test_registering_webhook():
    @webhooks.register("test")
    def handler(event, data, event_subtype):
        pass

    assert len(webhooks.REGISTRY["test"]) == 1

    webhooks.remove_handler("test", handler)
    assert len(webhooks.REGISTRY["test"]) == 0


def test_registering_calling_webhook():
    m = mock.Mock()
    webhooks.register("test")(m)
    webhooks.call_handlers(None, None, "test", None)

    assert m.called
    m.assert_called_with(None, None, None)
