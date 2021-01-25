from django.shortcuts import render,get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse,HttpResponseRedirect
from vendors.forms import VendorForm
from vendors.models import Vendor
from purchases.models import Purchase
from main.models import Shop
import json
from dal import autocomplete
from django.db.models import Q
import datetime
from django.utils import timezone
from datetime import date, time
from main.functions import get_auto_id, generate_form_errors, get_a_id
from users.functions import get_current_shop
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from vendors.functions import update_vendor_credit_debit


class VendorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        vendor = Vendor.objects.filter(is_deleted=False)

        if self.q:
            vendor = vendor.filter(Q(name__istartswith=self.q)
                                 )

        return vendor


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_vendor'])
def create_vendor(request):
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = VendorForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Vendor)
            a_id = get_a_id(Vendor, request)

            first_time_credit = form.cleaned_data['first_time_credit']
            first_time_debit = form.cleaned_data['first_time_debit']

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.creator = request.user
            data.updator = request.user
            data.shop = current_shop
            data.save()

            update_vendor_credit_debit(data.pk,"credit",first_time_credit)
            update_vendor_credit_debit(data.pk,"debit",first_time_debit)

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Vendor created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('vendors:vendors')
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
        form = VendorForm()

        context = {
            "title" : "Create Vendor",
            "form" : form,
            "redirect" : "true",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
  
        }

        return render(request, 'vendor/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_vendor'])
def vendors(request):
    current_shop = get_current_shop(request)
    instances = Vendor.objects.filter(is_deleted=False, shop=current_shop)
    query = request.GET.get("q")

    if query:
        instances = instances.filter(Q(name__icontains=query)|Q(address__icontains=query)|Q(phone__icontains=query)|Q(email__icontains=query))

    context = {
        'instances': instances,
        "title" : 'Vendors',

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
    return render(request, "vendor/vendors.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_vendor'])
def edit_vendor(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Vendor.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)|Q(address__icontains=query)|Q(phone__icontains=query)|Q(email__icontains=query))


    if request.method == "POST":
        form = VendorForm(request.POST, instance=instance)

        if form.is_valid():

            vendor = Vendor.objects.get(pk=pk)
            previous_first_time_credit = vendor.first_time_credit
            previous_first_time_debit = vendor.first_time_debit  
                   
            #update vendor
            first_time_credit = form.cleaned_data['first_time_credit']
            first_time_debit = form.cleaned_data['first_time_debit']

            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            #restore previos credit debit
            update_vendor_credit_debit(pk,"debit",previous_first_time_credit)            
            update_vendor_credit_debit(pk,"credit",previous_first_time_debit) 
            
            #update credit debit
            update_vendor_credit_debit(pk,"credit",first_time_credit)
            update_vendor_credit_debit(pk,"debit",first_time_debit)

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Vendor updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('vendors:vendors')
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
        form = VendorForm(instance=instance)

        context = {
            "instance" : instance,
            "title" : "Edit Vendor :" + instance.name,
            "form" : form,
            "redirect" : "true",
            "url" : reverse('vendors:edit_vendor', kwargs={'pk':instance.pk}),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_popup_box" : True,
            "is_need_datetime_picker" : True,
      
        }
        return render(request, 'vendor/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_vendor'])
def vendor(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Vendor.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)|Q(address__icontains=query)|Q(phone__icontains=query)|Q(email__icontains=query))


    context = {
        'instance': instance,
        'title':'Vendor',

        "is_need_select_picker" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_popup_box" : True,
        "is_need_datetime_picker" : True,
        "purchases" : Purchase.objects.filter(vendor=instance,is_deleted=False,shop=current_shop),
    
    }
    return render(request, "vendor/vendor.html", context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_vendor'])
def delete_vendor(request, pk):
    current_shop = get_current_shop(request)
    Vendor.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Vendor deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('vendors:vendors')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_vendor'])
def delete_selected_vendors(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Vendor.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
            Vendor.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Vendor Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('vendors:vendors')
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
def get_debit(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')
    instance = Vendor.objects.get(pk=pk,is_deleted=False,shop=current_shop)
    if instance:
        response_data = {
                "status" : "true",
                'credit' : float(instance.credit), 
                'debit' : float(instance.debit), 
            }
    else:
        response_data = {
            "status" : "false",
            "message" : "Credit Error"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')