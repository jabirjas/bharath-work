# Generated by Django 3.1.5 on 2021-01-24 07:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_auto_20210124_1304'),
        ('finance', '0005_auto_20210124_1304'),
        ('purchases', '0004_purchase_tax'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetpurchaseitem',
            name='asset',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_deleted': False}, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.asset'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='tax_category',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_deleted': False}, null=True, on_delete=django.db.models.deletion.CASCADE, to='finance.taxcategory'),
        ),
    ]