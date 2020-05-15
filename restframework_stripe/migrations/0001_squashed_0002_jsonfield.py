# Generated by Django 2.2.11 on 2020-05-15 11:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    replaces = [('restframework_stripe', '0001_initial'), ('restframework_stripe', '0002_jsonfield')]

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('status', models.CharField(max_length=25)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_charges', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('duration', models.PositiveSmallIntegerField(choices=[(0, 'forever'), (1, 'once'), (2, 'repeating')])),
                ('amount_off', models.PositiveIntegerField(null=True)),
                ('currency', models.CharField(blank=True, max_length=3, null=True)),
                ('duration_in_months', models.PositiveSmallIntegerField(null=True)),
                ('max_redemptions', models.PositiveIntegerField(null=True)),
                ('percent_off', models.PositiveSmallIntegerField(null=True)),
                ('redeem_by', models.DateTimeField(null=True)),
                ('is_created', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('event_type', models.CharField(max_length=50)),
                ('processed', models.BooleanField(default=False)),
                ('verified', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventProcessingError',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_type', models.SmallIntegerField(choices=[(0, 'processing'), (1, 'validating')], default=0)),
                ('message', models.TextField()),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processing_errors', to='restframework_stripe.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('name', models.CharField(max_length=120, unique=True)),
                ('amount', models.PositiveIntegerField()),
                ('interval', models.PositiveSmallIntegerField(choices=[(0, 'day'), (1, 'week'), (2, 'month'), (3, 'year')])),
                ('name_on_invoice', models.CharField(max_length=50)),
                ('statement_descriptor', models.CharField(max_length=22)),
                ('interval_count', models.PositiveSmallIntegerField(default=1)),
                ('trial_period_days', models.PositiveIntegerField(null=True)),
                ('is_created', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('currency', models.CharField(blank=True, max_length=3, null=True)),
                ('default_for_currency', models.NullBooleanField()),
                ('status', models.CharField(max_length=20)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_bank_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('currency', models.CharField(blank=True, max_length=3, null=True)),
                ('default_for_currency', models.NullBooleanField()),
                ('cvc_check', models.CharField(blank=True, max_length=20, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_cards', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConnectedAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('managed', models.BooleanField()),
                ('secret_key', models.CharField(blank=True, max_length=120, null=True)),
                ('publishable_key', models.CharField(blank=True, max_length=120, null=True)),
                ('access_token', models.CharField(blank=True, max_length=120, null=True)),
                ('refresh_token', models.CharField(blank=True, max_length=120, null=True)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_account', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('source_id', models.PositiveIntegerField(null=True)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_customer', to=settings.AUTH_USER_MODEL)),
                ('source_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('amount', models.PositiveIntegerField()),
                ('reason', models.PositiveSmallIntegerField(choices=[(0, 'duplicate'), (1, 'fraudulent'), (2, 'requested_by_customer')])),
                ('refund_application_fee', models.NullBooleanField()),
                ('reverse_transfer', models.NullBooleanField()),
                ('is_created', models.BooleanField(default=False)),
                ('charge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='restframework_stripe.Charge')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_refunds', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('canceled', models.BooleanField(default=False)),
                ('coupon', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='restframework_stripe.Coupon')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_subscriptions', to=settings.AUTH_USER_MODEL)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='restframework_stripe.Plan')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('source', jsonfield.fields.JSONField()),
                ('status', models.CharField(max_length=20)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_transfers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]