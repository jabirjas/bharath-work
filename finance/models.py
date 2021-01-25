from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from django.core.validators import MinValueValidator
from decimal import Decimal


TRANSACTION_CATEGORIES = (
    ('income','Income'),
    ('expense','Expense'),
)

TRANSACTION_MODE = (
    ('cash','Cash'),
    ('bank','Bank'),
)

PAYMENT_MODE = (
    ('cheque_payment','Cheque Payment'),
    ('internet_banking','Internet Banking'),
    ('card_payment','Card Payment'),
)

PAYMENT_TO = (
    ('cash_account','Cash Account'),
    ('bank_account','Bank Account'),
)

ACC_TYPE = (
    ('savings','Savings'),
    ('current','Current'),
)


class CashAccount(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    is_system_generated = models.BooleanField(default=False)
    first_time_balance = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'cash_account'
        verbose_name = _('cash account')
        verbose_name_plural = _('cash accounts')
        ordering = ('name',)

    class Admin:
        list_display = ('name',)

    def __unicode__(self):
        return self.name


class BankAccount(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    ifsc = models.CharField(max_length=128)
    branch = models.CharField(max_length=128)
    account_type = models.CharField(max_length=128,choices=ACC_TYPE)
    account_no = models.CharField(max_length=128)
    first_time_balance = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cheque_return_charge = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    is_deleted = models.BooleanField(default=False)
    # Balance to be added, its a self function

    class Meta:
        db_table = 'bank_account'
        verbose_name = _('bank account')
        verbose_name_plural = _('bank accounts')
        ordering = ('name',)

    class Admin:
        list_display = ('name',)

    def __unicode__(self):
        return self.name


class TransactionCategory(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    category_type = models.CharField(max_length=7,choices=TRANSACTION_CATEGORIES)
    is_system_generated = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'transaction_category'
        verbose_name = 'transaction category'
        verbose_name_plural = 'transaction categories'
        ordering = ('category_type',)
        unique_together = (('category_type','name','shop'),)

    class Admin:
        list_display = ('name', 'category_type', 'is_system_generated')

    def __unicode__(self):
        return self.name


class TaxCategory(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    tax = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'tax_category'
        verbose_name = 'tax category'
        verbose_name_plural = 'tax categories'

    class Admin:
        list_display = ('name')

    def __unicode__(self):
        return self.name


class Transaction(BaseModel):
    staff = models.ForeignKey("staffs.Staff",null=True,blank=True,on_delete=models.CASCADE)
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=7,choices=TRANSACTION_CATEGORIES,default="income",blank=True)
    transaction_category = models.ForeignKey("finance.TransactionCategory",blank=True,null=True,on_delete=models.CASCADE)

    sale = models.ForeignKey("sales.Sale",null=True,blank=True,related_name="sale%(class)s_objects",on_delete=models.CASCADE)
    sale_return = models.ForeignKey("sales.SaleReturn",null=True,blank=True,related_name="sale_return%(class)s_objects",on_delete=models.CASCADE)
    purchase_return = models.ForeignKey("sales.ProductReturn",null=True,blank=True,related_name="purchase_return%(class)s_objects",on_delete=models.CASCADE)
    collect_amount = models.ForeignKey("sales.CollectAmount",null=True,blank=True,related_name="collect_amount%(class)s_objects",on_delete=models.CASCADE)
    customer_payment = models.ForeignKey("sales.CustomerPayment",null=True,blank=True,related_name="customer_payment%(class)s_objects",on_delete=models.CASCADE)
    vender_payment = models.ForeignKey("purchases.CollectAmounts",null=True,blank=True,related_name="customer_payment%(class)s_objects",on_delete=models.CASCADE)
    purchase = models.ForeignKey("purchases.Purchase",null=True,blank=True,on_delete=models.CASCADE)
    asset_purchase = models.ForeignKey("purchases.AssetPurchase",null=True,blank=True,on_delete=models.CASCADE)
    paid = models.ForeignKey("purchases.PaidAmount",null=True,blank=True,on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",null=True,blank=True,on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor",null=True,blank=True,on_delete=models.CASCADE)
    staff_salary = models.ForeignKey('staffs.StaffSalary',blank=True,null=True,on_delete=models.CASCADE)

    transaction_mode = models.CharField(max_length=15,choices=TRANSACTION_MODE,default="cash")
    payment_mode = models.CharField(max_length=128,choices=PAYMENT_MODE,blank=True,null=True)
    cheque_details = models.CharField(max_length=128,null=True,blank=True)
    is_cheque_withdrawed = models.BooleanField(default=False)
    is_cheque_returned = models.BooleanField(default=False)
    card_details = models.CharField(max_length=128,null=True,blank=True)
    payment_to = models.CharField(max_length=128,choices=PAYMENT_TO,default="cash_account",null=True,blank=True)
    bank_account = models.ForeignKey("finance.BankAccount",null=True,blank=True,on_delete=models.CASCADE)
    cash_account = models.ForeignKey("finance.CashAccount",null=True,blank=True,on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))],null=True,blank=True)
    description = models.CharField(max_length=128,blank=True,null=True)
    cheque_date = models.DateField(blank=True,null=True)

    date = models.DateTimeField()
    first_transaction = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'transaction'
        verbose_name = 'transaction'
        verbose_name_plural = 'transactions'
        ordering = ('-date',)

    class Admin:
        list_display = ('id', 'amount','transaction_type')

    def __unicode__(self):
        return self.id


class StaffSalaryPayment(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    staff_salary = models.ForeignKey("staffs.StaffSalary",null=True,blank=True,on_delete=models.CASCADE)
    transaction = models.ForeignKey("finance.Transaction",null=True,blank=True,on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'staff_salary_payment'
        verbose_name = 'staff salary payment'
        verbose_name_plural = 'staff salary payments'
        ordering = ('a_id',)

    class Admin:
        list_display = ('transaction', 'staff_salary', 'amount')

    def __unicode__(self):
        return self.amount


class CashTransfer(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    from_cash_account = models.ForeignKey("finance.CashAccount",null=True,blank=True,related_name="from_%(class)s_objects",on_delete=models.CASCADE)
    to_cash_account = models.ForeignKey("finance.CashAccount",null=True,blank=True,related_name="to_%(class)s_objects",on_delete=models.CASCADE)
    distributor = models.ForeignKey("distributors.Distributor",null=True,blank=True,on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))]) 

    is_deleted= models.BooleanField(default=False)
    
    class Meta:
        db_table = 'finance_cash_transfer'
        verbose_name = _('cash transafer')
        verbose_name_plural = _('cash transafers')
        ordering = ('a_id',)
        
    def __unicode__(self):
        return str(self.amount)


class Journel(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    date = models.DateField() 

    cash_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    cash_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    bank_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    bank_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    transaction = models.ForeignKey("finance.Transaction",null=True,blank=True,on_delete=models.CASCADE)
    income = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])    
    expense = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    sale = models.ForeignKey("sales.Sale",null=True,blank=True,related_name="sale%(class)s_objects",on_delete=models.CASCADE)
    sale_return = models.ForeignKey("sales.SaleReturn",null=True,blank=True,related_name="sale_return%(class)s_objects",on_delete=models.CASCADE)
    purchase_return = models.ForeignKey("sales.ProductReturn",null=True,blank=True,related_name="purchase_return%(class)s_objects",on_delete=models.CASCADE)
    collect_amount = models.ForeignKey("sales.CollectAmount",null=True,blank=True,related_name="collect_amount%(class)s_objects",on_delete=models.CASCADE)
    customer_payment = models.ForeignKey("sales.CustomerPayment",null=True,blank=True,related_name="customer_payment%(class)s_objects",on_delete=models.CASCADE)
    vender_payment = models.ForeignKey("purchases.CollectAmounts",null=True,blank=True,related_name="customer_payment%(class)s_objects",on_delete=models.CASCADE)
    purchase = models.ForeignKey("purchases.Purchase",null=True,blank=True,on_delete=models.CASCADE)
    asset_purchase = models.ForeignKey("purchases.AssetPurchase",null=True,blank=True,on_delete=models.CASCADE)
    paid = models.ForeignKey("purchases.PaidAmount",null=True,blank=True,on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",null=True,blank=True,on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor",null=True,blank=True,on_delete=models.CASCADE)
    
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'finance_journel'
        verbose_name = 'journel'
        verbose_name_plural = 'journels'
        
    class Admin:
        list_display = ('date')
        
    def __unicode__(self):
        return str(self.date)
