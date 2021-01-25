from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from products.models import Product,ProductGroup,ProductAlternativeUnitPrice,Category,SubCategory,Measurement,Asset,Batch,Brand,ProductExpiryDate,ProductBatch,InventoryAdjustment,InventoryAdjustmentItem
from finance.models import TaxCategory
from finance.forms import TaxCategoryForm
from sales.models import ReturnableProduct
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from main.functions import generate_form_errors, get_auto_id, get_a_id
import datetime
from django.db.models import Q,Sum
from dal import autocomplete
from django.views.decorators.http import require_GET
from django.forms.widgets import Select,TextInput
from users.functions import get_current_shop
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from products.forms import ProductBarcodeForm,ProductPriceForm,SkipRowForm,ProductAlternativeUnitForm,ProductAlternativeUnitPriceForm,SubCategoryForm,NewProductForm,FileForm,InventoryForm,InventoryAdjustmentForm,\
 MeasurementForm, ProductForm, CategoryForm,BrandForm,AssetForm,ProductExpiryForm,ProductBatchForm,BatchForm,DisInventoryForm
from django.core import serializers
from decimal import Decimal
import xlrd
from vendors.models import Vendor
from purchases.models import PurchaseItem
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.conf import settings
from distributors.models import DistributorStock, Distributor
from customers.models import Customer


class CategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Category.objects.filter(is_deleted=False,shop=current_shop)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(name__istartswith=self.q)
                                )

        return items

    def create_object(self, text):
        current_shop = get_current_shop(self.request)
        auto_id = get_auto_id(Category)
        a_id = get_a_id(Category,self.request)
        return Category.objects.create(
            auto_id=auto_id,
            a_id=a_id,
            name=text,
            shop=current_shop,
            creator=self.request.user,
            updator=self.request.user
        )


class SubcategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = SubCategory.objects.filter(is_deleted=False,shop=current_shop)

        category = self.forwarded.get('category', None)

        if category:
            items = items.filter(category=category)
        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(name__istartswith=self.q)
                                )

        return items

    def create_object(self, text):
        current_shop = get_current_shop(self.request)
        auto_id = get_auto_id(SubCategory)
        a_id = get_a_id(SubCategory,self.request)
        category_pk = self.request.POST.get('forward[category]')
        if category_pk:
            category = Category.objects.get(pk=category_pk)
            return SubCategory.objects.create(
                auto_id=auto_id,
                a_id=a_id,
                name=text,
                category=category,
                shop=current_shop,
                creator=self.request.user,
                updator=self.request.user
            )


class BrandAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Brand.objects.filter(is_deleted=False,shop=current_shop)


        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(name__istartswith=self.q)
                                )

        return items

    def create_object(self, text):
        current_shop = get_current_shop(self.request)
        auto_id = get_auto_id(Brand)
        a_id = get_a_id(Brand,self.request)

        return Brand.objects.create(
            auto_id=auto_id,
            a_id=a_id,
            name=text,
            shop=current_shop,
            creator=self.request.user,
            updator=self.request.user
        )

class ProductBatchAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = ProductBatch.objects.filter(is_deleted=False,shop=current_shop)


        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(batch_code__name__istartswith=self.q)
                                )

        return items

    def create_object(self, text):
        current_shop = get_current_shop(self.request)

        return Brand.objects.create(
            auto_id=auto_id,
            a_id=a_id,
            name=text,
            shop=current_shop,
            creator=self.request.user,
            updator=self.request.user
        )


class BatchAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Batch.objects.filter(is_deleted=False,shop=current_shop)
        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(name__istartswith=self.q)
                                )

        return items    

class ProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Product.objects.filter(is_deleted=False,shop=current_shop)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(product_group__name__istartswith=self.q) |
                                 Q(category__name__istartswith=self.q)
                                )

        return items


class AssetAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Asset.objects.filter(is_deleted=False,shop=current_shop)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(name__istartswith=self.q)
                                )

        return items

    def create_object(self, text):
        current_shop = get_current_shop(self.request)
        auto_id = get_auto_id(Asset)
        a_id = get_a_id(Asset,self.request)

        return Asset.objects.create(
            auto_id=auto_id,
            a_id=a_id,
            name=text,
            shop=current_shop,
            creator=self.request.user,
            updator=self.request.user
        )


@check_mode
@login_required
@shop_required
def dashboard(request):
    return HttpResponseRedirect(reverse('products:products'))


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_product'])
def create(request):
    current_shop = get_current_shop(request)
    AlternativeUnitFormset = formset_factory(ProductAlternativeUnitPriceForm,extra=1)
    ProductExpiryFormset = formset_factory(ProductExpiryForm,extra=1)
    ProductPriceFormset = formset_factory(ProductPriceForm,extra=1)
    if request.method == 'POST':
        form = ProductForm(request.POST)
        form.fields['unit_type'].queryset = Measurement.objects.filter(shop=current_shop,is_base=True,is_deleted=False)
        alternative_unit_formset = AlternativeUnitFormset(request.POST,prefix='alternative_unit_formset')
        product_price_formset = ProductPriceFormset(request.POST,prefix='product_price_formset')
        if form.is_valid() and alternative_unit_formset.is_valid() and product_price_formset.is_valid() :
            
            error_messages = ''
            unit_type = form.cleaned_data['unit_type']
            base_unit = Measurement.objects.get(shop=current_shop,is_base=True,is_deleted=False,unit_type=unit_type)
            units = []
            for f in alternative_unit_formset:

                unit = f.cleaned_data['unit']

                if unit in units:
                    error_messages += "Duplicate unit %s" % unit.unit_name
                else:
                    units.append(unit)

            if not error_messages:
                name = form.cleaned_data['name']
                name = name.capitalize()
                pr_name = name
                if not ProductGroup.objects.filter(name=name).exists():
                    ProductGroup.objects.create(name=name)
                product_name = ProductGroup.objects.filter(name=name)[0]
                discount = form.cleaned_data['discount']            
                tax_category = form.cleaned_data['tax_category']
                stock = form.cleaned_data['stock']
                category = form.cleaned_data['category']
                hsn = form.cleaned_data['hsn']
                subcategory = None
                if category:
                    subcategory = form.cleaned_data['subcategory']
                brand = form.cleaned_data['brand']
                low_stock_limit = form.cleaned_data['low_stock_limit']
                discount = form.cleaned_data['discount']
                tax_instance = None
                tax = 0
                if tax_category:
                    tax_instance = get_object_or_404(TaxCategory.objects.filter(is_deleted=False,pk=tax_category.pk))
                    tax = tax_instance.tax

                is_tax_included = form.cleaned_data['is_tax_included']
                for f in product_price_formset:
                    try:
                        auto_id = get_auto_id(Product)
                        a_id = get_a_id(Product,request)
                        vendor = f.cleaned_data['vendor']
                        cost = f.cleaned_data['cost']
                        price = f.cleaned_data['price']  
                        mrp = f.cleaned_data['mrp']   
                        wholesale_price = f.cleaned_data['wholesale_price'] 
                        code = "000" + str(auto_id)
                        name = pr_name + str(code)
                        actual_price = price - discount                        
                        if is_tax_included:
                            tax_excluded_price = (100*actual_price)/(100+tax)
                            wholesale_tax_excluded_price = (100*wholesale_price)/(100+tax)
                        else :
                            tax_excluded_price = actual_price
                            price = tax_excluded_price + (tax_excluded_price*tax)/100

                            wholesale_tax_excluded_price = wholesale_price
                            wholesale_price = wholesale_tax_excluded_price + (wholesale_tax_excluded_price*tax)/100

                        #create product

                        pr = Product(
                            auto_id = auto_id,
                            a_id = a_id,
                            code = code,
                            creator = request.user,
                            updator = request.user,
                            shop = current_shop,
                            name = name,
                            price = price,
                            cost = cost,
                            mrp = mrp,
                            vendor = vendor,
                            tax = tax,
                            unit_type = unit_type,
                            hsn = hsn,
                            unit = base_unit,
                            stock = stock,
                            wholesale_price = wholesale_price,
                            product_group = product_name,
                            wholesale_tax_excluded_price = wholesale_tax_excluded_price,
                            tax_excluded_price = tax_excluded_price,
                            tax_category = tax_category,
                            discount = discount,
                            is_tax_included = is_tax_included,
                            brand = brand,
                            category = category,
                            subcategory = subcategory
                        ).save()                  

                        #save alternate units
                        for f in alternative_unit_formset:
                            try:
                                unit = f.cleaned_data['unit']
                                cost = f.cleaned_data['cost']
                                price = f.cleaned_data['price']
                                ProductAlternativeUnitPrice(
                                    product = pr,
                                    unit = unit,
                                    cost = cost,
                                    price = price,
                                    shop = current_shop
                                ).save()
                            except:
                                pass
                        total_qty = 0

                    except:
                        pass
                
                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Product created successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('products:products')
                }
            else:

                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Duplicate Entry",
                    "message" : error_messages
                }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        else:
            print(form.errors)
            print(alternative_unit_formset.errors)
            
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(alternative_unit_formset,formset=True)
            message += generate_form_errors(product_price_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        unit_type_instance = Measurement.objects.get(shop=current_shop,unit_type="quantity",is_base=True)
        product_form = ProductForm(initial={'shop':current_shop,'unit_type':unit_type_instance})
        product_form.fields['unit_type'].queryset = Measurement.objects.filter(shop=current_shop,is_base=True,is_deleted=False)
        product_form.fields['unit_type'].label_from_instance = lambda obj: "%s" % (obj.unit_type.capitalize())
        alternative_unit_formset = AlternativeUnitFormset(prefix='alternative_unit_formset')
        for form in alternative_unit_formset:
            form.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,is_base=False,is_deleted=False)
            form.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)
        product_price_formset = ProductPriceFormset(prefix='product_price_formset')
        context = {
            "title" : "Create Product ",
            "form" : product_form,
            "alternative_unit_formset" : alternative_unit_formset,
            "product_price_formset" : product_price_formset,
            "url" : reverse('products:create'),
            'new_redirect_window':True,
            "is_create" : True,
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_create_page" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_product'])
def products(request):
    current_shop = get_current_shop(request)
    instances = Product.objects.filter(is_deleted=False,shop=current_shop)
    categories = Category.objects.filter(shop=current_shop,is_deleted=False)
    subcategories = SubCategory.objects.filter(shop=current_shop,is_deleted=False)
    brands = Brand.objects.filter(shop=current_shop,is_deleted=False)
    title = "Products"

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query) | Q(code__icontains=query))
        title = "Products - %s" %query

    category = request.GET.get('category')
    subcategory = request.GET.get('subcategory')
    brand = request.GET.get('brand')
    if category:
        instances = instances.filter(category=category)
        if Category.objects.filter(pk=category).exists():
            cat = Category.objects.get(pk=category)
            title = "Products - %s" %cat.name

    if subcategory:
        instances = instances.filter(subcategory=subcategory)
        if SubCategory.objects.filter(pk=subcategory).exists():
            sub = SubCategory.objects.get(pk=subcategory)
            title = "Products - %s" %sub.name

    if brand:
        instances = instances.filter(brand=brand)
        if Brand.objects.filter(pk=brand).exists():
            bnd = Brand.objects.get(pk=brand)
            title = "Products - %s" %bnd.name

    total_cost = 0
    total_price = 0
    total_stock = instances.aggregate(stock=Sum('stock')).get('stock')
    for instance in instances:
        total_cost += instance.total_cost()
        total_price += instance.total_price()

    total_profit = total_price - total_cost

    context = {
        "instances" : instances,
        'title' : title,
        "brands" : brands,
        "categories" : categories,
        "subcategories" : subcategories,

        "total_profit" : total_profit,
        "total_cost" : total_cost,
        "total_price" : total_price,
        "total_stock" : total_stock,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/products.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_product'])
def product(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Product.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    alternative_units=ProductAlternativeUnitPrice.objects.filter(shop=current_shop,product=instance,is_deleted=False)
    context = {
        "instance" : instance,
        "alternative_units" : alternative_units,
        "title" : "Product : " + instance.product_group.name + " " + instance.code,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/product.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_product'])
def edit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Product.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
  
    if request.method == 'POST':
        response_data = {}
        form = ProductForm(request.POST,instance=instance)
        price_form = ProductPriceForm(request.POST,instance=instance)
        if form.is_valid() and price_form.is_valid():
            name = form.cleaned_data['name']
            pr_name = name.split('0')
            pr_group = ProductGroup.objects.filter(name=pr_name[0])[0]
            price = price_form.cleaned_data['price']
            cost = price_form.cleaned_data['cost']
            wholesale_price = price_form.cleaned_data['wholesale_price']
            mrp = price_form.cleaned_data['mrp']
            discount = form.cleaned_data['discount']
            actual_price = price - discount
            tax_category = form.cleaned_data['tax_category']
            unit_type = form.cleaned_data['unit_type']
            base_unit = Measurement.objects.get(shop=current_shop,is_base=True,is_deleted=False,unit_type=unit_type)
            if tax_category :
                tax_instance = get_object_or_404(TaxCategory.objects.filter(is_deleted=False,pk=tax_category.pk))
                tax = tax_instance.tax
            else:
                tax = 0
            is_tax_included = form.cleaned_data['is_tax_included']

            if is_tax_included:
                tax_excluded_price = (100*actual_price)/(100+tax)
                wholesale_tax_excluded_price = (100*wholesale_price)/(100+tax)
            else :
                old_price = instance.tax_excluded_price

                tax_excluded_price = actual_price
                price = tax_excluded_price + (tax_excluded_price*tax)/100

                wholesale_tax_excluded_price = wholesale_price
                wholesale_price = wholesale_tax_excluded_price + (wholesale_tax_excluded_price*tax)/100

            #update product
            data = form.save(commit=False)
            data.updator = request.user
            data.tax_excluded_price = tax_excluded_price
            data.is_tax_included = is_tax_included
            data.wholesale_tax_excluded_price = wholesale_tax_excluded_price
            data.price = price
            data.cost = cost
            data.wholesale_price = wholesale_price
            data.mrp = mrp
            data.date_updated = datetime.datetime.now()
            data.name = name
            data.tax = tax
            data.product_group = pr_group
            data.unit = base_unit
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Product Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:product',kwargs={'pk':data.pk})
            }
        else:
            message = ""
            message += generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        price = instance.price
        wholesale_price = instance.wholesale_price
        if not instance.is_tax_included:
            price = instance.tax_excluded_price
            wholesale_price = instance.wholesale_tax_excluded_price

        product_form = ProductForm(instance=instance,initial={'shop':current_shop,'price':price,'wholesale_price':wholesale_price})
        product_form.fields['unit_type'].queryset = Measurement.objects.filter(shop=current_shop,is_base=True,is_deleted=False)
        product_form.fields['unit_type'].label_from_instance = lambda obj: "%s" % (obj.unit_type.capitalize())

        product_form.fields['subcategory'].queryset = SubCategory.objects.filter(shop=current_shop,category=instance.category,is_deleted=False)
        price_form = ProductPriceForm(instance=instance)
        context = {
            "form" : product_form,
            "title" : "Edit Product : " + instance.name,
            "instance" : instance,
            "url" : reverse('products:edit',kwargs={'pk':instance.pk}),
            "price_form" : price_form,
            "redirect" : True,
            "is_edit" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/edit.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_product'])
def edit_expiry_date(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductExpiryDate.objects.filter(pk=pk,shop=current_shop))

    if request.method == "POST":
        response_data = {}
        form = ProductExpiryForm(request.POST,instance=instance)

        if form.is_valid():

            #update product
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Updated",
                "redirect" : "true",
                "redirect_url" : reverse('products:product', kwargs = {'pk' :data.product.pk}),
                "message" : "Product Expiry Date Successfully Updated."
            }
        else:
            message = generate_form_errors(form,formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : form.errors
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = ProductExpiryForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Product Expiry Date : " + str(instance.manufacture_date),
            "instance" : instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_animations": True,
            "is_need_datetime_picker" : True,
            "redirect" : True,
        }
        return render(request, 'products/entry_expiry_date.html', context)

@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_product'],allow_self=True,model=Product)
def delete(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Product.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if instance.code == None:
        code = 0
    else:
        code = instance.code

    Product.objects.filter(pk=pk).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Product Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:products')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_product'])
def delete_selected_products(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Product.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Product.objects.filter(pk=pk).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Product(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:products')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_product(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')
    transfer = request.GET.get('transfer')
    sale_type = request.GET.get('sale_type')
    distributor_pk = request.GET.get('distributor')
    customer_pk = request.GET.get('customer')
    purchase_request = request.GET.get('purchase_request')
    barcode = request.GET.get('barcode')
    product_exists = False
    batches = []
    is_mrp = "false"
    distributor = None
    discount = 0
    if barcode == "yes": 
        if Product.objects.filter(shop=current_shop,code=pk).exists():
            item = Product.objects.get(shop=current_shop,code=pk)
            product_exists = True
    else:     
        if Product.objects.filter(pk=pk,shop=current_shop).exists():
            item = Product.objects.get(pk=pk)
            product_exists = True
    if distributor_pk:
        if Distributor.objects.filter(shop=current_shop,pk=distributor_pk).exists():
            distributor = Distributor.objects.get(shop=current_shop,pk=distributor_pk)   

    if product_exists:
        units = []
        unit = {
            "pk" : str(item.unit.pk),
            "name" : item.unit.unit_name,
            "code": item.unit.code,
        }
        units.append(unit)
        alternate_units = ProductAlternativeUnitPrice.objects.filter(product=item,shop=current_shop)
        for u in alternate_units:
            unit = {
                "pk" : str(u.unit.pk),
                "name" : u.unit.unit_name,
                "code": u.unit.code,
            }
            units.append(unit)
        if ProductBatch.objects.filter(product=item,shop=current_shop).exists():            
            batch_instance = ProductBatch.objects.filter(product=item,shop=current_shop).exclude(qty=0)
            for u in batch_instance:
                batch = {
                    "pk" : str(u.batch_code.pk),
                    "name" : u.batch_code.name,
                }
                batches.append(batch)
        vendor = None
        if item.vendor:
            vendor = item.vendor
        elif PurchaseItem.objects.filter(product=item).exists():
            purchase_items = PurchaseItem.objects.filter(product = item)
            purchase_item = purchase_items.latest('purchase__auto_id')
            vendor = purchase_item.purchase.vendor

        tax_excluded_price = item.tax_excluded_price
        if sale_type ==  "retail" :
            tax_excluded_price = item.tax_excluded_price
        elif sale_type == "wholesale":
            tax_excluded_price = item.wholesale_tax_excluded_price

        discount = item.discount
        price = tax_excluded_price

        discount_amount = 0
        if customer_pk:
            if Customer.objects.filter(shop=current_shop,pk=customer_pk).exists():
                customer = Customer.objects.get(shop=current_shop,pk=customer_pk)
                customer_discount = customer.discount
                if customer_discount >  0 :
                    price = item.price
                    discount = customer_discount
                    discount_amount = (price * discount)/100
                    is_mrp = "true"

        stock = 0
        if transfer == "true" or purchase_request == "true" or request.user.is_superuser:
            stock = str(item.stock)
            price = item.price

        elif distributor:
            if DistributorStock.objects.filter(is_deleted=False,product=item,distributor=distributor,shop=current_shop).exists():
                price = item.price
                stock = DistributorStock.objects.get(is_deleted=False,product=item,distributor=distributor,shop=current_shop).stock
        else:
            if DistributorStock.objects.filter(is_deleted=False,product=item,distributor__user=request.user,shop=current_shop).exists():
                stock = DistributorStock.objects.get(is_deleted=False,product=item,distributor__user=request.user,shop=current_shop).stock        

        response_data = {
            "status" : "true",
            'pk' : str(item.pk),
            'code' : item.code,
            'name' :str(item.name),
            'vendor' : str(item.vendor),
            'unit_code' : str(item.unit.code),
            'unit_name' : str(item.unit.unit_name),
            'unit_type' : str(item.unit.unit_type),
            'cost' : str(item.cost),
            'price' : str(item.price),
            'tax' : str(item.tax),
            'stock' : str(item.stock),
            'discount' : str(discount),
            'discount_amount' : str(discount_amount),
            'is_deleted' : item.is_deleted,
            'units' : units ,
            "batches" : batches,
            'wholesale_price' : str(item.wholesale_price),
            'is_mrp' : is_mrp
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@require_GET
def get_unit_price(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('unit')
    product = request.GET.get('product')
    sale_type = request.GET.get('sale_type')
    customer_pk = request.GET.get('customer')
    new_customer_discount = request.GET.get('customer_discount')
    is_mrp = "false"
    if Product.objects.filter(shop=current_shop,pk=product).exists() and Measurement.objects.filter(shop=current_shop,pk=pk).exists():
        instance =  Measurement.objects.get(pk=pk)
        product_instance = Product.objects.get(shop=current_shop,pk=product)
        if ProductAlternativeUnitPrice.objects.filter(unit=instance,product=product_instance,shop=current_shop).exists():
            alternate_unit_instance = ProductAlternativeUnitPrice.objects.get(unit=instance,product=product_instance,shop=current_shop)
            cost = alternate_unit_instance.cost
            price = alternate_unit_instance.price
        else:
            cost = product_instance.cost
            price = product_instance.tax_excluded_price    
        discount_amount = product_instance.discount
        if sale_type ==  "retail" :
            org_price = price + product_instance.discount
        elif sale_type == "wholesale":
            org_price = product_instance.wholesale_tax_excluded_price + product_instance.discount
        if instance.is_base:
            discount_amount = product_instance.discount
            price = product_instance.tax_excluded_price
            discount = round((discount_amount*100)/price)
            if customer_pk:
                if Customer.objects.filter(shop=current_shop,pk=customer_pk).exists():
                    customer = Customer.objects.get(shop=current_shop,pk=customer_pk)
                    customer_discount = customer.discount
                    if customer_discount >  0 :
                        org_price = product_instance.price
                        discount = customer_discount  
                        discount_amount = (org_price * discount)/100
                        is_mrp = "true"
            elif Decimal(new_customer_discount) > 0 :
                org_price = product_instance.mrp
                discount = Decimal(new_customer_discount)
                discount_amount = (org_price * discount)/100  
                is_mrp = "true"          
        else:
            alternate_unit_instance = ProductAlternativeUnitPrice.objects.get(unit=instance,product=product_instance,shop=current_shop)
            cost = alternate_unit_instance.cost
            org_price = alternate_unit_instance.price 
        response_data = {
            'price' : str(org_price),
            'cost' : str(cost),
            "pk" : str(instance.pk),
            "name" : instance.unit_name,
            "discount" : str(discount),
            "discount_amount" : str(discount_amount),
            "status" : "true",
            "is_mrp" : is_mrp,
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Unit or product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@login_required 
@shop_required
@require_GET
def get_unit_cost_price(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('unit')
    product = request.GET.get('product')
    sale_type = request.GET.get('sale_type')
    if Product.objects.filter(shop=current_shop,pk=product).exists() and Measurement.objects.filter(shop=current_shop,pk=pk).exists():
        instance =  Measurement.objects.get(pk=pk)
        product_instance = Product.objects.get(shop=current_shop,pk=product)
        if instance.is_base:
            cost = product_instance.cost
            price = product_instance.price
            discount = product_instance.discount 
            discount_amount = (price * discount)/100
            tax_excluded_price = (price - discount) * 100 /(100+product_instance.tax)
            wholesale_tax_excluded_price = (product_instance.wholesale_price - discount) * 100 /(100+product_instance.tax)
            tax_excluded_cash_price = (product_instance.price - discount) * 100 /(100+product_instance.tax)
            if sale_type ==  "retail" :
                price = tax_excluded_price
            elif sale_type == "wholesale":
                price = wholesale_tax_excluded_price
            elif sale_type == "cash_price":
                price = tax_excluded_cash_price  
        else:
            alternate_unit_instance = ProductAlternativeUnitPrice.objects.get(unit=instance,product=product_instance,shop=current_shop)
            cost = alternate_unit_instance.cost
            price = alternate_unit_instance.price
            
        response_data = {
            'price' : str(price),
            'cost' : str(cost),
            "pk" : str(instance.pk),
            "name" : instance.unit_name, 
            "status" : "true"
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Unit or product not found"
        }
    
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@require_GET
def get_returnable_product(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')

    product_exists = False

    if ReturnableProduct.objects.filter(pk=pk,shop=current_shop).exists():

        item = ReturnableProduct.objects.get(pk=pk,shop=current_shop).product
        product_exists = True

    if product_exists:
        units = []
        unit = {
            "pk" : str(item.unit.pk),
            "code" : item.unit.code,
            "name" : item.unit.unit_name,
            }
        units.append(unit)
        alternate_units = ProductAlternativeUnitPrice.objects.filter(product=item,shop=current_shop)
        for u in alternate_units:
            unit = {
                "pk" : str(u.unit.pk),
                "code" : u.unit.code,
                "name" : u.unit.unit_name,
            }
            units.append(unit)

        response_data = {
            "status" : "true",
            'pk' : str(item.pk),
            'code' : item.code,
            'name' : item.name,
            'cost' : str(item.cost),
            'price' : str(item.price),
            'stock' : str(item.stock),
            'tax' : str(item.tax),
            'discount' : str(item.discount),
            'is_deleted' : item.is_deleted,
            "units" : units
             }
    else:
        response_data = {
            "status" : "false",
            "message" : "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

@check_mode
@login_required
def get_asset(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')

    asset_exists = False

    if Asset.objects.filter(pk=pk,shop=current_shop).exists():
        item = Asset.objects.get(pk=pk)
        asset_exists = True

    if asset_exists:

        response_data = {
            "status" : "true",
            'pk' : str(item.pk),
            'name' : item.name,
            'cost' : str(item.cost),
            'stock' : str(item.quantity),
            'is_deleted' : item.is_deleted
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Asset not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_category'])
def create_category(request):
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(Category)
            a_id = get_a_id(Category,request)

            #create category
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.shop = current_shop
            data.a_id = a_id
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Category created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:category',kwargs={'pk':data.pk})
            }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = CategoryForm()
        context = {
            "title" : "Create Category ",
            "form" : form,
            "url" : reverse('products:create_category'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/category_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_category'])
def categories(request):
    current_shop = get_current_shop(request)
    instances = Category.objects.filter(is_deleted=False,shop=current_shop)
    title = "Categories"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Categories - %s" %query

    context = {
        "instances" : instances,
        'title' : title,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/categories.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_category'])
def category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Category.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Category : " + instance.name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/category.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_category'])
def edit_category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Category.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        response_data = {}
        form = CategoryForm(request.POST,instance=instance)

        if form.is_valid():

            #update category
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Category Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:category',kwargs={'pk':data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = CategoryForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Category : " + instance.name,
            "instance" : instance,
            "url" : reverse('products:edit_category',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/category_entry.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_category'])
def delete_category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Category.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Category.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Category Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:categories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_category'])
def delete_selected_categories(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Category.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Category.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Categories Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:categories')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_alternative_unit'])
def create_alternative_unit(request):
    current_shop = get_current_shop(request)
    AlternativeUnitFormset = formset_factory(ProductAlternativeUnitForm,extra=1)
    if request.method == 'POST':
        alternative_formset = AlternativeUnitFormset(request.POST,prefix='alternative_formset')
        if alternative_formset.is_valid():
            for form in alternative_formset:
                try:
                    product = form.cleaned_data['product']
                    unit = form.cleaned_data['unit']
                    cost = form.cleaned_data['cost']
                    price = form.cleaned_data['price']
                    ProductAlternativeUnitPrice(
                        product = product,
                        unit = unit,
                        cost = cost,
                        price = price,
                        shop = current_shop
                    ).save()
                except:
                    pass
           
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Alternative unit created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:alternative_units')
            }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        alternative_formset = AlternativeUnitFormset(prefix='alternative_formset')
        context = {
            "title" : "Create Product Alternative Unit ",
            "alternative_formset" : alternative_formset,
            "url" : reverse('products:create_alternative_unit'),
            "is_redirct" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/alternative_unit_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_alternative_unit'])
def alternative_units(request):
    current_shop = get_current_shop(request)
    instances = ProductAlternativeUnitPrice.objects.filter(is_deleted=False,shop=current_shop)
    title = "Alternative Unit"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Alternative Units - %s" %query

    context = {
        "instances" : instances,
        'title' : title,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/alternative_units.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_alternative_unit'])
def alternative_unit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Alternative Unit",
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/alternative_unit.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_alternative_unit'])
def edit_alternative_unit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        response_data = {}
        form = ProductAlternativeUnitForm(request.POST,instance=instance)

        if form.is_valid():

            #update alternative unit
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Alternative Unit Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:alternative_unit',kwargs={'pk':data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = ProductAlternativeUnitForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Alternative Unit",
            "instance" : instance,
            "url" : reverse('products:edit_alternative_unit',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/alternative_unit_edit.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_alternative_unit'])
def delete_alternative_unit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    ProductAlternativeUnitPrice.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Product Alternative Unit Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:alternative_units')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_alternative_unit'])
def delete_selected_alternative_units(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            ProductAlternativeUnitPrice.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Product Alternative Unit Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:alternative_units')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_measurement'])
def create_measurement(request):
    current_shop = get_current_shop(request)
    MeasurementFormset = formset_factory(MeasurementForm,extra=1)
    if request.method == 'POST':
        #print"post"
        measurement_formset = MeasurementFormset(request.POST,prefix='measurement_formset')
        if measurement_formset.is_valid():
            for form in measurement_formset:
                #print"formset"
                try:
                    code = form.cleaned_data['code']
                    unit_type = form.cleaned_data['unit_type']
                    unit_name = form.cleaned_data['unit_name']
                    conversion_factor = form.cleaned_data['conversion_factor']
                    Measurement(
                        code = code,
                        unit_type = unit_type,
                        unit_name = unit_name,
                        conversion_factor = conversion_factor,
                        shop = current_shop,
                        auto_id=get_auto_id(Measurement),
                        a_id=get_a_id(Measurement,request),
                        creator=request.user,
                        updator=request.user
                    ).save()
                except:
                    pass
           
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Measurement created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:measurements')
            }

        else:
            message = generate_form_errors(measurement_formset,formset=True)
            #printmeasurement_formset.errors
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        measurement_formset = MeasurementFormset(prefix='measurement_formset')
        context = {
            "title" : "Create Measurement ",
            "measurement_formset" : measurement_formset,
            "url" : reverse('products:create_measurement'),
            "is_redirct" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/measurement_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_measurement'])
def measurements(request):
    current_shop = get_current_shop(request)
    instances = Measurement.objects.filter(is_deleted=False,shop=current_shop)
    title = "Measurment"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Measurments - %s" %query

    context = {
        "instances" : instances,
        'title' : title,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/measurements.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_measurement'])
def measurement(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Measurementt : " + instance.name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/measurement.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_measurement'])
def edit_measurement(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        response_data = {}
        form = MeasurementForm(request.POST,instance=instance)

        if form.is_valid():

            #update measurement
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Measurement Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:measurement',kwargs={'pk':data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = MeasurementForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Measurement : " + instance.name,
            "instance" : instance,
            "url" : reverse('products:edit_measurement',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/measurement_entry.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_measurement'])
def delete_measurement(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Measurement.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Measurement Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:measurements')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_measurement'])
def delete_selected_measurements(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Measurement.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Measurement Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:measurements')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_subcategory'])
def create_subcategory(request):
    current_shop = get_current_shop(request)
    instances = SubCategory.objects.filter(is_deleted=False, shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)|Q(category__name=query))

    if request.method == 'POST':
        form = SubCategoryForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(SubCategory)
            a_id = get_a_id(SubCategory,request)

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.creator = request.user
            data.updator = request.user
            data.shop = current_shop
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "SubCategory created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:create_subcategory')
            }
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SubCategoryForm()

        context = {
            "title" : "Create SubCategory",
            "form" : form,
            "redirect" : True,
            "url" : reverse('products:create_subcategory'),
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "products" : True,
            "products" : True,
        }
        return render(request,'products/subcategory_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_subcategory'])
def subcategories(request):
    current_shop = get_current_shop(request)
    instances = SubCategory.objects.filter(is_deleted=False, shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)|Q(category__name=query))

    context = {
        'instances': instances,
        "title" : 'subcategories',
        "is_need_select_picker" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_popup_box" : True,
        "is_need_animations": True,
        "products" : True,
        "products" : True,
        }
    return render(request, "products/subcategories.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_subcategory'])
def edit_subcategory(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(name__icontains=query)|Q(category__name=query))

    if request.method == "POST":
        form = SubCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "SubCategory updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:subcategories')
            }
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SubCategoryForm(instance=instance)

        context = {
            "instance" : instance,
            "title" : "Edit SubCategory :" + instance.name,
            "form" : form,
            "redirect" : True,
            "url" : reverse('products:edit_subcategory', kwargs={'pk':instance.pk}),
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "products" : True,

        }
        return render(request,'products/subcategory_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_subcategory'])
def subcategory(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(name__icontains=query)|Q(category__name=query))

    context = {
        'instance': instance,
        'title':'SubCategory',
        "is_need_select_picker" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_popup_box" : True,
        "products" : True,
    }
    return render(request, "products/subcategory.html", context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_subcategory'])
def delete_subcategory(request,pk):
    current_shop = get_current_shop(request)
    SubCategory.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "SubCategory deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('products:subcategories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_subcategory'])
def delete_selected_subcategories(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
            SubCategory.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Sub Category Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:subcategories')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_brand'])
def create_brand(request):
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = BrandForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(Brand)
            a_id = get_a_id(Brand,request)

            #create brand

            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.shop = current_shop
            data.a_id = a_id
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Brand created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:brand',kwargs={'pk':data.pk})
            }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = BrandForm()
        context = {
            "title" : "Create Brand ",
            "form" : form,
            "url" : reverse('products:create_brand'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/brand_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_brand'])
def brands(request):
    current_shop = get_current_shop(request)
    instances = Brand.objects.filter(is_deleted=False,shop=current_shop)
    title = "Brands"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Brands - %s" %query

    context = {
        "instances" : instances,
        'title' : title,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/brands.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_brand'])
def brand(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Brand.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Brand : " + instance.name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/brand.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_brand'])
def edit_brand(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Brand.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        response_data = {}
        form = BrandForm(request.POST,instance=instance)

        if form.is_valid():

            #update brand
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Brand Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:brand',kwargs={'pk':data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = BrandForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Brand : " + instance.name,
            "instance" : instance,
            "url" : reverse('products:edit_brand',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/brand_entry.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_brand'])
def delete_brand(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Brand.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Brand.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Brand Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:categories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_brand'])
def delete_selected_brands(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Brand.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Brand.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Brands Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:brands')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_batch'])
def create_batch(request):
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = BatchForm(request.POST)

        if form.is_valid():

            #create batch

            data = form.save(commit=False)
            data.shop = current_shop
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Batch created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('products:batch',kwargs={'pk':data.pk})
            }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = BatchForm()
        context = {
            "title" : "Create Batch ",
            "form" : form,
            "url" : reverse('products:create_batch'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/batch_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_batch'])
def batches(request):
    current_shop = get_current_shop(request)
    instances = Batch.objects.filter(is_deleted=False,shop=current_shop)
    title = "Batches"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Batches - %s" %query

    context = {
        "instances" : instances,
        'title' : title,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/batchs.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_batch'])
def batch(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Batch.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Batch : " + instance.name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/batch.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_batch'])
def edit_batch(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Batch.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        response_data = {}
        form = BrandForm(request.POST,instance=instance)

        if form.is_valid():

            #update batch
            data = form.save(commit=False)
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Batch Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:batch',kwargs={'pk':data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = BrandForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Batch : " + instance.name,
            "instance" : instance,
            "url" : reverse('products:edit_batch',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/batch_entry.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_batch'])
def delete_batch(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Batch.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Batch.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Batch Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:categories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_batch'])
def delete_selected_batches(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Batch.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Batch.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Batches Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:batchs')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_unit'])
def create_unit(request):
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = MeasurementForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)

            #create unit
            code = form.cleaned_data['code']
            code = code.upper()
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.shop = current_shop
            data.a_id = a_id
            data.code = code
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Create",
                "message" : "Measurement Successfully Create.",
                "redirect" : "true",
                "redirect_url" : reverse('products:unit',kwargs={'pk':data.pk})
            }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = MeasurementForm(initial={'shop':current_shop})
        context = {
            "title" : "Create Measurement ",
            "form" : form,
            "url" : reverse('products:create_unit'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'products/unit_entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_unit'])
def units(request):
    current_shop = get_current_shop(request)
    instances = Measurement.objects.filter(is_deleted=False,shop=current_shop)
    title = "Units"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Units - %s" %query

    context = {
        "instances" : instances,
        'title' : title,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/units.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_unit'])
def unit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Measurement : " + instance.unit_name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/unit.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_unit'])
def edit_unit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        response_data = {}
        form = MeasurementForm(request.POST,instance=instance)

        if form.is_valid():

            #update unit
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Measurement Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('products:unit',kwargs={'pk':data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = MeasurementForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Measurement : " + instance.unit_name,
            "instance" : instance,
            "url" : reverse('products:edit_unit',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/unit_entry.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_unit'])
def delete_unit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Measurement.objects.filter(pk=pk).update(is_deleted=True,code=instance.code + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Measurement Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('products:units')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_unit'])
def delete_selected_units(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Measurement.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Measurement.objects.filter(pk=pk).update(is_deleted=True,code=instance.code + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Categories Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:units')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@check_mode
@login_required
@shop_required
@permissions_required(['can_manage_barcode'])
def create_barcode(request):
    product = None
    pk = request.GET.get('product')
    if pk:
        product = get_object_or_404(Product.objects.filter(pk=pk))
    current_shop = get_current_shop(request)

    unit = 10
    qty = request.GET.get('qty')
    if qty:
        if qty.isdigit():
            unit = qty

    ProductBarcodeFormset = formset_factory(ProductBarcodeForm,extra=1)
    product_barcode_formset = ProductBarcodeFormset(prefix='product_barcode_formset')
    form = SkipRowForm(initial={"skip_row":0})
    context = {
        'title' : "Create Barcode",
        "product_barcode_formset" : product_barcode_formset, 
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'products/create_barcode.html',context)


@check_mode
@login_required


@check_mode
@login_required
@shop_required
@permissions_required(['can_manage_barcode'])
def print_barcodes(request):
    current_shop = get_current_shop(request)
    checkitem_price = request.GET.getlist('checkitem_price')
    products = request.GET.getlist('barcode')
    units = request.GET.getlist('barcode_unit')
    skip_row = request.GET.get('skip_row')
    barcode_items = {}
    if not skip_row:
        skip_row = 0
    padding_top = 0
    additional_padding = float(skip_row) * 21.2
    padding_top += additional_padding

    items = zip(products,units,checkitem_price)
    for item in items:
        product_pk = item[0]
        try:
            product_instance= Product.objects.get(pk=product_pk,shop=current_shop)
        except:
            product_instance = None

        unit = item[1]

        if not unit:
            unit = 1
        else:
            if unit < 0:
                unit = 0
            else:
                unit = int(unit)
        n_range = range(0,unit)
        hide_value = item[2]
        if hide_value == 'true':
            check_hide = True
        else:
            check_hide = False
        if str(product_instance.pk) in barcode_items:
            u = barcode_items[str(product_instance.pk)]["n_range"]
            barcode_items[str(product_instance.pk)]["n_range"] = u + n_range
        else:
            dic = {
                "n_range" : n_range,
                "product_instance" : product_instance,
                "check_hide" : check_hide
            }
            barcode_items[str(product_instance.pk)] = dic
    skip = 65-(5*int(skip_row))
    context = {
        'title' : "Barcodes : ",
        "barcode_items" : barcode_items,    
        "padding_top" : padding_top,
        "skip" : skip,
        
    }
    return render(request,'products/print_barcodes.html',context)


@login_required
def get_product_sub_categories(request):
    pk = request.GET.get('pk')
    instances = SubCategory.objects.filter(category__pk=pk,is_deleted=False)

    json_models = serializers.serialize("json", instances)
    return HttpResponse(json_models, content_type="application/javascript")


@check_mode
@ajax_required
@login_required
@shop_required
def get_product_units(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('pk')
    if Measurement.objects.filter(shop=current_shop,is_deleted=False,unit_type=pk,is_base=False).exists():
        instances = Measurement.objects.filter(shop=current_shop,unit_type=pk,is_deleted=False,is_base=False)
    else:
        instances = []

    json_models = serializers.serialize("json", instances)
    return HttpResponse(json_models, content_type="application/javascript")


@check_mode
@login_required
def upload_product_list(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = FileForm(request.POST,request.FILES)

        if form.is_valid():
            input_excel = request.FILES['file']
            book = xlrd.open_workbook(file_contents=input_excel.read())
            sheet = book.sheet_by_index(0)

            dict_list = []
            keys = [str(sheet.cell(0, col_index).value) for col_index in xrange(sheet.ncols)]
            for row_index in xrange(1, sheet.nrows):
                d = {keys[col_index]: str(sheet.cell(row_index, col_index).value)
                    for col_index in xrange(sheet.ncols)}
                dict_list.append(d)

            is_ok = True
            message = ''
            row_count = 2

            for item in dict_list:
                code = item['code']
                category = item['category']
                product = item['product']
                stock = Decimal(item['qty'])
                unit = item['unit']
                cost = Decimal(item['cost'])
                price = Decimal(item['price'])
                wholesale_price = Decimal(item['wholesale_price'])
                tax = Decimal(item['tax'])
                vendor = item['vendor']

                if Category.objects.filter(name=category,is_deleted=False,shop=current_shop).exists():
                    category = Category.objects.get(name=category,is_deleted=False,shop=current_shop)
                else:
                    category = Category.objects.create(
                                    name=category,
                                    shop=current_shop,
                                    creator=request.user,
                                    updator=request.user,
                                    auto_id=get_auto_id(Category),
                                    a_id=get_a_id(Category,request)
                                )
                if Vendor.objects.filter(name=vendor,is_deleted=False,shop=current_shop).exists():
                    vendor = Vendor.objects.get(name=vendor,is_deleted=False,shop=current_shop)
                else:
                    vendor = Vendor.objects.create(
                                    name=vendor,
                                    address='address',
                                    phone="9999999999",
                                    shop=current_shop,
                                    creator=request.user,
                                    updator=request.user,
                                    auto_id=get_auto_id(Vendor),
                                    a_id=get_a_id(Vendor,request)
                                )
                tax_category = None
                if TaxCategory.objects.filter(shop=current_shop,is_deleted=False,tax=tax).exists():
                	tax_category = TaxCategory.objects.get(shop=current_shop,is_deleted=False,tax=tax)
                else:
                	tax_category = TaxCategory.objects.create(
                		shop=current_shop,
                		name = str(tax),
                		is_deleted=False,
                		tax=tax,
                        creator=request.user,
                        updator=request.user,
                        auto_id=get_auto_id(TaxCategory),
                        a_id=get_a_id(TaxCategory,request)
                	)
                tax_excluded_price = (100*price)/(100+tax)
                wholesale_tax_excluded_price = (100*wholesale_price)/(100+tax)

                unit_type = "quantity"
                unit_instance = None
                if unit == "each":
                    unit_type = "quantity"
                    unit_instance = Measurement.objects.get(shop=current_shop,is_system_generated=True,code="EA")
                elif unit == "m":
                    unit_type = "distance"
                    unit_instance = Measurement.objects.get(shop=current_shop,is_system_generated=True,code="MT")
                elif unit == "sq":
                    unit_type = "area"
                    if not Measurement.objects.filter(shop=current_shop,is_system_generated=True,code="SQ").exists():
                        auto_id = get_auto_id(Measurement)
                        a_id = get_a_id(Measurement,request)
                        Measurement(code='SQ',unit_type='area',unit_name='square_feet',conversion_factor=0.0,shop=current_shop,creator=request.user,updator=request.user,auto_id=auto_id,a_id=a_id,is_system_generated=True).save()

                    unit_instance = Measurement.objects.get(shop=current_shop,is_system_generated=True,code="SQ")
                    ('area', 'Area'),
                elif unit == "set":
                    unit_type = "quantity"
                    if Measurement.objects.filter(shop=current_shop,code="SET").exists():
                        unit_instance = Measurement.objects.get(shop=current_shop,code="SET")
                    else:
                        auto_id = get_auto_id(Measurement)
                        a_id = get_a_id(Measurement,request)
                        unit_instance = Measurement.objects.create(code='SET',unit_type='quantity',unit_name='set',conversion_factor=2,shop=current_shop,creator=request.user,updator=request.user,auto_id=auto_id,a_id=a_id)
                elif unit == "dz":
                    unit_type = "quantity"
                    unit_instance = Measurement.objects.get(shop=current_shop,code="DZ")
                elif unit == "kg":
                    unit_type = "weight"
                    unit_instance = Measurement.objects.get(shop=current_shop,unit_type='weight',is_system_generated=True,code="KG")

                if not Product.objects.filter(code=code,shop=current_shop,is_deleted=False).exists():
                    instance = Product(
                                   code = code,
                                   name = product,
                                   cost = cost,
                                   price = price,
                                   wholesale_price = wholesale_price,
                                   tax = tax,
                                   discount = 0,
                                   stock = stock,
                                   category = category,
                                   low_stock_limit = 0,
                                   creator = request.user,
                                   updator = request.user,
                                   shop = current_shop,
                                   a_id = get_a_id(Product,request),
                                   auto_id=get_auto_id(Product),
                                   is_tax_included = True,
                                   tax_excluded_price = tax_excluded_price,
                                   tax_category = tax_category,
                                   unit_type = unit_type,
                                   unit = unit_instance,
                                   wholesale_tax_excluded_price = wholesale_tax_excluded_price,
                                   vendor=vendor
                                )
                    instance.save()

            return HttpResponseRedirect(reverse('products:products'))
        else:
            form = FileForm()

            context = {
                "form" : form,
                "title" : "Upload Product List",

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,
            }
            return render(request, 'products/upload_product_list.html', context)
    else:
        form = FileForm()

        context = {
            "form" : form,
            "title" : "Upload Product List",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/upload_product_list.html', context)


@login_required
def export_products(request):
    current_shop = get_current_shop(request)
    instances = Product.objects.filter(is_deleted=False,shop=current_shop)

    import xlwt
    import urllib

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Products')

    ws.write(0, 0, "code")
    ws.write(0, 1, "category")
    ws.write(0, 2, "product")
    ws.write(0, 3, "qty")
    ws.write(0, 4, "unit")
    ws.write(0, 5, "cost")
    ws.write(0, 6, "price")
    ws.write(0, 7, "wholesale_price")
    ws.write(0, 8, "tax")
    ws.write(0, 9, "vendor")
    ws.write(0, 10, "total_cost")
    ws.write(0, 11, "total_price")

    counter = 1
    for instance in instances:
        vendor_name = ""
        if instance.vendor:
            vendor_name = instance.vendor.name

        category_name = ""
        if instance.category:
            category_name = instance.category.name

        unit_name = ""
        if instance.unit:
            unit_name = instance.unit.unit_name

        ws.write(counter, 0, instance.code)
        ws.write(counter, 1, category_name)
        ws.write(counter, 2, instance.name)
        ws.write(counter, 3, instance.stock)
        ws.write(counter, 4, unit_name)
        ws.write(counter, 5, instance.cost)
        ws.write(counter, 6, instance.price)
        ws.write(counter, 7, instance.wholesale_price)
        ws.write(counter, 8, instance.tax)
        ws.write(counter, 9, vendor_name)
        ws.write(counter, 10, instance.total_cost())
        ws.write(counter, 11, instance.total_price())
        counter += 1

    file_location = settings.MEDIA_ROOT + "product_list.xls"
    wb.save(file_location)
    protocol = "http://"
    if request.is_secure():
        protocol = "https://"

    web_host = request.get_host()
    file_url = protocol + web_host + "/media/product_list.xls"
    #printfile_url

    response_data = {
        "status" : "true",
        "file_url" : file_url
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_expiry(request):
    manufacture_date = request.GET.get('manufacture_date')
    period = request.GET.get('period')
    best_before = int(request.GET.get('best_before'))


    if manufacture_date:
        try:
            manufacture_date = datetime.datetime.strptime(manufacture_date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"
    expiry_date = ""
    if period == 'days' :
        expiry_date = manufacture_date +  datetime.timedelta(days=best_before)
    if period == 'month':
        month_days = 30 * best_before
        expiry_date = manufacture_date + datetime.timedelta(days=month_days)
    response_data = {
            "status" : "true",
            "expiry_date" : str(expiry_date)
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_asset'])
def create_asset(request):
    current_shop = get_current_shop(request)
    if request.method == "POST":
        form = AssetForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(Asset)
            a_id = get_a_id(Asset,request)

            #create asset
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Created",
                "redirect" : "true",
                "redirect_url" : reverse('products:assets'),
                "message" : "Asset Successfully Created."
            }
        else:
            message = generate_form_errors(form,formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = AssetForm()
        context = {
            "form" : form,
            "title" : "Create Asset",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_animations": True,
            "is_need_datetime_picker" : True,

        }
        return render(request, 'products/entry_asset.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_asset'])
def edit_asset(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Asset.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == "POST":
        response_data = {}
        form = AssetForm(request.POST,instance=instance)

        if form.is_valid():

            #update asset
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Updated",
                "redirect" : "true",
                "redirect_url" : reverse('products:asset', kwargs = {'pk' :pk}),
                "message" : "Asset Successfully Updated."
            }
        else:
            message = generate_form_errors(form,formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : form.errors
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = AssetForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Asset : " + instance.name,
            "instance" : instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_animations": True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'products/entry_asset.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_asset'])
def assets(request):
    current_shop = get_current_shop(request)
    instances = Asset.objects.filter(is_deleted=False,shop=current_shop)

    title = "Assets"

    #filter by query
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))

    context = {
        'title' : title,
        "instances" : instances,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/assets.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_asset'])
def asset(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Asset.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    context = {
        "instance" : instance,
        "title" : "Asset : " + instance.name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/asset.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_asset'])
def delete_asset(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Asset.objects.filter(pk=pk,shop=current_shop))
    Asset.objects.filter(pk=pk).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Succesfully Deleted",
        "redirect" : "true",
        "redirect_url" : reverse('products:assets'),
        "message" : "Asset Successfully Deleted."
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def delete_selected_assets(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Asset.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Asset.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Asset(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('products:assets')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some asset first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@require_POST
@permissions_required(['can_create_product'])
def create_new_product(request):
    current_shop = get_current_shop(request)

    form = NewProductForm(request.POST)
    form.fields['unit_type'].queryset = Measurement.objects.filter(shop=current_shop,is_base=True,is_deleted=False)
    if form.is_valid():
        auto_id = get_auto_id(Product)
        input_row_counter = request.POST.get('input_row_counter')
        a_id = get_a_id(Product,request)
        error_messages = ''
        unit_type = form.cleaned_data['unit_type']
        base_unit = Measurement.objects.get(shop=current_shop,is_base=True,is_deleted=False,unit_type=unit_type)
        if not error_messages:
            name = form.cleaned_data['name']
            name = name.capitalize()
            price = form.cleaned_data['price']
            wholesale_price = form.cleaned_data['wholesale_price']
            tax_category = form.cleaned_data['tax_category']
            tax_instance = None
            tax = 0

            if tax_category:
                tax_instance = get_object_or_404(TaxCategory.objects.filter(is_deleted=False,pk=tax_category.pk))
                tax = tax_instance.tax

            is_tax_included = form.cleaned_data['is_tax_included']
            is_expired = form.cleaned_data['is_expired']

            if is_tax_included:
                tax_excluded_price = (100*price)/(100+tax)
                wholesale_tax_excluded_price = (100*wholesale_price)/(100+tax)
            else :
                tax_excluded_price = price
                price = tax_excluded_price + (tax_excluded_price*tax)/100

                wholesale_tax_excluded_price = wholesale_price
                wholesale_price = wholesale_tax_excluded_price + (wholesale_tax_excluded_price*tax)/100

            #create product
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.shop = current_shop
            data.name = name
            data.tax_excluded_price = tax_excluded_price
            data.is_tax_included = is_tax_included
            data.wholesale_tax_excluded_price = wholesale_tax_excluded_price
            data.is_expired = is_expired
            data.price = price
            data.a_id = a_id
            data.tax = tax
            data.unit = base_unit
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Product created successfully.",
                "redirect" : "true",
                "data" : {
                    "pk" : str(data.pk),
                    "text" : str(data.code) + " - " + str(data.name),
                    "input_row_counter" : str(input_row_counter)
                }
            }
        else:

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Duplicate Entry",
                "message" : error_messages
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        message = generate_form_errors(form,formset=False)
        #printform.errors
        response_data = {
            "status" : "false",
            "stable" : "true",
            "title" : "Form validation error",
            "message" : form.errors
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_purchase_items(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')
    response_data = {}
    template_name = 'purchases/includes/purchase_invoice_items.html'
    purchase_invoice_items_list = []
    instances = []
    if Product.objects.filter(vendor__pk=pk).exists():
        instances = Product.objects.filter(vendor__pk=pk)
        for instance in instances:
            if instance.stock < instance.product_expiry_before:
                purchase_invoice_items_dict = {
                    'product':instance,
                }
                purchase_invoice_items_list.append(purchase_invoice_items_dict)
    if instances :
        context = {
            'purchase_invoice_items' : purchase_invoice_items_list,
        }
        html_content = render_to_string(template_name,context)
        response_data = {
            "status" : "true",
            'template' : html_content,
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
def create_inventory(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = DisInventoryForm()

    context = {
        'title' : "Create Inventory",
        "form" : form,
        "url": reverse('products:create_inventory_adjustment'),
        "view_url" : reverse('products:inventory_adjustments'),

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'products/create_inventory.html',context)


@check_mode
@login_required
@shop_required
def create_inventory_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = InventoryForm()

    context = {
        'title' : "Create Inventory Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'products/create_inventory_report.html',context)


@check_mode
@login_required
@shop_required
def inventory(request) :
    current_shop = get_current_shop(request)
    products = Product.objects.filter(is_deleted=False,shop=current_shop,stock__gt=0)
    value = request.GET.get('print')
    category = request.GET.get('category')
    subcategory = request.GET.get('subcategory')
    radio = request.GET.get('radio')
    total = 0
    if category :
        products = products.filter(category=category)
    if subcategory :
         products = products.filter(subcategory=subcategory)

    template = 'products/inventory.html'
    if value == 'True' :
        template = 'products/print_inventory.html'
    
    for product in products :
        if radio == 'cost' :
            cost = product.cost
        elif radio == 'price' :
            cost = product.price
        elif radio == 'cash_price' :
            cost = product.cash_price
        elif radio == 'wholesale' :
            cost = product.wholesale_price
            
        sub_total = cost * product.stock
        total += sub_total

    context = {

        "instances" : products,
        'title' : "Inventory",
        "total" : total,
        "radio" : radio,

        "category" : category,
        "subcategory" : subcategory,


        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,template,context)


@login_required
@permissions_required(['can_create_inventory'])
def create_inventory_adjustment(request):
    current_shop = get_current_shop(request)
    distributor = request.GET.get('distributor')
    
    InventoryAdjustmentFormset = formset_factory(InventoryAdjustmentForm,extra=1)

    if request.method == 'POST':
        auto_id = get_auto_id(InventoryAdjustment)
        a_id = get_a_id(InventoryAdjustment,request)
        distributor_instance = None
        if distributor:
            distributor_instance = Distributor.objects.get(pk=distributor)
        data = InventoryAdjustment.objects.create(creator=request.user,updator=request.user,auto_id=auto_id,a_id=a_id,shop=current_shop,distributor=distributor_instance)
        inventory_adjustment_formset = InventoryAdjustmentFormset(request.POST,prefix='inventory_adjustment_formset')
        total_qty = 0
        total_new_qty = 0
        if inventory_adjustment_formset.is_valid():

            for detail in inventory_adjustment_formset:
                product = detail.cleaned_data['product']
                qty = product.stock
                new_qty = detail.cleaned_data['new_qty']
                
                InventoryAdjustmentItem( 
                    inventory_adjustment = data,
                    product = product,
                    qty = qty,
                    new_qty = new_qty,                    
                ).save()

                if distributor :
                    if DistributorStock.objects.filter(product=product,shop=current_shop,distributor=distributor,is_deleted=False).exists():
                        DistributorStock.objects.filter(product=product,shop=current_shop,distributor=distributor,is_deleted=False).update(stock=new_qty)   
                else :
                    Product.objects.filter(pk=product.pk).update(stock=new_qty)

            response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Inventory Adjustment(s) created successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('products:inventory_adjustments')
                }

        else:
            message = generate_form_errors(inventory_adjustment_formset, formset=True)
            #printinventory_adjustment_formset.errors
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }   
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else: 
        initial = []
        if distributor:
            items = DistributorStock.objects.filter(is_deleted=False,distributor=distributor)
            for item in items:
                if item.stock < 0:
                    qty = 0
                else:
                    qty = int(item.stock)
                product_dict = {
                    'product': item.product,
                    'qty' : qty,
                }
                initial.append(product_dict)
            dist = distributor
        else :        
            items = Product.objects.filter(is_deleted=False).order_by('code')
            for item in items:
                if item.stock < 0:
                    qty = 0
                else:
                    qty = int(item.stock)
                product_dict = {
                    'product': item,
                    'qty' : qty,
                }
                initial.append(product_dict)
            dist = ""
        inventory_adjustment_formset = InventoryAdjustmentFormset(prefix='inventory_adjustment_formset',initial=initial)
        
        context = {
            "title": "Create Inventory Adjustment",
            "url": reverse('products:create_inventory_adjustment')+"?distributor="+str(dist),
            "inventory_adjustment_formset" : inventory_adjustment_formset,
            "redirect" : True,
            "distributor" : dist,

            "is_create_page" : True,
            
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "stock_transfers" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "redirect" : True,
            "is_need_animations": True,
            "block_payment_form_media" : True,
            "purchase_page" : True,
        }
        return render(request,'products/entry_inventory_adjustment.html',context)


@login_required
@permissions_required(['can_create_inventory'])
def inventory_adjustments(request):
    instances = InventoryAdjustment.objects.filter(is_deleted=False)
    distributor = request.GET.get('distributor')
    value = request.GET.get('print')
    title = "Inventory Adjustments"
    admin = True
    template = 'products/inventory_adjustments.html'
    if value == 'True' :
        template = 'products/print_inventory_adjustments.html'
    if distributor :
        admin = False
        title = "Distributor Inventory Adjustment"
        instances = instances.filter(distributor__isnull=False)
    else :
        title = "Admin Inventory Adjustment"
        instances = instances.filter(distributor__isnull=True)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(product__name__icontains=query))
        title = "Inventory Adjustments - %s" % query

    context = {
        "instances": instances,
        'title': title,
        'distributor' : distributor,
        "admin" : admin,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "stock_transfers" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "redirect" : True,
        "is_need_animations": True,
        "block_payment_form_media" : True,
    }
    return render(request,template, context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_inventory'])
def inventory_adjustment(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(InventoryAdjustment.objects.filter(pk=pk,shop=current_shop))
    value = request.GET.get('print')
    title = "Inventory Adjustment"
    admin = True
    template = 'products/inventory_adjustment.html'
    if value == 'True' :
        template = 'products/print_inventory_adjustment.html'   
    
    adjustment_items = InventoryAdjustmentItem.objects.filter(inventory_adjustment=instance,is_deleted=False)

    context = {
        "instance" : instance,
        "title" : "Inventory Adjustment : ",
        "adjustment_items" : adjustment_items,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,template,context)


@check_mode
@login_required
@shop_required
def product_stocks(request) :
    current_shop = get_current_shop(request)
    products = Product.objects.filter(is_deleted=False,shop=current_shop)
    value = request.GET.get('print')
    category = request.GET.get('category')
    subcategory = request.GET.get('subcategory')

    if category :
        products = products.filter(category=category)
    if subcategory:
        products = products.filter(subcategory=subcategory)
    template = 'products/product_stock.html'
    if value == 'True' :
        template = 'products/product_stocks.html'
    
    context = {

        "instances" : products,
        'title' : "Product Stocks",

        "category" : category,
        "subcategory" : subcategory,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,template,context) 


@check_mode
@login_required
@shop_required
def distributor_product_stocks(request) :
    current_shop = get_current_shop(request)
    distributor = request.GET.get('distributor')
    if distributor :
        distributor_stocks = DistributorStock.objects.filter(distributor=distributor,shop=current_shop)     
    context = {

        "instances" : distributor_stocks,
        'title' : "Distributor Product Stocks",

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'products/distributor_product_stocks.html',context) 