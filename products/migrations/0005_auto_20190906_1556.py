# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2019-09-06 10:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_auto_20190906_1529'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='productgroup',
            unique_together=set([]),
        ),
    ]
