from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select
from customers.models import Customer
from django.utils.translation import ugettext_lazy as _


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        exclude = ['creator','updator','auto_id','is_deleted','credit','debit','a_id','is_system_generated','shop','return_amount','no_of_boxes']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'email': TextInput(attrs={'class': 'form-control','placeholder' : 'Email'}),
            'phone': TextInput(attrs={'class': 'form-control','placeholder' : 'Phone'}),
            'address': TextInput(attrs={'class': 'required form-control','placeholder' : 'Address'}),
            'first_time_credit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'First Time Credit'}),
            'first_time_debit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'First Time Debit'}),
            'shop': HiddenInput(),
            'state': Select(attrs={'class': 'required selectpicker'}),
            'gstin': TextInput(attrs={'class': 'form-control','placeholder' : 'Gstin'}),
            'discount': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Discount'}),
            'credit_limit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Credit Limit'}),
            'remarks' : TextInput(attrs={'class': 'form-control','placeholder' : 'Remarks'}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'email' : {
                'required' : _("Email field is required."),
            },
            'phone' : {
                'required' : _("Phone field is required."),
            },
            'address' : {
                'required' : _("Address field is required."),
            },
            'first_time_credit' : {
                'required' : _("First time credit field is required."),
            },
            'first_time_debit' : {
                'required' : _("First time debit field is required."),
            },
            'theme' : {
                'required' : _("Theme field is required."),
            },
            'state' : {
                'required' : _("State field is required."),
            }
        }
        help_texts = {
            'first_time_credit' : "Your fund at customer's hand",
            'first_time_debit' : "Customer's fund in your hand"
        }

    def clean(self):
        cleaned_data=super(CustomerForm, self).clean()

        debit = self.cleaned_data.get('first_time_debit')
        credit = self.cleaned_data.get('first_time_credit')

        if debit > 0 and credit > 0:
            raise forms.ValidationError(
                "Credit and debit can't be greater than zero at the same time"
            )

        return cleaned_data
