# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2019-09-07 10:57
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchases', '0003_purchase_tax_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='tax',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
    ]
