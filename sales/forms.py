from django import forms
from django.forms.widgets import TextInput, Textarea, Select
from sales.models import Sale, SaleItem,CollectAmount,SaleReturn,SaleReturnItem,PurchaseRequest,PurchaseRequestItem,\
    ReturnableProduct,ProductReturn,ProductReturnItem,CustomerPayment,Estimate,EstimateItem, DamagedProduct,VendorReturn,VendorReturnItem
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from main.models import STATE


class SaleForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Name","class" : 'form-control required'}),required=False)
    customer_address = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Address","class" : ' form-control'}),required=False)
    customer_email = forms.EmailField(widget=forms.TextInput(attrs={"placeholder":"Customer Email","class" : ' form-control'}),required=False)
    customer_phone = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Phone","class" : ' form-control'}),required=False)
    gstin = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Gstin","class" : ' form-control'}),required=False)
    customer_state = forms.ChoiceField(widget=forms.Select(attrs={"class" : 'selectpicker form-control'}),required=False,choices=STATE)
    customer_discount = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Discount","class" : 'form-control'}),required=False)

    class Meta:
        model = Sale
        fields = ['customer','time','special_discount','payment_received','payment_remainder_date','sale_type','no_of_boxes','return_boxes']
        widgets = {
            'customer' : autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 1},),
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'special_discount': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Special Discount'}),
            'payment_received': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Payment Received'}),
            'payment_by_bank': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Payment By bank'}),
            'payment_by_cash': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Payment By cash'}),
            'sale_type': Select(attrs={'class': 'required form-control selectpicker'}),

        }
        error_messages = {
            'customer' : {
                'required' : _("Customer field is required."),
            },
            'time' : {
                'required' : _("Time field is required."),
            },
            'special_discount' : {
                'required' : _("Special discount field is required."),
            },
            'payment_received' : {
                'required' : _("Payment received field is required."),
            },
            'sale_type' : {
                'required' : _("Sale type field is required."),
            }
        }
        help_texts = {
            'customer' : 'Click the x button to select an existing customer or create a new one.',
        }

    def clean(self):
        cleaned_data=super(SaleForm, self).clean()
        customer = self.cleaned_data.get('customer')
        customer_name = self.cleaned_data.get('customer_name')
        customer_address = self.cleaned_data.get('customer_address')

        if not customer and not customer_name and not customer_address:
            if not customer_name:
                string = "enter customer name"
            if not customer_address:
                string = "enter customer address"
            raise forms.ValidationError(
                "Select One of the customer or" +" " + string
            )

        return cleaned_data


class SaleItemForm(forms.ModelForm):

    class Meta:
        model = SaleItem
        exclude = ['creator','updator','auto_id','is_deleted','tax','tax_amount','subtotal','sale','batch_code','tax_added_price']
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Price'}),
            'subtotal': TextInput(attrs={'disabled' : 'disabled', 'class': 'required form-control number','placeholder' : 'Sub Total'}),
            'discount_amount' : TextInput(attrs={'class': 'form-control number','placeholder' : 'Discount Amount'}),
            'discount' : TextInput(attrs={'class': 'form-control number','placeholder' : 'Discount'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'qty' : {
                'required' : _("Quantity field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },
            'cost' : {
                'required' : _("Cost field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'subtotal' : {
                'required' : _("Sub total field is required."),
            }
        }


class EmailSaleForm(forms.Form):
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


class CollectAmountForm(forms.ModelForm):

    class Meta:
        model = CollectAmount
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','balance','remaining_balance','date']
        widgets = {
            'customer' : autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 1},),
            'collect_amount' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Collected Cash'}),
            'balance' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Balance'}),
            'remaining_balance' :TextInput(attrs={'class': 'required form-control','placeholder' : 'Remaining Balance'}),
            'discount' : TextInput(attrs={'class': 'form-control','placeholder' : 'Adjustment'}),
            'remarks' : TextInput(attrs={'class': 'form-control','placeholder' : 'Remarks'}),

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
            'customer' : {
                'required' : _("Customer field is required."),
            },
            'remaining_balance' : {
                'required' : _("Remaining Balance field is required."),
            },
        }


class CustomerPaymentForm(forms.ModelForm):

    class Meta:
        model = CustomerPayment
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop','balance']
        widgets = {
            'customer' : autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 1},),
            'date' : TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}),
            'paid_amount' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Collected Cash'}),
            'balance' : TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Balance'}),
            'remaining_balance' :TextInput(attrs={'class': 'required form-control','placeholder' : 'Remaining Balance'}),
        }
        error_messages = {
            'date' : {
                'required' : _("Date field is required."),
            },
            'paid_amount' : {
                'required' : _("Collect Amount field is required."),
            },
            'balance' : {
                'required' : _("Balance is required."),
            },
            'customer' : {
                'required' : _("Customer field is required."),
            },
            'remaining_balance' : {
                'required' : _("Remaining Balance field is required."),
            },
        }


class SaleReturnForm(forms.ModelForm):

    class Meta:
        model = SaleReturn
        exclude = ['creator','updator','user','shop','a_id','auto_id','distributor','commission_deducted']
        widgets = {
            'customer' : autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 1},),
            'sale' : autocomplete.ModelSelect2(url='sales:sale_autocomplete',attrs={'data-placeholder': 'Sale','data-minimum-input-length': 1},),
            'time' : TextInput(attrs={'placeholder': 'Enter Time','class':'datetimepicker required'}),
            'returnable_amount' : TextInput(attrs={'placeholder': 'Enter Return Amount','class':'form-control number'}),
        }


class SaleReturnItemForm(forms.ModelForm):

    class Meta:
        model = SaleReturnItem
        exclude = ['creator','updator','user','sale_return','shop','cost','is_returned']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Price'}),
        }


class ReturnableProductForm(forms.ModelForm):

    class Meta:
        model = ReturnableProduct
        exclude = ['creator','updator','user','shop','a_id','auto_id','sale_return','damaged_product']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'qty': TextInput(attrs={'placeholder': 'Quantity','class':'required'}),
            'price': TextInput(attrs={'placeholder': 'Price','class':'required number'}),
            'cost': TextInput(attrs={'placeholder': 'Cost','class':'required number'}),
        }


class ProductReturnForm(forms.ModelForm):

    class Meta:
        model = ProductReturn
        exclude = ['creator','updator','user','shop','a_id','auto_id']
        widgets = {
            'distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'Distributor', 'data-minimum-input-length': 1},),
            'time' : TextInput(attrs={'placeholder': 'Enter Time','class':'datetimepicker required'}),
            'amount_returned' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Amount'}),
        }
        error_messages = {
            'distributor' : {
                'required' : _("Distributor field is required."),
            }
        }


class ProductReturnItemForm(forms.ModelForm):

    class Meta:
        model = ProductReturnItem
        exclude = ['creator','updator','user','shop','product_return']
        widgets = {
            'product': autocomplete.ModelSelect2(url='sales:returnable_product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Price'}),
            'returned_qty': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Returned Quantity'}),
            'returned_amount':   TextInput(attrs={'class': 'required form-control','placeholder' : 'Amount'}),
        }


class DamagedProductForm(forms.ModelForm):

    class Meta:
        model = DamagedProduct
        exclude = ['distributor','shop','is_deleted','is_returned']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
        }


class EstimateForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Name","class" : 'form-control required'}),required=False)
    customer_address = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Address","class" : ' form-control'}),required=False)
    customer_email = forms.EmailField(widget=forms.TextInput(attrs={"placeholder":"Customer Email","class" : ' form-control'}),required=False)
    customer_phone = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Phone","class" : ' form-control'}),required=False)
    customer_state = forms.ChoiceField(widget=forms.Select(attrs={"class" : 'selectpicker form-control'}),required=False,choices=STATE)

    class Meta:
        model = Estimate
        fields = ['customer','time','payment_remainder_date','sale_type']
        widgets = {
            'customer' : autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 1},),
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),
            'special_discount': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Special Discount'}),
            'payment_received': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Payment Received'}),
            'sale_type': Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'customer' : {
                'required' : _("Customer field is required."),
            },
            'time' : {
                'required' : _("Time field is required."),
            },
            'special_discount' : {
                'required' : _("Special discount field is required."),
            },
            'payment_received' : {
                'required' : _("Payment received field is required."),
            },
            'sale_type' : {
                'required' : _("Sale type field is required."),
            }
        }
        help_texts = {
            'customer' : 'Click the x button to select an existing customer or create a new one.',
        }

    def clean(self):
        cleaned_data=super(EstimateForm, self).clean()
        customer = self.cleaned_data.get('customer')
        customer_name = self.cleaned_data.get('customer_name')
        customer_address = self.cleaned_data.get('customer_address')

        if not customer and not customer_name and not customer_address:
            if not customer_name:
                string = "enter customer name"
            if not customer_address:
                string = "enter customer address"
            raise forms.ValidationError(
                "Select One of the customer or" +" " + string
            )

        return cleaned_data


class EstimateItemForm(forms.ModelForm):

    class Meta:
        model = EstimateItem
        exclude = ['creator','updator','auto_id','is_deleted','tax','tax_amount','cost','subtotal','estimate','tax_added_price']
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Price'}),
            'subtotal': TextInput(attrs={'disabled' : 'disabled', 'class': 'required form-control number','placeholder' : 'Sub Total'}),
            'discount_amount' : TextInput(attrs={'class': 'form-control number','placeholder' : 'Discount Amount'}),
            'discount' : TextInput(attrs={'class': 'form-control number','placeholder' : 'Discount'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'qty' : {
                'required' : _("Quantity field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },
            'cost' : {
                'required' : _("Cost field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'subtotal' : {
                'required' : _("Sub total field is required."),
            }
        }


class VendorReturnForm(forms.ModelForm):

    class Meta:
        model = VendorReturn
        exclude = ['creator','updator','user','shop','a_id','auto_id','time','total_amount']
        widgets = {
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 1},),
            'time' : TextInput(attrs={'placeholder': 'Enter Time','class':'datetimepicker required'}),
            'total_amount' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Amount'}),
        }
        error_messages = {
            'vendor' : {
                'required' : _("Vendor field is required."),
            }
        }


class VendorReturnItemForm(forms.ModelForm):

    class Meta:
        model = VendorReturnItem
        exclude = ['creator','updator','user','shop','vendor_return']
        widgets = {
            'product': autocomplete.ModelSelect2(url='sales:returnable_product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Price'}),
        }


class PurchaseRequestForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Name","class" : 'form-control required'}),required=False)
    customer_address = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Address","class" : ' form-control'}),required=False)
    customer_email = forms.EmailField(widget=forms.TextInput(attrs={"placeholder":"Customer Email","class" : ' form-control'}),required=False)
    customer_phone = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Customer Phone","class" : ' form-control'}),required=False)
    gstin = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Gstin","class" : ' form-control'}),required=False)
    customer_state = forms.ChoiceField(widget=forms.Select(attrs={"class" : 'selectpicker form-control'}),required=False,choices=STATE)
    customer_discount = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Discount","class" : 'form-control'}),required=False)

    class Meta:
        model = PurchaseRequest
        fields = ['customer','time']
        widgets = {
            'customer' : autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 1},),
            'time': TextInput(attrs={'class': 'required form-control date-time-picker','placeholder' : 'Time'}),            
        }
        error_messages = {
            'customer' : {
                'required' : _("Customer field is required."),
            },
            'time' : {
                'required' : _("Time field is required."),
            },           
        }
        help_texts = {
            'customer' : 'Click the x button to select an existing customer or create a new one.',
        }

    def clean(self):
        cleaned_data=super(PurchaseRequestForm, self).clean()
        customer = self.cleaned_data.get('customer')
        customer_name = self.cleaned_data.get('customer_name')
        customer_address = self.cleaned_data.get('customer_address')

        if not customer and not customer_name and not customer_address:
            if not customer_name:
                string = "enter customer name"
            if not customer_address:
                string = "enter customer address"
            raise forms.ValidationError(
                "Select One of the customer or" +" " + string
            )

        return cleaned_data


class PurchaseRequestItemForm(forms.ModelForm):

    class Meta:
        model = PurchaseRequestItem
        exclude = ['creator','updator','auto_id','is_deleted','cost','subtotal','purchase_request','price']
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'qty': TextInput(attrs={'class': 'required form-control number qty','placeholder' : 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Price'}),
            'subtotal': TextInput(attrs={'disabled' : 'disabled', 'class': 'required form-control number','placeholder' : 'Sub Total'}),           
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'qty' : {
                'required' : _("Quantity field is required."),
            },
            'unit' : {
                'required' : _("Unit field is required."),
            },
            'cost' : {
                'required' : _("Cost field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'subtotal' : {
                'required' : _("Sub total field is required."),
            }
        }