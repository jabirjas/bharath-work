# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2019-08-31 15:40
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('distributors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocktransferitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
        ),
        migrations.AddField(
            model_name='stocktransferitem',
            name='stock_transfer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributors.StockTransfer'),
        ),
        migrations.AddField(
            model_name='stocktransferitem',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Measurement'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='creator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='creator_stocktransfer_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributors.Distributor'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shop'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='updator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='updator_stocktransfer_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributorstocktransferitem',
            name='distributor_stock_transfer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributors.DistributorStockTransfer'),
        ),
        migrations.AddField(
            model_name='distributorstocktransferitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
        ),
        migrations.AddField(
            model_name='distributorstocktransferitem',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Measurement'),
        ),
        migrations.AddField(
            model_name='distributorstocktransfer',
            name='creator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='creator_distributorstocktransfer_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributorstocktransfer',
            name='from_distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_distributorstocktransfer_objects', to='distributors.Distributor'),
        ),
        migrations.AddField(
            model_name='distributorstocktransfer',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shop'),
        ),
        migrations.AddField(
            model_name='distributorstocktransfer',
            name='to_distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_distributorstocktransfer_objects', to='distributors.Distributor'),
        ),
        migrations.AddField(
            model_name='distributorstocktransfer',
            name='updator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='updator_distributorstocktransfer_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributorstock',
            name='distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributors.Distributor'),
        ),
        migrations.AddField(
            model_name='distributorstock',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
        ),
        migrations.AddField(
            model_name='distributorstock',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shop'),
        ),
        migrations.AddField(
            model_name='distributor',
            name='creator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='creator_distributor_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributor',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shop'),
        ),
        migrations.AddField(
            model_name='distributor',
            name='updator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='updator_distributor_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributor',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='directstocktransferitem',
            name='direct_stock_transfer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributors.DirectStockTransfer'),
        ),
        migrations.AddField(
            model_name='directstocktransferitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
        ),
        migrations.AddField(
            model_name='directstocktransferitem',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Measurement'),
        ),
        migrations.AddField(
            model_name='directstocktransfer',
            name='creator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='creator_directstocktransfer_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='directstocktransfer',
            name='distributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributors.Distributor'),
        ),
        migrations.AddField(
            model_name='directstocktransfer',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shop'),
        ),
        migrations.AddField(
            model_name='directstocktransfer',
            name='updator',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='updator_directstocktransfer_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='distributor',
            unique_together=set([('shop', 'name', 'address')]),
        ),
    ]
