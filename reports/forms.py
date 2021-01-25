from django import forms
from distributors.models import Distributor
from products.models import Product
from customers.models import Customer
from dal import autocomplete


MONTH = (
    ('0','All'),
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
CATEGORY = (
    ('bb','B-B'),
    ('bc','B-C'),
    ('all','All'),
    )

SALETYPE = (
    ('top_selling','Top Selling Products'),
    ('low_selling','Low Selling Products')
)


class ReportForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    category = forms.ChoiceField(choices=CATEGORY,widget=forms.Select(attrs={"placeholder":"Category","class": 'form-control selectpicker'})) 

class DailyReportForm(forms.Form):
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}))

class DistributorReportForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}))
    distributor = forms.ModelChoiceField(
        queryset=Distributor.objects.filter(is_deleted=False),
        widget=forms.Select(attrs={"class": 'form-control selectpicker'}),
        )
    def __init__(self, *args, **kwargs):
        super(DistributorReportForm, self).__init__(*args, **kwargs)
        self.fields['distributor'].empty_label = 'All'

class MaufactureReportForm(forms.Form):
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'form-control date-picker','placeholder' : 'Date'}))
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_deleted=False),
        widget=autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
        )
    def __init__(self, *args, **kwargs):
        super(MaufactureReportForm, self).__init__(*args, **kwargs)
        self.fields['product'].empty_label = 'All'


class CollectAmountReportForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}))


class PerformanceReportForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}))
    distributor = forms.ModelChoiceField(
        queryset=Distributor.objects.filter(is_deleted=False),
        widget=forms.Select(attrs={"class": 'form-control selectpicker'}),
        )
    sale_type = forms.ChoiceField(choices=SALETYPE,widget=forms.Select(attrs={"class": 'form-control select2'}))    
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_deleted=False),
        widget=autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
        )
    def __init__(self, *args, **kwargs):
        super(PerformanceReportForm, self).__init__(*args, **kwargs)
        self.fields['distributor'].empty_label = 'All'


class CustomerReportForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}))
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_deleted=False),
        widget=autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer', 'data-minimum-input-length': 1},),
        ) 


class ReturnReportForm(forms.Form):
    month = forms.ChoiceField(choices=MONTH,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'})) 
    year = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"yyyy","class": 'form-control'}))
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Date'}))
    distributor = forms.ModelChoiceField(
        queryset=Distributor.objects.filter(is_deleted=False),
        widget=forms.Select(attrs={"class": 'form-control selectpicker'}),
        )
    def __init__(self, *args, **kwargs):
        super(ReturnReportForm, self).__init__(*args, **kwargs)
        self.fields['distributor'].empty_label = 'All'