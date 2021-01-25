from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel



HOLIDAY_CATEGORY = (
	('public','Public'),
	('national','National'),

)

EVENT_CATEGORY = (
	('birthday','Birthday'),
	('anniversary','Anniversary'),
	('holiday','Holiday'),
	('leave','Leave'),
	('task','Task'),
)



class Task(BaseModel):
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	assignee = models.ForeignKey("auth.User",on_delete=models.CASCADE)
	staff = models.ForeignKey("staffs.Staff",on_delete=models.CASCADE)
	time = models.DateTimeField(blank=True,null=True)
	from_time = models.DateTimeField(blank=True,null=True)
	to_time = models.DateTimeField(blank=True,null=True)
	title = models.CharField(max_length=128)
	description = models.TextField()
	is_deleted = models.BooleanField(default=False)


	class Meta:
		db_table = 'tasks_task'
		verbose_name = _('task')
		verbose_name_plural = _('tasks')

	def __unicode__(self):
		return self.title


class Reminder(BaseModel):
	title = models.CharField(max_length=128)
	description = models.TextField()
	attachment = models.FileField(blank=True,null=True)
	time = models.DateTimeField(blank=True,null=True)
	remind_on = models.DateTimeField()
	is_deleted = models.BooleanField(default=False)


	class Meta:
		db_table = 'tasks_reminder'
		verbose_name = _('reminder')
		verbose_name_plural = _('reminders')


class Anniversary(models.Model):
	title = models.CharField(max_length=128)
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	date = models.DateField()
	note = models.TextField(null=True,blank=True)

	is_deleted = models.BooleanField(default=False)

	class Meta:
		db_table = 'task_anniversary'
		verbose_name = _('anniversary')
		verbose_name_plural = _('anniversaries') 
		
	def __unicode__(self):
		return self.shop.name 


class Holiday(BaseModel):
	holiday_category = models.CharField(max_length=10,choices=HOLIDAY_CATEGORY,default="public")
	date = models.DateField()
	is_deleted = models.BooleanField(default=False)
	note = models.TextField(null=True,blank=True)
	
	class Meta:
		db_table = 'holiday'
		verbose_name = _('holiday')
		verbose_name_plural = _('holidays')
		
	def __unicode__(self):
		return self.date


class Event(models.Model):
	event_category = models.CharField(max_length=128,choices=EVENT_CATEGORY)
	user = models.ForeignKey("auth.User",blank=True,null=True,on_delete=models.CASCADE)
	date=models.DateField()
	title = models.CharField(max_length=128)
	note = models.TextField(null=True,blank=True)
	holiday = models.ForeignKey("tasks.Holiday",blank=True,null=True,on_delete=models.CASCADE)
	anniversary = models.ForeignKey("tasks.Anniversary",blank=True,null=True,on_delete=models.CASCADE)
	shop = models.ForeignKey("main.Shop",on_delete=models.CASCADE)
	task = models.ForeignKey("tasks.Task",blank=True,null=True,on_delete=models.CASCADE)
	is_deleted = models.BooleanField(default=False)
	class Meta:
		db_table = 'event'
		verbose_name = _('event')
		verbose_name_plural = _('events')
	
	def __unicode__(self):
		return self.event_category