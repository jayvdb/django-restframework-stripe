import stripe

from .. import util


CARD = {
    "id": "card_14Lc4K2eZvKYlo2CcXyAXlDR",
    "object": "card",
    "address_city": None,
    "address_country": None,
    "address_line1": None,
    "address_line1_check": None,
    "address_line2": None,
    "address_state": None,
    "address_zip": None,
    "address_zip_check": None,
    "brand": "Visa",
    "country": "US",
    "customer": "cus_4UbFSo9tl62jqj",
    "cvc_check": None,
    "dynamic_last4": None,
    "exp_month": 7,
    "exp_year": 2015,
    "funding": "credit",
    "last4": "4242",
    "metadata": {},
    "name": None,
    "tokenization_method": None
    }

CUSTOMER = {
    "id": "cus_7i7PcjtB5sFNhL",
    "object": "customer",
    "account_balance": 0,
    "created": 1452662849,
    "currency": "usd",
    "default_source": "card_17ShAG2eZvKYlo2CkaMDP2dR",
    "delinquent": False,
    "description": None,
    "discount": None,
    "email": "example@stripe.com",
    "livemode": False,
    "metadata": {},
    "shipping": None,
    "sources": {
        "object": "list",
        "data": [
            {
                "id": "card_17ShAG2eZvKYlo2CkaMDP2dR",
                "object": "card",
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": None,
                "address_zip_check": None,
                "brand": "Visa",
                "country": "US",
                "customer": "cus_7i7PcjtB5sFNhL",
                "cvc_check": "pass",
                "dynamic_last4": None,
                "exp_month": 10,
                "exp_year": 2019,
                "funding": "credit",
                "last4": "4242",
                "metadata": {},
                "name": "sankukatti@gmail.com",
                "tokenization_method": None
                }
            ],
        "has_more": False,
        "total_count": 1,
        "url": "/v1/customers/cus_7i7PcjtB5sFNhL/sources"
        },
    "subscriptions": {
        "object": "list",
        "data": [],
        "has_more": False,
        "total_count": 0,
        "url": "/v1/customers/cus_7i7PcjtB5sFNhL/subscriptions"
        }
    }

CHARGE = {
    "id": "ch_17ShBD2eZvKYlo2CSIOZLEpq",
    "object": "charge",
    "amount": 3000,
    "amount_refunded": 0,
    "application_fee": None,
    "balance_transaction": "txn_17KGyT2eZvKYlo2CoIQ1KPB1",
    "captured": False,
    "created": 1452662903,
    "currency": "usd",
    "customer": "cus_4UbFSo9tl62jqj",
    "description": None,
    "destination": None,
    "dispute": None,
    "failure_code": "expired_card",
    "failure_message": "Your card has expired.",
    "fraud_details": {},
    "invoice": "in_17Sg9Z2eZvKYlo2C0uv3To3D",
    "livemode": False,
    "metadata": {},
    "paid": False,
    "receipt_email": None,
    "receipt_number": None,
    "refunded": False,
    "refunds": {
        "object": "list",
        "data": [],
        "has_more": False,
        "total_count": 0,
        "url": "/v1/charges/ch_17ShBD2eZvKYlo2CSIOZLEpq/refunds"
        },
    "shipping": None,
    "source": {
        "id": "card_14Lc4K2eZvKYlo2CcXyAXlDR",
        "object": "card",
        "address_city": None,
        "address_country": None,
        "address_line1": None,
        "address_line1_check": None,
        "address_line2": None,
        "address_state": None,
        "address_zip": None,
        "address_zip_check": None,
        "brand": "Visa",
        "country": "US",
        "customer": "cus_4UbFSo9tl62jqj",
        "cvc_check": None,
        "dynamic_last4": None,
        "exp_month": 7,
        "exp_year": 2015,
        "funding": "credit",
        "last4": "4242",
        "metadata": {},
        "name": None,
        "tokenization_method": None
        },
    "statement_descriptor": None,
    "status": "failed"
    }

TOKEN = {
    "id": "tok_17UENr2eZvKYlo2CSy49docZ",
    "object": "token",
    "client_ip": None,
    "created": 1453028867,
    "livemode": False,
    "used": False
}

TOKEN_CARD = TOKEN.copy().update({
    "card": CARD,
    "type": "card"
    })

ACCOUNT = {
    "id": "acct_1032D82eZvKYlo2C",
    "object": "account",
    "business_logo": None,
    "business_name": "Stripe.com",
    "business_url": None,
    "charges_enabled": False,
    "country": "US",
    "currencies_supported": [
        "usd",
    ],
    "debit_negative_balances": True,
    "decline_charge_on": {
        "avs_failure": False,
        "cvc_failure": False
    },
    "default_currency": "usd",
    "details_submitted": False,
    "display_name": "Stripe.com",
    "email": "site@stripe.com",
    "external_accounts": {
        "object": "list",
        "data": [

        ],
        "has_more": False,
        "total_count": 0,
        "url": "/v1/accounts/acct_1032D82eZvKYlo2C/external_accounts"
    },
    "legal_entity": {
        "additional_owners": None,
        "address": {
            "city": None,
            "country": "US",
            "line1": None,
            "line2": None,
            "postal_code": None,
            "state": None
        },
        "business_name": None,
        "dob": {
            "day": None,
            "month": None,
            "year": None
        },
        "first_name": None,
        "last_name": None,
        "personal_address": {
            "city": None,
            "country": None,
            "line1": None,
            "line2": None,
            "postal_code": None,
            "state": None
        },
        "personal_id_number_provided": False,
        "ssn_last_4_provided": False,
        "type": None,
        "verification": {
            "details": None,
            "details_code": "failed_other",
            "document": None,
            "status": "unverified"
        }
    },
    "managed": False,
    "product_description": None,
    "statement_descriptor": None,
    "support_phone": None,
    "timezone": "US/Pacific",
    "tos_acceptance": {
        "date": None,
        "ip": None,
        "user_agent": None
    },
    "transfer_schedule": {
        "delay_days": 7,
        "interval": "daily"
    },
    "transfers_enabled": False,
    "verification": {
        "disabled_reason": "fields_needed",
        "due_by": None,
        "fields_needed": [
            "business_url",
            "external_account",
            "product_description",
            "support_phone",
            "tos_acceptance.date",
            "tos_acceptance.ip"
        ]
    }
}

BANKACCOUNT = {
    "id": "ba_17VQnJ2eZvKYlo2Ck1rpaiO4",
    "object": "bank_account",
    "account": "acct_1032D82eZvKYlo2C",
    "account_holder_type": "individual",
    "bank_name": "STRIPE TEST BANK",
    "country": "US",
    "currency": "usd",
    "default_for_currency": False,
    "fingerprint": "1JWtPxqbdX5Gamtc",
    "last4": "6789",
    "metadata": {},
    "name": "Jane Austen",
    "routing_number": "110000000",
    "status": "new",
    "customer": "cus_7kwP9BoX2V4Ack"
}


TOKEN_BANKACCOUNT = TOKEN.copy().update({
    "BankAccount": CARD,
    "type": "card"
    })


MOCKS = {
    "Card": CARD,
    "Customer": CUSTOMER,
    "Charge": CHARGE,
    "BankAccount": BANKACCOUNT,
    "Account": ACCOUNT
    }


def get_mock_resource(resource_string, **overrides):
    mock = MOCKS[resource_string].copy()
    mock = util.recursive_mapping_update(mock, **overrides)
    return stripe.convert_to_stripe_object(mock, stripe.api_key, None)
