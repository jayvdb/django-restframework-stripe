from rest_framework.permissions import BasePermission, SAFE_METHODS


class OwnerOnlyPermission(BasePermission):
    """
    """
    def has_permissions(self, request, view):
        return request.user and request.user.is_authenticated()

    def has_object_permissions(self, request, view, obj):
        return request.user and (request.user.is_staff or request.user == obj.owner)


class PaymentTypePermission(OwnerOnlyPermission):
    def has_permissions(self, request, view):
        if not (request.user and request.user.is_authenticated()):
            return False

        type_ = request.data["type"]
        if type_ == "merchant":
            return hasattr(request.user, "stripe_account")
        elif type_ == "customer":
            return hasattr(request.user, "stripe_customer")
        # if the user is authenticated but doesnt have these objects return True and
        # raise a validation error in the serializer.
        return True
