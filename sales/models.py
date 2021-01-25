from __future__ import unicode_literals
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from finance.models import Transaction
from versatileimagefield.fields import VersatileImageField


STATUS_SALE_RETURN = (('returnable', 'Returnable'),('damaged', 'Damaged'))

SALE_TYPE = (
    ('retail','Retail'),
    ('wholesale','Wholesale'),
)

GST_TYPE = (
    ('sgst','SGST'),
    ('igst','IGST'),
)

STATUS = (
    ('orginal','Orginal'),
    ('edited','Edited'),
    ('deleted','Deleted')
)

class Sale(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    sale_type = models.CharField(max_length=128,choices=SALE_TYPE,default="retail")
    invoice_id = models.CharField(max_length=128)
    time = models.DateTimeField()
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    total_tax_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    total_discount_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    special_discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    payment_received = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    round_off = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    collected_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    payment_remainder_date = models.DateField(blank=True,null=True)
    gst_type = models.CharField(max_length=128,choices=GST_TYPE,default="sgst")
    old_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    old_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    commission_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    amount_from_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    return_item_total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    return_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    customer_gstin_invoice_id = models.PositiveIntegerField(blank=True,null=True)
    customer_non_gstn_invoice_id = models.PositiveIntegerField(blank=True,null=True) 
    status = models.CharField(max_length=128,choices=STATUS,default="orginal")

    no_of_boxes = models.PositiveIntegerField(default=0,blank=True,null=True)
    return_boxes = models.PositiveIntegerField(default=0,blank=True,null=True)
     
    is_deleted = models.BooleanField(default=False)
    
    def total_taxable_amount(self):
        sale_items = SaleItem.objects.filter(sale=self)
        total_taxable_amount = 0
        for sale_item in sale_items:
            if not sale_item.return_item:
                total_taxable_amount += sale_item.taxable_amount()

        return total_taxable_amount

    def get_sale_items(self):
        return SaleItem.objects.filter(sale=self)

    def get_return_sale_items(self):
        return SaleItem.objects.filter(sale=self,return_item=True)

    def sale_return_amount(self):
        return_amount = 0
        if SaleReturn.objects.filter(sale=self).exists() :
            return_amount = SaleReturn.objects.filter(sale=self).aggregate(amount=Sum('returnable_amount')).get('amount',0)
        return return_amount

    def product_list(self):
        permlist = list(set([item.product.name for item in self.get_sale_items()]))
        list_string = ", ".join(str(x) for x in permlist)
        return list_string

    def hsn_list(self):
        permlist = list(set([item.product.hsn for item in self.get_sale_items()]))
        list_string = ", ".join(str(x) for x in permlist)
        return list_string

    def tax_report(self):

        gst_type = self.gst_type
        sgst_amount = 0
        cgst_amount = 0

        if gst_type == "sgst":
            sgst_amount = self.total_tax_amount/2
            cgst_amount = self.total_tax_amount/2

        elif gst_type == "igst":
            cgst_amount = self.total_tax_amount

        results = {
            "cgst_amount" : cgst_amount,
            "sgst_amount" : sgst_amount
        }
        return results   


    class Meta:
        db_table = 'sales_sale'
        verbose_name = _('sale')
        verbose_name_plural = _('sales')
        ordering = ('-time',)

    def __unicode__(self):
        return "%s - %s - %s" %(str(self.a_id), self.customer.name,str(self.total))


class SaleItem(models.Model):
    sale = models.ForeignKey("sales.Sale",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    batch_code = models.ForeignKey("products.Batch",blank=True,null=True,limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax_added_price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    return_qty = models.DecimalField(default=0,null=True,blank=True,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    return_item = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def taxable_amount(self):
        return self.subtotal - self.tax_amount

    def actual_qty(self):
        return self.qty - self.return_qty

    class Meta:
        db_table = 'sales_sale_item'
        verbose_name = _('sale item')
        verbose_name_plural = _('sale items')
        ordering = ('product',)

    def __unicode__(self):
        return "%s - %s" %(self.product.name,str(self.qty))


class CollectAmount(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    date = models.DateField()
    collect_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    customer = models.ForeignKey("customers.Customer",blank=True,null=True,on_delete=models.CASCADE)
    remaining_balance = models.DecimalField(default=0,decimal_places=2, max_digits=15)
    remarks = models.TextField(null=True,blank=True)

    is_deleted = models.BooleanField(default=False)

    def get_status(self):
        status = ""
        if Transaction.objects.filter(collect_amount=self).exists() :
            transaction = Transaction.objects.get(collect_amount=self)
            transaction_mode = transaction.transaction_mode
            if transaction_mode == 'cash' :
                status = "Cash Paid"
            else :
                if transaction.payment_mode == 'cheque_payment' :
                    if transaction.is_cheque_withdrawed :
                        status = "Cheque Withdrawed"
                    elif transaction.is_cheque_returned :
                        status = "Cheque Returned"
                    else :
                        status = "Pending"
                elif transaction.payment_mode == 'internet_banking' :
                    status = "Paid Through Internet Banking"
                else :
                    status = "Paid Through Card Payment"
                    
        return status

    class Meta:
        db_table = 'collect_amount'
        verbose_name = _('collect_amount')
        verbose_name_plural = _('collect_amounts')
        ordering = ('-auto_id',)


    def __unicode__(self):
        return "%s" %(self.collect_amount)


class SaleCollectAmountHistory(models.Model):
    sale = models.ForeignKey("sales.Sale",on_delete=models.CASCADE)
    amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    collect_amount = models.ForeignKey("sales.CollectAmount",blank=True,null=True,on_delete=models.CASCADE)
    paid_from_sale = models.ForeignKey("sales.Sale",related_name="paid_from_%(class)s_objects",blank=True,null=True,on_delete=models.CASCADE)

    class meta:
        db_table = 'sales_sale_collect_amount_history'
        verbose_name = _('sale collect amount history')
        verbose_name_plural = _('sale collect amount histories')

    def __unicode__(self):
        return self.amount


class CustomerPayment(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    date = models.DateField()
    paid_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    customer = models.ForeignKey("customers.Customer",blank=True,null=True,on_delete=models.CASCADE)
    remaining_balance = models.DecimalField(default=0,decimal_places=2, max_digits=15)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'payment_amount'
        verbose_name = _('payment_amount')
        verbose_name_plural = _('payment_amounts')
        ordering = ('-auto_id',)


    def __unicode__(self):
        return "%s" %(self.collect_amount)


class SaleReturn(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    sale = models.ForeignKey("sales.Sale",on_delete=models.CASCADE)
    time = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)
    commission_deducted = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    returnable_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    distributor = models.ForeignKey("distributors.Distributor",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    is_from_sale = models.BooleanField(default=False)

    class Meta:
        db_table = 'sale_return'
        verbose_name = _('sale return')
        verbose_name_plural = _('sale returns')
        ordering = ('-auto_id',)

    class Admin:
        list_display = ('customer',)

    def get_sale_return_items(self):
        return SaleReturnItem.objects.filter(sale_return=self)

    def __unicode__(self):
        return "%s - %s" %(str(self.customer.name),str(self.time.date()))

    def t(self):
        items_total = 0
        total_cost = 0
        items = SaleReturnItem.objects.filter(sale_return=self)
        for i in items:
            qty = Decimal(i.qty)
            price = i.price
            sub = qty * price
            packing_charge = qty * i.product.packing_charge
            items_total += sub

            cost = i.cost
            t_cost = (qty * cost) + packing_charge
            total_cost += t_cost

        subtotal =  items_total
        total =  items_total

        sale_amount = self.sale.total
        sale_balance = self.sale.balance
        return_amount = 0
        if sale_balance > 0:
            return_amount = sale_amount - sale_balance
        else:
            return_amount = sale_amount

        result = {
            "subtotal" : subtotal,
            "total" : round(total,2),
            "total_cost" : round(total_cost),
            "return_amount" : return_amount,
        }
        return result


class DamagedProduct(models.Model):
    time = models.DateTimeField(null=True,blank=True)
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",blank=True,null=True,on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    image = VersatileImageField('Image',upload_to="sales/damaged-items/",blank=True,null=True)

    class Meta:
        db_table = 'damaged_product'
        verbose_name = _('damaged product')
        verbose_name_plural = _('damaged products')

    class Admin:
        list_display = ('product',)

    def __unicode__(self):
        return self.product.name


class VendorProduct(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)

    class Meta:
        db_table = 'vender_product'
        verbose_name = _('vendor product')
        verbose_name_plural = _('vendor products')

    class Admin:
        list_display = ('product',)

    def __unicode__(self):
        return self.product.name


class SaleReturnItem(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    sale_return = models.ForeignKey("sales.SaleReturn",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)
    image = VersatileImageField('Image',upload_to="sales/return-items/",blank=True,null=True)

    class Meta:
        db_table = 'sale_return_item'
        verbose_name = _('sale return item')
        verbose_name_plural = _('sale return items')

    class Admin:
        list_display = ('product',)

    def __unicode__(self):
        return self.product.name

    def sub_total(self):
        return self.price * self.qty


class ReturnableProduct(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    sale_return = models.ForeignKey("sales.SaleReturn",null=True,blank=True,on_delete=models.CASCADE)
    damaged_product = models.ForeignKey("sales.DamagedProduct",null=True,blank=True,on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)

    class Meta:
        db_table = 'returnable_product'
        verbose_name = _('returnable product')
        verbose_name_plural = _('returnable products')

    class Admin:
        list_display = ('product',)

    def __unicode__(self):
        return self.product.name


class ProductReturn(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",on_delete=models.CASCADE)
    time = models.DateTimeField(blank=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'product_return'
        verbose_name = _('product return')
        verbose_name_plural = _('product returns')
        ordering = ('-auto_id',)

    class Admin:
        list_display = ('distributor',)

    def __unicode__(self):
        return self.distributor.name


class ProductReturnItem(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product_return = models.ForeignKey("sales.ProductReturn",on_delete=models.CASCADE)
    product = models.ForeignKey("sales.DamagedProduct",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_return_item'
        verbose_name = _('product return item')
        verbose_name_plural = _('product return items')

    class Admin:
        list_display = ('product',)

    def __unicode__(self):
        return self.product.product.name


class VendorReturn(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor",on_delete=models.CASCADE)
    time = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)
    total_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    class Meta:
        db_table = 'sales_vendor_return'    
        verbose_name = _('vendor return')
        verbose_name_plural = _('vendor returns')
        ordering = ('-auto_id',)
 
    class Admin:
        list_display = ('vendor','time','total_amount')
         
    def __unicode__(self):
        return self.vendor.name


class VendorReturnItem(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    vendor_return = models.ForeignKey("sales.VendorReturn",on_delete=models.CASCADE)
    product = models.ForeignKey("sales.VendorProduct",on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)
     
    class Meta:
        db_table = 'sales_vendor_return_item'
        verbose_name = _('vendor return item')
        verbose_name_plural = _('vendor return items')
 
    class Admin:
        list_display = ('product','qty','cost')
         
    def __unicode__(self):
        return self.product.name 


class Estimate(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    sale_type = models.CharField(max_length=128,choices=SALE_TYPE,default="retail")
    time = models.DateTimeField()
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    total_tax_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    total_discount_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    special_discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    payment_received = models.DecimalField(decimal_places=2,blank=True,null=True, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0,decimal_places=2,blank=True,null=True, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    round_off = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    collected_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    payment_remainder_date = models.DateField(blank=True,null=True)
    gst_type = models.CharField(max_length=128,choices=GST_TYPE,default="sgst")
    old_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    old_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    def total_taxable_amount(self):
        estimate_items = EstimateItem.objects.filter(estimate=self)
        total_taxable_amount = 0
        for estimate_item in estimate_items:
            total_taxable_amount += estimate_item.taxable_amount()

        return total_taxable_amount

    class Meta:
        db_table = 'sales_estimate'
        verbose_name = _('estimate')
        verbose_name_plural = _('estimates')
        ordering = ('-auto_id',)

    def __unicode__(self):
        return "%s - %s - %s" %(str(self.a_id), self.customer.name,str(self.total))


class EstimateItem(models.Model):
    estimate = models.ForeignKey("sales.Estimate",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Measurement",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax_added_price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    return_qty = models.DecimalField(default=0,null=True,blank=True,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    def taxable_amount(self):
        return self.subtotal - self.tax_amount

    def actual_qty(self):
        return self.qty - self.return_qty

    class Meta:
        db_table = 'sales_estimate_item'
        verbose_name = _('estimate item')
        verbose_name_plural = _('estimate items')
        ordering = ('product',)

    def __unicode__(self):
        return "%s - %s" %(self.product.name,str(self.qty))


class PaymentHistory(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    payment_from = models.ForeignKey("sales.Sale",related_name='payment_from',on_delete=models.CASCADE)
    payment_to = models.ForeignKey("sales.Sale",related_name='payment_to',on_delete=models.CASCADE)
    amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'sales_payment_history'    
        verbose_name = _('sales payment history')
        verbose_name_plural = _('sales payment histories')
        
    def __unicode__(self):
        return str(self.amount)


class PurchaseRequest(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",limit_choices_to={'is_deleted': False},blank=True,null=True,on_delete=models.CASCADE)
    time = models.DateTimeField()
    total = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_created = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'sales_purchase_request'
        verbose_name = _('purchase_request')
        verbose_name_plural = _('purchase_requests')
        ordering = ('-auto_id',)

    def __unicode__(self):
        return "%s - %s - %s" %(str(self.a_id), self.customer.name,str(self.total))


class PurchaseRequestItem(models.Model):
    purchase_request = models.ForeignKey("sales.PurchaseRequest",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    qty = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])    
    subtotal = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    return_qty = models.DecimalField(default=0,null=True,blank=True,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    return_item = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def taxable_amount(self):
        return self.subtotal - self.tax_amount

    def actual_qty(self):
        return self.qty - self.return_qty

    class Meta:
        db_table = 'sales_purchase_request_item'
        verbose_name = _('purchase_request item')
        verbose_name_plural = _('purchase_request items')
        ordering = ('product',)

    def __unicode__(self):
        return "%s - %s" %(self.product.name,str(self.qty))
