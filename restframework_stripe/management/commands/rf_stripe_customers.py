import asyncio

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from restframework_stripe import STRIPE


class Command(BaseCommand):
    """ Since an application will likely consider *all users* to be paying customers this
    method will create a corresponding Customer objects for all users in your database.

    The primary usecase for this command is, when adding rf_stripe to an existing Django
    project. Otherwise Customer objects should be created at the time a user registers.

    Futher changes, such as adding subscriptions to Customers can be done at a later
    time.
    """
    help = "Create customer objects for all users without one."

    def handle(self, *args, **kwargs):
        User = get_user_model()

        builders = []
        for user in User.objects.filter(stripe_customer__isnull=True).iterator():
            desc = "{0} Customer for {1}.".format(STRIPE["project_title"], user.username)
            email = user.email
            builders.append(syncronize_user(user, description=desc, email=email))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*builders, return_exceptions=True))
        loop.close()


@asyncio.coroutine
def syncronize_user(user, **kwargs):
    """ the main coroutine for cooperatively sending a request to the Stripe api and,
    if that succeeds, saving the results to the database.
    """
    stripe_object = yield from create_stripe_instance(**kwargs)
    customer = None
    if stripe_object is not None:
        customer = yield from create_stripe_model(user, stripe_object)
    return customer


@asyncio.coroutine
def create_stripe_instance(**kwargs):
    """ do the actual Stripe API POST request.
    """
    stripe_object = None
    try:
        stripe_object = Customer.stripe_api_create(
            description=desc,
            )
    except stripe.StripeError as err:
        print("Error creating", desc, err._message)

    return stripe_object


@asyncio.coroutine
def create_stripe_model(owner, stripe_object):
    """ Save the model to the database.
    """
    customer_model = Customer.stripe_object_to_model(stripe_object)
    customer_model.owner = user
    customer.save()
    print("Created Customer object for {}".format(owner.username))
    return customer
