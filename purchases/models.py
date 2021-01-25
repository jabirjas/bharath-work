from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from decimal import Decimal
from django.core.validators import MinValueValidator


UNIT_TYPES = (
	('quantity', 'Quantity'),
	('weight', 'Weight'),
	('distance', 'Distance'),
	('volume', 'Volume'),
	('time', 'Time'),
	('area', 'Area'),
)


PERIOD = (
	('days', 'Days'),
	('month', 'Month'),
)


INVOICE_TYPE = (
	('general','General'),
	('vendor','Vendor'),
)


class Purchase(BaseModel):
	time = models.DateTimeField()
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	vendor = models.ForeignKey("vendors.Vendor",on_delete=models.CASCADE)
	subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	special_discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	paid_amount= models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	is_deleted = models.BooleanField(default=False)
	paid = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	credit_amount_added = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	paid_amount_added = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	invoice_id = models.CharField(max_length=128,null=True,blank=True)
	tax_category = models.ForeignKey("finance.TaxCategory",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
	tax = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

	old_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	old_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

	class meta:
		db_table = 'purchases_purchase'
		verbose_name = _('purchase')
		verbose_name_plural = _('purchases')
		ordering = ('time',)

	def __unicode__(self):
		return self.vendor.name


class PurchaseCollectAmountHistory(models.Model):
	purchase = models.ForeignKey("purchases.Purchase",on_delete=models.CASCADE)
	amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	paid_amount = models.ForeignKey("purchases.PaidAmount",blank=True,null=True,on_delete=models.CASCADE)
	paid_from_purchase = models.ForeignKey("purchases.Purchase",related_name="paid_from_%(class)s_objects",blank=True,null=True,on_delete=models.CASCADE)

	class meta:
		db_table = 'purchases_purchase_collect_amount_history'
		verbose_name = _('purchase collect amount history')
		verbose_name_plural = _('purchase collect amount historyies')

	def __unicode__(self):
		return self.amount


class PurchaseItem(models.Model):
	purchase = models.ForeignKey("purchases.Purchase",on_delete=models.CASCADE)
	product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
	unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
	qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	selling_price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	is_deleted = models.BooleanField(default=False)
	is_split = models.BooleanField(default=False)
	qty_to_split = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

	class meta:
		db_table = 'purchases_purchase_item'
		verbose_name = _('purchase item')
		verbose_name_plural = _('purchase items')

	def __unicode__(self):
		return self.product.name


class PurchaseItemSplit(models.Model):

	purchase_item = models.ForeignKey("purchases.PurchaseItem",on_delete=models.CASCADE)
	product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
	qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	conversion = models.DecimalField(default=0,decimal_places=3, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	total_taken = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	is_deleted = models.BooleanField(default=False)
	packing_charge = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	
	class meta:
		db_table = 'purchases_purchase_item_split'
		verbose_name = _('purchase item split')
		verbose_name_plural = _('purchase item splits')

	def __unicode__(self):
		return self.product.name


class PaidAmount(BaseModel):
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	date = models.DateField()
	paid = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	vendor = models.ForeignKey("vendors.Vendor",blank=True,null=True,on_delete=models.CASCADE)
	remaining_balance = models.DecimalField(default=0,decimal_places=2, max_digits=15)
	
	is_deleted = models.BooleanField(default=False)
	
	class Meta:
		db_table = 'paid_amount'
		verbose_name = _('paid_amount')
		verbose_name_plural = _('paid_amounts')
		ordering = ('-auto_id',)
	
	
	def __unicode__(self): 
		return "%s" %(self.paid_amount)


class CollectAmounts(BaseModel):
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	date = models.DateField()
	collect_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	vendor = models.ForeignKey("vendors.Vendor",blank=True,null=True,on_delete=models.CASCADE)
	remaining_balance = models.DecimalField(default=0,decimal_places=2, max_digits=15)
	
	is_deleted = models.BooleanField(default=False)
	
	class Meta:
		db_table = 'vendor_collect_amount'
		verbose_name = _('vendor_collect_amount')
		verbose_name_plural = _('vendor_collect_amounts')
		ordering = ('-auto_id',)
	
	
	def __unicode__(self): 
		return "%s" %(self.collect_amount)


class PurchaseInvoice(BaseModel):
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	time = models.DateTimeField()	
	vendor = models.ForeignKey("vendors.Vendor",blank=True,null=True,on_delete=models.CASCADE)
	invoice_type = models.CharField(max_length=128,choices=INVOICE_TYPE,default="general")

	is_deleted = models.BooleanField(default=False)
	
	class meta:
		db_table = 'purchases_purchaseInvoice'
		verbose_name = _('purchaseinvoice')
		verbose_name_plural = _('purchasesinvoices')

	def __unicode__(self):
		return self.vendor.name


class PurchaseInvoiceItem(models.Model):
	invoice = models.ForeignKey("purchases.PurchaseInvoice",on_delete=models.CASCADE)
	product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
	unit = models.ForeignKey("products.Measurement",on_delete=models.CASCADE)
	qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

	is_deleted = models.BooleanField(default=False)

	class meta:
		db_table = 'purchases_purchase_invoice_item'
		verbose_name = _('purchase invoice item')
		verbose_name_plural = _('purchase invoice items')

	def __unicode__(self):
		return self.product.name


class AssetPurchase(BaseModel):
	time = models.DateTimeField()
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	vendor = models.ForeignKey("vendors.Vendor",on_delete=models.CASCADE)
	subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	special_discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	round_off = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	paid_amount= models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])	
	paid = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	is_deleted = models.BooleanField(default=False)
	class meta:
		db_table = 'purchases_asset_purchase'
		verbose_name = _('asset_purchase')
		verbose_name_plural = _('asset_purchases')

	def __unicode__(self):
		return self.vendor.name


class AssetPurchaseItem(models.Model):

	purchase = models.ForeignKey("purchases.AssetPurchase",on_delete=models.CASCADE)
	asset = models.ForeignKey("products.Asset",null=True,blank=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
	qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])	
	discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	is_deleted = models.BooleanField(default=False)

	class meta:
		db_table = 'purchases_asset_purchase_item'
		verbose_name = _('asset_purchase item')
		verbose_name_plural = _('asset_purchase items')

	def __unicode__(self):
		return self.asset.name

