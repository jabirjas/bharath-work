from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select
from products.models import Product, Category,SubCategory,ProductAlternativeUnitPrice,Measurement,Asset,Batch,Brand,ProductExpiryDate,\
ProductBatch,InventoryAdjustment,StockReturnItem,InventoryAdjustmentItem
from distributors.models import Distributor
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _


CATEGORY = (
    ('all','All'),
    ('category','Category'),
) 

class ProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        exclude = ['creator','updator','auto_id','is_deleted','a_id','tax_excluded_price','code','mrp','wholesale_price','wholesale_tax_excluded_price','tax','unit','best_before','packing_charge','product_expiry_before','vendor','cost','price']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'code': TextInput(attrs={'class': 'required form-control','placeholder' : 'Code'}),
            'net_weight': TextInput(attrs={'class': 'form-control','placeholder' : 'Net Weight'}),
            'hsn': TextInput(attrs={'class': 'form-control','placeholder' : 'HSN'}),
            'category' : autocomplete.ModelSelect2(url='products:category_autocomplete',attrs={'data-placeholder': 'Category','data-minimum-input-length': 1},),
            'subcategory': autocomplete.ModelSelect2(url='products:subcategory_autocomplete',forward=['category'] ,attrs={'data-placeholder': 'Sub Category', 'data-minimum-input-length': 1},),
            'tax_category':autocomplete.ModelSelect2(url='finance:tax_category_autocomplete', attrs={'data-placeholder': 'Tax Category', 'data-minimum-input-length': 1},),
            'brand' : autocomplete.ModelSelect2(url='products:brand_autocomplete',attrs={'data-placeholder': 'Brand','data-minimum-input-length': 1},),
            'unit_type' : Select(attrs={'class': 'required form-control selectpicker'}),
            'stock': TextInput(attrs={'class': 'required form-control','placeholder' : 'Stock'}),
            'tax_excluded_price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Tax Excluded Price'}),            
            'discount': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Discount'}),
            'low_stock_limit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Low stock limit'}),
            'best_before': TextInput(attrs={'class': 'number form-control','placeholder' : 'Best before'}),
            'product_expiry_before': TextInput(attrs={'class': 'number form-control','placeholder' : 'Expiry limit'}),
            'packing_charge': TextInput(attrs={'class': 'number form-control','placeholder' : 'Packing Charge'}),
            'shop': HiddenInput(),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'code' : {
                'required' : _("Code field is required."),
            },
            'unit_type' : {
                'required' : _("Unit type field is required."),
            },
            'stock' : {
                'required' : _("Stock field is required."),
            },
            'cost' : {
                'required' : _("Cost field is required."),
            },
            'mrp' : {
                'required' : _("MRP field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'tax_excluded_price' : {
                'required' : _(" Tax Excluded Price field is required."),
            },
            'tax_category' : {
                'required' : _("Tax category field is required."),
            },
            'discount' : {
                'required' : _("Discount field is required."),
            },
            'low_stock_limit' : {
                'required' : _("Low stock limit field is required."),
            },
           
        }
        
        help_texts = {
            'low_stock_limit' : 'You will get one notification when reach this limit',
            'tax' : 'Tax in Percentage',
            'discount' : 'Discount in Rupees',
            'product_expiry_before' : 'You will get one expiry notification when reach this limit',
        }

        labels = {
            'product_expiry_before' : 'Expiry notification',
            'price' : 'Selling Price',
            'mrp' : 'MRP'
        }
        

class ProductPriceForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ["cost","price","vendor",'mrp','wholesale_price']
        widgets = {
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 1},), 
            'cost': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Price'}),
            'mrp': TextInput(attrs={'class': 'number required form-control','placeholder' : 'MRP'}),
            'wholesale_price' : TextInput(attrs={'class': 'number form-control','placeholder' : ' Whole Sale Price'}),
            
        }
        error_messages = {
            'cost' : {
                'required' : _("Cost field is required."),
            },
        }


class ProductAlternativeUnitPriceForm(forms.ModelForm):
    
    class Meta:
        model = ProductAlternativeUnitPrice
        fields = ["unit","cost","price","is_deleted"]
        widgets = {
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'cost': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Price'}),
        }
        error_messages = {
            'unit' : {
                'required' : _("Unit field is required."),
            },
        }


class ProductAlternativeUnitForm(forms.ModelForm):
    
    class Meta:
        model = ProductAlternativeUnitPrice
        fields = ["product","unit","cost","price"]
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'unit': Select(attrs={'class': 'required form-control selectpicker'}),
            'cost': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Cost'}),
            'price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Price'}),
        }
        error_messages = {
            'unit' : {
                'required' : _("Unit field is required."),
            },
        }


class ProductBatchForm(forms.ModelForm):
    
    class Meta:
        model = ProductBatch
        fields = ["cost","qty",'batch_code']
        widgets = {
            'batch_code': Select(attrs={'class': 'required form-control selectpicker'}),
            'cost': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Cost'}),
            'qty': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Qty'}),
        }
        error_messages = {
            'cost' : {
                'required' : _("Cost field is required."),
            },
        }


class ProductExpiryForm(forms.ModelForm):
    
    class Meta:
        model = ProductExpiryDate
        fields = ["manufacture_date","best_before","period","is_deleted"]
        widgets = {
            'manufacture_date': TextInput(attrs={'class': 'required form-control datepickerold','placeholder' : 'Date'}),
            'best_before': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Best before'}),
            'period': Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'manufacture_date' : {
                'required' : _("Manufacture date field is required."),
            },
            'best_before' : {
                'required' : _("Best before field is required."),
            }
        }


class CategoryForm(forms.ModelForm):
    
    class Meta:
        model = Category
        exclude = ['shop','creator','updator','auto_id','is_deleted','a_id']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            }
        }


class SubCategoryForm(forms.ModelForm):

    class Meta:
        model = SubCategory
        exclude = ['creator','updator','auto_id','is_deleted','shop','a_id']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete', attrs={'data-placeholder': 'Category','class':'form-control required', 'data-minimum-input-length': 1}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'category' : {
                'required' : _("Category field is required."),
            },
        }


class BrandForm(forms.ModelForm):
    
    class Meta:
        model = Brand
        exclude = ['shop','creator','updator','auto_id','is_deleted','a_id']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'description': TextInput(attrs={'class': 'form-control','placeholder' : 'Description'}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            }
            
        }


class BatchForm(forms.ModelForm):
    
    class Meta:
        model = Batch
        exclude = ['shop','is_deleted']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'description': TextInput(attrs={'class': 'form-control','placeholder' : 'Description'}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            }
            
        }


class MeasurementForm(forms.ModelForm):
    
    class Meta:
        model = Measurement
        exclude = ['creator','shop','updator','auto_id','is_deleted','a_id','is_base','is_system_generated',]
        widgets = {
            'code': TextInput(attrs={'class': 'required form-control','placeholder' : 'Code'}),
            'unit_type' : Select(attrs={'class': 'required form-control selectpicker'}),
            'unit_name' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'conversion_factor' : TextInput(attrs={'class': 'required form-control','placeholder' : 'conversion factor'}),
            'shop': HiddenInput(),

        }
        error_messages = {
            'code' : {
                'required' : _("Code field is required."),
            }
        } 


class AssetForm(forms.ModelForm):
    
    class Meta:
        model = Asset
        exclude = ['id','is_deleted','creator','updator','shop','auto_id','a_id']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            }            
        }
            

class ProductBarcodeForm(forms.Form):
    unit = forms.IntegerField(widget=forms.TextInput(attrs={"placeholder":"Number","class" : 'form-control required'}))
    product = forms.ModelChoiceField(queryset=Product.objects.filter(is_deleted=False), empty_label=None,widget=autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},) )


class SkipRowForm(forms.Form):
    skip_row = forms.IntegerField(widget=forms.TextInput(attrs={"placeholder":"Number","class" : 'form-control required'}))    
        

class FileForm(forms.Form):
    file = forms.FileField()


class NewProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        exclude = ['creator','updator','code','auto_id','is_deleted','a_id','tax_excluded_price','wholesale_tax_excluded_price','tax','unit','best_before','stock']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'code': TextInput(attrs={'class': 'required form-control','placeholder' : 'Code'}),
            'net_weight': TextInput(attrs={'class': 'form-control','placeholder' : 'Net Weight'}),
            'category' : autocomplete.ModelSelect2(url='products:category_autocomplete',attrs={'data-placeholder': 'Category','data-minimum-input-length': 1},),
            'subcategory': autocomplete.ModelSelect2(url='products:subcategory_autocomplete',forward=['category'] ,attrs={'data-placeholder': 'Sub Category', 'data-minimum-input-length': 1},),
            'tax_category':autocomplete.ModelSelect2(url='finance:tax_category_autocomplete', attrs={'data-placeholder': 'Tax Category', 'data-minimum-input-length': 1},),
            'brand' : autocomplete.ModelSelect2(url='products:brand_autocomplete',attrs={'data-placeholder': 'Brand','data-minimum-input-length': 1},),
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 1},), 
            'unit_type' : Select(attrs={'class': 'required form-control selectpicker'}),
            'cost': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Cost'}),
            'mrp' : TextInput(attrs={'class': 'number required form-control','placeholder' : 'MRP'}),
            'wholesale_price' : TextInput(attrs={'class': 'number required form-control','placeholder' : 'Price'}),
            'price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Price'}),
            'tax_excluded_price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Tax Excluded Price'}),            
            'discount': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Discount'}),
            'low_stock_limit': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Low stock limit'}),
            'best_before': TextInput(attrs={'class': 'form-control','placeholder' : 'Best before'}),
            'packing_charge' : TextInput(attrs={'class': 'number form-control','placeholder' : 'PAcking Charge'}),
            'product_expiry_before': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Expiry limit'}),
            'shop': HiddenInput(),
        }

        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'code' : {
                'required' : _("Code field is required."),
            },
            'unit_type' : {
                'required' : _("Unit type field is required."),
            },
            'stock' : {
                'required' : _("Stock field is required."),
            },
            'cost' : {
                'required' : _("Cost field is required."),
            },
            'wholesale_price' : {
                'required' : _("Wholesale Price field is required."),
            },
            'price' : {
                'required' : _("Price field is required."),
            },
            'tax_excluded_price' : {
                'required' : _(" Tax Excluded Price field is required."),
            },
            'tax_category' : {
                'required' : _("Tax category field is required."),
            },
            'discount' : {
                'required' : _("Discount field is required."),
            },
            'low_stock_limit' : {
                'required' : _("Low stock limit field is required."),
            }
        }
        
        help_texts = {
            'low_stock_limit' : 'You will get one notification when reach this limit',
            'tax' : 'Tax in Percentage',
            'discount' : 'Discount in Rupees',
            'product_expiry_before' : 'You will get one expiry notification when reach this limit',
        }

        labels = {
            'product_expiry_before' : 'Expiry notification',
            'price' : 'Price',
            'mrp' : 'MRP'
        }

class InventoryForm(forms.Form):
    selection_type = forms.ChoiceField(choices=CATEGORY,widget=forms.Select(attrs={"placeholder":"Month","class": 'form-control selectpicker'}))  
    category = forms.ModelChoiceField(
        queryset = Category.objects.all(),
        widget = autocomplete.ModelSelect2(url='products:categories_autocomplete',attrs={'data-placeholder': 'Search','data-minimum-input-length': 1},)
    )
    subcategory = forms.ModelChoiceField(
        queryset = SubCategory.objects.all(),
        widget = autocomplete.ModelSelect2(url='products:subcategories_autocomplete',attrs={'data-placeholder': 'Search','data-minimum-input-length': 1},)
    )


class InventoryAdjustmentForm(forms.ModelForm):
    
    class Meta:
        model = InventoryAdjustmentItem
        fields = ["qty","new_qty","product"]
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'qty': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Qty'}),
            'new_qty': TextInput(attrs={'class': 'number required form-control','placeholder' : 'New Qty'}),           
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
        }


class DisInventoryForm(forms.Form): 
    distributor = forms.ModelChoiceField(
        queryset = Distributor.objects.filter(is_deleted=False,is_salesman=False),
        widget = Select(attrs={'class': 'required form-control selectpicker'}),
    )
   
class StockReturnItemForm(forms.ModelForm):
    
    class Meta:
        model = StockReturnItem
        fields = ["qty","new_qty","product"]
        widgets = {
            'product' : autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 1},),
            'qty': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Qty'}),
            'new_qty': TextInput(attrs={'class': 'number required form-control','placeholder' : 'New Qty'}),           
        }
        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
        }