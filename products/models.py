from __future__ import unicode_literals
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel


UNIT_TYPES = (
    ('quantity', 'Quantity'),
)


PERIOD = (
    ('days', 'Days'),
    ('month', 'Month'),
)


class Product(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128)
    hsn = models.CharField(max_length=128,blank=True,null=True)

    brand = models.ForeignKey("products.Brand",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    category = models.ForeignKey("products.Category",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    subcategory = models.ForeignKey("products.SubCategory",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    unit_type = models.CharField(max_length=128, choices=UNIT_TYPES,default="quantity")
    unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor",blank=True,null=True,on_delete=models.CASCADE)

    product_group = models.ForeignKey("products.ProductGroup",blank=True,null=True,on_delete=models.CASCADE)

    stock = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    mrp = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    wholesale_price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    wholesale_tax_excluded_price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax_excluded_price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax_category = models.ForeignKey("finance.TaxCategory",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    tax = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    low_stock_limit = models.PositiveIntegerField(default=1)

    is_deleted = models.BooleanField(default=False)
    is_tax_included = models.BooleanField(default=False)

    def total_cost(self):
        return self.cost * self.stock

    def total_price(self):
        return self.price * self.stock

    def total_mrp(self):
        return self.mrp * self.stock

    class Meta:
        db_table = 'products_product'
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ('auto_id',)
        unique_together = (("shop","code"),)

    def __unicode__(self):
        value =  self.product_group.name + self.code
        if self.category:
            value += " - " + self.category.name
        if self.subcategory:
            value += " - " + self.subcategory.name

        return value


class ProductGroup(models.Model):    
    name = models.CharField(max_length=128)

    class Meta:
        db_table = 'products_product_group'
        verbose_name = _('product group')
        verbose_name_plural = _('product groups')
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class ProductExpiryDate(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    auto_id = models.PositiveIntegerField(db_index=True,unique=True)
    date_added = models.DateTimeField(db_index=True,auto_now_add=True)
    product = models.ForeignKey("products.Product",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    purchase = models.ForeignKey("purchases.Purchase",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    stock_transfer = models.ForeignKey("distributors.StockTransfer",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    batch_code = models.CharField(max_length=128)
    manufacture_date = models.DateField(null=True,blank=True,)
    best_before = models.PositiveIntegerField(null=True,blank=True,)
    expiry_date = models.DateField(null=True,blank=True,)
    period = models.CharField(max_length=128, choices=PERIOD)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_expiry_date'
        verbose_name = _('products_expiry_date')
        verbose_name_plural = _('products_expiry_dates')
        ordering = ('product',)

    def __unicode__(self):
        return self.batch_code


class Category(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_category'
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class SubCategory(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    category = models.ForeignKey("products.Category",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_sub_category'
        verbose_name = _('Sub category')
        verbose_name_plural = _('Sub categories')
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class Brand(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_brand'
        verbose_name = _('brand')
        verbose_name_plural = _('brands')
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Batch(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_batch'
        verbose_name = _('batch')
        verbose_name_plural = _('batchs')
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class Measurement(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    code = models.CharField(max_length=18)
    unit_type = models.CharField(max_length=128, choices=UNIT_TYPES,default="quantity")
    unit_name = models.CharField(max_length=128)
    is_base = models.BooleanField(default=False)
    conversion_factor = models.DecimalField(default=0,decimal_places=4, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_system_generated = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_measurement'
        verbose_name = _('measurement')
        verbose_name_plural = _('measurements')
        ordering = ('auto_id',)
        unique_together = (("shop", "code"),)

    class Admin:
        list_display = ('code','unit_type','unit_name')

    def __unicode__(self):
        return self.unit_name + '(' + self.code +')'


class ProductAlternativeUnitPrice(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
    cost = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_alternative_unit_price'
        verbose_name = _('product alternative price')
        verbose_name_plural = _('product alternative prices')
        ordering = ('product',)

    class Admin:
        list_display = ('product','unit','cost','price')

    def __unicode__(self):
        return str(self.price)


class ProductBatch(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    batch_code = models.ForeignKey("products.Batch",on_delete=models.CASCADE)
    cost = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_batch'
        verbose_name = _('product batch')
        verbose_name_plural = _('product batches')
        ordering = ('product',)

    class Admin:
        list_display = ('product','cost')

    def __unicode__(self):
        return str(self.batch_code.name)


class Asset(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'productss_asset'
        verbose_name = _('asset')
        verbose_name_plural = _('assets')
        ordering = ('auto_id',)

    def __unicode__(self):
        return self.name


class ProductBatchHistory(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    batch = models.ForeignKey("products.ProductBatch",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    sale = models.ForeignKey("sales.Sale",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_batch_history'
        verbose_name = _('product batch history')
        verbose_name_plural = _('product batch histories')

    def __unicode__(self):
        return str(self.batch.product.name)


class InventoryAdjustment(BaseModel) :
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",blank=True,null=True,on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",blank=True,null=True,on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    new_qty = models.DecimalField(default=0,decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_inventory_adjustment'
        verbose_name = _('product inventory adjustment')
        verbose_name_plural = _('product inventory adjustments')
        ordering = ('-auto_id',)


    def __unicode__(self):
        return str(self.distributor.name)


class InventoryAdjustmentItem(models.Model) :
    inventory_adjustment = models.ForeignKey("products.InventoryAdjustment",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",blank=True,null=True,on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    new_qty = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_inventory_adjustment_item'
        verbose_name = _('product inventory adjustment item')
        verbose_name_plural = _('product inventory adjustment items')


    def __unicode__(self):
        return str(self.product.name)


class StockReturn(BaseModel) :
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",blank=True,null=True,on_delete=models.CASCADE)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_stock_return'
        verbose_name = _('product stock return')
        verbose_name_plural = _('product stock returns')
        ordering = ('-auto_id',)


    def __unicode__(self):
        return str(self.distributor.name)

class StockReturnItem(models.Model) :
    stock_return = models.ForeignKey("products.StockReturn",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",blank=True,null=True,on_delete=models.CASCADE)
    qty = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    new_qty = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_stock_return_item'
        verbose_name = _('product stock return item')
        verbose_name_plural = _('product stock return items')


    def __unicode__(self):
        return str(self.product.name)