from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from customers.models import Customer
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from customers.forms import CustomerForm
from main.functions import generate_form_errors, get_auto_id, get_a_id, get_current_role
import datetime
from django.db.models import Q
from dal import autocomplete
from sales.models import Sale,CollectAmount
from customers.functions import update_customer_credit_debit,\
    get_customer_credit, get_customer_debit
from users.functions import get_current_shop
from django.db.models import Sum
from products.models import Product
from decimal import Decimal
from distributors.models import Distributor


class CustomerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Customer.objects.filter(is_deleted=False,shop=current_shop)
        current_role = get_current_role(self.request)
        if current_role == "distributor":
            distributor_user_list = Distributor.objects.filter(is_deleted=False).exclude(user=self.request.user).values('user')
            items = items.filter().exclude(creator__id__in=distributor_user_list)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(name__istartswith=self.q) |
                                 Q(phone__istartswith=self.q) |
                                 Q(email__istartswith=self.q) |
                                 Q(address__istartswith=self.q)
                                )

        return items


@check_mode
@login_required
@shop_required
def dashboard(request):
    return HttpResponseRedirect(reverse('customers:customers'))


@check_mode
@login_required
@shop_required
def create(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = CustomerForm(request.POST,request.FILES)

        if form.is_valid():

            auto_id = get_auto_id(Customer)
            a_id = get_a_id(Customer,request)

            #create customer

            first_time_credit = form.cleaned_data['first_time_credit']
            first_time_debit = form.cleaned_data['first_time_debit']

            data = form.save(commit=False)
            data.a_id = a_id
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.shop = current_shop
            data.save()

            #update credit debit
            update_customer_credit_debit(data.pk,"credit",first_time_credit)
            update_customer_credit_debit(data.pk,"debit",first_time_debit)

            return HttpResponseRedirect(reverse('customers:customer',kwargs={'pk':data.pk}))            

        else:
            form = CustomerForm(initial={'shop':current_shop})
            context = {
                "title" : "Create Customer ",
                "form" : form,
                "url" : reverse('customers:create'),

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,

            }
            return render(request,'customers/entry.html',context)

    else:
        form = CustomerForm(initial={'shop':current_shop})
        context = {
            "title" : "Create Customer ",
            "form" : form,
            "url" : reverse('customers:create'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,

        }
        return render(request,'customers/entry.html',context)


@check_mode
@login_required
@shop_required
def customers(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request)
    purpose = request.GET.get("purpose")
    template = 'customers/customers.html'
    if purpose == 'print' :
        template = 'customers/print_customers.html'
    instances = Customer.objects.filter(is_deleted=False,is_system_generated=False,shop=current_shop)
    title = "Customers"
    credit = request.GET.get('credit')
    debit = request.GET.get('debit')
    if current_role == "distributor":
        instances = instances.filter(creator=request.user)

    total_credit_amount  = instances.aggregate(credit=Sum('credit')).get('credit',0)
    credit_customer_count = instances.filter(credit__gt=0).count()
    total_debit_amount  = instances.aggregate(debit=Sum('debit')).get('debit',0)
    debit_customer_count = instances.filter(debit__gt=0).count()

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query) | Q(address__icontains=query))
        title = "Customers - %s" %query

    if credit == 'credit':
        instances = instances.filter(credit__gt=0)
        total_credit_amount  = instances.aggregate(credit=Sum('credit')).get('credit',0)
        credit_customer_count = instances.count()
        total_debit_amount = 0
        debit_customer_count = 0

    if debit == 'debit':
        instances = instances.filter(debit__gt=0)
        total_debit_amount  = instances.aggregate(debit=Sum('debit')).get('debit',0)
        debit_customer_count = instances.count()
        total_credit_amount = 0
        credit_customer_count = 0

    context = {
        "instances" : instances,
        'title' : title,
        "total_credit_amount" : total_credit_amount,
        "total_debit_amount" : total_debit_amount,
        "credit_customer_count" : credit_customer_count,
        "debit_customer_count" : debit_customer_count,

        "filter_credit" : credit,
        "filter_debit" : debit,

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
def customer(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Customer.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    collected_amounts = CollectAmount.objects.filter(customer=instance,is_deleted=False,shop=current_shop) 
    context = {
        "instance" : instance,
        "title" : "Customer : " + instance.name,
        "single_page" : True,
        "sales" : Sale.objects.filter(customer=instance,is_deleted=False,shop=current_shop),
        "collected_amounts" : collected_amounts,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "purchases" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'customers/customer.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_customer'],allow_self=True,model=Customer)
def edit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Customer.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    old_first_time_credit = instance.first_time_credit
    if request.method == 'POST':

        response_data = {}
        form = CustomerForm(request.POST,instance=instance)

        if form.is_valid():

            customer = Customer.objects.get(pk=pk)
            previous_first_time_credit = customer.first_time_credit
            previous_first_time_debit = customer.first_time_debit

            #update customer
            first_time_credit = form.cleaned_data['first_time_credit']
            first_time_debit = form.cleaned_data['first_time_debit']

            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            #restore previos credit debit
            update_customer_credit_debit(pk,"debit",previous_first_time_credit)
            update_customer_credit_debit(pk,"credit",previous_first_time_debit)

            #update credit debit
            update_customer_credit_debit(pk,"credit",first_time_credit)
            update_customer_credit_debit(pk,"debit",first_time_debit)

            return HttpResponseRedirect(reverse('customers:customer',kwargs={'pk':data.pk}))  
        else:
            form = CustomerForm(instance=instance,initial={'shop':current_shop})

            context = {
                "form" : form,
                "title" : "Edit Customer : " + instance.name,
                "instance" : instance,
                "url" : reverse('customers:edit',kwargs={'pk':instance.pk}),
                "redirect" : True,

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "purchases" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,
            }
            return render(request, 'customers/entry.html', context)

    else:

        form = CustomerForm(instance=instance,initial={'shop':current_shop})

        context = {
            "form" : form,
            "title" : "Edit Customer : " + instance.name,
            "instance" : instance,
            "url" : reverse('customers:edit',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'customers/entry.html', context)

@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_customer'],allow_self=True,model=Customer)
def delete(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Customer.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Customer.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Customer Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('customers:customers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_customer'],allow_self=True,model=Customer)
def delete_selected_customers(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Customer.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Customer.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Customer(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('customers:customers')
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
def get_credit(request):
    pk = request.GET.get('id')
    current_shop = get_current_shop(request)
    instance = Customer.objects.get(pk=pk,is_deleted=False)
    if instance:
        if instance.is_system_generated == True:
            response_data = {
                "status" : "true",
                'credit' : float(0.00),
                'debit' : float(0.00),
                'return_amount' : float(0.00),
            }
        else:
            response_data = {
                "status" : "true",
                'credit' : float(instance.credit),
                'debit' : float(instance.debit),
                'return_amount' : float(instance.return_amount),
            }
    else:
        response_data = {
            "status" : "false",
            "message" : "Credit Error"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_customer_discount(request):
    current_shop = get_current_shop(request)
    customer_pk = request.GET.get('id')
    product = request.GET.get('product')
    sale_type = request.GET.get('sale_type')
    new_discount = request.GET.get('new_discount')
    product_exists = False
    batches = []
    is_mrp = "false"
    if Product.objects.filter(pk=product,shop=current_shop).exists():
        item = Product.objects.get(pk=product)
        product_exists = True

    if product_exists:
        if customer_pk:
            if Customer.objects.filter(shop=current_shop,pk=customer_pk).exists():
                customer = Customer.objects.get(shop=current_shop,pk=customer_pk)
                customer_discount = customer.discount
                if customer_discount >  0 :
                    discount = customer_discount
                    mrp = item.mrp
                    discount_amount = (mrp * discount)/100
                    price = mrp
                    is_mrp = "true"
                    
        elif Decimal(new_discount) > 0 :
            discount = Decimal(new_discount)
            mrp = item.mrp
            discount_amount = (mrp * discount)/100
            price = mrp  
            is_mrp = "true" 
        else :
            tax_excluded_price = item.tax_excluded_price
            if sale_type ==  "retail" :
                tax_excluded_price = item.tax_excluded_price
            elif sale_type == "wholesale":
                tax_excluded_price = item.wholesale_tax_excluded_price

            discount_amount = item.discount
            price = tax_excluded_price
            discount = 0
            if price > 0 : 
                discount = round((discount_amount*100)/price)  

        response_data = {
            "status" : "true",
            'price' : str(price),
            'discount' : str(discount),
            'discount_amount' : str(discount_amount),
            'is_mrp' : is_mrp,
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
@ajax_required
def check_sale_restriction(request):
    current_shop = get_current_shop(request)
    customer = request.GET.get('customer')
    balance = request.GET.get('balance')
    credit_limit = current_shop.credit_limit
    if customer :
        if Customer.objects.filter(pk=customer,is_deleted=False,credit_limit__gt=0) :
            instance = Customer.objects.get(pk=customer,is_deleted=False,credit_limit__gt=0)
            credit_limit = instance.credit_limit
        if credit_limit > 0:
            if float(balance) > float(credit_limit) :
                response_data = {
                    "status" : "false",
                }
            else :       
                response_data = {
                    "status" : "true",
                }
        else:       
            response_data = {
                "status" : "true",
            }
    else:
        response_data = {
            "status" : "false",
            "message" : "Customer Id Not found"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
