from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
import json
from web.models import About,ProductCategory,Offer,WebProduct
from web.forms import AboutForm,ProductCategoryForm,OfferForm,WebProductForm
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from main.functions import generate_form_errors, get_auto_id, get_timezone, get_a_id
import datetime
from django.db.models import Q
from users.functions import get_current_shop
from dal import autocomplete


class ProductCategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = ProductCategory.objects.filter(is_deleted=False)

        if self.q:
            items = items.filter(Q(name__istartswith=self.q) 
                                )
    
        return items


class WebProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = WebProduct.objects.filter(is_deleted=False)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | 
                                 Q(product__istartswith=self.q) | 
                                 Q(category__name__istartswith=self.q)
                                )
    
        return items


def dashboard(request):
    return HttpResponseRedirect(reverse('app'))

def index(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    about = None
    if About.objects.filter(is_deleted=False).exists():
        about = About.objects.filter(is_deleted=False).latest('time')
    categories = ProductCategory.objects.filter(is_deleted=False)
    offers = Offer.objects.filter(is_deleted=False)
    products = WebProduct.objects.filter(is_deleted=False)
    context = {
        "title" : "Home",
        "current_shop" : current_shop,
        "about" : about,
        "categories" : categories,
        "offers" : offers,
        "products" : products
    }
    return render(request,"web/index.html",context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_about'])
def create_about(request):

    if request.method == 'POST':
        form = AboutForm(request.POST,request.FILES)

        if form.is_valid():
            data = form.save(commit=False)
            data.save()

            return HttpResponseRedirect(reverse('web:about', kwargs={'pk': data.pk}))

        else:
            message = generate_form_errors(form,formset=False)
            form =AboutForm
            context = {
                "title" : "Create About ",
                "form" : form,
                "redirect" : True,

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
            }
            return render(request,'web/entry_about.html',context)
    else:
        form =AboutForm
        context = {
            "title" : "Create About ",
            "form" : form,
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
        }
        return render(request,'web/entry_about.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_about'])
def abouts(request):
    instances = About.objects.filter(is_deleted=False)
    query = ""
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))
    context = {
        'instances': instances,
        "title" : 'About',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        }
    return render(request, "web/abouts.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_about'])
def about(request, pk):
    instance = About.objects.get(pk=pk)
    context = {
        'instance': instance,
        'title':'book',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
    }
    return render(request, "web/about.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_about'])
def edit_about(request, pk):
    instance = About.objects.get(pk=pk)
    if request.method == "POST":
        form = AboutForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            data = form.save(commit=False)
            data.save()

            return HttpResponseRedirect(reverse('web:about', kwargs={'pk': data.pk}))

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
        form = AboutForm(instance=instance)
        context = {
            "instance" : instance,
            "title" : "edit about :" + instance.address,
            "form" : form,
            "url" : reverse('web:edit_about',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
        }
        return render(request,'web/entry_about.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_about'])
def delete_about(request, pk):
    About.objects.filter(pk=pk).update(is_deleted=True)
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "About deleted successfully.",
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_about'])
def delete_selected_abouts(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(About.objects.filter(pk=pk,is_deleted=False)) 
            About.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected About(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('web:about')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some abouts first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_product_category'])
def create_category(request):
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        
        if form.is_valid(): 
            
            #create category
            data = form.save(commit=False)
            data.save()    
            
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Category created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('web:category',kwargs={'pk':data.pk})
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
        form = ProductCategoryForm()
        context = {
            "title" : "Create Category ",
            "form" : form,
            "url" : reverse('web:create_category'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'web/category_entry.html',context)


@check_mode
@login_required 
@shop_required
@permissions_required(['can_view_product_category'])
def categories(request):
    current_shop = get_current_shop(request)
    instances = ProductCategory.objects.filter(is_deleted=False)
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
    return render(request,'web/categories.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_product_category'])
def category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductCategory.objects.filter(pk=pk,is_deleted=False))
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
    return render(request,'web/category.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_product_category'])
def edit_category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductCategory.objects.filter(pk=pk,is_deleted=False)) 
    
    if request.method == 'POST':
        response_data = {}
        form = ProductCategoryForm(request.POST,instance=instance)
        
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
                "redirect_url" : reverse('web:category',kwargs={'pk':data.pk})
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

        form = ProductCategoryForm(instance=instance)
        
        context = {
            "form" : form,
            "title" : "Edit Category : " + instance.name,
            "instance" : instance,
            "url" : reverse('web:edit_category',kwargs={'pk':instance.pk}),
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
        return render(request, 'web/category_entry.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_product_category'])
def delete_category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductCategory.objects.filter(pk=pk,is_deleted=False))
    
    ProductCategory.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Category Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('web:categories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_product_category'])
def delete_selected_categories(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(ProductCategory.objects.filter(pk=pk,is_deleted=False))
            ProductCategory.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Categories Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('web:categories')
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
@permissions_required(['can_create_offer'])
def create_offer(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = OfferForm(request.POST)
        
        if form.is_valid(): 
            product = form.cleaned_data['product']
            offer_percentage = form.cleaned_data['offer_percentage']
            auto_id = get_auto_id(Offer)
            a_id = get_a_id(Offer,request)
            actual_price = product.price
            offer_price = actual_price - (actual_price * offer_percentage/100)
            #create offer
            data = form.save(commit=False)
            data.actual_price = actual_price
            data.offer_price = offer_price
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.save()    
            
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Offer created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('web:offer',kwargs={'pk':data.pk})
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
        form = OfferForm()
        context = {
            "title" : "Create Offer ",
            "form" : form,
            "url" : reverse('web:create_offer'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
    
        return render(request,'web/entry_offer.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_offer'])
def edit_offer(request,pk):
    instance = get_object_or_404(Offer.objects.filter(pk=pk,is_deleted=False)) 
    if request.method == 'POST':
            
        response_data = {}
        form = OfferForm(request.POST,instance=instance)
        
        if form.is_valid():  
            
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()    
            
            return HttpResponseRedirect(reverse("web:offer",kwargs={"pk":pk}))   
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

        form = OfferForm(instance=instance)
        
        context = {
            "form" : form,
            "title" : "Edit offer: " + instance.product.product + ' - ' + str(instance.offer_percentage),
            "instance" : instance,
            "url" : reverse('web:edit_offer',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_popup_box": True,
            "is_need_grid_system": True,
            "is_need_animations": True,
            "is_need_datetime_picker": True,
            "is_need_checkbox": True,
            "is_need_select_picker" : True,
        }
        return render(request, 'web/entry_offer.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_offer'])
def offers(request):
    instances = Offer.objects.filter(is_deleted=False)
    title = "Offer"

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))
        title = "Offer - %s" % query

    context = {
        "instances": instances,
        'title': title,

        "is_need_popup_box": True,
        "is_need_grid_system": True,
        "is_need_animations": True,
        "is_need_datetime_picker": True,
        "is_need_checkbox": True
    }
    return render(request, 'web/offers.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_offer'])
def offer(request, pk):
    instance = get_object_or_404(Offer.objects.filter(is_deleted=False,pk=pk))
    title = "Offfer"

    context = {
        "instance": instance,
        'title': title,

        "is_need_popup_box": True,
        "is_need_grid_system": True,
        "is_need_animations": True,
        "is_need_datetime_picker": True,
        "is_need_checkbox": True
    }
    return render(request, 'web/offer.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_offer'])
def delete_offer(request,pk):
    instance = get_object_or_404(Offer.objects.filter(pk=pk,is_deleted=False))
    
    Offer.objects.filter(pk=pk).update(is_deleted=True)
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Offer Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('web:offers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_offer'])
def delete_selected_offers(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(Offer.objects.filter(pk=pk,is_deleted=False)) 
            Offer.objects.filter(pk=pk).update(is_deleted=True)
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Offer(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('web:offers')
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
@permissions_required(['can_create_web_product'])
def create_product(request):    
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = WebProductForm(request.POST,request.FILES)
        
        if form.is_valid(): 
            
            auto_id = get_auto_id(WebProduct)
            a_id = get_a_id(WebProduct,request)
            
            #create product
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.save()    
            
            return HttpResponseRedirect(reverse('web:product', kwargs={'pk': data.pk}))
        else:            
            message = generate_form_errors(form,formset=False)     
                    
            form = WebProductForm()
            context = {
                "title" : "Create Product ",
                "form" : form,
                "url" : reverse('web:create_product'),

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,
            }
            return render(request,'web/entry_product.html',context)
    
    else:
        form = WebProductForm()
        context = {
            "title" : "Create Product ",
            "form" : form,
            "url" : reverse('web:create_product'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'web/entry_product.html',context)


@check_mode
@login_required
@shop_required 
@permissions_required(['can_view_web_product'])
def products(request):
    current_shop = get_current_shop(request)
    instances = WebProduct.objects.filter(is_deleted=False)
    title = "Products"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Products - %s" %query
        
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
    return render(request,'web/products.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_web_product'])
def product(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(WebProduct.objects.filter(pk=pk,is_deleted=False))
    context = {
        "instance" : instance,
        "title" : "Product : " + instance.product,
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
    return render(request,'web/product.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_web_product'])
def edit_product(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(WebProduct.objects.filter(pk=pk,is_deleted=False)) 
    
    if request.method == 'POST':
        response_data = {}
        form = WebProductForm(request.POST,instance=instance)
        
        if form.is_valid():      
                   
            #update category
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()            
            
            return HttpResponseRedirect(reverse('web:product', kwargs={'pk': data.pk}))
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

        form = WebProductForm(instance=instance)
        
        context = {
            "form" : form,
            "title" : "Edit Category : " + instance.name,
            "instance" : instance,
            "url" : reverse('web:edit_product',kwargs={'pk':instance.pk}),
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
        return render(request, 'web/entry_product.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_web_product'])
def delete_product(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(WebProduct.objects.filter(pk=pk,is_deleted=False))
    
    WebProduct.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Product Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('web:products')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_web_product'])
def delete_selected_products(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(WebProduct.objects.filter(pk=pk,is_deleted=False))
            WebProduct.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Productss Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('web:products')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_products(request):
    instances = WebProduct.objects.filter(is_deleted=False)
    pk = request.GET.get("category")
    if pk :
        category = ProductCategory.objects.get(pk=pk)
        instances = instances.filter(category=category)
    
    results = [as_json(request,ob) for ob in instances]
    return HttpResponse(json.dumps(results), content_type="application/json")
