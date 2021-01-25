from django import forms
from django.forms.widgets import TextInput, Select, Textarea
from purchases.models import Purchase, PurchaseItem,PaidAmount,CollectAmounts,PurchaseInvoice,\
    PurchaseInvoiceItem,AssetPurchaseItem,AssetPurchase, PurchaseItemSplit
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _



class PurchaseForm(forms.ModelForm):

    
    class Meta:
        model = Purchase
        exclude = ['creator','tax','updator','auto_id','is_deleted','a_id','shop','subtotal','total','balance','paid','credit_amount_added','paid_amount_added','old_debit','old_credit']
        widgets = {
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 1},), 
            'subtotal' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Subtotal'}),
            'special_discount': TextInput(attrs={'class': 'required form-control','placeholder' : 'Special discount'}),
            'total': TextInput(attrs={'class': 'required form-control','placeholder' : 'Total'}),
            'balance': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Balance'}),
            'invoice_id': TextInput(attrs={'class': 'form-control','placeholder' : 'Invoice Id'}),
            'tax_category':autocomplete.ModelSelect2(url='finance:tax_category_autocomplete', attrs={'data-placeholder': 'Tax Category', 'data-minimum-input-length': 1},),
            'paid_amount': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Paid Amount'}),
        }
        error_messages = {
            'time' : {
                'required' : _("Time field is required."),
            },
			'vendor' : {
                'required' : _("Vendor field is required."),
            },
            'subtotal' : {
                'required' : _("Subtotal field is required."),
            },
            'special_discount' : {
                'required' : _("Special discount field is required."),
            },
            'total' : {
                'required' : _("Total field is required."),
            },
            
        }


class PurchaseItemForm(forms.ModelForm):
    
    class Meta:
        model = PurchaseItem
        exclude = ['creator','updator','auto_id','is_deleted','a_id','purchase','subtotal','tax','qty_to_split']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},), 
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
            'price' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Price'}),
            'selling_price' : TextInput(attrs={'class': 'required form-control','placeholder' : ' Selling Price'}),
            'packing_charge' : TextInput(attrs={'class': 'required form-control','placeholder' : 'PAcking Charge'}),
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
            'discount' : {
                'required' : _("Discount field is required."),
            },
            'subtotal' : {
                'required' : _("Subtotal field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },
            'packing_charge' : {
                'required' : _("Packing charge field is required."),
            },
            
        }


class PurchaseItemSplitForm(forms.ModelForm):
    
    class Meta:
        model = PurchaseItemSplit
        exclude = ['is_deleted','total_taken','purchase_item','packing_charge']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},), 
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'conversion' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Conversion'}),
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'qty' : {
                'required' : _("Qty field is required."),
            },
            'conversion' : {
                'required' : _("Conversion field is required."),
            },
            
        }


class EmailPurchaseForm(forms.Form):
    email = forms.EmailField(widget=TextInput(attrs={'class': 'required form-control email','placeholder' : 'Email'}))
    name = forms.CharField(widget=TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}))
    content = forms.CharField(
        help_text="Link will be added automatically. You do not need to insert manually.",
        widget=Textarea(attrs={
             'class': 'required form-control limit-hieght',
             'placeholder' : 'Content'
            }
        )
    )


class PaidAmountForm(forms.ModelForm):
    
    class Meta:
        model = PaidAmount
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','balance']
        widgets = {
            'vendor' : autocomplete.ModelSelect2(url='vendors:vendor_autocomplete',attrs={'data-placeholder': 'Vendor','data-minimum-input-length': 1},),
            'date' : TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}),
            'paid' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Paided Cash'}),
            'balance' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Balance'}),
            'remaining_balance' :TextInput(attrs={'class': 'required form-control','placeholder' : 'Remaining Balance'}),
            
        }
        error_messages = {
            'date' : {
                'required' : _("Date field is required."),
            },
            'paid' : {
                'required' : _("Paid Amount field is required."),
            },
            'balance' : {
                'required' : _("Balance is required."),
            },
            'vendor' : {
                'required' : _("vendor field is required."),
            },
            'remaining_balance' : {
                'required' : _("Remaining Balance field is required."),
            },
        }


class CollectAmountsForm(forms.ModelForm):
    
    class Meta:
        model = CollectAmounts
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','balance']
        widgets = {
            'vendor' : autocomplete.ModelSelect2(url='vendors:vendor_autocomplete',attrs={'data-placeholder': 'Vendor','data-minimum-input-length': 1},),
            'date' : TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}),
            'collect_amount' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Collected Cash'}),
            'balance' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Balance'}),
            'remaining_balance' :TextInput(attrs={'class': 'required form-control','placeholder' : 'Remaining Balance'}),
            
        }
        error_messages = {
            'date' : {
                'required' : _("Date field is required."),
            },
            'collect_amount' : {
                'required' : _("Collect Amount field is required."),
            },
            'balance' : {
                'required' : _("Balance is required."),
            },
            'vendor' : {
                'required' : _("Vendor field is required."),
            },
            'remaining_balance' : {
                'required' : _("Remaining Balance field is required."),
            },
        }


class PurchaseInvoiceForm(forms.ModelForm):
    
    class Meta:
        model = PurchaseInvoice
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop']
        widgets = {
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 1},), 
            'total' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Total'}), 
            'invoice_type' : Select(attrs={'class': 'required form-control selectpicker'}),           
        }
        error_messages = {
            'time' : {
                'required' : _("Time field is required."),
            },
            'vendor' : {
                'required' : _("Vendor field is required."),
            },           
            
        }


class PurchaseInvoiceItemForm(forms.ModelForm):
    
    class Meta:
        model = PurchaseInvoiceItem
        exclude = ['creator','updator','auto_id','is_deleted','a_id','invoice']
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
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
            'unit' : {
                'required' : _("Unit field is required."),
            },
            
        }


class AssetPurchaseForm(forms.ModelForm):
    
    class Meta:
        model = AssetPurchase
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','subtotal','total','balance','paid','round_off']
        widgets = {
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 1},), 
            'subtotal' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Subtotal'}),
            'special_discount': TextInput(attrs={'class': 'required form-control','placeholder' : 'Special discount'}),
            'total': TextInput(attrs={'class': 'required form-control','placeholder' : 'Total'}),
            'balance': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Balance'}),
            'paid_amount': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Paid Amount'}),
        }
        error_messages = {
            'time' : {
                'required' : _("Time field is required."),
            },
            'vendor' : {
                'required' : _("Vendor field is required."),
            },
            'subtotal' : {
                'required' : _("Subtotal field is required."),
            },
            'special_discount' : {
                'required' : _("Special discount field is required."),
            },
            'total' : {
                'required' : _("Total field is required."),
            },
            
        }


class AssetPurchaseItemForm(forms.ModelForm):
    
    class Meta:
        model = AssetPurchaseItem
        exclude = ['creator','updator','auto_id','is_deleted','a_id','purchase','subtotal','tax']
        widgets = {
            'asset': autocomplete.ModelSelect2(url='products:asset_autocomplete', attrs={'data-placeholder': 'Asset', 'data-minimum-input-length': 1},), 
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'price' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Price'}),
            'discount': TextInput(attrs={'class': 'required form-control','placeholder' : 'Discount'}),
            'subtotal': TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Subtotal'}),
        }
        error_messages = {
            'asset' : {
                'required' : _("Asset field is required."),
            },
            'qty' : {
                'required' : _("Qty field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'discount' : {
                'required' : _("Discount field is required."),
            },
            'subtotal' : {
                'required' : _("Subtotal field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },
            
        }
        

class EmailInvoiceForm(forms.Form):
    email = forms.EmailField(widget=TextInput(attrs={'class': 'required form-control email','placeholder' : 'Email'}))
    name = forms.CharField(widget=TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}))
    content = forms.CharField(
        help_text="Link will be added automatically. You do not need to insert manually.",
        widget=Textarea(attrs={
             'class': 'required form-control',
             'placeholder' : 'Content'
            }
        )
    )