# Generated by Django 3.1.5 on 2021-01-24 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_auto_20190831_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='account_type',
            field=models.CharField(choices=[('savings', 'Savings'), ('current', 'Current')], max_length=128),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_mode',
            field=models.CharField(blank=True, choices=[('cheque_payment', 'Cheque Payment'), ('internet_banking', 'Internet Banking'), ('card_payment', 'Card Payment')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_to',
            field=models.CharField(blank=True, choices=[('cash_account', 'Cash Account'), ('bank_account', 'Bank Account')], default='cash_account', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_mode',
            field=models.CharField(choices=[('cash', 'Cash'), ('bank', 'Bank')], default='cash', max_length=15),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(blank=True, choices=[('income', 'Income'), ('expense', 'Expense')], default='income', max_length=7),
        ),
        migrations.AlterField(
            model_name='transactioncategory',
            name='category_type',
            field=models.CharField(choices=[('income', 'Income'), ('expense', 'Expense')], max_length=7),
        ),
    ]
