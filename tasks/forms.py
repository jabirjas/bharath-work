from django import forms
from django.forms.widgets import TextInput, Select,Textarea
from tasks.models import Task, Reminder,Anniversary,Holiday
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete




class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','assignee']
        widgets = {
            'staff': autocomplete.ModelSelect2(url='staffs:staffs_autocomplete', attrs={'data-placeholder': 'Name', 'data-minimum-input-length': 1},),
            'time': TextInput(attrs={'class': 'form-control date-time-picker','placeholder' : 'Time'}),
            'from_time': TextInput(attrs={'class': 'form-control date-time-picker','placeholder' : 'From Time'}),
            'to_time': TextInput(attrs={'class': 'form-control date-time-picker','placeholder' : 'To Time'}),
            'title' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Title'}),
            'description': Textarea(attrs={'class': 'required form-control','placeholder' : 'Description'}),
        }
        error_messages = {
			'staff' : {
                'required' : _("Staff field is required."),
            },
            'title' : {
                'required' : _("Title field is required."),
            },
            'description' : {
                'required' : _("Description field is required."),
            }
        }


class ReminderForm(forms.ModelForm):

    class Meta:
        model = Reminder
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop']
        widgets = {
        	'title' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Title'}),
            'description': TextInput(attrs={'class': 'required form-control','placeholder' : 'Description'}),
            'time': TextInput(attrs={'class': 'form-control date-time-picker','placeholder' : 'Time'}),
            'remind_on': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Remind On'}),
        }
        error_messages = {
            'title' : {
                'required' : _("Title field is required."),
            },
            'description' : {
                'required' : _("Description field is required."),
            },
            'remind_on' : {
                'required' : _("Remind On field is required."),
            },
        }


class AnniversaryForm(forms.ModelForm):
    class Meta:
        model = Anniversary
        fields = ['shop','date','title','note']
        widgets = {
            "title": TextInput(attrs={'class': 'required form-control','placeholder' : 'Title'}),
            "shop" : Select(attrs={'class':'required selectpicker form-control','placeholder' : 'shop'}),
            "date" : TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'date'}),
            "note" : Textarea(attrs={'class':'required form-control limit-height','placeholder' : "Note"}),

        }

        error_messages = {
            'title ' : {
                'required' : _(" Title field is required."),
            },
            'shop' : {
                'required' : _(" shop  field is required."),
            },
            'date' : {
                'required' : _("Start Date field is required."),
            },
            
        }

class HolidayForm(forms.ModelForm):

    class Meta:
        model = Holiday
        fields = ['holiday_category','date','note']
        widgets = {
            "holiday_category" : Select(attrs={'class':'single required selectpicker','placeholder' : 'HOLIDAY_CATEGORY'}),
            "date" : TextInput(attrs={'class':'required form-control date-picker','placeholder' : 'DATE'}),
            "note" : Textarea(attrs={'class':'form-control limit-height','placeholder' : "Note"}),
        }
        error_messages = {
            'holiday_category' : {
                'required' : _("Holiday Category field is required."),
            },
            'date' : {
                'required' : _("Date field is required."),
            }
        }
        