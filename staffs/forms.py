from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select
from staffs.models import Staff, Designation, StaffSalary
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete


class DesignationForm(forms.ModelForm):

    class Meta:
        model = Designation
        exclude = ['creator', 'updator', 'auto_id', 'is_deleted', 'a_id','shop']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'})
        }
        error_messages = {
            'name': {
                'required': _("Name field is required."),
            }
        }


class StaffForm(forms.ModelForm):

    class Meta:
        model = Staff
        exclude = ['creator', 'updator', 'auto_id', 'is_deleted', 'a_id','user','shop','permissions','credit','debit']
        widgets = {
            'distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'Distributor', 'data-minimum-input-length': 1},),
            'first_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'First Name'}),
            'last_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'designation': autocomplete.ModelSelect2(url='staffs:designation_autocomplete', attrs={'data-placeholder': 'Designation', 'data-minimum-input-length': 1},),
            'salary': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Salary'}),
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'gender': Select(attrs={'class': 'required form-control selectpicker', 'placeholder': 'Gender'}),
            'salary_type': Select(attrs={'class': 'required form-control selectpicker'}),
            'dob': TextInput(attrs={'class': 'required form-control date-picker', 'placeholder': 'Date Of Birth'}),
            'joined_date': TextInput(attrs={'class': 'required form-control date-picker', 'placeholder': 'Joined DAte'}),
        }
        error_messages = {
            'first_name': {
                'required': _("First Name field is required."),
            },
            'designation': {
                'required': _("Designation field is required."),
            },
            'salary': {
                'required': _("Salary field is required."),
            },
            'phone': {
                'required': _("phone field is required."),
            },
            'gender': {
                'required': _("Sex field is required."),
            },
            'salary_type': {
                'required': _("Salary Type field is required."),
            },
            'joined_date': {
                'required': _("Joined Date field is required."),
            },
            'dob': {
                'required': _("DOB field is required."),
            },
            'photo' : {
            'required' : _("Photo field is required."),
            },
            'image' : {
            'required' : _("Image field is required."),
            }
        }
        labels = {
            'dob' : 'Date of birth'
        }



class StaffSalaryForm(forms.ModelForm):
    
    class Meta:
        model=StaffSalary
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','total_amount']            
        widgets = {
            'staff': autocomplete.ModelSelect2(url='staffs:staffs_autocomplete', attrs={'data-placeholder': 'Staff', 'data-minimum-input-length': 1},),
            'from_date': TextInput(attrs={'class': 'date-picker form-control','placeholder' : 'From date'}),
            'to_date': TextInput(attrs={'class': 'form-control date-picker','placeholder' : 'To Date'}),
            'days': TextInput(attrs={'class': 'form-control','placeholder' : 'No. days'}),
            'basic_salary': TextInput(attrs={'class': 'form-control','placeholder' : 'Basic Salary'}),
            'allowance': TextInput(attrs={'class': 'form-control','placeholder' : 'Allowance'}),
            'deduction': TextInput(attrs={'class': 'form-control','placeholder' : 'Deduction'}),
            'commission_amount': TextInput(attrs={'class': 'form-control','placeholder' : 'Commission Amount'}),
        }
        error_messages = {
            'staff' : {
                'required' : _("Staff field is required."),
            },
            'date' : {
                'required' : _("Date field is required."),
            },
            'amount' : {
                'required' : _("Amount field is required."),
            },
            'commission_amount' : {
                'required' : _("Commission Amount field is required."),
            }
        }
    def clean(self):
        cleaned_data=super(StaffSalaryForm, self).clean()
        staff = self.cleaned_data.get('staff')
        from_date = self.cleaned_data.get('from_date')
        if StaffSalary.objects.filter(staff__pk=staff.pk,is_deleted=False).exists():
            staff_salaries = StaffSalary.objects.filter(staff__pk=staff.pk,is_deleted=False).exclude(pk=self.instance.pk)
            for staff_salary in staff_salaries:
                if staff_salary.to_date > from_date or staff_salary.to_date == from_date:
                    raise forms.ValidationError(
                        "Salary already paid"
                    )
        return cleaned_data
