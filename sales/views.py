from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from sales.models import Sale, SaleItem,CollectAmount,SaleReturn,SaleReturnItem,DamagedProduct,ReturnableProduct,\
    ProductReturn,ProductReturnItem,CustomerPayment,Estimate,EstimateItem,PurchaseRequest,PurchaseRequestItem, DamagedProduct,VendorReturn,VendorReturnItem,VendorProduct,PaymentHistory
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required, role_required, check_salesman
from sales.forms import SaleForm, SaleItemForm, EmailSaleForm,CollectAmountForm,SaleReturnForm,SaleReturnItemForm,PurchaseRequestForm,PurchaseRequestItemForm,\
    ReturnableProductForm,ProductReturnForm,ProductReturnItemForm,CustomerPaymentForm,EstimateForm,EstimateItemForm, DamagedProductForm,VendorReturnForm,VendorReturnItemForm
from main.functions import generate_form_errors, get_auto_id, get_timezone, get_a_id, get_current_role
from finance.functions import add_transaction
from finance.forms import BankAccountForm, CashAccountForm, TransactionCategoryForm, TransactionForm
from finance.models import BankAccount, CashAccount, TransactionCategory, Transaction, TaxCategory,Journel
from purchases.models import Purchase,PurchaseItem
import datetime
from django.db.models import Q
from dal import autocomplete
from django.forms.models import inlineformset_factory
from django.forms.widgets import TextInput,Select
from django.forms.formsets import formset_factory
from products.functions import update_sock,get_exact_qty
from customers.functions import update_customer_credit_debit, update_customer_return_amount
from vendors.functions import update_vendor_credit_debit
from products.models import Product,Category,Measurement,ProductAlternativeUnitPrice,ProductBatch,ProductBatchHistory
from main.functions import render_to_pdf
from django.utils import timezone
import pytz
from users.functions import get_current_shop, send_email,create_notification,get_activity_description
from vendors.functions import update_vendor_credit_debit
from django.template.loader import render_to_string
from users.models import NotificationSubject, Notification,UserActivity
from customers.models import Customer
from purchases.models import Purchase
from decimal import Decimal
from django.db.models import Sum
import xlwt
import urllib
from django.conf import settings
from django.core import serializers
import inflect
from distributors.models import DistributorStock, Distributor
from distributors.functions import distributor_stock_update
import math


class SaleAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Sale.objects.filter(is_deleted=False,shop=current_shop,creator=self.request.user)

        if self.q:
            items = items.filter(Q(a_id__istartswith=self.q) |
                                 Q(customer__name__istartswith=self.q) |
                                 Q(customer__address__istartswith=self.q) |
                                 Q(customer__email__istartswith=self.q) |
                                 Q(customer__phone__istartswith=self.q)
                                )

        return items


class ReturnableProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = ReturnableProduct.objects.filter(is_deleted=False,shop=current_shop)

        if self.q:
            items = items.filter(Q(a_id__istartswith=self.q) |
                                 Q(product__name__istartswith=self.q) |
                                 Q(product__code__istartswith=self.q)
                                )
        return items


@check_mode
@login_required
@shop_required
def dashboard(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False)
    sale_items = SaleItem.objects.filter(sale__shop=current_shop,sale__is_deleted=False)
    sale_return_instances = SaleReturn.objects.filter(is_deleted=False,sale__shop=current_shop)
    sales_count = 0
    sales_total = 0
    final_discount_amount = 0
    payment_received_total = 0
    balance_total = 0
    total_tax_amount_total = 0
    profit_amount = 0
    special_discount_all = 0
    total_special_discount = 0
    total_discount = 0
    sale_return_amount = 0
    final_profit_amount = 0
    sale_return_returnable_amount = 0
    sale_return_commission_deducted = 0
    title = "Sales Dashboard"
    tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
    counter = 0
    tax_percentage_dict = {}
    filter_date = date

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

    #filter by date created range
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_from_date = from_date
    filter_to_date = to_date

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
            sale_return_instances = sale_return_instances.filter(time__year=today.year)
        elif period == 'month' :
            instances = instances.filter(time__year=today.year,time__month=today.month)
            sale_return_instances = sale_return_instances.filter(time__year=today.year,time__month=today.month)
        elif period == "today" :
            instances = instances.filter(time__year=today.year,time__month=today.month,time__day=today.day)
            sale_return_instances =sale_return_instances.filter(time__year=today.year,time__month=today.month,time__day=today.day)

    elif filter_date_period:
        title = "Report : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, time__range=[from_date, to_date])
            sale_return_instances = sale_return_instances.filter(is_deleted=False, time__range=[from_date, to_date])

    elif date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)
            sale_return_instances = sale_return_instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)

    if instances:
        sale_items = sale_items.filter(sale__in=instances)
        sales_dict = instances.aggregate(Sum('total'),Sum('special_discount'),Sum('payment_received'),Sum('balance'),Sum('total_discount_amount'),Sum('total_tax_amount'))
        sale_return_dict = sale_return_instances.aggregate(Sum('commission_deducted'),Sum('returnable_amount'))

        sales_total  = sales_dict['total__sum']
        balance_total = sales_dict['balance__sum']
        total_tax_amount_total = sales_dict['total_tax_amount__sum']
        sales_count = instances.count()

        if sale_items:
            for item in sale_items:
                cost = item.cost
                price = item.price
                quantity = item.qty
                tax_amount = item.tax_amount
                profit = (quantity * (price - cost))- tax_amount
                profit_amount += profit
        for tax in tax_categories:
            items = sale_items.filter(product__tax_category=tax)

            tax_amount = 0
            if items :
                tax_amount = items.aggregate(tax_amount=Sum('tax_amount')).get("tax_amount",0)
            tax_percentage_dict[str(tax.tax)] = tax_amount
            counter += 1

        final_discount_amount = sales_dict['special_discount__sum'] + sales_dict['total_discount_amount__sum']
        total_special_discount = sales_dict['special_discount__sum']
        total_discount = sales_dict['total_discount_amount__sum']

        payment_received_total = sales_dict['payment_received__sum']

        final_profit_amount = profit_amount - total_special_discount - total_discount

        sale_return_commission_deducted = sale_return_dict['commission_deducted__sum']
        sale_return_returnable_amount = sale_return_dict['returnable_amount__sum']

    context = {
        'title' : title,
        "sales_count" : sales_count,
        "sales_total" : sales_total,
        "special_discount_total" : total_special_discount,
        "payment_received_total" : payment_received_total,
        "balance_total" : balance_total,
        "total_tax_amount_total" : total_tax_amount_total,
        "tax_percentage_dict" : tax_percentage_dict,
        "total_discount" : total_discount,
        "filter_from_date" : filter_from_date,
        "period" : period,
        "filter_to_date" : filter_to_date,
        "filter_date" : filter_date,
        "year" : year,
        "month" : month,
        "profit_amount" : round(final_profit_amount,2),
        "sale_return_returnable_amount" : sale_return_returnable_amount,
        "sale_return_commission_deducted" : sale_return_commission_deducted,
        "instances" : instances,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
    }
    return render(request,'sales/dashboard.html',context)


@login_required
def export_report(request):
    current_shop = get_current_shop(request)
    instances = Product.objects.filter(is_deleted=False,shop=current_shop)

    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False)
    sale_items = SaleItem.objects.filter(sale__shop=current_shop,sale__is_deleted=False)
    sales_count = 0
    sales_total = 0
    final_discount_amount = 0
    payment_received_total = 0
    balance_total = 0
    total_tax_amount_total = 0
    title = "Report"
    tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
    counter = 0
    tax_percentage_dict = {}
    filter_date = date

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

    #filter by date created range
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_from_date = from_date
    filter_to_date = to_date

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

    if instances:
        sale_items = sale_items.filter(sale__in=instances)
        sales_dict = instances.aggregate(Sum('total'),Sum('special_discount'),Sum('payment_received'),Sum('balance'),Sum('total_discount_amount'),Sum('total_tax_amount'))
        payment_received_total = sales_dict['payment_received__sum']
        sales_total  = sales_dict['total__sum']
        balance_total = sales_dict['balance__sum']
        total_tax_amount_total = sales_dict['total_tax_amount__sum']
        sales_count = instances.count()

        for tax in tax_categories:
            items = sale_items.filter(product__tax_category=tax)

            tax_amount = 0
            if items :
                tax_amount = items.aggregate(tax_amount=Sum('tax_amount')).get("tax_amount",0)
            tax_percentage_dict[str(tax.tax)] = tax_amount
            counter += 1

        final_discount_amount = sales_dict['special_discount__sum'] + sales_dict['total_discount_amount__sum']

    wb = xlwt.Workbook()
    ws = wb.add_sheet(title)

    ws.write(0, 0, "Total Sales")
    ws.write(0, 1, sales_count)

    ws.write(1, 0, "Total Sales Amount")
    ws.write(1, 1, sales_total)

    ws.write(2, 0, "Special Discounts")
    ws.write(2, 1, sales_total)

    ws.write(3, 0, "Special Discounts")
    ws.write(3, 1, final_discount_amount)

    ws.write(4, 0, "Payment Recieved")
    ws.write(4, 1, payment_received_total)

    ws.write(5, 0, "Total Balance")
    ws.write(5, 1, balance_total)

    ws.write(6, 0, "Total Tax Amount")
    ws.write(6, 1, total_tax_amount_total)

    ws.write(7, 0, "Sales Count")
    ws.write(7, 1, sales_count)

    if instances :
        counter = 8
        for key, value in tax_percentage_dict.items():
            title = "Tax Amount" + key + "%"
            ws.write(counter, 0, title)
            ws.write(counter, 1, value)
            counter += 1

    media_root = settings.MEDIA_ROOT + '/excel_report.xls'
    wb.save(media_root)

    host_name = request.get_host()
    full_url = 'http://' + host_name + '/media/excel_report.xls'

    response_data = {
        "status" : "true",
        "file_url" : full_url
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
def taxed_sale_items(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    tax_category = request.GET.get('tax_category')
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False)
    sale_items = []
    title = "Tax Category : " + tax_category + "%"
    filter_date = date

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

    #filter by date created range
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_from_date = from_date
    filter_to_date = to_date

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

    if instances:
        if TaxCategory.objects.filter(tax=tax_category,shop=current_shop,is_deleted=False).exists():
            tax_category = TaxCategory.objects.get(tax=tax_category,shop=current_shop,is_deleted=False)
            sale_items = SaleItem.objects.filter(sale__in=instances,product__tax_category=tax_category)

    context = {
        'title' : title,
        "sale_items" : sale_items,

        "filter_from_date" : filter_from_date,
        "period" : period,
        "filter_to_date" : filter_to_date,
        "filter_date" : filter_date,
        "year" : year,
        "month" : month,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
    }
    return render(request,'sales/taxed_sale_items.html',context)


@check_mode
@login_required
@shop_required
def print_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False)
    sale_items = SaleItem.objects.filter(sale__shop=current_shop,sale__is_deleted=False)
    sales_count = 0
    sales_total = 0
    final_discount_amount = 0
    payment_received_total = 0
    balance_total = 0
    total_tax_amount_total = 0
    title = "Sales Report"
    tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
    counter = 0
    tax_percentage_dict = {}
    filter_date = date

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

    #filter by date created range
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_from_date = from_date
    filter_to_date = to_date

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

    if instances:
        sale_items = sale_items.filter(sale__in=instances)
        sales_dict = instances.aggregate(Sum('total'),Sum('special_discount'),Sum('payment_received'),Sum('balance'),Sum('total_discount_amount'),Sum('total_tax_amount'))
        payment_received_total = sales_dict['payment_received__sum']
        sales_total  = sales_dict['total__sum']
        balance_total = sales_dict['balance__sum']
        total_tax_amount_total = sales_dict['total_tax_amount__sum']
        sales_count = instances.count()

        for tax in tax_categories:
            items = sale_items.filter(product__tax_category=tax)

            tax_amount = 0
            if items :
                tax_amount = items.aggregate(tax_amount=Sum('tax_amount')).get("tax_amount",0)
            tax_percentage_dict[str(tax.tax)] = tax_amount
            counter += 1

        final_discount_amount = sales_dict['special_discount__sum'] + sales_dict['total_discount_amount__sum']

    context = {
        'title' : title,
        "sales_count" : sales_count,
        "sales_total" : sales_total,
        "special_discount_total" : final_discount_amount,
        "payment_received_total" : payment_received_total,
        "balance_total" : balance_total,
        "total_tax_amount_total" : total_tax_amount_total,
        "tax_percentage_dict" : tax_percentage_dict,

        "filter_from_date" : filter_from_date,
        "period" : period,
        "filter_to_date" : filter_to_date,
        "filter_date" : filter_date,
        "year" : year,
        "month" : month,
        "instances" : instances,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
    }
    return render(request,'sales/print_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_sale'],roles=[],both_check=False)
def create(request):
    current_shop = get_current_shop(request)

    SaleItemFormset = formset_factory(SaleItemForm,extra=1)
    today = datetime.datetime.today()
    if request.method == 'POST':

        form = SaleForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        sale_item_formset = SaleItemFormset(request.POST,prefix='sale_item_formset')
        for sale_form in sale_item_formset:
            sale_form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
        if form.is_valid() and sale_item_formset.is_valid() and transaction_form.is_valid():

            items = {}
            total_tax_amount = 0
            total_discount_amount = 0
            customer = form.cleaned_data['customer']
            no_of_boxes = form.cleaned_data['no_of_boxes']
            return_boxes = form.cleaned_data['return_boxes']
            if customer :
                customer_discount = customer.discount
            else :
                customer_discount = form.cleaned_data['customer_discount']

            for f in sale_item_formset:    
                discount_amount = f.cleaned_data['discount_amount']
                discount = f.cleaned_data['discount']
                total_discount_amount += discount_amount
                product = f.cleaned_data['product']
                unit = f.cleaned_data['unit']
                return_item = f.cleaned_data['return_item']
                qty = f.cleaned_data['qty']
                exact_qty = get_exact_qty(qty,unit)                
               
                price = f.cleaned_data['price']                
                cost = f.cleaned_data['cost']

                if customer_discount > 0 :    
                    actual_price = price-(discount_amount/qty)                
                    tax_added_price = price
                    tax_amount = 0
                    if not return_item:
                        tax_amount = qty * (((100*actual_price)/ (100+product.tax)) * product.tax / 100)
                else :
                    product_tax_amount = price * product.tax / 100
                    tax_added_price = price + product_tax_amount
                    tax_amount = 0
                    if not return_item:
                        tax_amount = qty * (price - discount_amount) * product.tax / 100
                tax_amount = Decimal(format(tax_amount, '.2f'))
                total_tax_amount += tax_amount
                if return_item:
                    new_pk = str(product.pk) +"_"+str(unit.pk)+"_"+str(return_item)
                else:
                    new_pk = str(product.pk) + "_" +str(unit.pk)
                if str(new_pk) in items:
                    p_unit = items[str(new_pk)]["unit"]
                    p_unit = Measurement.objects.get(pk=p_unit)
                    if p_unit == unit:
                        q = items[str(new_pk)]["qty"]
                        amount = items[str(new_pk)]["tax_amount"]
                        items[str(new_pk)]["qty"] = q + qty
                        items[str(new_pk)]["tax_amount"] = tax_amount + amount   
                        dis_amount = items[str(new_pk)]["discount_amount"] 
                        items[str(new_pk)]['discount_amount'] = discount_amount + dis_amount             
                    else:
                        dic = {
                            "qty" : qty,
                            "price" : price,
                            "cost" : cost,
                            "tax_amount" : tax_amount,
                            "tax_added_price" : tax_added_price,
                            "discount_amount" : discount_amount,
                            "unit" : unit.pk,
                            "return_item" : return_item,
                            "discount" : discount
                        }
                        items[str(new_pk)] = dic
                else:
                    dic = {
                        "qty" : qty,
                        "price" : price,
                        "cost" : cost,
                        "tax_amount" : tax_amount,
                        "tax_added_price" : tax_added_price,
                        "discount_amount" : discount_amount,
                        "unit" : unit.pk,
                        "return_item" : return_item,
                        "discount" : discount
                    }
                    items[str(new_pk)] = dic

            stock_ok = True
            error_message = ''
            for key, value in items.iteritems():
                product_pk = key.split("_")[0]
                return_item = value['return_item']
                if not return_item :
                    stock = 0
                    distributor_product_stock = None
                    if request.user.is_superuser:
                        stock = str(product.stock)
                        unit = Measurement.objects.get(pk=value['unit'])
                        exact_qty = get_exact_qty(value['qty'],unit)
                        if exact_qty > stock:
                            stock_ok = False
                            error_message += "%s has only %s in stock, " %(product.name,str(product.stock))
                    elif DistributorStock.objects.filter(is_deleted=False,product__pk=product_pk,distributor__user=request.user).exists():
                        distributor_product_stock = DistributorStock.objects.get(is_deleted=False,product__pk=product_pk,distributor__user=request.user)
                        stock = distributor_product_stock.stock
                        unit = Measurement.objects.get(pk=value['unit'])
                        exact_qty = get_exact_qty(value['qty'],unit)
                        if exact_qty > stock:
                            stock_ok = False
                            error_message += "%s has only %s in stock, " %(distributor_product_stock.product.name,str(distributor_product_stock.stock))
                    else:
                        stock = str(product.stock)
                        unit = Measurement.objects.get(pk=value['unit'])
                        exact_qty = get_exact_qty(value['qty'],unit)
                        if exact_qty > stock:
                            stock_ok = False
                            error_message += "%s has only %s in stock, " %(product.name,str(product.stock))
            
            if stock_ok:
                customer_name = form.cleaned_data['customer_name']
                customer_address = form.cleaned_data['customer_address']
                customer_email = form.cleaned_data['customer_email']
                customer_phone = form.cleaned_data['customer_phone']
                customer = form.cleaned_data['customer']
                customer_state = form.cleaned_data['customer_state']
                gstin = form.cleaned_data['gstin']
                discount = form.cleaned_data['customer_discount']

                if not customer:
                    auto_id = get_auto_id(Customer)
                    a_id = get_a_id(Customer,request)

                    customer = Customer(
                        name = customer_name,
                        email = customer_email,
                        phone = customer_phone,
                        address = customer_address,
                        gstin = gstin,
                        shop = current_shop,
                        first_time_credit = 0,
                        first_time_debit = 0,
                        credit = 0,
                        debit = 0,
                        creator = request.user,
                        updator = request.user,
                        auto_id = auto_id,
                        a_id = a_id,
                        state = customer_state,
                        discount = discount
                    )
                    customer.save()

                gst_type = "sgst"
                if not customer.state == current_shop.state:
                    gst_type = "igst"

                auto_id = get_auto_id(Sale)
                a_id = get_a_id(Sale,request)

                customer_gstin_invoice_id = None
                customer_non_gstn_invoice_id = None
                if customer:
                    if customer.gstin:
                        sale_type = 'wholesale'
                        gst_sale = Sale.objects.filter(shop=current_shop,customer_gstin_invoice_id__isnull=False,is_deleted=False).order_by("-date_added")[:1]
                        customer_gstin_invoice_id = 1
                        for l in gst_sale:
                            if l.customer_gstin_invoice_id:
                                customer_gstin_invoice_id = int(l.customer_gstin_invoice_id) + 1
                                
                        invoice_id = "GA1"
                        last_sale = Sale.objects.filter(is_deleted=False,shop=current_shop,sale_type='wholesale').order_by("-date_added")[:1]
                        if last_sale:
                            invoice = last_sale[0].invoice_id[2:]
                            invoice_letter = last_sale[0].invoice_id[:2]
                            invoice = int(invoice) + 1 
                            invoice_id = invoice_letter +str(invoice)
                            sale_type = 'wholesale'
                        if today.month >=4:
                            if not Sale.objects.filter(shop=current_shop,is_deleted=False,time__year=today.year,time__month__gte=4,sale_type='wholesale').exists():
                                invoice_id = "GA1"
                                if last_sale:
                                    char = last_sale[0].invoice_id
                                    if not char[2].isdigit():
                                        c=char[1]
                                        ch = chr(ord(c) +1)
                                    else:
                                        ch = "A"

                                    invoice_id = "G" +ch +"1" 
                    else:
                        sale_type = 'retail'
                        non_gst_sale = Sale.objects.filter(shop=current_shop,customer_non_gstn_invoice_id__isnull=False,is_deleted=False).order_by("-date_added")[:1]
                        customer_non_gstn_invoice_id = 1
                        for l in non_gst_sale:
                            if l.customer_non_gstn_invoice_id:
                                customer_non_gstn_invoice_id = int(l.customer_non_gstn_invoice_id) + 1
                                
                        invoice_id = "NA1"
                        last_sale = Sale.objects.filter(is_deleted=False,shop=current_shop,sale_type='retail').order_by("-date_added")[:1]
                        if last_sale:
                            invoice = last_sale[0].invoice_id[2:]
                            invoice_letter = last_sale[0].invoice_id[:2]
                            invoice = int(invoice) + 1 
                            invoice_id = invoice_letter +str(invoice)
                            sale_type = 'retail'
                            
                        if today.month >=4:
                            if not Sale.objects.filter(shop=current_shop,is_deleted=False,time__year=today.year,time__month__gte=4,sale_type='retail').exists():
                                invoice_id = "NA1"
                                if last_sale:
                                    char = last_sale[0].invoice_id
                                    if not char[2].isdigit():
                                        c=char[1]
                                        ch = chr(ord(c) +1)
                                    else:
                                        ch = "A"
                                    invoice_id = "N" +ch +"1"

                #create sale
                special_discount = form.cleaned_data['special_discount']
                payment_received = form.cleaned_data['payment_received']

                date = form.cleaned_data['time']
                if Distributor.objects.filter(user=request.user).exists():
                    distributor = Distributor.objects.get(user=request.user)

                data1 = form.save(commit=False)
                data1.creator = request.user
                data1.updator = request.user
                data1.auto_id = auto_id
                data1.shop = current_shop
                data1.total_discount_amount = total_discount_amount
                data1.total_tax_amount = total_tax_amount
                data1.customer_gstin_invoice_id = customer_gstin_invoice_id
                data1.customer_non_gstn_invoice_id = customer_non_gstn_invoice_id
                data1.a_id = a_id
                data1.gst_type = gst_type
                data1.customer = customer
                data1.invoice_id = invoice_id
                data1.sale_type = sale_type
                if Distributor.objects.filter(user=request.user).exists():
                    distributor = Distributor.objects.get(user=request.user)                
                data1.save()
                all_subtotal = 0
                commission_amount = 0
                return_item_total = 0
                return_instance = {}
                #save items
                for key, value in items.iteritems():
                    product_pk = key.split("_")[0]
                    product = Product.objects.get(pk=product_pk)
                    qty = value["qty"]
                    price = value["price"]
                    tax = product.tax
                    discount = value["discount"]
                    tax_amount = value["tax_amount"]
                    unit = value["unit"]
                    unit = Measurement.objects.get(pk=unit)
                    exact_qty = get_exact_qty(qty,unit)
                    discount_amount = value["discount_amount"]
                    tax_added_price = value["tax_added_price"]
                    return_item = value['return_item']
                    cost = value["cost"]
                    batch_full_qty = 0
                    batch_full_cost = 0
                   
                    if ProductBatch.objects.filter(product=product,shop=current_shop).exists():            
                        batch_instance = ProductBatch.objects.filter(product=product,shop=current_shop).exclude(qty=0).order_by('id')
                        
                        for batch in batch_instance : 
                            if batch_full_qty > qty :
                                break;
                            else :
                                balance_qty = qty - batch_full_qty
                                batch_balance_qty = batch.qty - balance_qty 
                                if batch_balance_qty >= 0 : 
                                    batch_full_cost += balance_qty * batch.cost
                                    batch_full_qty += balance_qty
                                    batch.qty = batch_balance_qty
                                    batch.save()
                                    ProductBatchHistory.objects.create(shop=current_shop,sale=data1,batch=batch,qty=balance_qty)  
                                    break;
                                else :                                
                                    batch_full_qty += batch.qty
                                    batch_full_cost = batch.qty * batch.cost
                                    batch.qty = 0
                                    ProductBatchHistory.objects.create(shop=current_shop,sale=data1,batch=batch,qty=batch.qty) 
                                    batch.save()    

                    if batch_full_qty < qty :
                        balance_qty = qty - batch_full_qty
                        batch_full_cost += cost * balance_qty
                        batch_full_qty += balance_qty
                    
                    cost = batch_full_cost / batch_full_qty
                    if customer_discount > 0 :
                        subtotal = (qty * price) - discount_amount
                        price = (100*price)/(100+product.tax)
                    else :
                        subtotal = (qty * price) - discount_amount + tax_amount

                    if return_item:
                        if SaleReturn.objects.filter(is_deleted=False,sale=data1,is_from_sale=True,distributor=distributor).exists():
                            return_instance = SaleReturn.objects.get(is_deleted=False,sale=data1,is_from_sale=True,distributor=distributor)
                        else:
                            sale_return_auto_id = get_auto_id(SaleReturn)
                            sale_return_a_id = get_a_id(SaleReturn,request)
                            return_instance = SaleReturn.objects.create(
                                auto_id = sale_return_auto_id,
                                a_id = sale_return_a_id,
                                shop = current_shop,
                                creator = request.user,
                                updator = request.user,
                                time = data1.time,
                                sale = data1,
                                distributor = distributor,
                                customer = customer,
                                is_from_sale = True 
                            )
                        SaleReturnItem(
                            shop = current_shop,
                            sale_return = return_instance,
                            product = product,
                            unit = unit,
                            qty = qty,
                            price = price,
                            cost = cost
                        ).save()

                        if DamagedProduct.objects.filter(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False).exists():
                            damaged_product = DamagedProduct.objects.get(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False)
                            old_qty = damaged_product.qty
                            damaged_qty = old_qty + Decimal(qty)
                            damaged_product.qty = damaged_qty
                            damaged_product.save()
                        else:
                            DamagedProduct.objects.create(
                                distributor=distributor,
                                shop=current_shop,
                                product=product,
                                unit=unit,
                                qty = Decimal(qty),
                                time = date
                            )

                        return_item_total += subtotal
                    else:
                        commission_amount += qty * current_shop.commission_per_packet
                    
                    all_subtotal += subtotal
                    SaleItem(
                        sale = data1,
                        product = product,
                        qty = qty,
                        cost = cost,
                        price = price,
                        tax = tax,
                        discount = discount,
                        tax_amount = tax_amount,
                        discount_amount = discount_amount,
                        subtotal = subtotal,
                        unit = unit,
                        tax_added_price = tax_added_price,
                        return_item = return_item,
                    ).save()

                    if Distributor.objects.filter(user=request.user).exists():
                        distributor_pk = Distributor.objects.get(user=request.user).pk
                        distributor_stock_update(request,distributor_pk,product.pk,exact_qty,"decrease")
                    else:                        
                        update_sock(product.pk,exact_qty,"decrease")
                   
                for key, value in items.iteritems():
                    product_pk = key.split("_")[0]
                    product = Product.objects.get(pk=product_pk)
                    stock = product.stock
                    low_stock_limit = product.low_stock_limit
                    if stock < low_stock_limit:
                        create_notification(request,'low_stock_notification',product)

                credit=0
                debit=0
                customer_return_amount = 0
                if customer:
                    if not customer.is_system_generated:
                        credit = customer.credit
                        debit = customer.debit
                        customer_return_amount = customer.return_amount

                        updated_boxes = no_of_boxes - return_boxes
                        customer.no_of_boxes += updated_boxes
                        customer.save()

                if return_instance :
                    return_instance.returnable_amount = return_item_total
                    return_instance.save()

                all_subtotal -= return_item_total
                
                if current_shop.remove_previous_balance_from_bill:
                    total_total = all_subtotal - special_discount
                else :
                    # Customer.objects.filter(pk=customer.pk,is_deleted=False).update(credit=0,debit=0)
                    total = all_subtotal - special_discount + credit - debit
                    total_total = total

                this_sale_total = all_subtotal - special_discount

                this_sale_rounded_total = round(this_sale_total)
                this_sale_extra = round(this_sale_total) - float(this_sale_total)
                this_sale_round_off = format(this_sale_extra, '.2f')

                # This code for finding customer balance using all credits and debits till date.
                rounded_total = round(total_total)
                balance = rounded_total - float(payment_received)
                balance = Decimal(balance)

                this_sale_balance = Decimal(this_sale_rounded_total) - payment_received
                if this_sale_balance < 0 :
                    response_data = {
                        "status" : "false",
                        "stable" : "true",
                        "title" : "Check Payment Recieved",
                        "message" : "Recieved amount greater than actual amount"
                        }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                # if this_sale_balance < 0 :
                #         balance_amount = abs(this_sale_balance)
                #         this_sale_balance = 0
                #         prev_sales = Sale.objects.filter(customer=customer,is_deleted=False).exclude(balance=0).order_by('date_added')
                #         for prev_sale in prev_sales: 
                #             prev_balance = prev_sale.balance
                #             prev_total = prev_sale.total                                                        
                #             prev_collect_amount = prev_sale.collected_amount                            
                #             new_balance = balance_amount 
                #             balance_amount -= prev_balance
                #             if balance_amount <= 0 :                        
                #                 balance_amount = abs(balance_amount)
                #                 prev_balance -= new_balance 
                #                 prev_collect_amount += new_balance
                #                 Sale.objects.filter(pk=prev_sale.pk).update(balance=prev_balance,collected_amount=prev_collect_amount)
                #                 PaymentHistory(
                #                     shop = current_shop,
                #                     creator =request.user, 
                #                     updator =request.user,
                #                     auto_id = get_auto_id(PaymentHistory),
                #                     a_id = get_a_id(PaymentHistory,request),
                #                     payment_from = data1,
                #                     payment_to = prev_sale,
                #                     amount = new_balance
                #                 ).save()
                #                 break;
                #             else :
                #                 Sale.objects.filter(pk=prev_sale.pk).update(collected_amount=prev_total,balance = 0)
                #                 PaymentHistory(
                #                     shop = current_shop,
                #                     creator =request.user, 
                #                     updator =request.user,
                #                     auto_id = get_auto_id(PaymentHistory),
                #                     a_id = get_a_id(PaymentHistory,request),
                #                     payment_from = data1,
                #                     payment_to = prev_sale,
                #                     amount = prev_balance
                #                 ).save()

                amount_from_return = 0
                if return_item_total > 0:
                    return_balance = return_item_total - customer_return_amount

                    if this_sale_balance < 0:
                        this_sale_balance = 0

                    if return_balance  > 0:
                        amount_from_return = customer_return_amount
                        customer.return_amount = 0
                        customer.save()
                    else:
                        amount_from_return = return_item_total
                        customer.return_amount = abs(return_balance)
                        customer.save()
                if not customer.is_system_generated:
                    #update credit
                    if balance > 0:
                        balance = balance
                        update_customer_credit_debit(customer.pk,"credit",this_sale_balance)
                    elif balance < 0:
                        balance = abs(balance)
                        update_customer_credit_debit(customer.pk,"debit",this_sale_balance)
                        balance = 0

                #update sale total,round_off and subtotal
                data1.subtotal=all_subtotal
                data1.total=rounded_total
                data1.balance=balance
                data1.round_off=this_sale_round_off
                data1.payment_received = payment_received
                data1.old_debit=debit
                data1.old_credit=credit
                data1.return_amount = amount_from_return
                data1.commission_amount = commission_amount
                data1.return_item_total = return_item_total
                data1.save()    
                # updating distributor commission amount
                if Distributor.objects.filter(user=request.user).exists():
                    if not distributor.no_commission:
                        old_commission_tobe_paid = distributor.commission_tobe_paid
                        distributor.commission_tobe_paid = old_commission_tobe_paid + commission_amount
                        distributor.save()

                amount = form.cleaned_data['payment_received']
               
                if amount > 0:
                    add_transaction(request,transaction_form,data1,amount,"sale_payment","income",debit,credit)

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Sale created successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('sales:print',kwargs={'pk':data1.pk})
                }
            else:
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Out of Stock",
                    "message" : error_message
                }

        else:
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(sale_item_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        default_customer = Customer.objects.get(name="default",address="default",shop=current_shop)
        sale_form = SaleForm(initial={"customer" : default_customer,"sale_type" : "retail"})
        sale_item_formset = SaleItemFormset(prefix='sale_item_formset')
        for form in sale_item_formset:
            form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            form.fields['unit'].queryset = Measurement.objects.none()
            form.fields['unit'].label_from_instance = lambda obj: "%s" % (obj.code)
        transaction_form = TransactionForm()
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "title" : "Create Sale ",
            "form" : sale_form,
            "transaction_form" : transaction_form,
            "url" : reverse('sales:create'),
            "sale_item_formset" : sale_item_formset,
            "redirect" : True,
            "is_create_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'sales/entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_sale'],roles=['distributor'],both_check=False)
def sales(request):
    current_shop = get_current_shop(request)
    sales = Sale.objects.filter(shop=current_shop)
    customers = Customer.objects.filter(is_deleted=False,shop=current_shop)

    current_role = get_current_role(request)
    if current_role == "distributor":
        instances = sales.filter(is_deleted=False,distributor__user=request.user)
        customers = customers.filter(creator=request.user)
    elif current_role == 'staff':
        instances = sales.filter(is_deleted=False,shop=current_shop)
    else:
        instances = sales

    today = datetime.date.today()
    customer = request.GET.get('customer')
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    payment = request.GET.get('payment')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(invoice_id__icontains=query) | Q(customer__name__icontains=query))
        
    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"

    if customer:
        instances = instances.filter(customer_id=customer)

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    if payment :
        if payment == "full":
            instances = instances.filter(balance=0)
        elif payment == "no":
            for instance in instances:
                payment_received = instance.payment_received
                if payment_received != 0:
                    instances = instances.exclude(pk = instance.pk)
        elif payment == "extra":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total >= payment_received:
                    instances = instances.exclude(pk=instance.pk)
        elif payment == "partial":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total <= payment_received or payment_received == 0:
                    instances = instances.exclude(pk=instance.pk)

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
        'sales' :sales,
        'customers' : customers,
        "title" : 'Sales',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "sales" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/sales.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_sale'],roles=['distributor'],both_check=False)
def return_sales(request):
    current_shop = get_current_shop(request)
    sales = Sale.objects.filter(shop=current_shop,return_item_total__gt=0)
    customers = Customer.objects.filter(is_deleted=False,shop=current_shop)

    current_role = get_current_role(request)
    if current_role == "distributor":
        instances = sales.filter(is_deleted=False,distributor__user=request.user)
        customers = customers.filter(creator=request.user)
    elif current_role == 'staff':
        instances = sales.filter(is_deleted=False,shop=current_shop)
    else:
        instances = sales

    today = datetime.date.today()
    customer = request.GET.get('customer')
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    payment = request.GET.get('payment')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(invoice_id__icontains=query) | Q(customer__name__icontains=query))
        
    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"

    if customer:
        instances = instances.filter(customer_id=customer)

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    if payment :
        if payment == "full":
            instances = instances.filter(balance=0)
        elif payment == "no":
            for instance in instances:
                payment_received = instance.payment_received
                if payment_received != 0:
                    instances = instances.exclude(pk = instance.pk)
        elif payment == "extra":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total >= payment_received:
                    instances = instances.exclude(pk=instance.pk)
        elif payment == "partial":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total <= payment_received or payment_received == 0:
                    instances = instances.exclude(pk=instance.pk)

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
        'sales' :sales,
        'customers' : customers,
        "title" : 'Return Sales',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "sales" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/return_sales.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_sale'],roles=['distributor'],both_check=False)
def sale(request,pk):
    current_shop = get_current_shop(request)
    return_sales = request.GET.get('return')
    instance = get_object_or_404(Sale.objects.filter(pk=pk,shop=current_shop))
    transactions = Transaction.objects.filter(sale=instance,shop=current_shop,collect_amount=None)
    sale_items = SaleItem.objects.filter(sale=instance,is_deleted=False)
    if return_sales :
        sale_items = SaleItem.objects.filter(sale=instance,is_deleted=False,return_item=True)
    context = {
        "instance" : instance,
        "transactions" : transactions,
        "title" : "Sale : #" + str(instance.auto_id),
        "sale_items" : sale_items,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/sale.html',context)


@check_mode
@login_required
@shop_required
@check_salesman
@permissions_required(['can_create_sale'])
def edit(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Sale.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = None
    old_credit = instance.old_credit
    old_debit = instance.old_debit
    if instance.distributor:
        distributor = instance.distributor
    else:
        distributor = request.user
    previous_customer = instance.customer
    activity_description = get_activity_description(instance,"Previous Info")
    if Transaction.objects.filter(sale=instance,shop=current_shop,first_transaction=True).exists():
        transaction = Transaction.objects.get(sale=instance,shop=current_shop,first_transaction=True)

    if SaleItem.objects.filter(sale=instance).exists():
        extra = 0
    else:
        extra= 1
    SaleItemFormset = inlineformset_factory(
        Sale,
        SaleItem,
        can_delete = True,
        extra = extra,
        exclude = ['creator','updator','auto_id','is_deleted','tax','tax_amount','subtotal','sale','tax_added_price','batch_code'],
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
    )

    if request.method == 'POST':
        response_data = {}
        form = SaleForm(request.POST,instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        sale_item_formset = SaleItemFormset(request.POST,prefix='sale_item_formset',instance=instance)

        if form.is_valid() and sale_item_formset.is_valid() and transaction_form.is_valid():
            #print"form valid"

            old_balance = Sale.objects.get(pk=pk).balance
            old_paid = Sale.objects.get(pk=pk).payment_received
            old_transaction = None
            if Transaction.objects.filter(sale=instance,shop=current_shop,first_transaction=True).exists():
                old_transaction = Transaction.objects.get(sale=instance,shop=current_shop,first_transaction=True)
            items = {}
            total_discount_amount = 0
            total_tax_amount = 0
            old_return_amount  =instance.return_amount
            
            # 500
            customer = form.cleaned_data['customer']
            if customer :
                customer_discount = customer.discount
            else :
                customer_discount = form.cleaned_data['customer_discount']
            for f in sale_item_formset:
                if f not in sale_item_formset.deleted_forms:
                    product = f.cleaned_data['product']
                    #print"product"
                    #printproduct

                    qty = f.cleaned_data['qty']
                    price = f.cleaned_data['price']
                    cost = f.cleaned_data['cost']
                    discount_amount = f.cleaned_data['discount_amount']
                    discount = f.cleaned_data['discount']
                    unit = f.cleaned_data['unit']
                    return_item = f.cleaned_data['return_item']                    
                    #printreturn_item
                    exact_qty = get_exact_qty(qty,unit) 
                    if customer_discount > 0 :    
                        actual_price = price-(discount_amount/qty)                
                        tax_added_price = price
                        tax_amount = 0
                        if not return_item:
                            tax_amount = qty * (((100*actual_price)/ (100+product.tax)) * product.tax / 100)
                    else :
                        product_tax_amount = price * product.tax / 100
                        tax_added_price = price + product_tax_amount
                        tax_amount = 0
                        if not return_item:
                            tax_amount = qty * (price - discount_amount) * product.tax / 100             

                    # if customer_discount > 0 :                    
                    #     tax_added_price = price
                    #     tax_amount = 0
                    #     if not return_item:
                    #         tax_amount = qty * (((100*(price-discount_amount))/ (100+product.tax))) * product.tax / 100
                    # else :
                    #     product_tax_amount = price * product.tax / 100
                    #     tax_added_price = price + product_tax_amount
                    #     tax_amount = 0
                    #     if not return_item:
                    #         tax_amount = qty * (price - discount_amount) * product.tax / 100


                    tax_amount = Decimal(format(tax_amount, '.2f'))
                    total_tax_amount += tax_amount
                    total_discount_amount += discount_amount

                    if return_item:
                        new_pk = str(product.pk) +"_" +str(unit.pk)+"_"+str(return_item)
                    else:
                        new_pk = str(product.pk) + "_" + str(unit.pk) 
                    if str(new_pk) in items:
                        #print"new_pk"
                        p_unit = items[str(new_pk)]["unit"]
                        p_unit = Measurement.objects.get(pk=p_unit)
                        if p_unit == unit:
                            q = items[str(new_pk)]["qty"]
                            amount = items[str(new_pk)]["tax_amount"]
                            dis_amount = items[str(new_pk)]["discount_amount"]
                            items[str(new_pk)]["qty"] = q + qty
                            items[str(new_pk)]["tax_amount"] = tax_amount + amount 
                            items[str(new_pk)]['discount_amount'] = discount_amount + dis_amount              
                    else:
                        #print"not new_pk"
                        dic = {
                            "qty" : qty,
                            "cost" : cost,
                            "price" : price,
                            "tax_amount" : tax_amount,
                            "tax_added_price" : tax_added_price,
                            "discount_amount" : discount_amount,
                            "unit" : unit.pk,
                            "return_item" : return_item,
                            "discount" : discount
                        }
                        items[str(new_pk)] = dic
                else:
                    #print"delete"
                    dic = {
                        "qty" : qty,
                        "price" : price,
                        "cost" : cost,
                        "tax_amount" : tax_amount,
                        "tax_added_price" : tax_added_price,
                        "discount_amount" : discount_amount,
                        "unit" : unit.pk,
                        "return_item" : return_item,
                        "discount" : discount
                    }
                    items[str(new_pk)] = dic                   

            stock_ok = True
            error_message = ''
            for key, value in items.iteritems():
                product_pk = key.split("_")[0]
                product = Product.objects.get(pk=product_pk)
                prev_qty = 0
                prev_exact_qty = 0
                return_item = value['return_item']

                if Distributor.objects.filter(user=request.user).exists():
                    distributor_product_stock = None
                    if DistributorStock.objects.filter(is_deleted=False,product__pk=product_pk,distributor__user=distributor.user).exists():
                        distributor_product_stock = DistributorStock.objects.get(is_deleted=False,product__pk=product_pk,distributor__user=distributor.user)
                        stock = distributor_product_stock.stock
                        stock = stock + prev_exact_qty
                        unit = Measurement.objects.get(pk=value['unit'])
                        exact_qty = get_exact_qty(value['qty'],unit)
                        if exact_qty > stock:
                            stock_ok = False
                            error_message += "%s has only %s in stock, " %(distributor_product_stock.product.name,str(distributor_product_stock.stock))
                    else:
                        stock_ok = False
                        product_obj  = Product.objects.get(pk=product_pk)
                        error_message += "%s is not in your stock." %(product_obj.name)    
                else :
                    product_obj  = Product.objects.get(pk=product_pk)
                    stock = product_obj.stock + prev_exact_qty
                    unit = Measurement.objects.get(pk=value['unit'])
                    exact_qty = get_exact_qty(value['qty'],unit)
                    unit = Measurement.objects.get(pk=value['unit'],shop=current_shop)
                    if exact_qty > stock:
                        stock_ok = False
                        error_message += "%s has only %s in stock, " %(product.name,str(stock))

            if stock_ok:
                if Distributor.objects.filter(user=request.user).exists():
                    distributor = Distributor.objects.get(user=distributor.user)
                customer_name = form.cleaned_data['customer_name']
                customer_address = form.cleaned_data['customer_address']
                customer_email = form.cleaned_data['customer_email']
                customer_phone = form.cleaned_data['customer_phone']
                customer = form.cleaned_data['customer']
                customer_state = form.cleaned_data['customer_state']

                if not customer:
                    auto_id = get_auto_id(Customer)
                    a_id = get_a_id(Customer,request)

                    customer = Customer(
                        name = customer_name,
                        email = customer_email,
                        phone = customer_phone,
                        address = customer_address,
                        shop = current_shop,
                        first_time_credit = 0,
                        first_time_debit = 0,
                        credit = 0,
                        debit = 0,
                        creator = request.user,
                        updator = request.user,
                        auto_id = auto_id,
                        a_id = a_id,
                        state = customer_state
                    )
                    customer.save()

                gst_type = "sgst"
                if not customer.state == current_shop.state:
                    gst_type = "igst"

                #update sale
                special_discount = form.cleaned_data['special_discount']
                payment_received = form.cleaned_data['payment_received']
                date = form.cleaned_data['time']
                data1 = form.save(commit=False)
                data1.updator = request.user
                data1.date_updated = datetime.datetime.now()
                data1.total_discount_amount = total_discount_amount
                data1.total_tax_amount = total_tax_amount
                data1.gst_type = gst_type
                data1.return_amount = 0
                data1.status = "edited"
                data1.save()
                all_subtotal = 0

                #delete previous items and update stock
                previous_sale_items = SaleItem.objects.filter(sale=instance)
                for p in previous_sale_items:
                    #print"prev_item"
                    product = p.product
                    return_item = p.return_item
                    if Distributor.objects.filter(user=request.user).exists():
                        distributor_stock_update(request,data1.distributor.pk,p.product.pk,prev_exact_qty,"increase")
                    else :
                        #print"super stock"
                        update_sock(p.product.pk,prev_exact_qty,"increase")
                                           
                previous_sale_items.delete()

                # delete previous payment history

                if PaymentHistory.objects.filter(payment_from=instance).exists():
                    #print"prev payment"
                    previous_payment_histories = PaymentHistory.objects.filter(payment_from=instance)
                    for p in previous_payment_histories: 
                        sale = get_object_or_404(Sale.objects.filter(pk=p.payment_to.pk))
                        prev_collect = sale.collected_amount
                        #printprev_collect
                        prev_bal = sale.balance
                        prev_collect -= p.amount
                        prev_bal += p.amount
                        Sale.objects.filter(pk=p.payment_to.pk).update(collected_amount=prev_collect,balance=prev_bal)
                    previous_payment_histories.delete()

                if ProductBatchHistory.objects.filter(sale=instance).exists():
                    previous_batch_histories = ProductBatchHistory.objects.filter(sale=instance)
                    for p in previous_batch_histories: 
                        batch = get_object_or_404(ProductBatch.objects.filter(pk=p.batch.pk))
                        available_qty = batch.qty
                        prev_bal = p.qty
                        new_qty = available_qty + prev_bal
                        ProductBatch.objects.filter(pk=p.batch.pk).update(qty=new_qty)
                    previous_batch_histories.delete()

                commission_amount = 0
                return_item_total = 0
                #save items
                for key, value in items.iteritems():
                    product_pk = key.split("_")[0]
                    product = Product.objects.get(pk=product_pk)
                    qty = value["qty"]
                    price = value["price"]
                    tax = product.tax
                    discount = value["discount"]
                    tax_amount = value["tax_amount"]
                    discount_amount = value["discount_amount"]
                    tax_added_price = value["tax_added_price"]
                    return_item  = value["return_item"]
                    unit = value["unit"]
                    cost = value["cost"]
                    batch_full_qty = 0
                    batch_full_cost = 0
                    if ProductBatch.objects.filter(product=product,shop=current_shop).exists():            
                        batch_instance = ProductBatch.objects.filter(product=product,shop=current_shop).exclude(qty=0).order_by('id')
                        batch_full_qty = 0
                        batch_full_cost = 0
                        for batch in batch_instance : 
                            if batch_full_qty > qty :
                                break;
                            else :
                                balance_qty = qty - batch_full_qty
                                batch_balance_qty = batch.qty - balance_qty 
                                if batch_balance_qty >= 0 : 
                                    batch_full_cost += balance_qty * batch.cost
                                    batch_full_qty += balance_qty
                                    batch.qty = batch_balance_qty
                                    batch.save()
                                    ProductBatchHistory.objects.create(shop=current_shop,sale=data1,batch=batch,qty=batch_balance_qty)  
                                    break;
                                else :                                
                                    batch_full_qty += batch.qty
                                    batch_full_cost = batch.qty * batch.cost
                                    batch.qty = 0
                                    ProductBatchHistory.objects.create(shop=current_shop,sale=data1,batch=batch,qty=batch.qty) 
                                    batch.save()    

                    if batch_full_qty < qty :
                        balance_qty = qty - batch_full_qty
                        batch_full_cost += cost * balance_qty
                        batch_full_qty += balance_qty

                    cost = batch_full_cost / batch_full_qty

                    if customer_discount > 0 :
                        subtotal = (qty * price) - discount_amount
                        price = (100*price)/(100+product.tax)
                    else :
                        subtotal = (qty * price) - discount_amount + tax_amount
                    unit = Measurement.objects.get(pk=unit)
                    exact_qty = get_exact_qty(qty,unit)

                    all_subtotal += subtotal

                    if return_item:
                        if SaleReturn.objects.filter(is_deleted=False,sale=data1,is_from_sale=True,distributor=distributor).exists():
                            return_instance = SaleReturn.objects.get(is_deleted=False,sale=data1,is_from_sale=True,distributor=distributor)
                        else:
                            sale_return_auto_id = get_auto_id(SaleReturn)
                            sale_return_a_id = get_a_id(SaleReturn,request)
                            return_instance = SaleReturn.objects.create(
                                auto_id = sale_return_auto_id,
                                a_id = sale_return_a_id,
                                shop = current_shop,
                                creator = request.user,
                                updator = request.user,
                                time = data1.time,
                                sale = data1,
                                distributor = distributor,
                                customer = customer,
                                is_from_sale = True 
                            )
                        SaleReturnItem(
                            shop = current_shop,
                            sale_return = return_instance,
                            product = product,
                            unit = unit,
                            qty = qty,
                            price = price,
                            cost = cost
                        ).save()

                        if DamagedProduct.objects.filter(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False).exists():
                            damaged_product = DamagedProduct.objects.get(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False)
                            old_qty = damaged_product.qty
                            damaged_qty = old_qty + Decimal(qty)
                            damaged_product.qty = damaged_qty
                            damaged_product.save()
                        else:
                            DamagedProduct.objects.create(
                                distributor=distributor,
                                shop=current_shop,
                                product=product,
                                unit=unit,
                                qty = Decimal(qty),
                                time = date
                            )

                        return_item_total += subtotal
                    else:
                        commission_amount += qty * current_shop.commission_per_packet

                    SaleItem(
                        sale = data1,
                        product = product,
                        qty = qty,
                        cost = cost,
                        price = price,
                        tax = tax,
                        discount = discount,
                        tax_amount = tax_amount,
                        discount_amount = discount_amount,
                        subtotal = subtotal,
                        unit = unit,
                        tax_added_price = tax_added_price,
                        return_item = return_item,

                    ).save()

                    if Distributor.objects.filter(user=request.user).exists():
                        distributor_stock_update(request,data1.distributor.pk,product.pk,qty,"decrease")
                    else :
                        update_sock(product.pk,qty,"decrease")

                credit=0
                debit=0
                customer_return_amount = 0
                if customer:
                    if not customer.is_system_generated:
                        credit = customer.credit
                        debit = customer.debit
                        customer_return_amount = customer.return_amount + old_return_amount
                all_subtotal -= return_item_total
                total = all_subtotal - special_discount + old_credit - old_debit
                total_total = total
                if current_shop.remove_previous_balance_from_bill:
                    total_total = all_subtotal - special_discount

                total = all_subtotal - special_discount
                rounded_total = Decimal(round(total))
                balance = rounded_total - payment_received - instance.amount_from_debit
                extra = Decimal(round(total)) - total
                round_off = Decimal(format(extra, '.2f'))
                balance = Decimal(balance)
                #printbalance
                this_sale_balance = (all_subtotal - special_discount) - payment_received - instance.collected_amount - instance.amount_from_debit
                if this_sale_balance < 0 :
                    response_data = {
                        "status" : "false",
                        "stable" : "true",
                        "title" : "Check Payment Recieved",
                        "message" : "Recieved amount greater than actual amount"
                        }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                # if this_sale_balance < 0 :
                #     balance_amount = abs(this_sale_balance)
                #     prev_sales = Sale.objects.filter(customer=customer,is_deleted=False).exclude(balance=0).order_by('date_added')
                #     for prev_sale in prev_sales: 
                #         prev_balance = prev_sale.balance
                #         prev_total = prev_sale.total                                                        
                #         prev_collect_amount = prev_sale.collected_amount                            
                #         new_balance = balance_amount 
                #         balance_amount -= prev_balance
                #         if balance_amount <= 0 :                        
                #             balance_amount = abs(balance_amount)
                #             prev_balance -= new_balance 
                #             prev_collect_amount += new_balance
                #             Sale.objects.filter(pk=prev_sale.pk).update(balance=prev_balance,collected_amount=prev_collect_amount)
                #             PaymentHistory(
                #                 shop = current_shop,
                #                 creator =request.user, 
                #                 updator =request.user,
                #                 auto_id = get_auto_id(PaymentHistory),
                #                 a_id = get_a_id(PaymentHistory,request),
                #                 payment_from = data1,
                #                 payment_to = prev_sale,
                #                 amount = new_balance
                #             ).save()
                #             break;
                #         else :
                #             Sale.objects.filter(pk=prev_sale.pk).update(collected_amount=prev_total,balance = 0)
                #             PaymentHistory(
                #                 shop = current_shop,
                #                 creator =request.user, 
                #                 updator =request.user,
                #                 auto_id = get_auto_id(PaymentHistory),
                #                 a_id = get_a_id(PaymentHistory,request),
                #                 payment_from = data1,
                #                 payment_to = prev_sale,
                #                 amount = prev_balance
                #             ).save()

                amount_from_return = 0
                if return_item_total > 0:
                    return_balance = return_item_total - customer_return_amount
                    if this_sale_balance < 0:
                        this_sale_balance = 0

                    if return_balance  > 0:
                        amount_from_return = customer_return_amount
                        customer.return_amount = 0
                        customer.save()
                    else:
                        amount_from_return = return_item_total
                        customer.return_amount = abs(return_balance)
                        customer.save()
                rounded_total = Decimal(round(total_total))       
                data1.subtotal=all_subtotal
                data1.total=rounded_total
                data1.balance=this_sale_balance
                data1.round_off=round_off
                data1.return_item_total=return_item_total
                data1.return_amount = amount_from_return
                #printdata1.return_amount
                data1.save()

                activity_description += get_activity_description(data1,"Current Info")
                activity = UserActivity(
                    shop=current_shop,
                    user=request.user,
                    activity_type="update",
                    app="sales",
                    title = "Modified a sale",
                    description=activity_description
                )
                #printactivity.app
                activity.save()

                #update credit
                if not previous_customer.is_system_generated:
                    update_customer_credit_debit(previous_customer.pk,"debit",old_balance)
                if not data1.customer.is_system_generated:
                    if balance > 0:
                        balance = balance
                        update_customer_credit_debit(data1.customer.pk,"credit",balance)
                    elif balance < 0:
                        balance = abs(balance)
                        update_customer_credit_debit(data1.customer.pk,"debit",balance)

                #update account balance
                if old_transaction:
                    if old_transaction.cash_account:
                        balance = old_transaction.cash_account.balance - old_paid
                        CashAccount.objects.filter(pk=old_transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                    else  :
                        balance = old_transaction.bank_account.balance - old_paid
                        BankAccount.objects.filter(pk=old_transaction.bank_account.pk,shop=current_shop).update(balance=balance)

                transaction_mode = transaction_form.cleaned_data['transaction_mode']
                payment_to = transaction_form.cleaned_data['payment_to']
                transaction_category = transaction_form.cleaned_data['transaction_category']
                amount = form.cleaned_data['payment_received']
                transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='sale_payment',category_type="income",is_deleted=False)[:1])

                #create Transaction
                data = transaction_form.save(commit=False)

                if transaction_mode == "cash":
                    data.payment_mode = None
                    data.payment_to = "cash_account"
                    data.bank_account = None
                    data.cheque_details = None
                    data.card_details = None
                    data.is_cheque_withdrawed = False
                    balance = balance + amount
                    CashAccount.objects.filter(pk=data.cash_account.pk,shop=current_shop).update(balance=balance)
                elif transaction_mode == "bank":
                    balance = balance + amount
                    BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                    payment_mode = transaction_form.cleaned_data['payment_mode']
                    if payment_mode == "cheque_payment":
                        is_cheque_withdrawed = transaction_form.cleaned_data['is_cheque_withdrawed']
                        data.card_details = None

                        if not is_cheque_withdrawed:
                            # data.payment_to = None
                            # data.bank_account = None
                            data.cash_account = None

                    elif payment_mode == "internet_banking":
                        data.payment_to = "bank_account"
                        data.cash_account = None
                        data.cheque_details = None
                        data.card_details = None
                        data.is_cheque_withdrawed = False

                    elif payment_mode == "card_payment":
                        data.payment_to = "bank_account"
                        data.cash_account = None
                        data.cheque_details = None
                        data.is_cheque_withdrawed = False

                    if payment_to == "cash_account":
                        data.bank_account = None
                    elif payment_to == "bank_account":
                        data.cash_account = None

                if not transaction_category == "credit":
                    data.updator = request.user
                    data.transaction_type = "income"
                    data.transaction_category = transaction_categories
                    data.amount = amount
                    data.date = date
                    data.shop = current_shop
                    if not transaction:
                        data.a_id = get_a_id(Transaction,request)
                        data.auto_id = get_auto_id(Transaction)
                        data.creator = request.user
                        data.updator = request.user
                        data.first_transaction = True
                    data.sale = data1
                    data.save()

                if transaction_mode == "cash":
                    cash_debit = amount
                    bank_debit = 0
                elif transaction_mode == "bank":
                    cash_debit = 0
                    bank_debit = amount

                if Journel.objects.filter(sale=data1).exists():
                    Journel.objects.filter(sale=data1).update(
                            cash_debit = cash_debit,
                            bank_debit = bank_debit,
                            income = amount
                        )    

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Updated",
                    "message" : "Sale Successfully Updated.",
                    "redirect" : "true",
                    "redirect_url" : reverse('sales:sale',kwargs={'pk':data1.pk})
                }
            else:
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Out of Stock",
                    "message" : error_message
                }
        else:
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(sale_item_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = SaleForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        if transaction:
            cash_account = transaction.cash_account
            bank_account = transaction.bank_account
        else:
            if instance.distributor:
                cash_account =  CashAccount.objects.filter(shop=current_shop,is_deleted=False,user=instance.distributor.user)
        sale_item_formset = SaleItemFormset(prefix='sale_item_formset',instance=instance)
        for item in sale_item_formset:
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop)
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Edit Sale #: " + str(instance.auto_id),
            "instance" : instance,
            "url" : reverse('sales:edit',kwargs={'pk':instance.pk}),
            "sale_item_formset" : sale_item_formset,
            "redirect" : True,
            "old_debit" : old_debit,
            "old_credit" : old_credit,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,

            "is_edit" : True
        }
        return render(request, 'sales/entry.html', context)


@check_mode
@login_required
@shop_required
def delete_sale_fun(request,instance,current_shop):
    old_balance = instance.balance
    return_amount = instance.return_amount
    old_paid = instance.payment_received
    #update credit debit
    if not instance.customer.is_system_generated:
        update_customer_credit_debit(instance.customer.pk,"debit",old_balance)
        update_customer_credit_debit(instance.customer.pk,"increase",return_amount)

    #update stock
    sale_items = SaleItem.objects.filter(sale=instance)
    for p in sale_items:
        qty = p.qty
        unit = p.unit
        exact_qty = get_exact_qty(qty,unit)
        update_sock(p.product.pk,exact_qty,"increase")
       
    #update account balance
    if Transaction.objects.filter(sale=instance,transaction_category__name='sale_payment').exists():
        old_transaction = get_object_or_404(Transaction.objects.filter(sale=instance,transaction_category__name='sale_payment'))
        if old_transaction.cash_account:
            balance = old_transaction.cash_account.balance - old_paid
            CashAccount.objects.filter(pk=old_transaction.cash_account.pk).update(balance=balance)
        else  :
            balance = old_transaction.bank_account.balance - old_paid
            BankAccount.objects.filter(pk=old_transaction.bank_account.pk).update(balance=balance)

        old_transaction.is_deleted=True
        old_transaction.save()

    activity_description = get_activity_description(instance,"Sale Info")
    activity = UserActivity(
        shop=current_shop,
        user=request.user,
        activity_type="delete",
        app="sales",
        title = "Deleted a sale",
        description=activity_description
    )
    activity.save()

    if SaleReturn.objects.filter(sale=instance,is_from_sale=True).exists():
        SaleReturn.objects.filter(sale=instance,is_from_sale=True).delete()

    instance.is_deleted=True
    instance.status = "deleted"
    instance.save()


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_create_sale'])
def delete(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Sale.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    delete_sale_fun(request,instance,current_shop)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Sale Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('sales:sales')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_create_sale'])
def delete_selected_sales(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Sale.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            delete_sale_fun(request,instance,current_shop)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Sale(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('sales:sales')
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
def print_sale(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Sale.objects.filter(pk=pk,shop=current_shop))
    sale_items = SaleItem.objects.filter(sale=instance)
    item_count = sale_items.count()
    final_total = instance.total
    final_taxable_amount = instance.total_taxable_amount()

    to_word = inflect.engine()
    total_in_words = to_word.number_to_words(final_total)

    saved_amount = instance.special_discount+instance.total_discount_amount
    sale_list = []
    row_list = []
    context = {}
    bill_page = float(item_count) / 16
    total_bill_page = int(math.ceil(bill_page))
    total_bill_page = range(total_bill_page)
    for i in total_bill_page:
        x = i * 16
        y = (i+1) * 16
        z = i
        sale_item_pk = SaleItem.objects.filter(sale=instance).exclude(return_item=True).values('id')[:x]
        item_name = str(i)+"_th_sale_items"
        name = str(i) +"_th_sale_items"
        item = SaleItem.objects.filter(sale=instance).exclude(id__in=sale_item_pk).exclude(return_item=True)[:16]
        exec("item_name = item")
        row_name = str(i) +"_th_rows"
        rowname = str(i) +"_th_rows"
        row = range(0,(16-item_name.count()))
        exec("row_name = row")
        context[name] = item_name
        context[rowname] = row_name
        context['total_bill_page'] = total_bill_page
        if item:
            sale_list.append(item_name)
            row_list.append(row_name)
    dict_list = zip(sale_list,row_list)

    #sale return items
    sale_list1 = []
    row_list1 = []
    f_item_count = sale_items.filter(return_item=True).count()
    f_bill_page = float(f_item_count) / 28
    f_total_bill_page = int(math.ceil(f_bill_page))
    f_total_bill_page = range(f_total_bill_page)
    for i in f_total_bill_page:
        x = i * 28
        y = (i+1) * 28
        z = i
        sale_item_pk = SaleItem.objects.filter(sale=instance,return_item=True).values('id')[:x]
        item_name = str(i)+"_th_sale_items"
        name = str(i) +"_th_sale_items"
        item = SaleItem.objects.filter(sale=instance,return_item=True).exclude(id__in=sale_item_pk)[:28]
        exec("item_name = item")
        row_name = str(i) +"_th_rows"
        rowname = str(i) +"_th_rows"
        row = range(0,(28-item_name.count()))
        exec("row_name = row")
        context[name] = item_name
        context[rowname] = row_name
        if item:
            sale_list1.append(item_name)
            row_list1.append(row_name)
    f_dict_list = zip(sale_list1,row_list1)

    context['f_dict_list'] = f_dict_list

    context['dict_list'] = dict_list
    saved_amount = instance.special_discount+instance.total_discount_amount
    context["total_in_words"] = total_in_words
    context["instance"] = instance
    context["final_taxable_amount"] = final_taxable_amount
    context["final_total"] = final_total
    context["title"] = "Sale : #" + str(instance.auto_id)
    context["single_page"] = True
    context["current_shop"] = get_current_shop(request)
    context["saved_amount"] = saved_amount
    context["is_need_wave_effect"] = True
    context["is_need_bootstrap_growl"] = True
    template_name = 'sales/' + current_shop.bill_print_type + '.html'
    return render(request,template_name,context)


@check_mode
@login_required
@shop_required
def email_sale(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Sale.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        form = EmailSaleForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']
            content += "<br />"
            link = request.build_absolute_uri(reverse('sales:print',kwargs={'pk':pk}))
            content += '<a href="%s">%s</a>' %(link,link)

            template_name = 'email/email.html'
            subject = "Purchase Details (#%s) | %s" %(str(instance.auto_id),current_shop.name)
            context = {
                'name' : name,
                'subject' : subject,
                'content' : content,
                'email' : email
            }
            html_content = render_to_string(template_name,context)
            send_email(email,subject,content,html_content)

            response_data = {
                "status" : "true",
                "title" : "Successfully Sent",
                "message" : "Sale Successfully Sent.",
                "redirect" : "true",
                "redirect_url" : reverse('sales:sale',kwargs={'pk':pk})
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
        email = instance.customer.email
        name = instance.customer.name
        content = "Thanks for your purchase from %s. Please follow the below link for your purchase details." %current_shop.name

        form = EmailSaleForm(initial={'name' : name, 'email' : email, 'content' : content})

        context = {
            "instance" : instance,
            "title" : "Email Sale : #" + str(instance.auto_id),
            "single_page" : True,
            'form' : form,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'sales/email_sale.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_collect_amount'],roles=['distributor'],both_check=False)
def create_collect_amount(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    if request.method == "POST":

        form = CollectAmountForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        if form.is_valid() and transaction_form.is_valid():

            auto_id = get_auto_id(CollectAmount)
            a_id = get_a_id(CollectAmount,request)
            #get values from form
            collect_amount = form.cleaned_data['collect_amount']
            discount = form.cleaned_data['discount']
            customer = form.cleaned_data['customer']

            instance = Customer.objects.get(pk=customer.pk,is_deleted=False)
            balance = instance.credit
            date = today
            remaining_balance = balance - (collect_amount + discount)
            # credit = remaining_balance
            # debit = customer.debit
            if remaining_balance <= 0:
            #     credit = 0
            #     if customer.debit > 0:
            #         debit = abs(remaining_balance) + customer.debit
            #     else:
            #         debit = abs(remaining_balance)
                remaining_balance = 0

            data1 = form.save(commit=False)
            data1.creator = request.user
            data1.updator = request.user
            data1.auto_id = auto_id
            data1.a_id = a_id
            data1.balance = balance
            data1.remaining_balance = remaining_balance
            data1.shop = current_shop
            data1.date = date
            data1.save()
            customer = Customer.objects.filter(pk= data1.customer.pk)
            new_collect_amount = collect_amount + discount
            if customer.exists():
                update_customer_credit_debit(instance.pk,"debit",new_collect_amount)
                # customer.update(credit=credit,debit=debit)

            if Sale.objects.filter(is_deleted=False,customer=data1.customer).exists():
                latest_sale = Sale.objects.filter(is_deleted=False,customer=data1.customer,shop=current_shop).latest('date_added')
                collected_amount = latest_sale.collected_amount + collect_amount
                latest_sale = Sale.objects.filter(pk=latest_sale.pk)
                if remaining_balance < 0:
                    remaining_balance = -debit
                latest_sale.update(collected_amount=collected_amount)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            transaction_category = transaction_form.cleaned_data['transaction_category']
            amount = form.cleaned_data['collect_amount']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='sale_payment',category_type="income",is_deleted=False)[:1])

            #create income
            data = transaction_form.save(commit=False)

            if transaction_mode == "cash":
                data.payment_mode = None
                data.payment_to = "cash_account"
                data.bank_account = None
                data.cheque_details = None
                data.card_details = None
                data.is_cheque_withdrawed = False
                balance = data.cash_account.balance
                balance = balance + amount
                CashAccount.objects.filter(pk=data.cash_account.pk,shop=current_shop).update(balance=balance)
            elif transaction_mode == "bank":
                balance = 0
                balance = data.bank_account.balance
                balance = balance + amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = transaction_form.cleaned_data['payment_mode']
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = transaction_form.cleaned_data['is_cheque_withdrawed']
                    data.card_details = None

                    if not is_cheque_withdrawed:
                        data.payment_to = "bank_account"
                        data.bank_account = data.bank_account
                        data.cash_account = None

                elif payment_mode == "internet_banking":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.card_details = None
                    data.is_cheque_withdrawed = False

                elif payment_mode == "card_payment":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.is_cheque_withdrawed = False

                if payment_to == "cash_account":
                    data.bank_account = None
                elif payment_to == "bank_account":
                    data.cash_account = None

            if not transaction_category == "credit":
                data.auto_id = get_auto_id(Transaction)
                data.a_id = get_a_id(Transaction,request)
                data.creator = request.user
                data.updator = request.user
                data.transaction_type = "income"
                data.transaction_category = transaction_categories
                data.amount = amount
                data.date = date
                if Sale.objects.filter(is_deleted=False,customer=data1.customer).exists():
                    latest_sale = Sale.objects.filter(is_deleted=False,customer=data1.customer,shop=current_shop).latest('date_added')
                    data.sale = latest_sale
                data.collect_amount = data1
                data.shop = current_shop
                data.save()

                if transaction_mode == "cash":
                    cash_debit = collect_amount
                    bank_debit = 0
                elif transaction_mode == "bank":
                    cash_debit = 0
                    bank_debit = collect_amount
                Journel.objects.create(
                    date = date,
                    shop = current_shop,
                    cash_debit = cash_debit,
                    bank_debit = bank_debit,
                    income = collect_amount,
                    transaction = data
                )

            response_data = {
                "status" : "true",
                "title" : "Succesfully Created",
                "redirect" : "true",
                "redirect_url" : reverse('sales:collect_amount',kwargs = {'pk' :data1.pk}),
                "message" : "Amount Collected Successfully."
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
        form = CollectAmountForm()
        transaction_form = TransactionForm()
        current_role = get_current_role(request)
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False)
        if current_role == 'distributor':
            transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False,user=request.user)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Amount Collection",
            "is_create_page" : True,
            "today" : today,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,

        }
        return render(request, 'sales/entry_collect_amount.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_collect_amount'],roles=['distributor'],both_check=False)
def edit_collect_amount(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CollectAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(collect_amount=instance,shop=current_shop))

    if request.method == "POST":
        response_data = {}
        old_collected_amount = instance.collect_amount + instance.discount
        old_balance = instance.balance
        balance = 0
        form = CollectAmountForm(request.POST,instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        if form.is_valid() and transaction_form.is_valid():

            #initialize customer credit

            update_customer_credit_debit(instance.customer.pk,"credit",old_collected_amount)
            amount = form.cleaned_data['collect_amount']
            discount = form.cleaned_data['discount']
            remaining_balance = old_balance - (amount + discount)
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.remaining_balance = remaining_balance
            data1.save()
            new_collect_amount = amount + discount
            #update customer credit
            update_customer_credit_debit(instance.customer.pk,"debit",new_collect_amount)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            transaction_category = transaction_form.cleaned_data['transaction_category']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='sale_payment',category_type="income",is_deleted=False)[:1])

            #update account balance
            if Transaction.objects.filter(collect_amount=pk).exists():
                if transaction.cash_account:
                    balance = transaction.cash_account.balance - old_collected_amount
                    CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = transaction.bank_account.balance - old_collected_amount
                    BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)
            #create transaction
            data = transaction_form.save(commit=False)
            if transaction_mode == "cash":
                cash_debit = amount
                bank_debit = 0
            elif transaction_mode == "bank":
                cash_debit = 0
                bank_debit = amount
            if Journel.objects.filter(transaction=data).exists():
                Journel.objects.filter(transaction=data).update(income=amount,cash_debit=cash_debit,bank_debit=bank_debit)
            
            if transaction_mode == "cash":
                data.payment_mode = None
                data.payment_to = "cash_account"
                data.bank_account = None
                data.cheque_details = None
                data.card_details = None
                data.is_cheque_withdrawed = False
                balance = balance + amount
                CashAccount.objects.filter(pk=data.cash_account.pk,shop=current_shop).update(balance=balance)
            elif transaction_mode == "bank":
                balance = balance + amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = transaction_form.cleaned_data['payment_mode']
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = transaction_form.cleaned_data['is_cheque_withdrawed']
                    data.card_details = None

                    if not is_cheque_withdrawed:
                        data.payment_to = "bank_account"
                        data.bank_account = data.bank_account
                        data.cash_account = None                        

                elif payment_mode == "internet_banking":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.card_details = None
                    data.is_cheque_withdrawed = False

                elif payment_mode == "card_payment":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.is_cheque_withdrawed = False

                if payment_to == "cash_account":
                    data.bank_account = None
                elif payment_to == "bank_account":
                    data.cash_account = None

            if not transaction_category == "credit":
                data.updator = request.user
                data.transaction_type = "income"
                data.transaction_category = transaction_categories
                data.amount = amount
                data.date = data1.date
                if Sale.objects.filter(is_deleted=False,customer=data1.customer,shop=current_shop).exists():
                    latest_sale = Sale.objects.filter(is_deleted=False,customer=data1.customer,shop=current_shop).latest('date_added')
                    data.sale = latest_sale
                data.collect_amount = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Updated",
                "redirect" : "true",
                "redirect_url" : reverse('sales:collect_amount', kwargs = {'pk' :pk}),
                "message" : "Collect Amount Successfully Updated."
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
        form = CollectAmountForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Edit Collect Amount : " + str(instance.collect_amount),
            "instance" : instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'sales/entry_collect_amount.html', context)



@check_mode
@login_required
@shop_required
@permissions_required(['can_view_collect_amount'],roles=['distributor'],both_check=False)
def collect_amounts(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request)
    instances = CollectAmount.objects.filter(is_deleted=False,shop=current_shop)
    if current_role == 'distributor':
       instances = CollectAmount.objects.filter(is_deleted=False,shop=current_shop,creator=request.user) 

    title = "Collect Amounts"
    date = request.GET.get('date')  
    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"   

    if date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(date__month=date.month,date__year=date.year,date__day=date.day)

    #filter by query
    query = request.GET.get("q")
    if query:
        title = "Collect Amount (Query - %s)" % query
        instances = instances.filter(Q(collect_amount__icontains=query) | Q(date__icontains=query) | Q(customer__name__icontains=query))

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
    return render(request,'sales/collect_amounts.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_collect_amount'],roles=['distributor'],both_check=False)
def collect_amount(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CollectAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(collect_amount=instance,shop=current_shop))
    context = {
        "instance" : instance,
        "transaction" : transaction,
        "title" : "Collect Amount: " + str(instance.collect_amount),

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/collect_amount.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_collect_amount'],roles=['distributor'],both_check=False)
def delete_collect_amount(request,pk):
    current_shop = get_current_shop(request)
    collect_amount_obj = CollectAmount.objects.get(pk=pk)

    if Customer.objects.filter(pk=collect_amount_obj.customer.pk,is_deleted=False):
        credit = Customer.objects.get(pk=collect_amount_obj.customer.pk,is_deleted=False).credit + collect_amount_obj.collect_amount + collect_amount_obj.discount
        new_credit = credit + collect_amount_obj.collect_amount + collect_amount_obj.discount
        Customer.objects.filter(pk=collect_amount_obj.customer.pk,is_deleted=False).update(credit=credit)

    if Transaction.objects.filter(collect_amount=collect_amount_obj).exists():
        old_transaction = get_object_or_404(Transaction.objects.filter(collect_amount=collect_amount_obj))
        if old_transaction.cash_account:
            balance = old_transaction.cash_account.balance - collect_amount_obj.collect_amount
            CashAccount.objects.filter(pk=old_transaction.cash_account.pk).update(balance=balance)
        else  :
            balance = old_transaction.bank_account.balance - collect_amount_obj.collect_amount
            BankAccount.objects.filter(pk=old_transaction.bank_account.pk).update(balance=balance)

        old_transaction.is_deleted=True
        old_transaction.save()

        CollectAmount.objects.filter(pk=pk).update(is_deleted=True,shop=current_shop)

    response_data = {
        "status" : "true",
        "title" : "Succesfully Deleted",
        "redirect" : "true",
        "redirect_url" : reverse('sales:collect_amounts'),
        "message" : "Collect Amount Successfully Deleted."
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_collect_amount'],roles=['distributor'],both_check=False)
def delete_selected_collect_amounts(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(CollectAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            collect_amount_obj = CollectAmount.objects.get(pk=pk)
            if Customer.objects.filter(pk=collect_amount_obj.customer.pk,is_deleted=False):
                credit = Customer.objects.get(pk=collect_amount_obj.customer.pk,is_deleted=False).credit + collect_amount_obj.collect_amount + collect_amount_obj.discount
                new_credit = credit + collect_amount_obj.collect_amount + collect_amount_obj.discount
                Customer.objects.filter(pk=collect_amount_obj.customer.pk,is_deleted=False).update(credit=credit)

            if Transaction.objects.filter(collect_amount=collect_amount_obj).exists():
                old_transaction = get_object_or_404(Transaction.objects.filter(collect_amount=collect_amount_obj))
                if old_transaction.cash_account:
                    balance = old_transaction.cash_account.balance - collect_amount_obj.collect_amount
                    CashAccount.objects.filter(pk=old_transaction.cash_account.pk).update(balance=balance)
                else  :
                    balance = old_transaction.bank_account.balance - collect_amount_obj.collect_amount
                    BankAccount.objects.filter(pk=old_transaction.bank_account.pk).update(balance=balance)

                old_transaction.is_deleted=True
                old_transaction.save()

            CollectAmount.objects.filter(pk=pk).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected CollectAmount(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('sales:collect_amounts')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some Collect Amount first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_collected_amount(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CollectAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    context = {
        "instance" : instance,
        "title" : "Collected Amount : #" + str(instance.auto_id),
        "single_page" : True,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'sales/print_collected_amount.html',context)


def print_collected_amounts(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    title = "Sale payment"
    instances = CollectAmount.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get('q')
    if query :
        instances = instances.filter(Q(auto_id__icontains=query) | Q(customer__name__icontains=query))

    date = request.GET.get('date')
    date_error = "no"

    if date :
        try:
            date = datetime.datetime.strptime(date, '%d/%m/%Y').date()
        except ValueError:
            date_error = "yes"

    period = request.GET.get('period')

    filter_period = None
    if period:
        if period == "today" or period == "month" or period == "year":
            filter_period = period

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    filter_date_period = False

    if from_date and to_date:
        try:
            from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date() + datetime.timedelta(days=1)
        except ValueError:
            date_error = "yes"

        filter_date_period = True


    if filter_period :
        if period == "today":
            title = "Purchases : Today"

            instances = instances.filter(date__year=today.year, date__month=today.month, date__day=today.day)
            total_purchases_created = instances.count()

        elif period == "month":
            title = "Purchases : This Month"
            instances = instances.filter(date__year=today.year, date__month=today.month)

        elif period == "year":
            title = "Purchases : This Year"
            instances = purchases.filter(date__year=today.year)
    elif filter_date_period:
        title = "Purchases : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(date__range=[from_date, to_date])
            total_purchases_created = instances.count()
    elif date:
        title = "Purchases : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(date__year=date.year, date__month=date.month, date__day=date.day)
    context = {
        "instances" : instances,
        "title" : title,
        "single_page" : True,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'sales/print_collected_amounts.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_customer_payment'],roles=['distributor'],both_check=False)
def create_customer_payment(request):
    current_shop = get_current_shop(request)
    if request.method == "POST":

        form = CustomerPaymentForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        if form.is_valid() and transaction_form.is_valid():

            auto_id = get_auto_id(CustomerPayment)
            a_id = get_a_id(CustomerPayment,request)
            paid_amount = form.cleaned_data['paid_amount']
            customer = form.cleaned_data['customer']
            date = form.cleaned_data['date']
            instance = Customer.objects.get(pk=customer.pk,is_deleted=False,shop=current_shop)
            balance = instance.debit

            remaining_balance = balance - paid_amount
            debit = remaining_balance
            credit = customer.credit
            if remaining_balance <= 0:
                debit = 0
                if customer.credit > 0:
                    credit = abs(remaining_balance) + customer.credit
                else:
                    credit = abs(remaining_balance)
                remaining_balance = 0

            #create staff
            data1 = form.save(commit=False)
            data1.creator = request.user
            data1.updator = request.user
            data1.auto_id = auto_id
            data1.a_id = a_id
            data1.balance = balance
            data1.remaining_balance = remaining_balance
            data1.shop = current_shop
            data1.save()

            customer = Customer.objects.filter(pk= data1.customer.pk)
            if customer.exists():
                customer.update(credit=credit,debit=debit)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            transaction_category = transaction_form.cleaned_data['transaction_category']
            amount = form.cleaned_data['paid_amount']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='customer_payment',category_type="expense",is_deleted=False)[:1])

            #create income
            data = transaction_form.save(commit=False)

            if transaction_mode == "cash":
                cash_credit = paid_amount
                bank_credit = 0
            elif transaction_mode == "bank":
                cash_credit = 0
                bank_credit = paid_amount
            Journel.objects.create(
                shop = current_shop,
                date = date,
                cash_credit = cash_credit,
                bank_credit = bank_credit,
                transaction = data,
                expense = paid_amount
                )

            if transaction_mode == "cash":
                data.payment_mode = None
                data.payment_to = "cash_account"
                data.bank_account = None
                data.cheque_details = None
                data.card_details = None
                data.is_cheque_withdrawed = False
                balance = data.cash_account.balance
                balance = balance - amount
                CashAccount.objects.filter(pk=data.cash_account.pk,shop=current_shop).update(balance=balance)
            elif transaction_mode == "bank":
                balance = 0
                balance = data.bank_account.balance
                balance = balance - amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = transaction_form.cleaned_data['payment_mode']
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = transaction_form.cleaned_data['is_cheque_withdrawed']
                    data.card_details = None

                    if not is_cheque_withdrawed:
                        # data.payment_to = None
                        # data.bank_account = None
                        data.cash_account = None

                elif payment_mode == "internet_banking":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.card_details = None
                    data.is_cheque_withdrawed = False

                elif payment_mode == "card_payment":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.is_cheque_withdrawed = False

                if payment_to == "cash_account":
                    data.bank_account = None
                elif payment_to == "bank_account":
                    data.cash_account = None

            if not transaction_category == "credit":
                data.auto_id = get_auto_id(Transaction)
                data.a_id = get_a_id(Transaction,request)
                data.creator = request.user
                data.updator = request.user
                data.transaction_type = "expense"
                data.transaction_category = transaction_categories
                data.amount = amount
                data.date = date
                data.customer_payment = data1
                data.shop = current_shop
                data.save()           

            response_data = {
                "status" : "true",
                "title" : "Succesfully Created",
                "redirect" : "true",
                "redirect_url" : reverse('sales:customer_payments'),
                "message" : "Amount Paid Successfully."
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
        form = CustomerPaymentForm()
        transaction_form = TransactionForm()
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)

        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Customer payment",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "is_create_page" : True

        }
        return render(request, 'sales/entry_customer_payment.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_customer_payment'],roles=['distributor'],both_check=False)
def edit_customer_payment(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CustomerPayment.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(customer_payment=instance,shop=current_shop))

    if request.method == "POST":
        response_data = {}
        balance = 0
        old_paid_amount = instance.paid_amount
        form = CustomerPaymentForm(request.POST,instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        if form.is_valid() and transaction_form.is_valid():

            #initialize customer debit
            update_customer_credit_debit(instance.customer.pk,"debit",old_paid_amount)
            amount = form.cleaned_data['paid_amount']
            date = form.cleaned_data['date']
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.save()
            update_customer_credit_debit(instance.customer.pk,"credit",amount)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            transaction_category = transaction_form.cleaned_data['transaction_category']

            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='customer_payment',category_type="expense",is_deleted=False)[:1])

            #update account balance
            if Transaction.objects.filter(customer_payment=pk).exists():
                if transaction.cash_account:
                    balance = transaction.cash_account.balance + old_paid_amount
                    #printbalance
                    CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = transaction.bank_account.balance + old_paid_amount
                    BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)
            #create transaction
            data = transaction_form.save(commit=False)
            if Journel.objects.filter(transaction=data).exists():
                Journel.objects.filter(transaction=data).update(expense=amount,cash_credit=amount)
          
            if transaction_mode == "cash":
                data.payment_mode = None
                data.payment_to = "cash_account"
                data.bank_account = None
                data.cheque_details = None
                data.card_details = None
                data.is_cheque_withdrawed = False
                balance = balance - amount
                CashAccount.objects.filter(pk=data.cash_account.pk,shop=current_shop).update(balance=balance)
            elif transaction_mode == "bank":
                balance = balance - amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = transaction_form.cleaned_data['payment_mode']
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = transaction_form.cleaned_data['is_cheque_withdrawed']
                    data.card_details = None

                    if not is_cheque_withdrawed:
                        # data.payment_to = None
                        # data.bank_account = None
                        data.cash_account = None

                elif payment_mode == "internet_banking":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.card_details = None
                    data.is_cheque_withdrawed = False

                elif payment_mode == "card_payment":
                    data.payment_to = "bank_account"
                    data.cash_account = None
                    data.cheque_details = None
                    data.is_cheque_withdrawed = False

                if payment_to == "cash_account":
                    data.bank_account = None
                elif payment_to == "bank_account":
                    data.cash_account = None

            if not transaction_category == "credit":
                data.updator = request.user
                data.transaction_type = "expense"
                data.transaction_category = transaction_categories
                data.amount = amount
                data.date = date
                data.customer_payment = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Updated",
                "redirect" : "true",
                "redirect_url" : reverse('sales:customer_payments'),
                "message" : "Customer Payment Successfully Updated."
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
        form = CustomerPaymentForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Edit customer payment : " + str(instance.paid_amount),
            "instance" : instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'sales/entry_customer_payment.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_customer_payment'],roles=['distributor'],both_check=False)
def customer_payments(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request)
    instances = CustomerPayment.objects.filter(is_deleted=False,shop=current_shop)
    if current_role == 'distributor':
        instances = CustomerPayment.objects.filter(is_deleted=False,shop=current_shop,creator=request.user)
    title = "Customer Payment"

    #filter by query
    query = request.GET.get("q")
    if query:
        title = "customer payment (Query - %s)" % query
        instances = instances.filter(Q(paid_amount__icontains=query) | Q(date__icontains=query) | Q(customer__name__icontains=query))

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
    return render(request,'sales/customer_payments.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_customer_payment'],roles=['distributor'],both_check=False)
def customer_payment(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CustomerPayment.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(customer_payment=instance,shop=current_shop))
    context = {
        "instance" : instance,
        "transaction" : transaction,
        "title" : "Customer Payment: " + str(instance.paid_amount),

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/customer_payment.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_customer_payment'],roles=['distributor'],both_check=False)
def delete_customer_payment(request,pk):
    CustomerPayment.objects.filter(pk=pk).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Succesfully Deleted",
        "redirect" : "true",
        "redirect_url" : reverse('sales:customer_payments'),
        "message" : "Paid Amount Successfully Deleted."
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_customer_payment'],roles=['distributor'],both_check=False)
def delete_selected_customer_payments(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(CustomerPayment.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            CustomerPayment.objects.filter(pk=pk).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Customer Payment(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('sales:customer_payments')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some Paid Amount first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def print_customer_payment(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CustomerPayment.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    context = {
        "instance" : instance,
        "title" : "Customer Payment : #" + str(instance.auto_id),
        "single_page" : True,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'sales/print_customer_payment.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
def print_customer_payments(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    title = "Sale payment"
    instances = CollectAmount.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get('q')
    if query :
        instances = instances.filter(Q(auto_id__icontains=query) | Q(customer__name__icontains=query))

    date = request.GET.get('date')
    date_error = "no"

    if date :
        try:
            date = datetime.datetime.strptime(date, '%d/%m/%Y').date()
        except ValueError:
            date_error = "yes"

    period = request.GET.get('period')

    filter_period = None
    if period:
        if period == "today" or period == "month" or period == "year":
            filter_period = period

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    filter_date_period = False

    if from_date and to_date:
        try:
            from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date() + datetime.timedelta(days=1)
        except ValueError:
            date_error = "yes"

        filter_date_period = True

    if filter_period :
        if period == "today":
            title = "Purchases : Today"

            instances = instances.filter(date__year=today.year, date__month=today.month, date__day=today.day)
            total_purchases_created = instances.count()

        elif period == "month":
            title = "Purchases : This Month"
            instances = instances.filter(date__year=today.year, date__month=today.month)

        elif period == "year":
            title = "Purchases : This Year"
            instances = purchases.filter(date__year=today.year)
    elif filter_date_period:
        title = "Purchases : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(date__range=[from_date, to_date])
            total_purchases_created = instances.count()
    elif date:
        title = "Purchases : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(date__year=date.year, date__month=date.month, date__day=date.day)
    context = {
        "instances" : instances,
        "title" : title,
        "single_page" : True,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'sales/print_customer_payments.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_sale_return'],both_check=False)
def create_sale_return(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    if request.method == "POST":
        response_data = {}
        form = SaleReturnForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        if form.is_valid() and transaction_form.is_valid():
            #print"form valid"
            message = ""
            is_ok = True

            products = request.POST.getlist('product_pk')
            units = request.POST.getlist('returned_product_unit')
            qtys = request.POST.getlist('returned_qty')
            sale = form.cleaned_data['sale']
            date = form.cleaned_data['time']
            returnable_amount = form.cleaned_data['returnable_amount']
            images = request.FILES.getlist('image')
            items = zip(products,units,qtys,images)
            returned_items = []
            for item in items:
                product_pk = item[0]
                try:
                    product_instance=Product.objects.get(pk=product_pk,shop=current_shop)
                except:
                    product_instance = None
                    message += "Invalid product selection"
                    is_ok = False
                unit_pk = item[1]
                try:
                    unit_instance=Measurement.objects.get(pk=unit_pk,shop=current_shop)
                except:
                    unit_instance = None
                    message += "Invalid unit selection"
                    is_ok = False
                qty = item[2]

                image = item[3]

                if SaleItem.objects.filter(sale=sale,product=product_instance,unit=unit_instance).exists():
                    sale_item = SaleItem.objects.get(sale=sale,product=product_instance,unit=unit_instance)
                    if Decimal(sale_item.actual_qty() ) >= Decimal(qty):
                        pr_ins = {
                            "product" : product_instance,
                            "unit" : unit_instance,
                            "qty" : qty,
                            "price" : sale_item.price,
                            "image" : image
                        }
                        returned_items.append(pr_ins)
                        #printreturned_items

                    else:
                        message += "Qty is greater than sold quantity."
                        is_ok = False
                else:
                    message += "Product with this unit is not in this sale. Please don't edit hidden values."
                    is_ok = False

            error_messages = ""
            title = ""

            if is_ok:
                #print"is_ok"
                #Save Sale Return
                customer =  sale.customer
                if not request.user.is_superuser:
                    distributor = Distributor.objects.get(user=request.user)
                data = form.save(commit=False)
                data.creator = request.user
                data.updator = request.user
                data.shop = current_shop
                data.time = datetime.datetime.now()
                data.a_id = get_a_id(SaleReturn,request)
                data.auto_id = get_auto_id(SaleReturn)
                data.sale = sale
                data.customer = customer
                if not request.user.is_superuser:
                    data.distributor = distributor
                data.save()
                #Save Sale Return Item
                commission_deducted = 0
                for f in returned_items:
                    #print"return item"

                    product = f['product']
                    unit = f['unit']
                    qty = f['qty']
                    image = f['image']
                    exact_qty = Decimal(get_exact_qty(qty,unit))
                    if unit.is_base == True :
                        cost = product.cost
                    else :
                        unit_instanse = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(product=product,unit=unit))
                        cost = unit_instanse.cost
                    price = f['price']

                    tax_added_price = Decimal(price) + (Decimal(price) * Decimal(product.tax)/100)

                    commission_deducted += Decimal(current_shop.commission_per_packet) * Decimal(qty)

                    SaleReturnItem(
                        shop = current_shop,
                        sale_return = data,
                        product = product,
                        qty = qty,
                        unit = unit,
                        price = tax_added_price,
                        cost = cost,
                        image = image
                    ).save()

                    if not request.user.is_superuser:
                        if DamagedProduct.objects.filter(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False).exists():
                            damaged_product = DamagedProduct.objects.get(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False)
                            old_qty = damaged_product.qty
                            damaged_qty = old_qty + Decimal(qty)
                            damaged_product.qty = damaged_qty
                            damaged_product.save()
                        else:
                            DamagedProduct.objects.create(
                                distributor=distributor,
                                shop=current_shop,
                                product=product,
                                unit=unit,
                                qty = Decimal(qty),
                                time = today,
                                image = image
                            )
                    else:
                        DamagedProduct.objects.create(
                            shop=current_shop,
                            product=product,
                            unit=unit,
                            qty = Decimal(qty),
                            time = today,
                            image = image
                        )

                    sale_item = SaleItem.objects.get(sale=sale,product=product,unit=unit)

                    returned_sale_items = SaleItem.objects.filter(sale=sale,is_deleted=False)
                    for item in returned_sale_items:
                        if item.product == product:
                            quantity = Decimal(qty)
                            saleitem_return_qty = SaleItem.objects.get(sale=sale,is_deleted=False,product=product)
                            price = saleitem_return_qty.tax_added_price - (saleitem_return_qty.discount_amount/ saleitem_return_qty.qty) * quantity
                            retuned_item_quantity = saleitem_return_qty.return_qty
                            retuned_item_quantity += quantity
                            sale_return_amount = price
                            SaleItem.objects.filter(sale=sale,is_deleted=False,product=product).update(return_qty=retuned_item_quantity)

                data.returnable_amount = returnable_amount
                data.save()

                if not customer.is_system_generated:
                    update_customer_return_amount(customer.pk,"increase",returnable_amount)

                transaction_mode = transaction_form.cleaned_data['transaction_mode']
                payment_to = transaction_form.cleaned_data['payment_to']       
                amount_returned = returnable_amount
                amount = returnable_amount
                #printamount_returned
                transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='salereturn_payment',category_type="expense",is_deleted=False)[:1])
                transaction_category = transaction_categories.name

                data1 = transaction_form.save(commit=False)

                if transaction_mode == "cash":
                    data1.payment_mode = None
                    data1.payment_to = "cash_account"
                    data1.bank_account = None
                    data1.cheque_details = None
                    data1.card_details = None
                    data1.is_cheque_withdrawed = False
                    balance = data1.cash_account.balance
                    balance = balance - amount
                    CashAccount.objects.filter(pk=data1.cash_account.pk,shop=current_shop).update(balance=balance)
                elif transaction_mode == "bank":
                    balance = 0
                    balance = data1.bank_account.balance
                    balance = balance - amount
                    BankAccount.objects.filter(pk=data1.bank_account.pk,shop=current_shop).update(balance=balance)
                    payment_mode = transaction_form.cleaned_data1['payment_mode'] 
                    if payment_mode == "cheque_payment":
                        is_cheque_withdrawed = transaction_form.cleaned_data1['is_cheque_withdrawed'] 
                        data1.card_details = None

                        if not is_cheque_withdrawed:
                            data1.payment_to = None
                            data1.bank_account = None
                            data1.cash_account = None

                    elif payment_mode == "internet_banking":
                        data1.payment_to = "bank_account"
                        data1.cash_account = None
                        data1.cheque_details = None
                        data1.card_details = None
                        data1.is_cheque_withdrawed = False
                    
                    elif payment_mode == "card_payment":
                        data1.payment_to = "bank_account"
                        data1.cash_account = None
                        data1.cheque_details = None
                        data1.is_cheque_withdrawed = False
                
                    if payment_to == "cash_account":
                        data1.bank_account = None
                    elif payment_to == "bank_account":
                        data1.cash_account = None

                if not transaction_category == "credit":
                    data1.auto_id = get_auto_id(Transaction) 
                    data1.a_id = get_a_id(Transaction,request)            
                    data1.creator = request.user
                    data1.updator = request.user
                    data1.transaction_type = "expense"
                    data1.transaction_category = transaction_categories
                    data1.amount = amount
                    data1.date = date
                    data1.sale_return = data
                    data1.shop = current_shop
                    data1.save()

                    if transaction_mode == "cash":
                        cash_credit = amount_returned
                        bank_credit = 0
                    elif transaction_mode == "bank":
                        cash_credit = 0
                        bank_credit = amount_returned
                   
                    Journel.objects.create(
                        date = date,
                        shop = current_shop,
                        cash_credit = cash_credit,   
                        bank_credit = bank_credit, 
                        transaction = data1,
                        expense = amount_returned
                    )

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Sale Return Successfully created.",
                    "redirect" : "true",
                    "redirect_url" : reverse('sales:sale_returns')
                }
            else:
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Out of Stock",
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
        form = SaleReturnForm()
        transaction_form = TransactionForm()
        context = {
            "form" : form,
            "transaction_form" : transaction_form, 
            "title" : "Create Sale Return",
            "redirect" : True,
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,

            "is_create_page" : True
        }
        return render(request, 'sales/returns/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_sale_return'],roles=['distributor'],both_check=False)
def sale_returns(request):
    current_shop = get_current_shop(request)
    instances = SaleReturn.objects.filter(shop=current_shop,is_deleted=False)
    current_role = get_current_role(request)
    if current_role == "distributor":
        instances = instances.filter(creator=request.user)

    customer = request.GET.get("customer")
    if customer:
        instances = instances.filter(Q(customer=customer))

    title = "Sale Returns"
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
    return render(request,'sales/returns/returns.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_sale_return'],allow_self=True,model=SaleReturn)
def sale_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(SaleReturn.objects.filter(pk=pk,shop=current_shop,is_deleted=False))
    sale_return_items=SaleReturnItem.objects.filter(shop=current_shop,sale_return=instance,is_deleted=False)

    context = {
        "instance" : instance,
        "sale_return_items" : sale_return_items,
        "title" : "Sale Return ",

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/returns/return.html',context)


def print_sale_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(SaleReturn.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    sale_return_items = SaleReturnItem.objects.filter(sale_return=instance)
    context = {
        "instance" : instance,
        "title" : "Sale : #" + str(instance.auto_id),
        "single_page" : True,
        "sale_return_items" : sale_return_items,
        "current_shop" : get_current_shop(request),
        "is_need_wave_effect" : True,
    }
    template_name = 'sales/returns/' + current_shop.bill_print_type + '.html'
    return render(request,template_name,context)


def delete_sale_return_fun(instance):
    old_balance = instance.returnable_amount
    sale = instance.sale
    customer = sale.customer
    if not customer.is_system_generated:
        update_customer_return_amount(customer.pk,"decrease",old_balance)

    if not instance.sale.customer.is_system_generated:
        update_customer_credit_debit(instance.sale.customer.pk,"debit",old_balance)

    #update stock
    sale_return_items = SaleReturnItem.objects.filter(sale_return=instance)
    for p in sale_return_items:
        qty = p.qty
        unit = p.unit
        sale_item = get_object_or_404(SaleItem.objects.filter(sale=sale,product=p.product,unit=p.unit))
        return_qty = sale_item.return_qty
        return_qty = return_qty - qty
        SaleItem.objects.filter(sale=sale,product=p.product,unit=p.unit).update(return_qty=return_qty)

    instance.is_deleted=True
    instance.save()


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_sale_return'],allow_self=True,model=SaleReturn)
def delete_sale_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(SaleReturn.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    delete_sale_return_fun(instance)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "SaleReturn Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('sales:sale_returns')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_damaged_product'],roles=['distributor'],both_check=False)
def damaged_products(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request)
    instances = DamagedProduct.objects.filter(shop=current_shop,is_deleted=False)
    if current_role == "distributor":
        instances = instances.filter(distributor__user=request.user)

    title = "Damaged Products"
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
    return render(request,'sales/returns/damaged_products.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_damaged_product'],roles=['distributor'],both_check=False)
def create_product_return(request):
    current_shop = get_current_shop(request)
    if request.method == "POST":
        response_data = {}
        form = ProductReturnForm(request.POST)
        if form.is_valid():
            message = ""
            is_ok = True
            products = request.POST.getlist('product_pk')
            units = request.POST.getlist('returned_product_unit')
            qtys = request.POST.getlist('returned_qty')
            distributor = form.cleaned_data['distributor']
            items = zip(products,units,qtys)
            returned_items = []
            for item in items:
                product_pk = item[0]
                try:
                    product_instance= Product.objects.get(pk=product_pk,shop=current_shop)
                except:
                    product_instance = None
                    message += "Invalid product selection"
                    is_ok = False
                unit_pk = item[1]
                try:
                    unit_instance=Measurement.objects.get(pk=unit_pk,shop=current_shop)
                except:
                    unit_instance = None
                    message += "Invalid unit selection"
                    is_ok = False
                qty = item[2]
                if DamagedProduct.objects.filter(product=product_instance,distributor=distributor,shop=current_shop,unit=unit_instance,is_returned=False).exists():
                    return_item_product = DamagedProduct.objects.get(product=product_instance,distributor=distributor,shop=current_shop,unit=unit_instance,is_returned=False)
                    if return_item_product.qty >= Decimal(qty):
                        pr_ins = {
                            "product" : return_item_product,
                            "unit" : unit_instance,
                            "qty" : qty,
                        }
                        returned_items.append(pr_ins)
                    else:
                        message += "Qty is greater than damaged quantity."
                        is_ok = False
                else:
                    message += "Product with this unit is not in list. Please don't edit hidden values."
                    is_ok = False
            if not returned_items:
                message += "Select atleast one product to return."
                is_ok = False
            error_messages = ""
            title = ""

            if is_ok:
                #Save Product Return
                data = form.save(commit=False)
                data.creator = request.user
                data.updator = request.user
                data.shop = current_shop
                data.time = datetime.datetime.now()
                data.a_id = get_a_id(ProductReturn,request)
                data.auto_id = get_auto_id(ProductReturn)
                data.save()
                #Save Sale Return Item
                for f in returned_items:
                    product = f['product']
                    unit = f['unit']
                    qty = f['qty']
                    exact_qty = Decimal(get_exact_qty(qty,unit))

                    ProductReturnItem(
                        shop = current_shop,
                        product_return = data,
                        product = product,
                        qty = qty,
                        unit = unit,
                    ).save()
                    vendor = product.product.vendor
                    if VendorProduct.objects.filter(is_deleted=False,vendor=vendor,shop=current_shop,product=product.product,unit=unit,is_returned=False).exists():
                        damaged_product = VendorProduct.objects.get(is_deleted=False,vendor=vendor,shop=current_shop,product=product.product,unit=unit,is_returned=False)
                        old_qty = damaged_product.qty
                        damaged_qty = old_qty + Decimal(qty)
                        damaged_product.qty = damaged_qty
                        damaged_product.save()                    
                    else:
                        VendorProduct.objects.create(
                            vendor=vendor,
                            shop=current_shop,
                            product=product.product,
                            unit=unit,
                            qty = Decimal(qty)
                        )

                    returned_product = get_object_or_404(DamagedProduct.objects.filter(is_deleted=False,product=product.product,distributor=distributor,unit=unit,shop=current_shop,is_returned=False))
                    
                    quantity = Decimal(qty)
                    if returned_product.qty == quantity:
                        DamagedProduct.objects.filter(is_deleted=False,product=product.product,is_returned=False,distributor=distributor,unit=unit,shop=current_shop).update(is_returned=True,qty=0)
                    else:
                        get_dproduct = get_object_or_404(DamagedProduct.objects.filter(is_deleted=False,product=product.product,distributor=distributor,unit=unit,shop=current_shop,is_returned=False))
                        quan = get_dproduct.qty - quantity
                        DamagedProduct.objects.filter(is_deleted=False,product=product.product,is_returned=False,distributor=distributor,unit=unit,shop=current_shop).update(qty=quan)
                
                response_data['status'] = 'true'
                response_data['title'] = "Successfully Created"
                response_data['redirect'] = 'true'
                response_data['redirect_url'] = reverse('sales:product_return', kwargs = {'pk' : data.pk})
                response_data['message'] = "Sale Return Successfully Created."
            else:
                response_data['status'] = 'false'
                response_data['title'] = "Error in input values"
                response_data['stable'] = "true"
                response_data['message'] = message
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"

            message = ''
            message += generate_form_errors(form,formset=False)
            response_data['message'] = message

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = ProductReturnForm()
        context = {
            "form" : form,
            "title" : "Create Product Return",
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
        return render(request, 'sales/returns/entry_product_return.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_product_return'])
def product_returns(request):
    current_shop = get_current_shop(request)
    instances = ProductReturn.objects.filter(shop=current_shop,is_deleted=False)

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(product__icontains=query))

    title = "Product Returns"
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
    return render(request,'sales/returns/product_returns.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_product_return'])
def product_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductReturn.objects.filter(pk=pk,shop=current_shop,is_deleted=False))
    product_returns = ProductReturnItem.objects.filter(product_return=instance,shop=current_shop,is_deleted=False)

    context = {
        "instance" : instance,
        "title" : "Product Return",
        "product_returns" : product_returns,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/returns/product_return.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_product_return'])
def delete_product_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(ProductReturn.objects.filter(pk=pk,shop=current_shop))
    return_items = ProductReturnItem.objects.filter(shop=current_shop,is_deleted=False,product_return=instance)

    for r in return_items:
        product = r.product
        unit = r.unit
        qty=r.qty
        if DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False).exists():
            old_damaged = get_object_or_404(DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False))
            quantity = old_damaged.qty + qty
            DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False).update(qty=quantity)
        else:
            DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False).update(is_returned=False)

    ProductReturn.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)
    response_data = {}
    response_data['status'] = 'true'
    response_data['title'] = "Successfully Deleted"
    response_data['redirect'] = 'true'
    response_data['redirect_url'] = reverse('sales:product_returns')
    response_data['message'] = "Product Return Successfully Deleted."
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_sale_items(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')
    template_name = 'sales/includes/sale_items.html'
    instances = SaleItem.objects.filter(sale__pk=pk)
    if instances :
        context = {
            'sale_items' : instances,
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
@ajax_required
@login_required
@shop_required
def get_return_items(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')
    template_name = 'sales/includes/return_items.html'
    instances = DamagedProduct.objects.filter(distributor__pk=pk,is_returned=False,is_deleted=False)
    if instances :
        context = {
            'sale_items' : instances,
        }
        html_content = render_to_string(template_name,context)
        response_data = {
            "status" : "true",
            'template' : html_content,
        }
    else:
        response_data = {
            "status" : "false",
            "template" : "<p class='text-center p-30'>No Products found</p>",
            "message" : "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_vendor_return_items(request):
    current_shop = get_current_shop(request)
    pk = request.GET.get('id')
    template_name = 'sales/includes/vendor_return_items.html'
    instances = VendorProduct.objects.filter(product__vendor__pk=pk,is_returned=False)
    if instances :
        context = {
            'sale_items' : instances,
        }
        html_content = render_to_string(template_name,context)
        response_data = {
            "status" : "true",
            'template' : html_content,
        }
    else:
        response_data = {
            "status" : "false",
            "template" : "<p class='text-center p-30'>No Products found</p>",
            "message" : "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
def get_customer(request):
    pk = request.GET.get('id')
    instance = Sale.objects.get(pk=pk,is_deleted=False)

    if instance.customer:
        if instance.customer.is_system_generated == True:
            response_data = {
                "status" : "true",
                'credit' : float(0.00),
                'debit' : float(0.00),
            }
        else:
            response_data = {
                "status" : "true",
                'credit' : float(instance.customer.credit),
                'debit' : float(instance.customer.debit),
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
@permissions_required(['can_create_estimate'],roles=['distributor'],both_check=False)
def create_estimate(request):
    current_shop = get_current_shop(request)

    EstimateItemFormset = formset_factory(EstimateItemForm,extra=1)

    if request.method == 'POST':
        form = EstimateForm(request.POST)
        estimate_item_formset = EstimateItemFormset(request.POST,prefix='estimate_item_formset')
        for estimate_form in estimate_item_formset:
            estimate_form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
        if form.is_valid() and estimate_item_formset.is_valid():
            items = {}
            total_tax_amount = 0
            total_discount_amount = 0

            for f in estimate_item_formset:

                discount_amount = f.cleaned_data['discount_amount']
                discount = f.cleaned_data['discount']
                total_discount_amount += discount_amount
                product = f.cleaned_data['product']
                unit = f.cleaned_data['unit']
                qty = f.cleaned_data['qty']
                exact_qty = get_exact_qty(qty,unit)
                if unit.is_base == True :
                    cost = product.cost
                else :
                    unit_instanse = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(product=product,unit=unit))
                    cost = unit_instanse.cost
                price = f.cleaned_data['price']
                product_tax_amount = price * product.tax / 100
                tax_added_price = price + product_tax_amount
                tax_amount = qty * (price - discount) * product.tax / 100

                tax_amount = Decimal(format(tax_amount, '.2f'))
                total_tax_amount += tax_amount
                new_pk = str(product.pk) + "_" +str(unit.pk)
                if str(new_pk) in items:
                    p_unit = items[str(new_pk)]["unit"]
                    p_unit = Measurement.objects.get(pk=p_unit)
                    if p_unit == unit:
                        q = items[str(new_pk)]["qty"]
                        items[str(new_pk)]["qty"] = q + qty             
                    else:
                        dic = {
                            "qty" : qty,
                            "cost" : cost,
                            "price" : price,
                            "tax_amount" : tax_amount,
                            "tax_added_price" : tax_added_price,
                            "discount_amount" : discount_amount,
                            "unit" : unit.pk
                        }
                        items[str(new_pk)] = dic
                else:
                    dic = {
                        "qty" : qty,
                        "cost" : cost,
                        "price" : price,
                        "tax_amount" : tax_amount,
                        "tax_added_price" : tax_added_price,
                        "discount_amount" : discount_amount,
                        "unit" : unit.pk
                    }
                    items[str(new_pk)] = dic

            customer_name = form.cleaned_data['customer_name']
            customer_address = form.cleaned_data['customer_address']
            customer_email = form.cleaned_data['customer_email']
            customer_phone = form.cleaned_data['customer_phone']
            customer = form.cleaned_data['customer']
            customer_state = form.cleaned_data['customer_state']

            if not customer:
                auto_id = get_auto_id(Customer)
                a_id = get_a_id(Customer,request)

                customer = Customer(
                    name = customer_name,
                    email = customer_email,
                    phone = customer_phone,
                    address = customer_address,
                    shop = current_shop,
                    first_time_credit = 0,
                    first_time_debit = 0,
                    credit = 0,
                    debit = 0,
                    creator = request.user,
                    updator = request.user,
                    auto_id = auto_id,
                    a_id = a_id,
                    state = customer_state
                )
                customer.save()

            gst_type = "sgst"
            if not customer.state == current_shop.state:
                gst_type = "igst"

            auto_id = get_auto_id(Estimate)
            a_id = get_a_id(Estimate,request)

            #create Estimate
            date = form.cleaned_data['time']

            data1 = form.save(commit=False)
            data1.creator = request.user
            data1.updator = request.user
            data1.auto_id = auto_id
            data1.shop = current_shop
            data1.total_discount_amount = total_discount_amount
            data1.total_tax_amount = total_tax_amount
            data1.a_id = a_id
            data1.gst_type = gst_type
            data1.customer = customer
            data1.save()

            all_subtotal = 0

            #save items
            for key, value in items.iteritems():
                product_pk = key.split("_")[0]
                product = Product.objects.get(pk=product_pk)
                qty = value["qty"]
                price = value["price"]
                tax = product.tax
                discount = discount
                tax_amount = value["tax_amount"]
                unit = value["unit"]
                unit = Measurement.objects.get(pk=unit)
                if unit.is_base == True :
                    cost = product.cost
                else :
                    unit_instanse = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(product=product,unit=unit))
                    cost = unit_instanse.cost
                discount_amount = value["discount_amount"]
                tax_added_price = value["tax_added_price"]
                subtotal = (qty * price) - discount_amount + tax_amount

                all_subtotal += subtotal

                EstimateItem(
                    estimate = data1,
                    product = product,
                    qty = qty,
                    cost = cost,
                    price = price,
                    tax = tax,
                    discount = discount,
                    tax_amount = tax_amount,
                    discount_amount = discount_amount,
                    subtotal = subtotal,
                    unit = unit,
                    tax_added_price = tax_added_price
                ).save()

            total = all_subtotal
            total_total = total
            if current_shop.remove_previous_balance_from_bill:
                total_total = all_subtotal

            rounded_total = round(total)
            extra = round(total) - float(total)
            round_off = format(extra, '.2f')


            #update sale total,round_off and subtotal

            Estimate.objects.filter(pk=data1.pk).update(subtotal=all_subtotal,total=total_total,round_off=round_off)

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Estimate created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('sales:estimates')
            }

        else:
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(estimate_item_formset,formset=True)
            #printestimate_item_formset.errors
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        default_customer = Customer.objects.get(name="default",address="default",shop=current_shop)
        estimate_form = EstimateForm(initial={"customer" : default_customer,"sale_type" : "retail"})
        estimate_item_formset = EstimateItemFormset(prefix='estimate_item_formset')
        for form in estimate_item_formset:
            form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            form.fields['unit'].queryset = Measurement.objects.none()
            form.fields['unit'].label_from_instance = lambda obj: "%s" % (obj.code)
        context = {
            "title" : "Create Estimate ",
            "form" : estimate_form,
            "url" : reverse('sales:create_estimate'),
            "estimate_item_formset" : estimate_item_formset,
            "redirect" : True,
            "is_create_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'sales/estimate/entry_estimate.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_estimate'],roles=['distributor'],both_check=False)
def estimates(request):
    current_shop = get_current_shop(request)
    instances = Estimate.objects.filter(is_deleted=False,shop=current_shop)
    customers = Customer.objects.filter(is_deleted=False,shop=current_shop)

    current_role = get_current_role(request)
    if current_role == "distributor":
        instances =instances.filter(creator=request.user)
        customers = customers.filter(creator=request.user) 
        
    today = datetime.date.today()
    customer = request.GET.get('customer')
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

    if customer:
        instances = instances.filter(customer_id=customer)

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    if payment :
        if payment == "full":
            instances = instances.filter(balance=0)
        elif payment == "no":
            for instance in instances:
                payment_received = instance.payment_received
                if payment_received != 0:
                    instances = instances.exclude(pk = instance.pk)
        elif payment == "extra":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total >= payment_received:
                    instances = instances.exclude(pk=instance.pk)
        elif payment == "partial":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total <= payment_received or payment_received == 0:
                    instances = instances.exclude(pk=instance.pk)

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
        'estimates' :estimates,
        'customers' : customers,
        "title" : 'Estimates',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "estimates" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/estimate/estimates.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_estimate'],roles=['distributor'],both_check=False)
def estimate(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Estimate.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    estimate_items = EstimateItem.objects.filter(estimate=instance,is_deleted=False)
    context = {
        "instance" : instance,
        "title" : "estimate : #" + str(instance.auto_id),
        "estimate_items" : estimate_items,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/estimate/estimate.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_estimate'],roles=['distributor'],both_check=False)
def edit_estimate(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Estimate.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if EstimateItem.objects.filter(estimate=instance).exists():
        extra = 0
    else:
        extra= 1
    EstimateItemFormset = inlineformset_factory(
        Estimate,
        EstimateItem,
        can_delete = True,
        extra = extra,
        exclude=('creator','updator','auto_id','is_deleted','tax','cost','subtotal','estimate','tax_amount','tax_added_price'),
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
    )

    if request.method == 'POST':
        response_data = {}
        form = EstimateForm(request.POST,instance=instance)
        estimate_item_formset = EstimateItemFormset(request.POST,prefix='estimate_item_formset',instance=instance)

        if form.is_valid() and estimate_item_formset.is_valid():

            old_balance = Estimate.objects.get(pk=pk).balance
            old_paid = Estimate.objects.get(pk=pk).payment_received
            items = {}
            total_discount_amount = 0
            total_tax_amount = 0

            for f in estimate_item_formset:
                if f not in estimate_item_formset.deleted_forms:
                    product = f.cleaned_data['product']

                    qty = f.cleaned_data['qty']
                    price = f.cleaned_data['price']
                    discount_amount = f.cleaned_data['discount_amount']
                    discount = f.cleaned_data['discount']
                    unit = f.cleaned_data['unit']
                    if unit.is_base == True :
                        cost = product.cost
                    else :
                        unit_instanse = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(product=product,unit=unit))
                        cost = unit_instanse.cost
                    exact_qty = get_exact_qty(qty,unit)
                    tax_amount = qty * price * product.tax / 100
                    tax_amount = Decimal(format(tax_amount, '.2f'))
                    total_tax_amount += tax_amount
                    total_discount_amount += discount_amount

                    product_tax_amount = price * product.tax / 100
                    tax_added_price = price + product_tax_amount
                    new_pk = str(product.pk) + "_" + str(unit.pk) 
                    if str(new_pk) in items:
                        q = items[str(new_pk)]["qty"]
                        items[str(new_pk)]["qty"] = q + qty

                        d = items[str(new_pk)]["discount_amount"]
                        items[str(new_pk)]["discount_amount"] = d + discount_amount

                        t = items[str(new_pk)]["tax_amount"]
                        items[str(new_pk)]["tax_amount"] = t + tax_amount

                    else:
                        dic = {
                            "qty" : qty,
                            "cost" : cost,
                            "price" : price,
                            "tax_amount" : tax_amount,
                            "discount_amount" :discount_amount,
                            "tax_added_price" : tax_added_price,
                            "unit" :unit.pk,
                            "discount" : discount
                        }
                        items[str(new_pk)] = dic

            customer_name = form.cleaned_data['customer_name']
            customer_address = form.cleaned_data['customer_address']
            customer_email = form.cleaned_data['customer_email']
            customer_phone = form.cleaned_data['customer_phone']
            customer = form.cleaned_data['customer']
            customer_state = form.cleaned_data['customer_state']

            #printcustomer
            if not customer:
                auto_id = get_auto_id(Customer)
                a_id = get_a_id(Customer,request)

                customer = Customer(
                    name = customer_name,
                    email = customer_email,
                    phone = customer_phone,
                    address = customer_address,
                    shop = current_shop,
                    first_time_credit = 0,
                    first_time_debit = 0,
                    credit = 0,
                    debit = 0,
                    creator = request.user,
                    updator = request.user,
                    auto_id = auto_id,
                    a_id = a_id,
                    state = customer_state
                )
                customer.save()

            gst_type = "sgst"
            if not customer.state == current_shop.state:
                gst_type = "igst"

            #update Estimate
            date = form.cleaned_data['time']
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.total_discount_amount = total_discount_amount
            data1.total_tax_amount = total_tax_amount
            data1.gst_type = gst_type
            data1.save()
            all_subtotal = 0

            #delete previous items and update stock
            previous_estimate_items = EstimateItem.objects.filter(estimate=instance)
            previous_estimate_items.delete()

            #save items
            for key, value in items.iteritems():                
                product_pk = key.split("_")[0]
                product = Product.objects.get(pk=product_pk)
                qty = value["qty"]
                price = value["price"]
                tax = product.tax
                discount = value["discount"]
                tax_amount = value["tax_amount"]
                discount_amount = value["discount_amount"]
                tax_added_price = value["tax_added_price"]
                unit = value["unit"]
                subtotal = (qty * price) - discount_amount + tax_amount
                unit = Measurement.objects.get(pk=unit)

                all_subtotal += subtotal

                EstimateItem(
                    estimate = data1,
                    product = product,
                    qty = qty,
                    cost = cost,
                    price = price,
                    tax = tax,
                    discount = discount,
                    tax_amount = tax_amount,
                    discount_amount = discount_amount,
                    subtotal = subtotal,
                    unit = unit,
                    tax_added_price = tax_added_price
                ).save()

            total = all_subtotal
            rounded_total = Decimal(round(total))
            extra = Decimal(round(total)) - total
            round_off = Decimal(format(extra, '.2f'))

            Estimate.objects.filter(pk=data1.pk).update(subtotal=all_subtotal,total=total,round_off=round_off)

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Estimate Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('sales:estimate',kwargs={'pk':data1.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(estimate_item_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = EstimateForm(instance=instance)
        estimate_item_formset = EstimateItemFormset(prefix='estimate_item_formset',instance=instance)
        for item in estimate_item_formset:
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop)
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop)
        context = {
            "form" : form,
            "title" : "Edit Estimate #: " + str(instance.auto_id),
            "instance" : instance,
            "url" : reverse('sales:edit_estimate',kwargs={'pk':instance.pk}),
            "estimate_item_formset" : estimate_item_formset,
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
        return render(request, 'sales/estimate/entry_estimate.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_estimate'],roles=['distributor'],both_check=False)
def delete_estimate(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Estimate.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    instance.is_deleted=True
    instance.save()

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Estimate Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('sales:estimates')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_estimate'],roles=['distributor'],both_check=False)
def delete_selected_estimates(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Estimate.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            instance.is_deleted=True
            instance.save()

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Estimate(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('sales:estimates')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_estimate(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Estimate.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    estimate_items = EstimateItem.objects.filter(estimate=instance)

    to_word = inflect.engine()
    total_in_words = to_word.number_to_words(instance.total)

    if instance.sale_type == "wholesale_with_customer":
        estimate_items_list = []
        total = 0
        for item in estimate_items:
            tax_amount = item.product.price * (item.tax/100)
            subtotal = (item.product.price - item.discount ) * item.qty
            total += subtotal
            dicts = {
                "product" : item.product.name,
                "qty" : item.qty,
                "price" : item.product.price,
                "tax" : item.tax,
                "discount" : item.discount,
                "subtotal" : subtotal
            }
            estimate_items_list.append(dicts)

        saved_amount = instance.special_discount+instance.total_discount_amount
        cash_payment = total - instance.balance
        context = {
            'total_in_words':total_in_words,
            "instance" : instance,
            "title" : "Estimate : #" + str(instance.auto_id),
            "single_page" : True,
            "sale_items" : estimate_items_list,
            "current_shop" : current_shop,
            "saved_amount" : saved_amount,
            "total" : total,
            "cash_payment" : cash_payment,
            "is_need_wave_effect" : True,
        }

        template_name = 'sales/estimate/' + current_shop.bill_print_type + 'wc.html'
        return render(request,template_name,context)

    else:
        saved_amount = instance.special_discount+instance.total_discount_amount
        context = {
            "total_in_words":total_in_words,
            "instance" : instance,
            "title" : "Estimate : #" + str(instance.auto_id),
            "single_page" : True,
            "sale_items" : estimate_items,
            "current_shop" : get_current_shop(request),
            "saved_amount" : saved_amount,
            "is_need_wave_effect" : True,
        }
        template_name = 'sales/estimate/' + current_shop.bill_print_type + '.html'
        return render(request,template_name,context)


@check_mode
@login_required
@shop_required
def email_estimate(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Estimate.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        form = EmailSaleForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']
            content += "<br />"
            link = request.build_absolute_uri(reverse('sales:print_estimate',kwargs={'pk':pk}))
            content += '<a href="%s">%s</a>' %(link,link)

            template_name = 'email/email.html'
            subject = "Purchase Details (#%s) | %s" %(str(instance.auto_id),current_shop.name)
            context = {
                'name' : name,
                'subject' : subject,
                'content' : content,
                'email' : email
            }
            html_content = render_to_string(template_name,context)
            send_email(email,subject,content,html_content)

            response_data = {
                "status" : "true",
                "title" : "Successfully Sent",
                "message" : "Estimate Successfully Sent.",
                "redirect" : "true",
                "redirect_url" : reverse('sales:estimate',kwargs={'pk':pk})
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
        email = instance.customer.email
        name = instance.customer.name
        content = "Thanks for your purchase from %s. Please follow the below link for your purchase details." %current_shop.name

        form = EmailSaleForm(initial={'name' : name, 'email' : email, 'content' : content})

        context = {
            "instance" : instance,
            "title" : "Email Sale : #" + str(instance.auto_id),
            "single_page" : True,
            'form' : form,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
        }
        return render(request,'sales/estimate/email_estimate.html',context)


def stock_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    instances = SaleItem.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    products = Product.objects.filter(is_deleted=False)
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    category = request.GET.get('category')
    product = request.GET.get('product')
    title = "Stock Movement"
    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"
    if category:

        instances = instances.filter(product__category_id=category)

    if product:
        instances = instances.filter(product_id=product)

    if year:
        instances = instances.filter(sale__time__year=year)

    if month:
        instances = instances.filter(sale__time__month=month)


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
            instances = instances.filter(sale__time__year=today.year)
        elif period == 'month' :
            instances = instances.filter(sale__time__year=today.year,sale__time__month=today.month)
        elif period == "today" :
            instances = instances.filter(sale__time__year=today.year,sale__time__month=today.month,sale__time__day=today.day)

    elif filter_date_period:
        title = "Report : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, sale__time__range=[from_date, to_date])

    elif date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(sale__time__month=date.month,sale__time__year=date.year,sale__time__day=date.day)


    items = {}
    for f in instances:
        product = f.product
        qty = f.qty
        stock = f.product.stock
        if str(product.pk) in items:
            q = items[str(product.pk)]["qty"]
            items[str(product.pk)]["qty"] = q + qty
        else:
            dic = {
                "product":product,
                "qty" : qty,
                "stock" : stock,
            }
            items[str(product.pk)] = dic

    context = {
        "items" : items,
        "instances" :instances,
        'categories' :categories ,
        "products":products,
        "title" : title,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "is_need_datetime_picker" : True,
        }
    return render(request, "sales/stock_report.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_damaged_product'],roles=['distributor'],both_check=False)
def create_damaged_product(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    DamagedProductFormset = formset_factory(DamagedProductForm,extra=1)

    if request.method == 'POST':

        damaged_product_formset = DamagedProductFormset(request.POST,request.FILES,prefix='damaged_product_formset')
        for damaged_form in damaged_product_formset:
            damaged_form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
        if damaged_product_formset.is_valid():
            stock_ok = True
            distributor = None
            if Distributor.objects.filter(user=request.user).exists():
                distributor = Distributor.objects.get(user=request.user)
            else:
                stock_ok = False
                error_message += "Sorry! You can't create damaged product."
            items = {}
            total_tax_amount = 0
            total_discount_amount = 0
            if distributor:
                for f in damaged_product_formset:
                    product = f.cleaned_data['product']
                    unit = f.cleaned_data['unit']
                    qty = f.cleaned_data['qty']
                    image = f.cleaned_data['image']
                    exact_qty = get_exact_qty(qty,unit)
                    new_pk = str(product.pk) + "_" + str(unit.pk)
                    if str(new_pk) in items:
                        p_unit = items[str(new_pk)]["unit"]
                        p_unit = Measurement.objects.get(pk=p_unit)
                        if p_unit == unit:
                            q = items[str(new_pk)]["qty"]
                            items[str(new_pk)]["qty"] = q + qty
                        else:
                            dic = {
                                "qty" : qty,
                                "unit" : unit.pk,
                                "image": image
                            }
                            items[str(new_pk)] = dic
                    else:
                        dic = {
                            "qty" : qty,
                            "unit" : unit.pk,
                            "image" : image
                        }
                        items[str(new_pk)] = dic

                error_message = ''
                for key, value in items.iteritems():
                    product_pk = key.split("_")[0]
                    product = Product.objects.get(pk=product_pk)
                    stock = 0
                    distributor_product_stock = None
                    if DistributorStock.objects.filter(is_deleted=False,product=product,distributor=distributor).exists():
                        distributor_product_stock = DistributorStock.objects.get(is_deleted=False,product=product,distributor=distributor)
                        stock = distributor_product_stock.stock
                        unit = Measurement.objects.get(pk=value['unit'])
                        exact_qty = get_exact_qty(value['qty'],unit)
                        if exact_qty > stock:
                            stock_ok = False
                            error_message += "%s has only %s in stock, " %(distributor_product_stock.product.name,str(distributor_product_stock.stock))
                    else:
                        stock_ok = False
                        error_message += "%s is not in your stock." %(product.name)

            if stock_ok:

                for key, value in items.iteritems():
                    product_pk = key.split("_")[0]
                    product = Product.objects.get(pk=product_pk)
                    qty = value["qty"]
                    unit = value["unit"]
                    image = value["image"]
                    unit = Measurement.objects.get(pk=unit)
                    exact_qty = get_exact_qty(qty,unit)
                    if DamagedProduct.objects.filter(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False).exists():
                        damaged_product = DamagedProduct.objects.get(is_deleted=False,distributor=distributor,shop=current_shop,product=product,unit=unit,is_returned=False)
                        old_qty = damaged_product.qty
                        damaged_qty = old_qty + Decimal(qty)
                        damaged_product.qty = damaged_qty
                        damaged_product.image = image
                        damaged_product.save()
                    else:
                        DamagedProduct.objects.create(
                            distributor=distributor,
                            shop=current_shop,
                            product=product,
                            unit=unit,
                            qty = Decimal(qty),
                            time = today,
                            image = image,
                        )                   
                    if Distributor.objects.filter(user=request.user).exists():
                        distributor_pk = Distributor.objects.get(user=request.user).pk
                        distributor_stock_update(request,distributor_pk,product.pk,exact_qty,"decrease")

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Damaged Product Successfully created.",
                    "redirect" : "true",
                    "redirect_url" : reverse('sales:damaged_products')
                }
            else:
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Out of Stock",
                }
        else:
            message = generate_form_errors(damaged_product_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
  
    else:
        damaged_product_formset = DamagedProductFormset(prefix='damaged_product_formset')
        for form in damaged_product_formset:
            form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            form.fields['unit'].queryset = Measurement.objects.none()
            form.fields['unit'].label_from_instance = lambda obj: "%s" % (obj.code)

        context = {
            "title" : "Create Damaged Product ",
            "url" : reverse('sales:create_damaged_product'),
            "damaged_product_formset" : damaged_product_formset,
            "redirect" : True,
            "is_create_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "is_need_formset" : True,
        }
        return render(request,'sales/returns/create_damaged_product.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_vendor_return'])
def create_vendor_return(request):
    current_shop = get_current_shop(request)
    if request.method == "POST":
        response_data = {}
        form = VendorReturnForm(request.POST)
        if form.is_valid():
            message = ""
            is_ok = True
            products = request.POST.getlist('product_pk')
            units = request.POST.getlist('returned_product_unit')
            qtys = request.POST.getlist('returned_qty')
            vendor = form.cleaned_data['vendor']
            items = zip(products,units,qtys)
            returned_items = []
            for item in items:
                product_pk = item[0]
                #printproduct_pk
                try:
                    product_instance= Product.objects.get(pk=product_pk,shop=current_shop)
                except:
                    product_instance = None
                    message += "Invalid product selection"
                    is_ok = False
                unit_pk = item[1]
                try:
                    unit_instance=Measurement.objects.get(pk=unit_pk,shop=current_shop)
                except:
                    unit_instance = None
                    message += "Invalid unit selection"
                    is_ok = False
                qty = item[2]
                if VendorProduct.objects.filter(product=product_instance,shop=current_shop,unit=unit_instance,is_returned=False).exists():
                    return_item_product = VendorProduct.objects.get(product=product_instance,shop=current_shop,unit=unit_instance,is_returned=False)
                    if return_item_product.qty >= Decimal(qty):
                        pr_ins = {
                            "product" : return_item_product,
                            "unit" : unit_instance,
                            "qty" : qty,
                        }
                        returned_items.append(pr_ins)
                    else:
                        message += "Qty is greater than damaged quantity."
                        is_ok = False
                else:
                    message += "Product with this unit is not in list. Please don't edit hidden values."
                    is_ok = False
            if not returned_items:
                message += "Select atleast one product to return."
                is_ok = False
            error_messages = ""
            title = ""

            if is_ok:
                #Save Product Return
                data = form.save(commit=False)
                data.creator = request.user
                data.updator = request.user
                data.shop = current_shop
                data.time = datetime.datetime.now()
                data.a_id = get_a_id(VendorReturn,request)
                data.auto_id = get_auto_id(VendorReturn)
                total_amount = 0
                data.save()
                #Save Sale Return Item
                for f in returned_items:
                    product = f['product']
                    unit = f['unit']
                    qty = f['qty']
                    exact_qty = Decimal(get_exact_qty(qty,unit))
                    total = (Decimal(qty) * product.product.cost)
                    total_amount += total
                    VendorReturnItem(
                        shop = current_shop,
                        vendor_return = data,
                        product = product,
                        cost = product.product.cost,
                        price = product.product.price,
                        qty = qty,
                        unit = unit,
                    ).save()

                    returned_product = get_object_or_404(VendorProduct.objects.filter(is_deleted=False,product=product.product,vendor=vendor,unit=unit,shop=current_shop,is_returned=False))
                    
                    quantity = Decimal(qty)
                    if returned_product.qty == quantity:
                        VendorProduct.objects.filter(is_deleted=False,product=product.product,is_returned=False,vendor=vendor).update(is_returned=True,qty=0)
                    else:
                        get_dproduct = get_object_or_404(VendorProduct.objects.filter(is_deleted=False,product=product.product,vendor=vendor,unit=unit,shop=current_shop,is_returned=False))
                        quan = get_dproduct.qty - quantity
                        VendorProduct.objects.filter(is_deleted=False,product=product.product,is_returned=False,vendor=vendor).update(qty=quan)
                data.total_amount = total_amount
                data.save()
                update_vendor_credit_debit(vendor.pk,"credit",total_amount)
                response_data['status'] = 'true'
                response_data['title'] = "Successfully Created"
                response_data['redirect'] = 'true'
                response_data['redirect_url'] = reverse('sales:vendor_return', kwargs = {'pk' : data.pk})
                response_data['message'] = "Vendor Return Successfully Created."
            else:
                response_data['status'] = 'false'
                response_data['title'] = "Error in input values"
                response_data['stable'] = "true"
                response_data['message'] = message
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"

            message = ''
            message += generate_form_errors(form,formset=False)
            response_data['message'] = message

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = VendorReturnForm()
        context = {
            "form" : form,
            "title" : "Create Vendor Return",
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
        return render(request, 'sales/returns/entry_vendor_return.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_vendor_return'])
def vendor_returns(request):
    current_shop = get_current_shop(request)
    instances = VendorReturn.objects.filter(shop=current_shop,is_deleted=False)

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(product__icontains=query))

    title = "Vendor Returns"
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
    return render(request,'sales/returns/vendor_returns.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_vendor_return'])
def vendor_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(VendorReturn.objects.filter(pk=pk,shop=current_shop,is_deleted=False))
    vendor_returns = VendorReturnItem.objects.filter(vendor_return=instance,shop=current_shop,is_deleted=False)

    context = {
        "instance" : instance,
        "title" : "Vendor Return",
        "vendor_returns" : vendor_returns,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/returns/vendor_return.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_vendor_return'])
def delete_vendor_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(VendorReturn.objects.filter(pk=pk,shop=current_shop))
    return_items = VendorReturnItem.objects.filter(shop=current_shop,is_deleted=False,vendor_return=instance)

    for r in return_items:
        product = r.product
        unit = r.unit
        qty=r.qty
        if DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False).exists():
            old_damaged = get_object_or_404(DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False))
            quantity = old_damaged.qty + qty
            DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False).update(qty=quantity)
        else:
            DamagedProduct.objects.filter(pk=product.pk,unit=unit,shop=current_shop,is_deleted=False).update(is_returned=False)

    VendorReturn.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)
    
    response_data = {}
    response_data['status'] = 'true'
    response_data['title'] = "Successfully Deleted"
    response_data['redirect'] = 'true'
    response_data['redirect_url'] = reverse('sales:vendor_returns')
    response_data['message'] = "Vendor Return Successfully Deleted."
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_purchase_request'],roles=['distributor'],both_check=False)
def create_purchase_request(request):
    current_shop = get_current_shop(request)

    PurchaseRequestItemFormset = formset_factory(PurchaseRequestItemForm,extra=0)

    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        purchase_request_item_formset = PurchaseRequestItemFormset(request.POST,prefix='purchase_request_item_formset')
       
        if form.is_valid() and purchase_request_item_formset.is_valid():

            customer_name = form.cleaned_data['customer_name']
            customer_address = form.cleaned_data['customer_address']
            customer_email = form.cleaned_data['customer_email']
            customer_phone = form.cleaned_data['customer_phone']
            customer = form.cleaned_data['customer']
            customer_state = form.cleaned_data['customer_state']

            if not customer:
                auto_id = get_auto_id(Customer)
                a_id = get_a_id(Customer,request)

                customer = Customer(
                    name = customer_name,
                    email = customer_email,
                    phone = customer_phone,
                    address = customer_address,
                    shop = current_shop,
                    first_time_credit = 0,
                    first_time_debit = 0,
                    credit = 0,
                    debit = 0,
                    creator = request.user,
                    updator = request.user,
                    auto_id = auto_id,
                    a_id = a_id,
                    state = customer_state
                )
                customer.save()

            gst_type = "sgst"
            if not customer.state == current_shop.state:
                gst_type = "igst"

            auto_id = get_auto_id(PurchaseRequest)
            a_id = get_a_id(PurchaseRequest,request)

            #create PurchaseRequest
            date = form.cleaned_data['time']

            data1 = form.save(commit=False)
            data1.creator = request.user
            data1.updator = request.user
            data1.auto_id = auto_id
            data1.shop = current_shop
            data1.a_id = a_id
            data1.customer = customer
            data1.save()

            all_subtotal = 0

            #save items
            for f in purchase_request_item_formset:
                qty = f.cleaned_data['qty']
                if qty > 0 : 
                    product = f.cleaned_data['product']
                    qty = f.cleaned_data["qty"]
                    return_item = f.cleaned_data["return_item"]                    
                    cost = product.cost
                    price = product.price                   
                    subtotal = (qty * price)
                    all_subtotal += subtotal

                    PurchaseRequestItem(
                        purchase_request = data1,
                        product = product,
                        qty = qty,
                        cost = cost,
                        price = price,                    
                        subtotal = subtotal,
                        return_item = return_item,
                    ).save()

            total = all_subtotal

            #update sale total,round_off and subtotal

            PurchaseRequest.objects.filter(pk=data1.pk).update(total=total)

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Purchase Request created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('sales:purchase_requests')
            }

        else:
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(purchase_request_item_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        initial = []
        distributor = None
        if Distributor.objects.filter(user=request.user).exists():
            distributor = Distributor.objects.get(user=request.user)
        items = DistributorStock.objects.filter(distributor=distributor,is_deleted=False)
        for item in items:
            estimate_dict = {
                'barcode': item.product.code,
                'product': item.product,
                'stock' : int(item.stock),
                'qty' : 0,
                'unit':item.product.unit,
                'price' : item.product.price,
            }
            initial.append(estimate_dict)

        estimate_form = PurchaseRequestForm()
        purchase_request_item_formset = PurchaseRequestItemFormset(prefix='purchase_request_item_formset',initial=initial)
        for form in purchase_request_item_formset:
            form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "title" : "Create Purchase Request ",
            "form" : estimate_form,
            "url" : reverse('sales:create_purchase_request'),
            "purchase_request_item_formset" : purchase_request_item_formset,
            "redirect" : True,
            "is_create_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'sales/estimate/entry_purchase_request.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase_request'],roles=['distributor'],both_check=False)
def purchase_requests(request):
    current_shop = get_current_shop(request)
    instances = PurchaseRequest.objects.filter(is_deleted=False,shop=current_shop)
    customers = Customer.objects.filter(is_deleted=False,shop=current_shop)

    current_role = get_current_role(request)
    if current_role == "distributor":
        instances =instances.filter(creator=request.user)
        customers = customers.filter(creator=request.user) 
        
    today = datetime.date.today()
    customer = request.GET.get('customer')
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

    if customer:
        instances = instances.filter(customer_id=customer)

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    if payment :
        if payment == "full":
            instances = instances.filter(balance=0)
        elif payment == "no":
            for instance in instances:
                payment_received = instance.payment_received
                if payment_received != 0:
                    instances = instances.exclude(pk = instance.pk)
        elif payment == "extra":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total >= payment_received:
                    instances = instances.exclude(pk=instance.pk)
        elif payment == "partial":
            for instance in instances:
                total = instance.total
                payment_received = instance.payment_received
                if total <= payment_received or payment_received == 0:
                    instances = instances.exclude(pk=instance.pk)

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
        'purchase_requests' :purchase_requests,
        'customers' : customers,
        "title" : 'PurchaseRequests',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "purchase_requests" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/estimate/purchase_requests.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase_request'],roles=['distributor'],both_check=False)
def purchase_request(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseRequest.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    purchase_request_items = PurchaseRequestItem.objects.filter(purchase_request=instance,is_deleted=False)
    context = {
        "instance" : instance,
        "title" : "purchase request : #" + str(instance.auto_id),
        "purchase_request_items" : purchase_request_items,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'sales/estimate/purchase_request.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_purchase_request'],roles=['distributor'],both_check=False)
def edit_purchase_request(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseRequest.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if PurchaseRequestItem.objects.filter(purchase_request=instance).exists():
        extra = 0
    else:
        extra= 1
    PurchaseRequestItemFormset = inlineformset_factory(
        PurchaseRequest,
        PurchaseRequestItem,
        can_delete = True,
        extra = extra,
        exclude=('creator','updator','auto_id','is_deleted','tax','cost','subtotal','purchase_request','tax_amount','tax_added_price','price'),
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
    )

    if request.method == 'POST':
        response_data = {}
        form = PurchaseRequestForm(request.POST,instance=instance)
        purchase_request_item_formset = PurchaseRequestItemFormset(request.POST,prefix='purchase_request_item_formset',instance=instance)

        if form.is_valid() and purchase_request_item_formset.is_valid():
            items = {}
            total_discount_amount = 0
            total_tax_amount = 0       

            customer_name = form.cleaned_data['customer_name']
            customer_address = form.cleaned_data['customer_address']
            customer_email = form.cleaned_data['customer_email']
            customer_phone = form.cleaned_data['customer_phone']
            customer = form.cleaned_data['customer']
            customer_state = form.cleaned_data['customer_state']
            if not customer:
                auto_id = get_auto_id(Customer)
                a_id = get_a_id(Customer,request)

                customer = Customer(
                    name = customer_name,
                    email = customer_email,
                    phone = customer_phone,
                    address = customer_address,
                    shop = current_shop,
                    first_time_credit = 0,
                    first_time_debit = 0,
                    credit = 0,
                    debit = 0,
                    creator = request.user,
                    updator = request.user,
                    auto_id = auto_id,
                    a_id = a_id,
                    state = customer_state
                )
                customer.save()

            gst_type = "sgst"
            if not customer.state == current_shop.state:
                gst_type = "igst"

            #update PurchaseRequest
            date = form.cleaned_data['time']
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.save()
            all_subtotal = 0

            #delete previous items and update stock
            previous_purchase_request_items = PurchaseRequestItem.objects.filter(purchase_request=instance)
            previous_purchase_request_items.delete()

            #save items
            for f in purchase_request_item_formset:
                product = f.cleaned_data['product']
                qty = f.cleaned_data['qty']
                price = product.price
                cost = product.cost
                return_item = f.cleaned_data["return_item"]
                subtotal = (qty * price)
                all_subtotal += subtotal

                PurchaseRequestItem(
                    purchase_request = data1,
                    product = product,
                    qty = qty,
                    cost = cost,
                    price = price,
                    subtotal = subtotal,
                    return_item = return_item
                ).save()

            total = all_subtotal
            rounded_total = Decimal(round(total))
            extra = Decimal(round(total)) - total
            round_off = Decimal(format(extra, '.2f'))

            PurchaseRequest.objects.filter(pk=data1.pk).update(total=total)

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "PurchaseRequest Successfully Updated.",
                "redirect" : "true",
                "redirect_url" : reverse('sales:purchase_request',kwargs={'pk':data1.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)
            message += generate_form_errors(purchase_request_item_formset,formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PurchaseRequestForm(instance=instance)
        purchase_request_item_formset = PurchaseRequestItemFormset(prefix='purchase_request_item_formset',instance=instance)
        for item in purchase_request_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop)
        context = {
            "form" : form,
            "title" : "Edit PurchaseRequest #: " + str(instance.auto_id),
            "instance" : instance,
            "url" : reverse('sales:edit_purchase_request',kwargs={'pk':instance.pk}),
            "purchase_request_item_formset" : purchase_request_item_formset,
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
        return render(request, 'sales/estimate/entry_purchase_request.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_purchase_request'],roles=['distributor'],both_check=False)
def delete_purchase_request(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseRequest.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    instance.is_deleted=True
    instance.save()

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "PurchaseRequest Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('sales:purchase_requests')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_purchase_request'],roles=['distributor'],both_check=False)
def delete_selected_purchase_requests(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(PurchaseRequest.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            instance.is_deleted=True
            instance.save()

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected PurchaseRequest(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('sales:purchase_requests')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_purchase_request(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseRequest.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    purchase_request_items = PurchaseRequestItem.objects.filter(purchase_request=instance)

    to_word = inflect.engine()
    total_in_words = to_word.number_to_words(instance.total)
    context = {
        "total_in_words":total_in_words,
        "instance" : instance,
        "title" : "PurchaseRequest : #" + str(instance.auto_id),
        "single_page" : True,
        "sale_items" : purchase_request_items,
        "current_shop" : get_current_shop(request),
        "is_need_wave_effect" : True,
    }
    template_name = 'sales/estimate/purchase_request_a4.html'
    return render(request,template_name,context)


@check_mode
@login_required
@shop_required
@check_salesman
@permissions_required(['can_create_sale'],roles=['distributor'],both_check=False)
def purchase_request_sale_create(request,pk):    
    current_shop = get_current_shop(request)
    SaleItemFormset = formset_factory(SaleItemForm,extra=1)
    today = datetime.datetime.today()
    purchase_request = get_object_or_404(PurchaseRequest.objects.filter(is_deleted=False,pk=pk))
    is_ok = True
    if purchase_request.is_created:
        is_ok = False

    if is_ok:
        if request.method == 'POST':
            form = SaleForm(request.POST)
            transaction_form = TransactionForm(request.POST)
            sale_item_formset = SaleItemFormset(request.POST,prefix='sale_item_formset')
            for sale_form in sale_item_formset:
                sale_form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            if form.is_valid() and sale_item_formset.is_valid() and transaction_form.is_valid():

                items = {}
                total_tax_amount = 0
                total_discount_amount = 0
                customer = form.cleaned_data['customer']
                if customer :
                    customer_discount = customer.discount
                else :
                    customer_discount = form.cleaned_data['customer_discount']

                for f in sale_item_formset:                

                    discount_amount = f.cleaned_data['discount_amount']
                    discount = f.cleaned_data['discount']
                    total_discount_amount += discount_amount
                    product = f.cleaned_data['product']
                    unit = f.cleaned_data['unit']
                    return_item = f.cleaned_data['return_item']
                    qty = f.cleaned_data['qty']
                    exact_qty = get_exact_qty(qty,unit)                
                   
                    price = f.cleaned_data['price']                

                    if customer_discount > 0 :    
                        actual_price = price-(discount_amount/qty)                
                        tax_added_price = price
                        tax_amount = 0
                        if not return_item:
                            tax_amount = qty * (((100*actual_price)/ (100+product.tax)) * product.tax / 100)
                    else :
                        product_tax_amount = price * product.tax / 100
                        tax_added_price = price + product_tax_amount
                        tax_amount = 0
                        if not return_item:
                            tax_amount = qty * (price - discount_amount) * product.tax / 100
                    tax_amount = Decimal(format(tax_amount, '.2f'))
                    total_tax_amount += tax_amount
                    if return_item:
                        new_pk = str(product.pk) +"_"+str(unit.pk)+"_" +str(return_item)
                    else:
                        new_pk = str(product.pk) + "_"+str(unit.pk)
                    if str(new_pk) in items:
                        p_unit = items[str(new_pk)]["unit"]
                        p_unit = Measurement.objects.get(pk=p_unit)
                        if p_unit == unit:
                            q = items[str(new_pk)]["qty"]
                            amount = items[str(new_pk)]["tax_amount"]
                            items[str(new_pk)]["qty"] = q + qty
                            items[str(new_pk)]["tax_amount"] = tax_amount + amount   
                            dis_amount = items[str(new_pk)]["discount_amount"] 
                            items[str(new_pk)]['discount_amount'] = discount_amount + dis_amount             
                        else:
                            dic = {
                                "qty" : qty,
                                "price" : price,
                                "tax_amount" : tax_amount,
                                "tax_added_price" : tax_added_price,
                                "discount_amount" : discount_amount,
                                "unit" : unit.pk,
                                "return_item" : return_item,
                                "discount" : discount
                            }
                            items[str(new_pk)] = dic
                    else:
                        dic = {
                            "qty" : qty,
                            "price" : price,
                            "tax_amount" : tax_amount,
                            "tax_added_price" : tax_added_price,
                            "discount_amount" : discount_amount,
                            "unit" : unit.pk,
                            "return_item" : return_item,
                            "discount" : discount
                        }
                        items[str(new_pk)] = dic

                stock_ok = True
                error_message = ''
                for key, value in items.iteritems():
                    product_pk = key.split("_")[0]
                    product_obj  = Product.objects.get(pk=product_pk)
                    stock = product_obj.stock
                    unit = Measurement.objects.get(pk=value['unit'])
                    exact_qty = get_exact_qty(value['qty'],unit)
                    if exact_qty > stock:
                        stock_ok = False                    
                        error_message += "%s is not in your stock." %(product_obj.name)           

                if stock_ok:

                    customer_name = form.cleaned_data['customer_name']
                    customer_address = form.cleaned_data['customer_address']
                    customer_email = form.cleaned_data['customer_email']
                    customer_phone = form.cleaned_data['customer_phone']
                    customer = form.cleaned_data['customer']
                    customer_state = form.cleaned_data['customer_state']
                    gstin = form.cleaned_data['gstin']
                    discount = form.cleaned_data['customer_discount']

                    if not customer:
                        auto_id = get_auto_id(Customer)
                        a_id = get_a_id(Customer,request)

                        customer = Customer(
                            name = customer_name,
                            email = customer_email,
                            phone = customer_phone,
                            address = customer_address,
                            gstin = gstin,
                            shop = current_shop,
                            first_time_credit = 0,
                            first_time_debit = 0,
                            credit = 0,
                            debit = 0,
                            creator = request.user,
                            updator = request.user,
                            auto_id = auto_id,
                            a_id = a_id,
                            state = customer_state,
                            discount = discount
                        )
                        customer.save()

                    gst_type = "sgst"
                    if not customer.state == current_shop.state:
                        gst_type = "igst"

                    auto_id = get_auto_id(Sale)
                    a_id = get_a_id(Sale,request)

                    customer_gstin_invoice_id = None
                    customer_non_gstn_invoice_id = None
                    if customer:
                        if customer.gstin:
                            sale_type = 'wholesale'
                            gst_sale = Sale.objects.filter(shop=current_shop,customer_gstin_invoice_id__isnull=False,is_deleted=False).order_by("-date_added")[:1]
                            customer_gstin_invoice_id = 1
                            for l in gst_sale:
                                if l.customer_gstin_invoice_id:
                                    customer_gstin_invoice_id = int(l.customer_gstin_invoice_id) + 1
                                    
                            invoice_id = "GA1"
                            last_sale = Sale.objects.filter(is_deleted=False,shop=current_shop,sale_type='wholesale').order_by("-date_added")[:1]
                            if last_sale:
                                invoice = last_sale[0].invoice_id[2:]
                                invoice_letter = last_sale[0].invoice_id[:2]
                                invoice = int(invoice) + 1 
                                invoice_id = invoice_letter +str(invoice)
                                sale_type = 'wholesale'
                            if today.month >=4:
                                if not Sale.objects.filter(shop=current_shop,is_deleted=False,time__year=today.year,time__month__gte=4,sale_type='wholesale').exists():
                                    invoice_id = "GA1"
                                    if last_sale:
                                        char = last_sale[0].invoice_id
                                        if not char[2].isdigit():
                                            c=char[1]
                                            ch = chr(ord(c) +1)
                                        else:
                                            ch = "A"

                                        invoice_id = "G" +ch +"1" 
                        else:
                            sale_type = 'retail'
                            non_gst_sale = Sale.objects.filter(shop=current_shop,customer_non_gstn_invoice_id__isnull=False,is_deleted=False).order_by("-date_added")[:1]
                            customer_non_gstn_invoice_id = 1
                            for l in non_gst_sale:
                                if l.customer_non_gstn_invoice_id:
                                    customer_non_gstn_invoice_id = int(l.customer_non_gstn_invoice_id) + 1
                                    
                            invoice_id = "NA1"
                            last_sale = Sale.objects.filter(is_deleted=False,shop=current_shop,sale_type='retail').order_by("-date_added")[:1]
                            if last_sale:
                                invoice = last_sale[0].invoice_id[2:]
                                invoice_letter = last_sale[0].invoice_id[:2]
                                invoice = int(invoice) + 1 
                                invoice_id = invoice_letter +str(invoice)
                                sale_type = 'retail'
                                
                            if today.month >=4:
                                if not Sale.objects.filter(shop=current_shop,is_deleted=False,time__year=today.year,time__month__gte=4,sale_type='retail').exists():
                                    invoice_id = "NA1"
                                    if last_sale:
                                        char = last_sale[0].invoice_id
                                        if not char[2].isdigit():
                                            c=char[1]
                                            ch = chr(ord(c) +1)
                                        else:
                                            ch = "A"
                                        invoice_id = "N" +ch +"1"

                    #create sale
                    special_discount = form.cleaned_data['special_discount']
                    payment_received = form.cleaned_data['payment_received']

                    date = form.cleaned_data['time']
                    distributor = Distributor.objects.get(user=purchase_request.creator)
                    data1 = form.save(commit=False)
                    data1.creator = request.user
                    data1.updator = request.user
                    data1.auto_id = auto_id
                    data1.shop = current_shop
                    data1.total_discount_amount = total_discount_amount
                    data1.total_tax_amount = total_tax_amount
                    data1.customer_gstin_invoice_id = customer_gstin_invoice_id
                    data1.customer_non_gstn_invoice_id = customer_non_gstn_invoice_id
                    data1.a_id = a_id
                    data1.gst_type = gst_type
                    data1.customer = customer
                    data1.invoice_id = invoice_id
                    data1.sale_type = sale_type
                    data1.distributor = distributor
                    data1.save()
                    #printinvoice_id

                    all_subtotal = 0
                    commission_amount = 0
                    return_item_total = 0

                    #save items
                    for key, value in items.iteritems():
                        product_pk = key.split("_")[0]
                        product = Product.objects.get(pk=product_pk)
                        qty = value["qty"]
                        price = value["price"]
                        tax = product.tax
                        discount = value["discount"]
                        tax_amount = value["tax_amount"]
                        unit = value["unit"]
                        unit = Measurement.objects.get(pk=unit)
                        exact_qty = get_exact_qty(qty,unit)
                        discount_amount = value["discount_amount"]
                        tax_added_price = value["tax_added_price"]
                        return_item = value['return_item']
                        cost = product.cost
                        batch_full_qty = 0
                        batch_full_cost = 0
                        if ProductBatch.objects.filter(product=product,shop=current_shop).exists():            
                            batch_instance = ProductBatch.objects.filter(product=product,shop=current_shop).exclude(qty=0).order_by('id')
                            
                            for batch in batch_instance : 
                                if batch_full_qty > qty :
                                    break;
                                else :
                                    balance_qty = qty - batch_full_qty
                                    batch_balance_qty = batch.qty - balance_qty 
                                    if batch_balance_qty >= 0 : 
                                        batch_full_cost += balance_qty * batch.cost
                                        batch_full_qty += balance_qty
                                        batch.qty = batch_balance_qty
                                        batch.save()
                                        ProductBatchHistory.objects.create(shop=current_shop,sale=data1,batch=batch,qty=balance_qty)  
                                        break;
                                    else :                                
                                        batch_full_qty += batch.qty
                                        batch_full_cost = batch.qty * batch.cost
                                        batch.qty = 0
                                        ProductBatchHistory.objects.create(shop=current_shop,sale=data1,batch=batch,qty=batch.qty) 
                                        batch.save()    

                        if batch_full_qty < qty :
                            balance_qty = qty - batch_full_qty
                            batch_full_cost += product.cost * balance_qty
                            batch_full_qty += balance_qty

                        cost = batch_full_cost / batch_full_qty

                        if customer_discount > 0 :
                            subtotal = (qty * price) - discount_amount
                            price = (100*price)/(100+product.tax)
                        else :
                            subtotal = (qty * price) - discount_amount + tax_amount

                        if return_item:
                            return_item_total += subtotal
                        else:
                            commission_amount += qty * current_shop.commission_per_packet
                        all_subtotal += subtotal
                        SaleItem(
                            sale = data1,
                            product = product,
                            qty = qty,
                            cost = cost,
                            price = price,
                            tax = tax,
                            discount = discount,
                            tax_amount = tax_amount,
                            discount_amount = discount_amount,
                            subtotal = subtotal,
                            unit = unit,
                            tax_added_price = tax_added_price,
                            return_item = return_item,
                        ).save()

                        update_sock(product.pk,exact_qty,"decrease")                    

                    for key, value in items.iteritems():
                        product_pk = key.split("_")[0]
                        product = Product.objects.get(pk=product_pk)
                        stock = product.stock
                        low_stock_limit = product.low_stock_limit
                        if stock < low_stock_limit:
                            create_notification(request,'low_stock_notification',product)

                    credit=0
                    debit=0
                    customer_return_amount = 0
                    if customer:
                        if not customer.is_system_generated:
                            credit = customer.credit
                            debit = customer.debit
                            customer_return_amount = customer.return_amount
                            #print"credit from 5853 is:%s" %(credit)
                            #print"debit from 5854 is:%s" %(debit)


                    all_subtotal -= return_item_total                    

                    if current_shop.remove_previous_balance_from_bill:
                        total_total = all_subtotal - special_discount
                    else :
                        Customer.objects.filter(pk=customer.pk,is_deleted=False).update(credit=0,debit=0)
                        total = all_subtotal - special_discount + credit - debit
                        total_total = total
                    
                    this_sale_total = all_subtotal - special_discount

                    this_sale_rounded_total = round(this_sale_total)
                    this_sale_extra = round(this_sale_total) - float(this_sale_total)
                    this_sale_round_off = format(this_sale_extra, '.2f')

                    # This code for finding customer balance using all credits and debits till date.
                    rounded_total = round(total_total)
                    balance = rounded_total - float(payment_received)
                    balance = Decimal(balance)
                    #print"balance from 5876 is:%s" %(balance)

                    this_sale_balance = Decimal(this_sale_rounded_total) - payment_received

                    if this_sale_balance < 0 :
                            balance_amount = abs(this_sale_balance)
                            this_sale_balance = 0
                            prev_sales = Sale.objects.filter(customer=customer,is_deleted=False).exclude(balance=0).order_by('date_added')
                            for prev_sale in prev_sales: 
                                prev_balance = prev_sale.balance
                                prev_total = prev_sale.total                                                        
                                prev_collect_amount = prev_sale.collected_amount                            
                                new_balance = balance_amount 
                                balance_amount -= prev_balance
                                if balance_amount <= 0 :                        
                                    balance_amount = abs(balance_amount)
                                    prev_balance -= new_balance 
                                    prev_collect_amount += new_balance
                                    Sale.objects.filter(pk=prev_sale.pk).update(balance=prev_balance,collected_amount=prev_collect_amount)
                                    PaymentHistory(
                                        shop = current_shop,
                                        creator =request.user, 
                                        updator =request.user,
                                        auto_id = get_auto_id(PaymentHistory),
                                        a_id = get_a_id(PaymentHistory,request),
                                        payment_from = data1,
                                        payment_to = prev_sale,
                                        amount = new_balance
                                    ).save()
                                    break;
                                else :
                                    Sale.objects.filter(pk=prev_sale.pk).update(collected_amount=prev_total,balance = 0)
                                    PaymentHistory(
                                        shop = current_shop,
                                        creator =request.user, 
                                        updator =request.user,
                                        auto_id = get_auto_id(PaymentHistory),
                                        a_id = get_a_id(PaymentHistory,request),
                                        payment_from = data1,
                                        payment_to = prev_sale,
                                        amount = prev_balance
                                    ).save()

                    amount_from_return = 0
                    if return_item_total > 0:
                        return_balance = return_item_total - customer_return_amount

                        if this_sale_balance < 0:
                            this_sale_balance = 0

                        if return_balance  > 0:
                            amount_from_return = customer_return_amount
                            customer.return_amount = 0
                            customer.save()
                        else:
                            amount_from_return = return_item_total
                            customer.return_amount = abs(return_balance)
                            customer.save()

                    if not customer.is_system_generated:
                        #update credit
                        if balance > 0:
                            balance = balance
                            #print"balance from 5939 is:%s" %(balance)
                            update_customer_credit_debit(customer.pk,"credit",balance)
                        elif balance < 0:
                            #print"balance from 5942 is:%s" %(balance)
                            balance = abs(balance)
                            update_customer_credit_debit(customer.pk,"debit",balance)
                            balance = 0                           
                            
                    #update sale total,round_off and subtotal
                    data1.subtotal=all_subtotal
                    data1.total=rounded_total
                    data1.balance=balance
                    data1.round_off=this_sale_round_off
                    data1.payment_received = payment_received
                    data1.old_debit=debit
                    data1.old_credit=credit
                    data1.return_amount = amount_from_return
                    data1.commission_amount = commission_amount
                    data1.return_item_total = return_item_total
                    data1.save()
                    purchase_request.is_created = True
                    purchase_request.save()
                    # updating distributor commission amount
                    if not distributor.no_commission:
                        old_commission_tobe_paid = distributor.commission_tobe_paid
                        distributor.commission_tobe_paid = old_commission_tobe_paid + commission_amount
                        distributor.save()

                    amount = form.cleaned_data['payment_received']
                    if amount > 0:
                        add_transaction(request,transaction_form,data1,amount,"sale_payment","income",debit,credit)

                    response_data = {
                        "status" : "true",
                        "title" : "Successfully Created",
                        "message" : "Sale created successfully.",
                        "redirect" : "true",
                        "redirect_url" : reverse('sales:print',kwargs={'pk':data1.pk})
                    }
                else:
                    response_data = {
                        "status" : "false",
                        "stable" : "true",
                        "title" : "Out of Stock",
                        "message" : error_message
                    }

            else:
                message = generate_form_errors(form,formset=False)
                message += generate_form_errors(sale_item_formset,formset=True)
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Form validation error",
                    "message" : message
                }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        else:
            purchase_request = get_object_or_404(PurchaseRequest.objects.filter(is_deleted=False,pk=pk))
            purchase_request_items = PurchaseRequestItem.objects.filter(is_deleted=False,purchase_request=purchase_request)
            initial = []
            for item in purchase_request_items:
                estimate_dict = {
                    'barcode': item.product.code,
                    'product': item.product,
                    'stock' : int(item.product.stock),
                    'qty' : int(item.qty),
                    'unit':item.product.unit,
                    'price' : item.product.price,
                    'return_item' : item.return_item,
                }
                initial.append(estimate_dict)

            default_customer = Customer.objects.get(name="default",address="default",shop=current_shop)
            sale_form = SaleForm(initial={"customer" : purchase_request.customer,"sale_type" : "retail"})
            sale_item_formset = SaleItemFormset(prefix='sale_item_formset',initial=initial)
            for form in sale_item_formset:
                form.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
                form.fields['unit'].queryset = Measurement.objects.none()
                form.fields['unit'].label_from_instance = lambda obj: "%s" % (obj.code)
            transaction_form = TransactionForm()
            transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False,user=request.user)
            transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
            context = {
                "title" : "Create Sale ",
                "form" : sale_form,
                "transaction_form" : transaction_form,
                "url" : reverse('sales:purchase_request_sale_create',kwargs={'pk':pk}),
                "sale_item_formset" : sale_item_formset,
                "redirect" : True,
                "is_create_page" : True,
                "is_purchase_request" : True,

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,
            }
            return render(request,'sales/entry.html',context)
    else:
        instances = PurchaseRequest.objects.filter(is_deleted=False)
        context = {
            "title" : "Purchase Requests",
            "instances" : instances,
            "message" : "This request already changed to sale",
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'sales/estimate/purchase_requests.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_transaction'],roles=['distributor'],both_check=False)
def cheque_lists(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request) 
    title = "Cheque Lists"
    instances = Transaction.objects.filter(is_deleted=False,shop=current_shop,payment_mode="cheque_payment").order_by('-a_id')   

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
    return render(request,'sales/estimate/cheque_lists.html',context) 


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_view_transaction'],roles=['distributor'],both_check=False)
def cheque_withdraw(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    instance.is_cheque_withdrawed=True
    instance.save()

    response_data = {
        "status" : "true",
        "title" : "Successfully withdrawed",
        "message" : "Cheque Successfully withdrawed.",
        "redirect" : "true",
        "redirect_url" : reverse('sales:cheque_lists')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_view_transaction'],roles=['distributor'],both_check=False)
def cheque_return(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    return_charge = instance.bank_account.cheque_return_charge
    amount = instance.amount
    total = amount + return_charge
    if instance.customer and instance.transaction_type == 'income' :
        update_customer_credit_debit(instance.customer.pk,"credit",total)

    instance.is_cheque_returned=True
    # instance.payment_to = None
    # instance.bank_account = None
    # instance.cash_account = None
    instance.save()

    response_data = {
        "status" : "true",
        "title" : "Successfully Returned",
        "message" : "Cheque Successfully Returned.",
        "redirect" : "true",
        "redirect_url" : reverse('sales:cheque_lists')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase_request_returns'],roles=['distributor'],both_check=False)
def purchase_request_returns(request):
    current_shop = get_current_shop(request)
    instances = PurchaseRequestItem.objects.filter(is_deleted=False,purchase_request__shop=current_shop,return_item=True)
    customers = Customer.objects.filter(is_deleted=False,shop=current_shop)

    current_role = get_current_role(request)
    if current_role == "distributor":
        instances =instances.filter(purchase_request__creator=request.user)
        
    today = datetime.date.today()
    customer = request.GET.get('customer')
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

    if customer:
        instances = instances.filter(purchase_request__customer_id=customer)

    if year:
        instances = instances.filter(purchase_request__time__year=year)

    if month:
        instances = instances.filter(purchase_request__time__month=month)

    
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
            instances = instances.filter(purchase_request__time__year=today.year)
        elif period == 'month' :
            instances = instances.filter(purchase_request__time__year=today.year,purchase_request__time__month=today.month)
        elif period == "today" :
            instances = instances.filter(purchase_request__time__year=today.year,purchase_request__time__month=today.month,time__day=today.day)

    elif filter_date_period:
        title = "Report : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, purchase_request__time__range=[from_date, to_date])

    elif date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(purchase_request__time__month=date.month,purchase_request__time__year=date.year,purchase_request__time__day=date.day)
    context = {
        'instances': instances,
        'customers' : customers,
        "title" : 'PurchaseRequests',

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
    return render(request,'sales/estimate/purchase_request_returns.html',context)

