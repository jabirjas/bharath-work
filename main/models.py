import uuid
from django.db import models
from django.utils.translation import ugettext_lazy as _
from versatileimagefield.fields import VersatileImageField
from decimal import Decimal
from django.core.validators import MinValueValidator


BOOL_CHOICES = ((1, 'Yes'), (0, 'No'))

THEME_CHOICES = (
    ('teal', 'Teal'),
    ('blue', 'Blue'),
    ('bluegrey', 'Blue Grey'),
    ('cyan-600', 'Cyan'),
    ('green', 'Green'),
    ('lightgreen', 'Light Green'),
    ('purple-400', 'Purple'),
    ('red-400', 'Red'),
    ('pink-400', 'Pink'),
    ('brown', 'Brown'),
    ('grey-600', 'Grey'),
    ('orange', 'Orange')
)

PRINT_CHOICES = (
    ('a4', 'A4'),
    ('compact', 'Compact(77mm)'),
)


STATE = (
    ('Kerala','Kerala'),
    ('Tamil Nadu','Tamil Nadu'),
    ('Karnataka','Karnataka'),
    ('Andaman and Nicobar Islands','Andaman and Nicobar Islands'),
    ('Andhra Pradesh','Andhra Pradesh'),
    ('Arunachal Pradesh','Arunachal Pradesh'),
    ('Assam','Assam'),
    ('Bihar','Bihar'),
    ('Chandigarh','Chandigarh'),
    ('Chhattisgarh','Chhattisgarh'),
    ('Dadra and Nagar Haveli ','Dadra and Nagar Haveli '),
    ('Daman and Diu','Daman and Diu'),
    ('National Capital Territory of Delhi','National Capital Territory of Delhi'),
    ('Goa','Goa'),
    ('Gujarat','Gujarat'),
    ('Haryana','Haryana'),
    ('Himachal Pradesh','Himachal Pradesh'),
    ('Jammu and Kashmir','Jammu and Kashmir'),
    ('Jharkhand','Jharkhand'),
    ('Lakshadweep union territory','Lakshadweep union territory'),
    ('Madhya Pradesh','Madhya Pradesh'),
    ('Maharashtra','Maharashtra'),
    ('Manipur','Manipur'),
    ('Meghalaya','Meghalaya'),
    ('Mizoram','Mizoram'),
    ('Nagaland','Nagaland'),
    ('Odisha','Odisha'),
    ('Puducherry union territory','Puducherry union territory'),
    ('Punjab','Punjab'),
    ('Rajasthan','Rajasthan'),
    ('Sikkim','Sikkim'),
    ('Telangana','Telangana'),
    ('Tripura','Tripura'),
    ('Uttar Pradesh','Uttar Pradesh'),
    ('Uttarakhand','Uttarakhand'),
    ('West Bengal','West Bengal')
)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.PositiveIntegerField(db_index=True,unique=True)
    creator = models.ForeignKey("auth.User",blank=True,related_name="creator_%(class)s_objects",on_delete=models.CASCADE)
    updator = models.ForeignKey("auth.User",blank=True,related_name="updator_%(class)s_objects",on_delete=models.CASCADE)
    date_added = models.DateTimeField(db_index=True,auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    a_id = models.PositiveIntegerField(db_index=True)

    class Meta:
        abstract = True


class Mode(models.Model):
    readonly = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)
    down = models.BooleanField(default=False)

    class Meta:
        db_table = 'mode'
        verbose_name = _('mode')
        verbose_name_plural = _('mode')
        ordering = ('id',)

    class Admin:
        list_display = ('id', 'readonly', 'maintenance', 'down')

    def __unicode__(self):
        return str(self.id)


class App(models.Model):
    date_added = models.DateTimeField(db_index=True,auto_now_add=True)
    application = models.FileField(upload_to="app/")

    class Meta:
        db_table = 'app'
        verbose_name = _('app')
        verbose_name_plural = _('app')
        ordering = ('id',)

    def __unicode__(self):
        return str(self.id)


class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.PositiveIntegerField(db_index=True,unique=True)
    creator = models.ForeignKey("auth.User",blank=True,related_name="creator_%(class)s_objects",on_delete=models.CASCADE)
    updator = models.ForeignKey("auth.User",blank=True,related_name="updator_%(class)s_objects",on_delete=models.CASCADE)
    date_added = models.DateTimeField(db_index=True,auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=128)
    address = models.TextField()
    phone = models.CharField(max_length=128)
    email = models.EmailField()
    website = models.CharField(null=True,blank=True,max_length=128)
    theme = models.CharField(max_length=40,choices=THEME_CHOICES,default="teal")
    logo = VersatileImageField('Logo',upload_to="shop/",blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    fssai_number = models.CharField(max_length=128,blank=True,null=True)
    gstin = models.CharField(max_length=128,blank=True,null=True)
    bill_print_type = models.CharField(max_length=128,choices=PRINT_CHOICES,default="a4")
    block_auto_redirect = models.BooleanField(default=False)
    state = models.CharField(choices=STATE,default="Kerala",max_length=128)
    remove_previous_balance_from_bill = models.BooleanField(default=False)
    commission_per_packet = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    default_paid_value = models.BooleanField(default=True)
    credit_limit = models.DecimalField(default=0,decimal_places=2,max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    
    class Meta:
        db_table = 'shop'
        verbose_name = _('shop')
        verbose_name_plural = _('shops')
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class ShopAccess(models.Model):

    user = models.ForeignKey('auth.User',null=True,on_delete=models.CASCADE)
    shop = models.ForeignKey('main.Shop',blank=True,on_delete=models.CASCADE)
    group = models.ForeignKey('auth.Group',on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_access'
        verbose_name = _('shop_access')
        verbose_name_plural = _('shop_access')
        ordering = ('shop',)

    class Admin:
        list_dispay = ('shop','group','is_accepted',)

    def __unicode__(self):
        return self.shop.name + ' ' + self.group.name
