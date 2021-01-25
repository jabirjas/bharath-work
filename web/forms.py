from django import forms
from django.forms.widgets import TextInput, Textarea, Select
from web.models import About,ProductCategory,Offer,WebProduct
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete



class AboutForm(forms.ModelForm):
    
    class Meta:
        model = About
        exclude = ['is_deleted','shop','time']
        widgets = {
            'email': TextInput(attrs={'class': 'required form-control email','placeholder' : 'Email'}),
            'phone': TextInput(attrs={'class': 'required form-control','placeholder' : 'phone'}),
            'facebook_link': TextInput(attrs={'class': 'form-control','placeholder' : 'Facebook Link'}),
            'twitter_link': TextInput(attrs={'class': 'form-control','placeholder' : 'Twitter Link'}),
            'gplus_link': TextInput(attrs={'class': 'form-control','placeholder' : 'Gplus Link'}),
            'address': Textarea(attrs={'class': 'required form-control','placeholder' : 'Address'}),
            'description': Textarea(attrs={'class': 'required form-control','placeholder' : 'description'}),
        }
        error_messages = {
            'description' : {
                'required' : _("description field is required."),
            },
            'address' : {
                'required' : _("address field is required."),
            },
            'email' : {
                'required' : _("Email field is required."),
            },
        }

    def clean(self):
        cleaned_data=super(AboutForm, self).clean()
        instances =  About.objects.filter(is_deleted=False)
        exists = False
        for instance in instances:
            if not instance == self.instance:
                exists = True
        if exists:
            raise forms.ValidationError(
                "You can only create this once. If you have any changes, then please update your existing detail."
            )
            
        return cleaned_data


class ProductCategoryForm(forms.ModelForm):
    
    class Meta:
        model = ProductCategory
        exclude = ['is_deleted']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'name'}),
            'description': Textarea(attrs={'class': 'required form-control','placeholder' : 'description'}),
        }
        error_messages = {
            'description' : {
                'required' : _("Description field is required."),
            },
            'name' : {
                'required' : _("Name field is required."),
            },
        }


class OfferForm(forms.ModelForm):

    class Meta:
        model = Offer
        exclude = ['creator','updator','auto_id','is_deleted','actual_price','offer_price','a_id','shop']
        widgets = {
            'product' : autocomplete.ModelSelect2(url='web:web_product_autocomplete', attrs={'data-placeholder': 'Product','class':'form-control required', 'data-minimum-input-length': 1}),            
            'offer_percentage': TextInput(attrs={'class': 'required form-control number','placeholder' : 'Offer percentage'}),
            'start_date': TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'Start date'}),
            'end_date': TextInput(attrs={'class': 'required form-control date-picker','placeholder' : 'End date'}),            
        }

        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'offer_percentage' : {
                'required' : _("Offer percentage field is required."),
            },
            'start_date' : {
                'required' : _("Start date field is required."),
            },
            'end_date' : {
                'required' : _("End Date field is required."),
            }            
        }



class WebProductForm(forms.ModelForm):

    class Meta:
        model = WebProduct
        exclude = ['creator','updator','auto_id','is_deleted','a_id','shop']
        widgets = {
            'product': TextInput(attrs={'class': 'required form-control','placeholder' : 'product'}),
            'category' : autocomplete.ModelSelect2(url='web:product_category_autocomplete',attrs={'data-placeholder': 'Category','data-minimum-input-length': 1},), 
            'price': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Price'}),                 
        }

        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'category' : {
                'required' : _("category  field is required."),
            },
            'price' : {
                'required' : _("Price  field is required."),
            },
              
                    
        }