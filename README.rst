===========================
django-restframework-stripe
===========================

.. image:: https://travis-ci.org/andrewyoung1991/django-restframework-stripe.svg?branch=master
    :target: https://travis-ci.org/andrewyoung1991/django-restframework-stripe

.. image:: https://coveralls.io/repos/github/andrewyoung1991/django-restframework-stripe/badge.svg?branch=master
    :target: https://coveralls.io/github/andrewyoung1991/django-restframework-stripe?branch=master

.. image:: https://codeclimate.com/github/andrewyoung1991/django-restframework-stripe/badges/gpa.svg
   :target: https://codeclimate.com/github/andrewyoung1991/django-restframework-stripe
      :alt: Code Climate


RESTful endpoints for Django Restframework applications using Stripe.


Requirements
============

Django Restframework Stripe has a minimum required Django version *1.8* and a minumum required Postgresql version *9.4*. The reason for this requirement is that Django Restframework Stripe uses a JSON field to store requests and responses from Stripe whenever a client updates a resource or a webhook is received.

Django Restframework Stripe is also aimed at Python 3.4 or higher (although you can get by with a lower version, but you will not be able to use some of the management commands provided. These commands are generally for createing Stripe resources based on models you already have present in your application -- Such as creating a Customer resource for each of your Users. The reason for using asyncio in this case is that the Stripe client for Python *as I understand it* does not support batch creation -- making for laborious syncronous code.


Setup
=====

A single dictionary may be provided in your settings file to configure Django Restframework Stripe.

.. code:: python

  # settings.py
  RESTFRAMEWORK_STRIPE = {
      "api_key": "my api key",
      "api_version": "2016-02-03",
      "project_title": "My Marketplace"
  }

The only *required* setting is `api_key` which allows for the Stripe client for Python to actually make real life requests to the Stripe api.


Models & Design
===============

The models present in Django Restframework Stripe are a *cached* representation of the actual records from Stripe. This pattern of storing request results locally saves extra round trips for basic GET requests. Basically, whenever a client creates a resource, Django Restframework Stripe facilitates the creation of that resource by:

1) validating the input to the best of its ability
2) sending the validated input to Stripe
3) processing the results from Stripe (returning any validation errors if necessary)
4) creating a local record of the resource

The design for each `StripeModel` includes at minimum a Stripe resource name, such as *Card* or *Account*, the unique id of the Stripe resource, and the validated stripe object (stored in a JSONField named *source*). When updating Stripe resources using Django Restframework Stripe, a client application only needs to pull down the locally *cached* model representation, update the *source* field, and send the updated *source* back to Django Restframework Stripe using the primary key of the *cached* model representation endpoint::

  # GET /cards/1/

  {
    "id": 1,
    "owner": 1,
    "stripe_id": "card_14Lc4K2eZvKYlo2CcXyAXlDR",
    "cvc_check": null
    "source": {
      "id": "card_14Lc4K2eZvKYlo2CcXyAXlDR",
      "object": "card",
      "address_city": null,
      "address_country": null,
      "address_line1": null,
      "address_line1_check": null,
      "address_line2": null,
      "address_state": null,
      "address_zip": null,
      "address_zip_check": null,
      "brand": "Visa",
      "country": "US",
      "customer": "cus_4UbFSo9tl62jqj",
      "cvc_check": null,
      "dynamic_last4": null,
      "exp_month": 7,
      "exp_year": 2015,
      "funding": "credit",
      "last4": "4242",
      "metadata": {},
      "name": null,
      "tokenization_method": null
    }
  }

  # PUT /cards/1/

  {
    "id": "card_14Lc4K2eZvKYlo2CcXyAXlDR",
    "object": "card",
    "address_city": null,
    "address_country": null,
    "address_line1": null,
    "address_line1_check": null,
    "address_line2": null,
    "address_state": null,
    "address_zip": null,
    "address_zip_check": null,
    "brand": "Visa",
    "country": "US",
    "customer": "cus_4UbFSo9tl62jqj",
    "cvc_check": null,
    "dynamic_last4": null,
    "exp_month": 7,
    "exp_year": 2015,
    "funding": "credit",
    "last4": "4242",
    "metadata": {},
    "name": "Rocky Road",
    "tokenization_method": null
  }

The prior example shows a client GETing one of their Card resources, updating the *name* of the source field, and sending the updated source field back to Django Restframework Stripe. If all is well and good in the source that was PUT to */cards/1/* then Django Restframework Stripe will then attempt to update the resource with Stripe. If the attempt to update fails then Django Restframework Stripe will return the error messages and afflicted field names from Stripe back to the client. If the attempt to update succeeds then Django Restframework Stripe will update the *cached* model representation and return it to the client.

Though this example shows a PUT request, you will most regularly want to submit PATCH requests, because only a limited subset of fields for each Stripe resource are permitted to be updated (for obvious reasons).


Testing
=======

Django Restframework Stripe provides a module *test.py* specifically for creating mock stripe resources for mocking your requests. The main utility is `get_mock_resource` which takes the name of a resource, such as *Card* or *Account* and a list of keyword arguments with which to update the default values of the mock object. For instance if I needed a *Card* where the card holders name was *Rocky Road*, then I would employ `get_mock_resource` in the following way.

.. code:: python

  from restframework_stripe.test import get_mock_resource

  card = get_mock_resource("Card", name="Rocky Road")
  assert card["name"] == "Rocky Road", "Somethings gone terribly wrong!"

The actual return type of `get_mock_resource` is a `stripe.StripeResource` instance, so you can actually treat it like a *real* instance returned by the Stripe Python client. To use these mocks in test cases you will simply need to patch the resource method and return the mocked resource. The following example shows a unittest that mocks the *Account* resource.

.. code:: python

  from unittest import mock

  from rest_framework.reverse import reverse
  from rest_framework.test import APIClient

  from restframework_stripe.test import get_mock_resource


  @mock.patch("stripe.Account.create")
  def test_fake_create(acct_create):
      data = get_mock_resource("Account", managed=True)
      acct_create.return_value = data
      uri = reverse("rf_stripe:connected-account-list")
      client = APIClient()
      response = client.post(uri, data=data, format="json")
      assert response.status_code == 201, response.data

Of course, these kinds of unittests are covered thouroughly in the Django Restframework Stripe test suite - so your tests, while using the patching system, should focus more on integrating this package into your code base. For instance an integration test outlining the possible failures of a transaction.


Webhooks
========

Stripe's primary mode of communication with your application is via webhook requests. You'll need to configure your Stripe settings to send these requests to an endpoint within your Application. For this you will use the `restframework_stripe.Event` view to capture and validate the data received from Stripe. With the Event stored locally, you can then call all of the registered handlers for the event type::

  # webhook event from Stripe
  {
    "id": "evt_17YhUu2eZvKYlo2Cxrh35V1T",
    "object": "event",
    "api_version": "2015-10-16",
    "created": 1454094092,
    "data": {
      "object": {
        "id": "in_17YgSq2eZvKYlo2CARrQ3gRe",
        "object": "invoice",
        "amount_due": 2000,
        "application_fee": None,
        "attempt_count": 1,
        "attempted": True,
        "charge": "ch_17YhUu2eZvKYlo2CZNfOjJMm",
        "closed": True,
        "currency": "usd",
        "customer": "cus_6hNQ8r1t4BNaBa",
        "date": 1454090120,
        "description": None,
        "discount": None,
        "ending_balance": 0,
        "forgiven": False,
        "lines": {
          "object": "list",
          "data": [
            {
              "id": "sub_6hNQy3MsNEQFlI",
              "object": "line_item",
              "amount": 2000,
              "currency": "usd",
              "description": None,
              "discountable": True,
              "livemode": False,
              "metadata": {

              },
              "period": {
                  "start": 1454089737,
                  "end": 145676813
              },
              "plan": {
                "id": "monthly",
                "object": "plan",
                "amount": 2000,
                "created": 1436978837,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                  "Order": "4"
                },
                "name": "Monthly Plan",
                "statement_descriptor": None,
                "trial_period_days": None,
              },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
          }
        ],
        "has_more": False,
        "total_count": 1,
        "url": "/v1/invoices/in_17YgSq2eZvKYlo2CARrQ3gRe/lines"
        },
        "livemode": False,
        "metadata": {
        },
        "next_payment_attempt": None,
        "paid": True,
        "period_end": 1454089737,
        "period_start": 1451411337,
        "receipt_number": None,
        "starting_balance": 0,
        "statement_descriptor": None,
        "subscription": "sub_6hNQy3MsNEQFlI",
        "subtotal": 2000,
        "tax": None,
        "tax_percent": None,
        "total": 2000,
        "webhooks_delivered_at": 145409017
      },
      "previous_attributes": {
        "attempted": False,
        "charge": None,
        "closed": False,
        "ending_balance": None,
        "next_payment_attempt": 1454093720,
        "paid": False
      }
    },
    "livemode": False,
    "pending_webhooks": 0,
    "request": None,
    "type": "invoice.updated"
  }

The Event type for this Stripe Event is *invoice* and its subtype is *updated*. To register a webhook handler for this request you will use to `webhooks.webhooks` object.

.. code:: python

  from restframework_stripe.webhooks import webhooks

  @webhooks.register("invoice")
  def invoice_handler(event, source, subtype):
      if subtype == "updated":
          stripe_object = source["data"]["object"]
          # does stuff with Invoice object

.. note::

  Django Restframework Stripe currently supports a small number of resources. Invoice is not supported at this time (though you can easily implement it in your application).

This webhook code needs to be imported into your application at some point. It is suggested to write these handlers in your *models.py* module, otherwise you can import your handlers in an AppConfig in the `.read()` method, e.g.:

.. code:: python

  class MyAppConfig(AppConfig):
      name = "my_app"

      def ready(self):
          # register all webhook handlers
          from .webhooks import *


Serialization
=============

Django Restframework Stripe provides several utilities for serializing client requests which will be sent to Stripe after validation. Because Stripe has different allowable arguments for the creation of resources and the updating of resources, the normal Restframework ModelSerializer would not work. as most fields are not even present between updating and creating. For instance, creating a *Card* resource requires a *Token* and a *Customer*, while updating the *Card* the only valid fields include *address*, *exp_month/year* and *name*. For this reason, Serializers in Django Restframework Stripe come in triplets. A Serializer for Creating, Updating, and Retrieveing -- each corresponding to a POST, PUT/PATCH, GET request respectively. The payoff of using three serializers is that we can use Restframework's awesome ModelViewSet feature.

.. code:: python

  class CardViewset(StripeResourceViewset):
      """ Normal CRUD operations on the stripe Card resource.

      a POST request expects a json document like this::

          {
              "token": "tok_fdsionNKO532N32nL",
              "card_type": "customer" or "merchant"
          }
      """
      model = models.Card
      queryset = models.Card.objects.all()
      serializer_class = serializers.CardSerializer
      create_stripe_serializer = serializers.CreateCardResourceSerializer
      update_stripe_serializer = serializers.UpdateCardResourceSerializer

      permission_classes = (permissions.PaymentTypePermission,)

The prior viewset inherits from `StripeResourceViewset`. It is a kind of `ModelViewSet` which routes requests to serializers based on the request method. A POST request handled by this ViewSet is routed to the `create_stripe_serializer` Serializer for validation and creation, while PUT/PATCH requests are routed to the `update_stripe_serializer` Serializer. The most important property, besides interacting with Stripe, of the special Create and Update serializers is that they return the data of a parent ModelSerializer, or better stated -- *they return the serialized version of the locally cached Stripe resource*.


Rational
========

The most important difference between Django Restframework Stripe and other Django and Stripe integrations is that it doesn't focus on one aspect of the Stripe API. It's main purpose is for creating API endpoints for marketplace applications while maintaining a sort of obliviousness to the nature of the marketplace or the nature of Stripe; it is a middleman between your applications logic and the Stripe API. I also believe that this is the first Stripe integration with and implementation of the *Account* resource. This resource gives your clients the ability to be Merchants within your marketplace structure and further, these *Accounts* can be managed (completely hidden from the customer and controlled exclusively by your application) or connected from existing Stripe accounts.
