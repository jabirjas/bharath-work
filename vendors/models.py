from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from decimal import Decimal
from django.core.validators import MinValueValidator


class Vendor(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    address = models.TextField()
    first_time_credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    first_time_debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    phone = models.CharField(max_length=128)
    phone2 = models.CharField(max_length=128,blank=True,null=True)
    email = models.EmailField(null=True,blank=True)
    gstin = models.CharField(max_length=128,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'vendors_vendor'
        verbose_name = _('vendor')
        verbose_name_plural = _('vendors')
        unique_together = (("shop","name"),)

    def __unicode__(self):
        return self.name
