from __future__ import unicode_literals
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel, Shop
from decimal import Decimal


GENDER_CHOICES = (
	('M','Male'),
	('F','Female'),
	('O','Other')
)

SALARY_TYPE = (
	('daily','Daily'),
	('monthly','Monthly')
)

MONTH = (
	('1','January'),
	('2','February'),
	('3','March'),
	('4','April'),
	('5','May'),
	('6','June'),
	('7','July'),
	('8','August'),
	('9','September'),
	('10','October'),
	('11','November'),
	('12','December'),
)


class Designation(BaseModel):
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	name = models.CharField(max_length=128)

	is_deleted = models.BooleanField(default=False)

	class Meta:
		db_table = 'staffs_designation'
		verbose_name = _('designation')
		verbose_name_plural = _('designations')

	def __unicode__(self):
		return self.name


class Staff(BaseModel):
	distributor = models.ForeignKey("distributors.Distributor",blank=True,null=True,on_delete=models.CASCADE)
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	user = models.OneToOneField("auth.user",blank=True,null=True,on_delete=models.CASCADE)
	first_name = models.CharField(max_length=128)
	last_name = models.CharField(max_length=128,blank=True,null=True)
	phone = models.CharField(max_length=15,null=True)
	gender = models.CharField(max_length=5,choices=GENDER_CHOICES)
	dob = models.DateField(blank=True,null=True)
	joined_date = models.DateField()
	salary_type = models.CharField(max_length=30,choices=SALARY_TYPE)
	designation = models.ForeignKey("staffs.Designation",blank=True,null=True,on_delete=models.CASCADE)
	salary = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	photo = models.ImageField(upload_to="uploads/staffs/",blank=True,null=True)
	permissions = models.ManyToManyField("users.Permission")
	
	credit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	debit = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

	is_deleted = models.BooleanField(default=False)

	def permissionlist(self):
		permlist = list(set([x.code for x in self.permissions.all()]))
		
		return permlist
		
	class Meta:
		db_table = 'staffs_staff'
		verbose_name = _('staff')
		verbose_name_plural = _('staffs')

	def __unicode__(self):
		return self.first_name +" " + self.last_name


class StaffSalary(BaseModel):
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	staff = models.ForeignKey("staffs.Staff",on_delete=models.CASCADE)
	from_date = models.DateField()
	to_date = models.DateField()
	days = models.PositiveIntegerField()
	time = models.DateTimeField()
	basic_salary = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	allowance = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))]) 
	deduction = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])    
	total_amount = models.DecimalField(default=0.0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
	is_deleted = models.BooleanField(default=False)
	commission_amount = models.DecimalField(default=0,decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])

	class Meta:
		db_table = 'staffs_staffsalary'
		verbose_name = _('staffsalary')
		verbose_name_plural = _('staffsalaries')
		ordering = ('-a_id',)
		
	def __unicode__(self):
		return self.staff

