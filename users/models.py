from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Notification(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User",blank=True,null=True,related_name="user_%(class)s_objects",on_delete=models.CASCADE)
    who = models.ForeignKey("auth.User",blank=True,null=True,related_name="who_%(class)s_objects",on_delete=models.CASCADE) 
    subject = models.ForeignKey("users.NotificationSubject",on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product",null=True,blank=True,on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer",null=True,blank=True,on_delete=models.CASCADE)
    sale = models.ForeignKey("sales.Sale",null=True,blank=True,on_delete=models.CASCADE)
    task = models.ForeignKey("tasks.Task",null=True,blank=True,on_delete=models.CASCADE)
    expiry_date = models.ForeignKey("products.ProductExpiryDate",null=True,blank=True,on_delete=models.CASCADE)
    
    amount = models.CharField(max_length=128,null=True,blank=True)
    
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users_notification'
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ('-time',)  
    
    class Admin:
        list_display = ('subject',)

    def __unicode__(self):
        return self.subject.name


class NotificationSubject(models.Model):
    code = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    
    class Meta:
        db_table = 'users_notification_subject'
        verbose_name = _('notification subject')
        verbose_name_plural = _('notification subjects')
        ordering = ('name',)
    
    class Admin:
        list_display = ('name',)

    def __unicode__(self):
        return self.name
    
    
class AccountBalance(models.Model):
    user = models.OneToOneField("auth.User",on_delete=models.CASCADE)
    balance = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    
    class Meta:
        db_table = 'users_account_balance'
        verbose_name = _('account balance')
        verbose_name_plural = _('account balances')
        ordering = ('user',)  
    
    def __unicode__(self):
        return self.user.username
    

class Permission(models.Model):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128)
    app = models.CharField(max_length=128)

    class Meta:
        db_table = 'permission'
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ('app',)

    class Admin:
        list_display = ('id', 'name', 'code', 'app')

    def __unicode__(self):
        return self.name + ' - ' + self.app


class UserActivity(models.Model):
    shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User",blank=True,on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    activity_type = models.CharField(max_length=128)
    app = models.CharField(max_length=128)
    title = models.CharField(max_length=128)
    description = models.TextField()
    
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_activity'
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        ordering = ('-time',)
        
    class Admin:
        list_display = ('shop','user','time','activity_type','app')
        
    def __unicode__(self):
        return self.title
    
    