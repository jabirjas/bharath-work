# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2019-09-07 10:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_auto_20190831_2110'),
        ('purchases', '0002_purchaseitem_selling_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='tax_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='finance.TaxCategory'),
        ),
    ]
