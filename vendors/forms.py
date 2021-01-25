from django import forms
from django.forms.widgets import TextInput
from vendors.models import Vendor
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _


class VendorForm(forms.ModelForm):

    class Meta:
        model = Vendor
        exclude = ['creator','updator','auto_id','is_deleted','a_id','credit','debit','shop']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'address': TextInput(attrs={'class': 'required form-control','placeholder' : 'Address'}),
            'first_time_credit': TextInput(attrs={'class': 'required form-control','placeholder' : 'First Time Credit'}),
            'first_time_debit': TextInput(attrs={'class': 'required form-control','placeholder' : 'First Time Debit'}),
            'phone': TextInput(attrs={'class': 'required form-control','placeholder' : 'Phone'}),
            'phone2': TextInput(attrs={'class': 'form-control','placeholder' : 'Phone'}),
            'gstin': TextInput(attrs={'class': 'form-control','placeholder' : 'GSTIN'}),
            'email': TextInput(attrs={'class': 'form-control','placeholder' : 'Email'}),

        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
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
            'phone' : {
                'required' : _("Phone field is required."),
            }
        }
        help_texts = {
            'first_time_credit' : "Vendor's fund in your hand",
            'first_time_debit' : "Your fund at Vendor's hand"
        }
        
