from rest_framework.permissions import BasePermission, SAFE_METHODS


class OwnerOnlyPermission(BasePermission):
    """
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        return request.user and (request.user.is_staff or request.user == obj.owner)


class PaymentTypePermission(OwnerOnlyPermission):
    """
    """
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:  # pragma: no cover
            return False

        type_ = request.data.get("type")
        if type_ == "merchant":
            return request.rf_stripe.is_merchant
        elif type_ == "customer":
            return request.rf_stripe.is_customer
        # if the user is authenticated but doesnt match request.data['type'] then return
        # True and raise a validation error in the serializer.
        return True


class CustomerOnlyPermission(OwnerOnlyPermission):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.rf_stripe.is_customer
