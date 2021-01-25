from __future__ import unicode_literals
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel


PERIOD = (
    ('days', 'Days'),
    ('month', 'Month'),
)


class Distributor(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User",null=True,blank=True,on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    address = models.TextField()
    phone = models.CharField(max_length=128,null=True,blank=True)
    email = models.EmailField(null=True,blank=True)

    first_time_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    first_time_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    commission_tobe_paid = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)
    is_system_generated = models.BooleanField(default=False)
    no_commission = models.BooleanField(default=False)
    is_salesman = models.BooleanField(default=False)

    class Meta:
        db_table = 'distributors_distributor'
        verbose_name = _('distributor')
        verbose_name_plural = _('distributors')
        ordering = ('auto_id',)
        unique_together = (("shop","name","address"),)

    def __unicode__(self):
        return "%s - %s" %(self.name,self.address)


class DistributorStock(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",on_delete=models.CASCADE)
    stock = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    def total_amount(self):
        return self.stock * self.product.price

    def total_cost(self):
        return self.product.cost * self.stock

    def total_mrp(self):
        return self.product.mrp * self.stock

    class Meta:
        db_table = 'distributors_distributor_stock'
        verbose_name = _('distributor stock')
        verbose_name_plural = _('distributor stocks')
        ordering = ('product',)

    def __unicode__(self):
        return str(self.stock)


class StockTransfer(BaseModel):
    time = models.DateTimeField()
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",limit_choices_to={'is_salesman': False},on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    class meta:
        db_table = 'distributors_stock_transfer'
        verbose_name = _('transfer stock')
        verbose_name_plural = _('transfer stocks')
        ordering = ('-a_id',)

    def __unicode__(self):
        return self.distributor.name


class StockTransferItem(models.Model):
    stock_transfer = models.ForeignKey("distributors.StockTransfer",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    class meta:
        db_table = 'distributors_stock_transfer_item'
        verbose_name = _('stock transfer item')
        verbose_name_plural = _('stock transfer items')

    def __unicode__(self):
        return self.product.name


class DistributorStockTransfer(BaseModel):
    time = models.DateTimeField()
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    from_distributor = models.ForeignKey("distributors.Distributor",related_name="from_%(class)s_objects",limit_choices_to={'is_salesman': False},on_delete=models.CASCADE)
    to_distributor = models.ForeignKey("distributors.Distributor",related_name="to_%(class)s_objects",limit_choices_to={'is_salesman': False},on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    class meta:
        db_table = 'distributors_distributor_stock_transfer'
        verbose_name = _('distributor transfer stock')
        verbose_name_plural = _('distributor transfer stocks')
        ordering = ('-a_id',)

    def __unicode__(self):
        return self.from_distributor.name


class DistributorStockTransferItem(models.Model):
    distributor_stock_transfer = models.ForeignKey("distributors.DistributorStockTransfer",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    class meta:
        db_table = 'distributors_distributor_stock_transfer_item'
        verbose_name = _('distributor stock transfer item')
        verbose_name_plural = _('distributor stock transfer items')

    def __unicode__(self):
        return self.product.name


class DirectStockTransfer(BaseModel):
    time = models.DateTimeField()
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",limit_choices_to={'is_salesman': False},on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    class meta:
        db_table = 'distributors_direct_stock_transfer'
        verbose_name = _('direct transfer stock')
        verbose_name_plural = _('direct transfer stocks')
        ordering = ('-a_id',)

    def __unicode__(self):
        return self.from_distributor.name


class DirectStockTransferItem(models.Model):
    direct_stock_transfer = models.ForeignKey("distributors.DirectStockTransfer",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    class meta:
        db_table = 'distributors_direct_stock_transfer_item'
        verbose_name = _('direct stock transfer item')
        verbose_name_plural = _('direct stock transfer items')

    def __unicode__(self):
        return self.product.name