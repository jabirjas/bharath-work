from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from distributors.models import Distributor, DistributorStock, StockTransfer, StockTransferItem, DistributorStockTransferItem, DistributorStockTransfer
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from distributors.forms import DistributorForm, StockTransferItemForm, StockTransferForm, DistributorStockTransferItemForm, DistributorStockTransferForm
from main.functions import generate_form_errors, get_auto_id, get_a_id, get_current_role
import datetime
from django.db.models import Q, Sum
from dal import autocomplete
from sales.models import Sale
from distributors.functions import update_distributor_credit_debit,\
    get_distributor_credit, get_distributor_debit, distributor_stock_update
from users.functions import get_current_shop
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from products.models import Product,Measurement, ProductExpiryDate
from django.forms.widgets import TextInput,Select
from products.functions import get_exact_qty, update_sock
from users.forms import UserForm
from django.contrib.auth.models import User, Group
from main.models import Shop,ShopAccess
from finance.models import CashAccount


class DistributorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)

        items = Distributor.objects.filter(is_deleted=False,shop=current_shop)

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
    return HttpResponseRedirect(reverse('distributors:distributors'))


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_distributor'])
def create(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = DistributorForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(Distributor)
            a_id = get_a_id(Distributor,request)

            #create distributor

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
            update_distributor_credit_debit(data.pk,"credit",first_time_credit)
            update_distributor_credit_debit(data.pk,"debit",first_time_debit)

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Distributor created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('distributors:create_user',kwargs={'pk':data.pk})
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
        form = DistributorForm(initial={'shop':current_shop})
        context = {
            "title" : "Create Distributor ",
            "form" : form,
            "url" : reverse('distributors:create'),
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
        return render(request,'distributors/entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_distributor'])
def distributors(request):
    current_shop = get_current_shop(request)
    instances = Distributor.objects.filter(is_deleted=False,is_system_generated=False,shop=current_shop)
    title = "Distributors"

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query) | Q(address__icontains=query))
        title = "Distributors - %s" %query

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
    return render(request,'distributors/distributors.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_distributor'])
def distributor(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Distributor.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Distributor : " + instance.name,
        "single_page" : True,
        "sales" : Sale.objects.filter(distributor=instance,is_deleted=False,shop=current_shop),

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "stock_transfers" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'distributors/distributor.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_distributor'])
def edit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Distributor.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    old_first_time_credit = instance.first_time_credit
    if request.method == 'POST':

        response_data = {}
        form = DistributorForm(request.POST,instance=instance)

        if form.is_valid():

            distributor = Distributor.objects.get(pk=pk)
            previous_first_time_credit = distributor.first_time_credit
            previous_first_time_debit = distributor.first_time_debit

            #update distributor
            first_time_credit = form.cleaned_data['first_time_credit']
            first_time_debit = form.cleaned_data['first_time_debit']

            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            #restore previos credit debit
            update_distributor_credit_debit(pk,"debit",previous_first_time_credit)
            update_distributor_credit_debit(pk,"credit",previous_first_time_debit)

            #update credit debit
            update_distributor_credit_debit(pk,"credit",first_time_credit)
            update_distributor_credit_debit(pk,"debit",first_time_debit)

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Distributor Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('distributors:distributor',kwargs={'pk':data.pk})
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

        form = DistributorForm(instance=instance,initial={'shop':current_shop})

        context = {
            "form" : form,
            "title" : "Edit Distributor : " + instance.name,
            "instance" : instance,
            "url" : reverse('distributors:edit',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "stock_transfers" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'distributors/entry.html', context)

@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_distributor'])
def delete(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Distributor.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    Distributor.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Distributor Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('distributors:distributors')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_distributor'])
def delete_selected_distributors(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Distributor.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            Distributor.objects.filter(pk=pk).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Distributor(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('distributors:distributors')
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
    instance = Distributor.objects.get(pk=pk,is_deleted=False)
    if instance:
        if instance.is_system_generated == True:
            response_data = {
                "status" : "true",
                'credit' : float(0.00),
                'debit' : float(0.00),
            }
        else:
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


@check_mode
@ajax_required
@login_required
@shop_required
def get_distributor(request):
    pk = request.GET.get('id')
    current_shop = get_current_shop(request)
    instance = Distributor.objects.get(pk=pk,is_deleted=False)
    if instance:
        response_data = {
            "status" : "true",
            'name' : str(instance.name),
            'address' : str(instance.address),
            'phone' : str(instance.phone),
            'email' : str(instance.email),
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Credit Error"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
def distributor_stocks(request):
    current_shop = get_current_shop(request)
    instances = DistributorStock.objects.filter(is_deleted=False,shop=current_shop)
    title = "Distributor stocks"
    current_role = get_current_role(request)
    if current_role == "distributor":
        instances =instances.filter(distributor__user=request.user)

    distributor = request.GET.get('distributor')
    if distributor:
        instances = instances.filter(distributor__id=distributor)

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(product__name__icontains=query) | Q(stock__icontains=query) | Q(distributor__name__icontains=query))
        title = "Distributor stocks - %s" %query

    total_mrp = 0
    total_cost = 0
    total_price = 0
    total_stock = 0
    total_stock = instances.aggregate(stock=Sum('stock')).get('stock',0)
    for instance in instances:
        total_cost += instance.total_cost()
        total_mrp += instance.total_mrp()
        total_price += instance.total_amount()

    total_profit = total_price - total_cost

    context = {
        "instances" : instances,
        'title' : title,

        "total_profit" : total_profit,
        "total_mrp" : total_mrp,
        "total_price" : total_price,
        "total_stock" : total_stock,
        "total_cost" : total_cost,

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
    return render(request,'distributors/distributor_stocks.html',context)


@check_mode
@login_required
@shop_required
def distributor_stock(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(DistributorStock.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Distributor Stock: " + instance.product.name,
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "stock_transfers" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'distributors/distributor_stock.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_stock_transfer'])
def create_stock_transfer(request):
    StockTransferItemFormset = formset_factory(StockTransferItemForm, extra=1)
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        stock_transfer_item_formset = StockTransferItemFormset(request.POST,prefix='stock_transfer_item_formset')

        for item in stock_transfer_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)

        if form.is_valid() and stock_transfer_item_formset.is_valid() :
            is_ok = True
            message = ""
            distributor = form.cleaned_data['distributor']
            for item in stock_transfer_item_formset:
                product = item.cleaned_data['product']
                qty = item.cleaned_data['qty']
                unit = item.cleaned_data['unit']
                exact_qty = get_exact_qty(qty,unit)

                stock = product.stock
                if exact_qty > stock:
                    is_ok = False
                    message += "%s has only %s in stock, " %(product.name,str(stock))

            if is_ok:

                auto_id = get_auto_id(StockTransfer)
                a_id = get_a_id(StockTransfer,request)
                date = form.cleaned_data['time']
                data = form.save(commit=False)
                data.auto_id = auto_id
                data.a_id = a_id
                data.shop = current_shop
                data.creator = request.user
                data.updator = request.user
                data.save()

                total = 0

                for f in stock_transfer_item_formset:
                    product = f.cleaned_data['product']
                    qty = f.cleaned_data['qty']
                    unit = f.cleaned_data['unit']
                    price = product.price
                    exact_qty = get_exact_qty(qty,unit)

                    subtotal = qty * price
                    total += subtotal

                    StockTransferItem(
                        stock_transfer = data,
                        product = product,
                        unit = unit,
                        qty = qty,
                        subtotal = subtotal,
                        price = price
                    ).save()

                    distributor_stock_update(request,distributor.pk,product.pk,exact_qty,"increase")

                    update_sock(product.pk,exact_qty,"decrease")

                data.total = total
                data.save()

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Stock Transfer created successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('distributors:stock_transfer',kwargs={"pk":data.pk})
                }
            else:
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Out of Stock",
                    "message" : message
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
        form = StockTransferForm()
        stock_transfer_item_formset = StockTransferItemFormset(prefix='stock_transfer_item_formset')
        for item in stock_transfer_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,unit_type="quantity",is_deleted=False)
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)

        context = {
            "stock_transfer_item_formset" : stock_transfer_item_formset,
            "title" : "Create stock transfer",
            "form" : form,
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
        return render(request,'distributors/entry_stock_transfer.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_stock_transfer'])
def stock_transfers(request):
    current_shop = get_current_shop(request)
    instances = StockTransfer.objects.filter(is_deleted=False,shop=current_shop).order_by('-date_added')
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    payment = request.GET.get('payment')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    filter_date_period = False

    if from_date and to_date:
        try:
            from_date = datetime.datetime.strptime(from_date, '%m/%d/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%m/%d/%Y').date() + datetime.timedelta(days=1)
        except ValueError:
            date_error = "yes"

        filter_date_period = True

    if period :
        if period =="year":
            instances = instances.filter(time__year=today.year)
        elif period == 'month' :
            instances = instances.filter(time__year=today.year,time__month=today.month)
        elif period == "today" :
            instances = instances.filter(time__year=today.year,time__month=today.month,time__day=today.day)

    elif filter_date_period:
        title = "Report : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, time__range=[from_date, to_date])

    elif date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)

    context = {
        'instances': instances,
        "title" : 'Stock Transfers',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "stock_transfers" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,

        }
    return render(request, "distributors/stock_transfers.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_stock_transfer'])
def edit_stock_transfer(request, pk):
    current_shop = get_current_shop(request)
    instance = StockTransfer.objects.get(pk=pk,is_deleted=False,shop=current_shop)
    if StockTransferItem.objects.filter(stock_transfer=instance).exists():
        extra = 0
    else:
        extra= 1
    StockTransferItemFormset = inlineformset_factory(
        StockTransfer,
        StockTransferItem,
        can_delete = True,
        extra = extra,
        exclude = ['creator','updator','auto_id','is_deleted','a_id','stock_transfer','price','subtotal'],
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
            }
        )

    if request.method == "POST":
        form = StockTransferForm(request.POST, instance=instance)
        stock_transfer_item_formset = StockTransferItemFormset(request.POST,prefix='stock_transfer_item_formset',instance=instance)

        if form.is_valid() and stock_transfer_item_formset.is_valid():
            items = {}
            distributor = form.cleaned_data['distributor']

            for f in stock_transfer_item_formset:
                if f not in stock_transfer_item_formset.deleted_forms:
                    product = f.cleaned_data['product']

                    qty = f.cleaned_data['qty']
                    unit = f.cleaned_data['unit']
                    exact_qty = get_exact_qty(qty,unit)

                    if str(product.pk) in items:
                        q = items[str(product.pk)]["qty"]
                        items[str(product.pk)]["qty"] = q + qty
                    else:
                        dic = {
                            "qty" : qty,
                            "unit" :unit.pk,
                        }
                        items[str(product.pk)] = dic

            #update stock_transfer

            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            previous_stock_transfer_items = StockTransferItem.objects.filter(stock_transfer=instance)
            for p in previous_stock_transfer_items:
                qty = p.qty
                unit = p.unit
                exact_qty = get_exact_qty(qty,unit)
                update_sock(p.product.pk,exact_qty,"increase")
                distributor_stock_update(request,distributor.pk,p.product.pk,exact_qty,"decrease")
            previous_stock_transfer_items.delete()

            total = 0
            #save items
            for key, value in items.iteritems():
                product = Product.objects.get(pk=key)
                qty = value["qty"]
                unit = value["unit"]
                unit = Measurement.objects.get(pk=unit)
                exact_qty = get_exact_qty(qty,unit)
                price = product.price

                subtotal = qty * price
                total += subtotal

                StockTransferItem(
                    stock_transfer = data,
                    product = product,
                    unit = unit,
                    qty = qty,
                    price = price,
                    subtotal = subtotal
                ).save()

                update_sock(product.pk,exact_qty,"decrease")
                distributor_stock_update(request,distributor.pk,product.pk,exact_qty,"increase")

            data.total = total
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Stock transfer updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('distributors:stock_transfer',kwargs={"pk":instance.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = StockTransferForm(instance=instance)
        stock_transfer_item_formset = StockTransferItemFormset(prefix='stock_transfer_item_formset',instance=instance)
        for item in stock_transfer_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop)
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,unit_type="quantity")
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)
        context = {
            "stock_transfer_item_formset" : stock_transfer_item_formset,
            "title" : "Edit stock transfer",
            "form" : form,
            "instance" : instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "stock_transfers" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            'redirect':True,
            "block_payment_form_media" : True,
        }
        return render(request,'distributors/entry_stock_transfer.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_stock_transfer'])
def stock_transfer(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(StockTransfer.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    stock_transfer_items = StockTransferItem.objects.filter(stock_transfer=instance)
    print stock_transfer_items
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(time__icontains=query)|Q(distributor__name__icontains=query))


    context = {
        'instance': instance,
        "stock_transfer_items" : stock_transfer_items,
        'title':'Stock Transfers',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "stock_transfers" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request, "distributors/stock_transfer.html", context)


def delete_stock_transfer_fun(request,instance):

    stock_transfer_items = StockTransferItem.objects.filter(stock_transfer=instance)
    for p in stock_transfer_items:
        qty = p.qty
        unit = p.unit
        exact_qty = get_exact_qty(qty,unit)
        update_sock(p.product.pk,exact_qty,"increase")
        distributor_stock_update(request,instance.distributor.pk,p.product.pk,exact_qty,"decrease")

    instance.is_deleted=True
    instance.save()


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_stock_transfer'])
def delete_stock_transfer(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(StockTransfer.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    delete_stock_transfer_fun(request,instance)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Stock Transfer deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('distributors:stock_transfers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_stock_transfer'])
def delete_selected_stock_transfers(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(StockTransfer.objects.filter(pk=pk,shop=current_shop))
            delete_stock_transfer_fun(request,instance)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Stock Transfer Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('distributors:stock_transfers')
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
@permissions_required(['can_create_user'])
def create_user(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Distributor.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == "POST":
        form = UserForm(request.POST)
        response_data = {}
        message = ""
        data = []
        emails = request.POST.get('email')
        username = request.POST.get('username')
        email = str(emails)
        error = False
        if User.objects.filter(email=email).exists():
            error = True
            message += "This email already exists."

        if instance.user:
            error = True
            message += "Distributor already has User Access."

        if not error:
            if form.is_valid():
                data = form.save(commit=False)
                data.email = email
                data.is_staff = True
                data.save()
                Distributor.objects.filter(pk=pk,is_deleted=False).update(user=data)
                instance = Distributor.objects.get(pk=pk)

                #create shop access
                group = Group.objects.get(name="distributor")
                is_default= True
                if ShopAccess.objects.filter(user=data).exists():
                    is_default = False
                ShopAccess(user=data,shop=current_shop,group=group,is_accepted=True,is_default=is_default).save()

                auto_id=get_auto_id(CashAccount)
                a_id = get_a_id(CashAccount,request)

                CashAccount.objects.create(
                    auto_id=auto_id,
                    a_id=a_id,
                    shop=current_shop,
                    name=instance.name,
                    user=data,
                    creator=request.user,
                    updator=request.user,
                    first_time_balance=0,
                )

                response_data = {
                    'status' : 'true',
                    'title' : "User Created",
                    'redirect' : 'true',
                    'redirect_url' : reverse('distributors:distributor',kwargs={"pk":pk}),
                    'message' : "User Created Successfully"
                }

            else:
                error = True
                message = ''
                message += generate_form_errors(form,formset=False)
                response_data = {
                    'status' : 'false',
                    'stable' : 'true',
                    'title' : "Form validation error",
                    "message" : message
                }

        else:
            response_data = {
                'status' : 'false',
                'title' : "Can't create this user",
                'redirect' : 'true',
                'redirect_url' : reverse('distributors:create_user', kwargs={"pk":pk}),
                'message' : message,
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        username = ""
        if instance.email:
            username = instance.email.split('@')[0]
        form = UserForm(initial={"email":instance.email,"username":username})

        context = {
            "form" : form,
            "title" : "Create User",
            "redirect" : True,

            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_grid_system": True,
            "is_need_datetime_picker" : True

        }
        return render(request, 'distributors/create_user.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_distributor_stock_transfer'])
def create_distributor_stock_transfer(request):
    DistributorStockTransferItemFormset = formset_factory(DistributorStockTransferItemForm, extra=1)
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = DistributorStockTransferForm(request.POST)
        distributor_stock_transfer_item_formset = DistributorStockTransferItemFormset(request.POST,prefix='distributor_stock_transfer_item_formset')

        for item in distributor_stock_transfer_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)

        if form.is_valid() and distributor_stock_transfer_item_formset.is_valid() :

            auto_id = get_auto_id(DistributorStockTransfer)
            a_id = get_a_id(DistributorStockTransfer,request)
            date = form.cleaned_data['time']
            from_distributor = form.cleaned_data['from_distributor']
            to_distributor = form.cleaned_data['to_distributor']
            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.creator = request.user
            data.updator = request.user
            data.save()

            total = 0

            for f in distributor_stock_transfer_item_formset:
                product = f.cleaned_data['product']
                qty = f.cleaned_data['qty']
                unit = f.cleaned_data['unit']
                price = product.price
                exact_qty = get_exact_qty(qty,unit)

                subtotal = qty * price
                total += subtotal

                DistributorStockTransferItem(
                    distributor_stock_transfer = data,
                    product = product,
                    unit = unit,
                    qty = qty,
                    subtotal = subtotal,
                    price = price
                ).save()

                distributor_stock_update(request,from_distributor.pk,product.pk,exact_qty,"decrease")
                distributor_stock_update(request,to_distributor.pk,product.pk,exact_qty,"increase")

            data.total = total
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Distributor Stock Transfer created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('distributors:distributor_stock_transfer',kwargs={"pk":data.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(distributor_stock_transfer_item_formset, formset=True)
            print distributor_stock_transfer_item_formset.errors
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = DistributorStockTransferForm()
        distributor_stock_transfer_item_formset = DistributorStockTransferItemFormset(prefix='distributor_stock_transfer_item_formset')
        for item in distributor_stock_transfer_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,unit_type="quantity",is_deleted=False)
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)

        context = {
            "distributor_stock_transfer_item_formset" : distributor_stock_transfer_item_formset,
            "title" : "Create distributor stock transfer",
            "form" : form,
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "distributor_stock_transfers" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "redirect" : True,
            "is_need_animations": True,
            "block_payment_form_media" : True,
        }
        return render(request,'distributors/entry_distributor_stock_transfer.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_distributor_stock_transfer'])
def distributor_stock_transfers(request):
    current_shop = get_current_shop(request)
    instances = DistributorStockTransfer.objects.filter(is_deleted=False,shop=current_shop)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    payment = request.GET.get('payment')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    filter_date_period = False

    if from_date and to_date:
        try:
            from_date = datetime.datetime.strptime(from_date, '%m/%d/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%m/%d/%Y').date() + datetime.timedelta(days=1)
        except ValueError:
            date_error = "yes"

        filter_date_period = True

    if period :
        if period =="year":
            instances = instances.filter(time__year=today.year)
        elif period == 'month' :
            instances = instances.filter(time__year=today.year,time__month=today.month)
        elif period == "today" :
            instances = instances.filter(time__year=today.year,time__month=today.month,time__day=today.day)

    elif filter_date_period:
        title = "Report : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, time__range=[from_date, to_date])

    elif date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)

    context = {
        'instances': instances,
        "title" : 'Stock Transfers',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "distributor_stock_transfers" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,

        }
    return render(request, "distributors/distributor_stock_transfers.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_distributor_stock_transfer'])
def edit_distributor_stock_transfer(request, pk):
    current_shop = get_current_shop(request)
    instance = DistributorStockTransfer.objects.get(pk=pk,is_deleted=False,shop=current_shop)
    if DistributorStockTransferItem.objects.filter(distributor_stock_transfer=instance).exists():
        extra = 0
    else:
        extra= 1
    DistributorStockTransferItemFormset = inlineformset_factory(
        DistributorStockTransfer,
        DistributorStockTransferItem,
        can_delete = True,
        extra = extra,
        exclude = ['creator','updator','auto_id','is_deleted','a_id','distributor_stock_transfer','price','subtotal'],
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
            }
        )

    if request.method == "POST":
        form = DistributorStockTransferForm(request.POST, instance=instance)
        distributor_stock_transfer_item_formset = DistributorStockTransferItemFormset(request.POST,prefix='distributor_stock_transfer_item_formset',instance=instance)

        if form.is_valid() and distributor_stock_transfer_item_formset.is_valid():
            items = {}
            from_distributor = form.cleaned_data['from_distributor']
            to_distributor = form.cleaned_data['to_distributor']

            for f in distributor_stock_transfer_item_formset:
                if f not in distributor_stock_transfer_item_formset.deleted_forms:
                    product = f.cleaned_data['product']

                    qty = f.cleaned_data['qty']
                    unit = f.cleaned_data['unit']
                    exact_qty = get_exact_qty(qty,unit)

                    if str(product.pk) in items:
                        q = items[str(product.pk)]["qty"]
                        items[str(product.pk)]["qty"] = q + qty
                    else:
                        dic = {
                            "qty" : qty,
                            "unit" :unit.pk,
                        }
                        items[str(product.pk)] = dic

            #update distributor_stock_transfer

            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            previous_distributor_stock_transfer_items = DistributorStockTransferItem.objects.filter(distributor_stock_transfer=instance)
            for p in previous_distributor_stock_transfer_items:
                qty = p.qty
                unit = p.unit
                exact_qty = get_exact_qty(qty,unit)
                distributor_stock_update(request,from_distributor.pk,p.product.pk,exact_qty,"increase")
                distributor_stock_update(request,to_distributor.pk,p.product.pk,exact_qty,"decrease")
            previous_distributor_stock_transfer_items.delete()

            total = 0
            #save items
            for key, value in items.iteritems():
                product = Product.objects.get(pk=key)
                qty = value["qty"]
                unit = value["unit"]
                unit = Measurement.objects.get(pk=unit)
                exact_qty = get_exact_qty(qty,unit)
                price = product.price

                subtotal = qty * price
                total += subtotal

                DistributorStockTransferItem(
                    distributor_stock_transfer = data,
                    product = product,
                    unit = unit,
                    qty = qty,
                    price = price,
                    subtotal = subtotal
                ).save()

                distributor_stock_update(request,from_distributor.pk,p.product.pk,exact_qty,"decrease")
                distributor_stock_update(request,to_distributor.pk,p.product.pk,exact_qty,"increase")

            data.total = total
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Distributor Stock transfer updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('distributors:distributor_stock_transfer',kwargs={"pk":instance.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = DistributorStockTransferForm(instance=instance)
        distributor_stock_transfer_item_formset = DistributorStockTransferItemFormset(prefix='distributor_stock_transfer_item_formset',instance=instance)
        for item in distributor_stock_transfer_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop)
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,unit_type="quantity")
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)
        context = {
            "distributor_stock_transfer_item_formset" : distributor_stock_transfer_item_formset,
            "title" : "Edit distributor stock transfer",
            "form" : form,
            "instance" : instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "distributor_stock_transfers" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            'redirect':True,
            "block_payment_form_media" : True,
        }
        return render(request,'distributors/entry_distributor_stock_transfer.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_distributor_stock_transfer'])
def distributor_stock_transfer(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(DistributorStockTransfer.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    distributor_stock_transfer_items = DistributorStockTransferItem.objects.filter(distributor_stock_transfer=instance)
    print distributor_stock_transfer_items
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(time__icontains=query)|Q(distributor__name__icontains=query))


    context = {
        'instance': instance,
        "distributor_stock_transfer_items" : distributor_stock_transfer_items,
        'title':'Distributor Stock Transfer : %s To %s' %(instance.from_distributor.name,instance.to_distributor.name),
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "distributor_stock_transfers" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request, "distributors/distributor_stock_transfer.html", context)


def delete_distributor_stock_transfer_fun(request,instance):

    distributor_stock_transfer_items = DistributorStockTransferItem.objects.filter(distributor_stock_transfer=instance)
    for p in distributor_stock_transfer_items:
        qty = p.qty
        unit = p.unit
        exact_qty = get_exact_qty(qty,unit)
        distributor_stock_update(request,instance.to_distributor.pk,p.product.pk,exact_qty,"decrease")
        distributor_stock_update(request,instance.from_distributor.pk,p.product.pk,exact_qty,"increase")

    instance.is_deleted=True
    instance.save()


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_distributor_stock_transfer'])
def delete_distributor_stock_transfer(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(DistributorStockTransfer.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    delete_distributor_stock_transfer_fun(request,instance)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Stock Transfer deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('distributors:distributor_stock_transfers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_distributor_stock_transfer'])
def delete_selected_distributor_stock_transfers(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(DistributorStockTransfer.objects.filter(pk=pk,shop=current_shop))
            delete_distributor_stock_transfer_fun(request,instance)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Stock Transfer Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('distributors:distributor_stock_transfers')
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
def print_distributor_stocks(request):
    current_shop = get_current_shop(request)
    instances = DistributorStock.objects.filter(is_deleted=False,shop=current_shop)
    title = "Distributor stocks"
    current_role = get_current_role(request)
    if current_role == "distributor":
        instances =instances.filter(distributor__user=request.user)

    distributor = request.GET.get('distributor')
    if distributor:
        instances = instances.filter(distributor__id=distributor)

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(product__name__icontains=query) | Q(stock__icontains=query) | Q(distributor__name__icontains=query))
        title = "Distributor stocks - %s" %query    

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
    return render(request,'distributors/print_distributor_stocks.html',context)