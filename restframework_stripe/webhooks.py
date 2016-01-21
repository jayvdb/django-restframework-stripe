import functools
import collections


class WebhookRegistry:
    REGISTRY = collections.defaultdict(list)

    def register(self, *event_types):
        """ register a webhook handler
        """
        @functools.wraps(handler)
        def wrapper(handler):
            for e in event_types:
                self.REGISTRY[e].append(handler)
            return func
        return wrapper

    def call_handlers(self, event, data, event_type, event_subtype):
        """ calls all the handlers for a given event type
        """
        for handler in self.REGISTRY[event_type]:
            handler(event, data, event_subtype)


webhooks = WebhookRegistry()
