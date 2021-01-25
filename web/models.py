from __future__ import unicode_literals
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from decimal import Decimal
from main.models import BaseModel


class About(models.Model):
    address = models.TextField()
    description = models.TextField()
    email = models.EmailField()
    phone = models.TextField()
    image = models.ImageField(upload_to="web/about",blank=True,null=True)
    facebook_link = models.URLField(max_length=200,blank=True, null=True)
    twitter_link = models.URLField(max_length=200,blank=True, null=True)
    gplus_link = models.URLField(max_length=200,blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    time = models.DateTimeField(db_index=True,auto_now_add=True) 
    
    class Meta:
        db_table = 'web_about'
        verbose_name = _('about')
        verbose_name_plural = _('about')
        ordering = ('address',)

    def __unicode__(self):
        return self.address


class ProductCategory(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    
    is_deleted = models.BooleanField(default=False)

    def get_products(self):
        return WebProduct.objects.filter(category=self)
    
    class Meta:
        db_table = 'web_product_category'
        verbose_name = _('product category')
        verbose_name_plural = _('product categories')

    def __unicode__(self):
        return self.name


class Offer(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.ForeignKey("web.WebProduct",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE)
    offer_percentage = models.DecimalField(null=True,blank=True,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    offer_price = models.DecimalField(null=True,blank=True,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    actual_price = models.DecimalField(null=True,blank=True,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    start_date = models.DateField()
    end_date = models.DateField()   

    is_featured = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'web_offer'
        verbose_name = _('offer')
        verbose_name_plural = _('offers')
        ordering = ('-start_date',)
        
    def __unicode__(self):
        return self.product.name + " - " + str(self.offer_percentage)


class WebProduct(BaseModel):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    product = models.CharField(max_length=128)
    category = models.ForeignKey("web.ProductCategory",limit_choices_to={'is_deleted': False},on_delete=models.CASCADE) 
    price = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])   
    image = models.ImageField(upload_to="web/offer",blank=True,null=True)   

    is_featured = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'web_product'
        verbose_name = _('product')
        verbose_name_plural = _('products')
        
    def __unicode__(self):
        return self.product + " - " + str(self.category.name)


