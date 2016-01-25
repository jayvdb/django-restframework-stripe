=========
Endpoints
=========

Below is a table of endpoints provided by Django-Restframework-Stripe. CRUD operations are limited to those provided by Stripe and are further limited to prevent client side applications from creating resources such as Charges and Transfers (such resources should only be created on the server side within the business logic of your application).

+----------------------+---------------------------+-----------------------------+
| Uri                  | Methods                   | Name                        |
+======================+===========================+=============================+
| /cards/              | GET,POST                  | rf_stripe:card              |
+----------------------+---------------------------+-----------------------------+
| /cards/{pk}/         | GET,POST,PUT,PATCH,DELETE | rf_stripe:card              |
+----------------------+---------------------------+-----------------------------+
| /connected-accounts/ | GET,POST,PUT,PATCH,DELETE | rf_stripe:connected-account |
+----------------------+---------------------------+-----------------------------+
| /bank-accounts/      | GET,POST,PUT,PATCH,DELETE | rf_stripe:bank-account      |
+----------------------+---------------------------+-----------------------------+
| /transfers/          | GET,PUT,PATCH             | rf_stripe:transfer          |
+----------------------+---------------------------+-----------------------------+
| /charges/            | GET,PUT,PATCH             | rf_stripe:charge            |
+----------------------+---------------------------+-----------------------------+
| /customers/          | GET,POST,PUT,PATCH,DELETE | rf_stripe:customer          |
+----------------------+---------------------------+-----------------------------+
| /refunds/            | GET                       | rf_stripe:refund            |
+----------------------+---------------------------+-----------------------------+
| /fee-refunds/        | GET                       | rf_stripe:fee-refund        |
+----------------------+---------------------------+-----------------------------+
| /coupons/            | GET                       | rf_stripe:coupon            |
+----------------------+---------------------------+-----------------------------+
| /invoices/           | GET                       | rf_stripe:invoice           |
+----------------------+---------------------------+-----------------------------+
| /invoice-items/      | GET                       | rf_stripe:invoice-item      |
+----------------------+---------------------------+-----------------------------+
| /plans/              | GET                       | rf_stripe:plan              |
+----------------------+---------------------------+-----------------------------+
