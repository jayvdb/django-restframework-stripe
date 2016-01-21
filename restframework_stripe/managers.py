import requests

from django.db.models import manager
from django.utils import timezone

import stripe

from .util import recursive_mapping_update


class ConnectedAccountManager(manager.Manager):
    """ This manager provides additional methods for creating managed and
    connecting standalone stripe accounts.
    """
    def managed_accounts(self):
        """ connected accounts that are managed.
        """
        return self.filter(managed=True)

    def standalone_accounts(self):
        """ connected accounts that are *not* managed.
        """
        return self.filter(managed=False)

    def connect_standalone_account(self, owner, auth_code):
        """ this is part 2 in a two part onboarding procedure it should be called in a
        callback view for the stripe connected account oath flow.

        :param owner: the user model that relates to the newly connected account
        :type owner: accounts.Account
        :param auth_code: the auth code returned in part 1 of the oath flow after a
            client has accepted the connection
        :type auth_code: string
        :returns: transactions.ConnectedAccount
        """
        data = {
            "client_secret": None,
            "grant_type": "authorization_code",
            "client_id": None,
            "code": auth_code,
            }
        uri = "https://connect.stripe.com/oauth/token"
        response = requests.post(uri, params=data).json()
        if response.get("error"):
            # 100% likely to be an error on our end from the `auth_code` parameter
            raise stripe.InvalidRequestError(
                message=response["error_description"],
                param=response["error"],
                json_body=response
                )
        # otherwise the request succeeded and we can format a stripe object.
        stripe_object = self.model.get_stripe_api_instance(response["stripe_user_id"])
        stripe_object = recursive_mapping_update(stripe_object, **{
            "managed": False,
            "keys": {
                "publishable": response["stripe_publishable_key"],
                "access_token": response["access_token"],
                "refresh_token": response["refresh_token"]
                }
            })
        connected_account = self.model.stripe_object_to_model(stripe_object)
        connected_account.owner = owner
        connected_account.save()
        return connected_account
