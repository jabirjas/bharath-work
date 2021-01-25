# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2019-08-31 15:40
from __future__ import unicode_literals

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('auto_id', models.PositiveIntegerField(db_index=True, unique=True)),
                ('date_added', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now_add=True)),
                ('a_id', models.PositiveIntegerField(db_index=True)),
                ('name', models.CharField(max_length=128)),
                ('address', models.TextField()),
                ('phone', models.CharField(blank=True, max_length=128, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('state', models.CharField(choices=[(b'Kerala', b'Kerala'), (b'Tamil Nadu', b'Tamil Nadu'), (b'Karnataka', b'Karnataka'), (b'Andaman and Nicobar Islands', b'Andaman and Nicobar Islands'), (b'Andhra Pradesh', b'Andhra Pradesh'), (b'Arunachal Pradesh', b'Arunachal Pradesh'), (b'Assam', b'Assam'), (b'Bihar', b'Bihar'), (b'Chandigarh', b'Chandigarh'), (b'Chhattisgarh', b'Chhattisgarh'), (b'Dadra and Nagar Haveli ', b'Dadra and Nagar Haveli '), (b'Daman and Diu', b'Daman and Diu'), (b'National Capital Territory of Delhi', b'National Capital Territory of Delhi'), (b'Goa', b'Goa'), (b'Gujarat', b'Gujarat'), (b'Haryana', b'Haryana'), (b'Himachal Pradesh', b'Himachal Pradesh'), (b'Jammu and Kashmir', b'Jammu and Kashmir'), (b'Jharkhand', b'Jharkhand'), (b'Lakshadweep union territory', b'Lakshadweep union territory'), (b'Madhya Pradesh', b'Madhya Pradesh'), (b'Maharashtra', b'Maharashtra'), (b'Manipur', b'Manipur'), (b'Meghalaya', b'Meghalaya'), (b'Mizoram', b'Mizoram'), (b'Nagaland', b'Nagaland'), (b'Odisha', b'Odisha'), (b'Puducherry union territory', b'Puducherry union territory'), (b'Punjab', b'Punjab'), (b'Rajasthan', b'Rajasthan'), (b'Sikkim', b'Sikkim'), (b'Telangana', b'Telangana'), (b'Tripura', b'Tripura'), (b'Uttar Pradesh', b'Uttar Pradesh'), (b'Uttarakhand', b'Uttarakhand'), (b'West Bengal', b'West Bengal')], default='Kerala', max_length=128)),
                ('first_time_credit', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('first_time_debit', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('credit', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('debit', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('gstin', models.CharField(blank=True, max_length=128, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_system_generated', models.BooleanField(default=False)),
                ('return_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('remarks', models.TextField(blank=True, null=True)),
                ('credit_limit', models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('no_of_boxes', models.PositiveIntegerField(default=0)),
                ('creator', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='creator_customer_objects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('auto_id',),
                'db_table': 'customers_customer',
                'verbose_name': 'customer',
                'verbose_name_plural': 'customers',
            },
        ),
    ]