from collections import namedtuple

from django.utils.functional import SimpleLazyObject


Info = namedtuple("Info", ["is_merchant", "is_customer"])
def get_customer_merchant(request):
    if not hasattr(request, "_cached_rf_stripe_info"):  # pragma: no branch
        request._cached_rf_stripe_info = Info(
            is_customer=hasattr(request.user, "stripe_customer"),
            is_merchant=hasattr(request.user, "stripe_account")
            )
    return request._cached_rf_stripe_info


class CustomerMerchantMiddleware:
    """ explicitly adds the request.users booleans indicating that the requesting user is
    a customer or merchant in your platform. This allows a simplification of API
    permissions and views.

    Example in view permissions::

        class CustomerOnlyPermission(BasePermission):
            def has_permission(self, request, view):
                return request.is_customer

        class MerchantOnlyPermission(BasePermission):
            def has_permission(self, request, view):
                return request.is_merchant
    """
    def process_request(self, request):
        """ add `.is_customer` and `.merchant` parameters to the request object. since
        the parameters are a reverse one to one relation we can save a roundtrip to the
        database by simply checking if the requesting user has the attributes
        `stripe_customer` and `stripe_account`.
        """
        request.rf_stripe = SimpleLazyObject(lambda: get_customer_merchant(request))
