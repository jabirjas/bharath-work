# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2019-09-06 09:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_auto_20190904_1215'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'products_product_group',
                'verbose_name': 'product group',
                'verbose_name_plural': 'product groups',
            },
        ),
        migrations.AlterUniqueTogether(
            name='productgroup',
            unique_together=set([('name',)]),
        ),
        migrations.AddField(
            model_name='product',
            name='product_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.ProductGroup'),
        ),
    ]
