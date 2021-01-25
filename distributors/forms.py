from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select
from distributors.models import Distributor, StockTransfer, StockTransferItem, DistributorStockTransfer, DistributorStockTransferItem,DirectStockTransferItem,DirectStockTransfer
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete


class DistributorForm(forms.ModelForm):

    class Meta:
        model = Distributor
        exclude = ['creator','updator','no_commission','is_salesman','auto_id','is_deleted','credit','debit','a_id','is_system_generated','shop','commission_tobe_paid','user']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'email': TextInput(attrs={'class': 'form-control','placeholder' : 'Email'}),
            'phone': TextInput(attrs={'class': 'form-control','placeholder' : 'Phone'}),
            'address': TextInput(attrs={'class': 'required form-control','placeholder' : 'Address'}),
            'first_time_credit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'First Time Credit'}),
            'first_time_debit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'First Time Debit'}),
            'shop': HiddenInput(),
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
            }
        }
        help_texts = {
            'first_time_credit' : "Your fund at customer's hand",
            'first_time_debit' : "Sales Man's fund in your hand"
        }

    def clean(self):
        cleaned_data=super(DistributorForm, self).clean()

        debit = self.cleaned_data.get('first_time_debit')
        credit = self.cleaned_data.get('first_time_credit')

        if debit > 0 and credit > 0:
            raise forms.ValidationError(
                "Credit and debit can't be greater than zero at the same time"
            )

        return cleaned_data


class StockTransferForm(forms.ModelForm):


    class Meta:
        model = StockTransfer
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','total']
        widgets = {
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'Sales Man', 'data-minimum-input-length': 1},),
        }

        error_messages = {
            'time' : {
                'required' : _("Time field is required."),
            },
			'distributor' : {
                'required' : _("Distributor field is required."),
            },

        }
        labels = {
            'distributor' : 'Sales Man'
        }


class StockTransferItemForm(forms.ModelForm):

    class Meta:
        model = StockTransferItem
        exclude = ['creator','updator','auto_id','is_deleted','a_id','stock_transfer','price','subtotal']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
			'qty' : {
                'required' : _("Qty field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },

        }


class DistributorStockTransferForm(forms.ModelForm):

    class Meta:
        model = DistributorStockTransfer
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','total']
        widgets = {
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'from_distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'From Sales Man', 'data-minimum-input-length': 1},),
            'to_distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'To Sales Man', 'data-minimum-input-length': 1},),
        }

        error_messages = {
            'time' : {
                'required' : _("Time field is required."),
            },
            'distributor' : {
                'required' : _("Distributor field is required."),
            },

        }

        labels = {
            'from_distributor' : 'From Sales Man',
            'to_distributor' : 'To Sales Man',
        }


class DistributorStockTransferItemForm(forms.ModelForm):

    class Meta:
        model = DistributorStockTransferItem
        exclude = ['creator','updator','auto_id','is_deleted','a_id','distributor_stock_transfer','price','subtotal']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'qty' : {
                'required' : _("Qty field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },

        }


class DirectStockTransferForm(forms.ModelForm):


    class Meta:
        model = DirectStockTransfer
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','total']
        widgets = {
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'Sales Man', 'data-minimum-input-length': 1},),
        }


        error_messages = {
            'time' : {
                'required' : _("Time field is required."),
            },
            'distributor' : {
                'required' : _("Distributor field is required."),
            },

        }
        labels = {
            'distributor' : 'Sales Man'
        }

class DirectStockTransferItemForm(forms.ModelForm):

    class Meta:
        model = DirectStockTransferItem
        exclude = ['creator','updator','auto_id','is_deleted','a_id','direct_stock_transfer','price','subtotal']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'qty' : {
                'required' : _("Qty field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },

        }
