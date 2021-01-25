from __future__ import unicode_literals
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from main.models import STATE


class Customer(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    address = models.TextField()
    phone = models.CharField(max_length=128,null=True,blank=True)
    email = models.EmailField(null=True,blank=True)
    state = models.CharField(max_length=128,choices=STATE,default="Kerala")

    first_time_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    first_time_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    gstin = models.CharField(max_length=128,null=True,blank=True)
    is_deleted = models.BooleanField(default=False)
    is_system_generated = models.BooleanField(default=False)
    return_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

    remarks = models.TextField(null=True,blank=True)
    credit_limit = models.DecimalField(default=0,decimal_places=2,max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    
    no_of_boxes = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'customers_customer'
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        ordering = ('auto_id',)
        unique_together = (("shop","name","address"),)

    def __unicode__(self):
        return "%s - %s" %(self.name,self.address)
