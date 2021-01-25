from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from sales.models import Sale, SaleItem,CollectAmount,SaleReturn,SaleReturnItem,DamagedProduct,ReturnableProduct,\
    ProductReturn,ProductReturnItem,CustomerPayment,Estimate,EstimateItem
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required, role_required
from main.functions import generate_form_errors, get_auto_id, get_timezone, get_a_id, get_current_role
from finance.functions import add_transaction
from finance.forms import BankAccountForm, CashAccountForm, TransactionCategoryForm, TransactionForm
from finance.models import BankAccount, CashAccount, TransactionCategory, Transaction, TaxCategory
from purchases.models import Purchase,PurchaseItem
import datetime
from django.db.models import Q
from dal import autocomplete
from django.forms.models import inlineformset_factory
from products.models import Product,Category,Measurement,ProductAlternativeUnitPrice
from main.functions import render_to_pdf
from django.utils import timezone
import pytz
from users.functions import get_current_shop, send_email,create_notification
from customers.models import Customer
from purchases.models import Purchase
from decimal import Decimal
from django.db.models import Sum
import xlwt
import urllib
from django.conf import settings
from django.core import serializers
from reports.forms import ReportForm,DailyReportForm,DistributorReportForm,MaufactureReportForm,CollectAmountReportForm,PerformanceReportForm,CustomerReportForm,ReturnReportForm
import calendar
from calendar import monthrange
from distributors.models import Distributor,DistributorStock


@check_mode
@login_required
@shop_required
@permissions_required(['sale_report'])
def create_sale_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = ReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Sale Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['sale_report'])
def sale_report(request):
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
        if not month == '0' :
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
                cost = item.product.cost
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
        "sales_total" : sales_total + total_special_discount + total_discount,
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
        if not month == '0' :
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
        if not month == '0' :
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
    category = request.GET.get('category')
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
        if not month == '0' :
            instances = instances.filter(time__month=month)
    if category:
        if category == 'bb':
            instances = instances.exclude(customer__gstin="")
        elif category == 'bc':
            instances = instances.filter(customer__gstin='')


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


def gstr1(request):
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
        if not month == '0' :
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
    return render(request,'sales/gstr1.html',context)


@check_mode
@login_required
@shop_required
def create_daily_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    form = DailyReportForm(initial={'date':today})

    context = {
        'title' : "Create Daily Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_daily_report.html',context)


@check_mode
@login_required
@shop_required
def print_daily_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()  
    date = request.GET.get('date')

    sales_count = 0
    sales_total = 0
    final_discount_amount = 0
    payment_received_total = 0
    balance_total = 0
    total_tax_amount_total = 0
    total_payable_tax_amount = 0 
    total_collected_amount = 0
    total_return_amount = 0
    title = "Day Report"
    expenses = Transaction.objects.filter(shop=current_shop,transaction_type="expense",is_deleted=False,creator=request.user,)
    incomes = Transaction.objects.filter(shop=current_shop,transaction_type="income",is_deleted=False,creator=request.user)
    tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
    expense_category = TransactionCategory.objects.filter(is_deleted=False).values_list('name',flat=True)
    bank_instances = Transaction.objects.filter(is_deleted=False,cash_account=None,creator=request.user)
    cash_instances = Transaction.objects.filter(is_deleted=False,bank_account=None,creator=request.user)
    collect_amounts = CollectAmount.objects.filter(shop=current_shop,is_deleted=False,creator=request.user)
    counter = 0
    tax_percentage_dict = {}    
    total_sale_taxable_amount = 0
    daily_report = {}
    expense_dict = {}

    total_sale_count = 0
    total_sale_amount = 0
    total_payable_tax = 0
    total_taxable_amount = 0
    total_tax_amount = 0
    total_payment_received = 0
    total_balance = 0
    total_special_discount = 0
    special_discount = 0
    total_expense = 0
    total_income = 0
    total_other_income = 0
    total_commission_amount = 0
    cheque_payment_total = 0
    collected_cheque_payment_total = 0

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"
    expenses = expenses.filter(transaction_category__name__in=expense_category,date__year=date.year, date__month=date.month, date__day=date.day).exclude(transaction_category__name='salereturn_payment')
    incomes = incomes.filter(date__year=date.year, date__month=date.month, date__day=date.day)
    other_incomes = incomes.filter(date__year=date.year, date__month=date.month, date__day=date.day).exclude(transaction_category__name='sale_payment')
    collect_amounts = collect_amounts.filter(date__month=date.month,date__year=date.year,date__day=date.day)
    # Distributor Details
    total_distributor_income = 0
    total_distributor_bank_amount = 0
    total_distributor_cash_amount = 0  

    for expense in expenses :
        if str(expense.transaction_category.pk) in expense_dict:                   
            t_amount = expense_dict[str(expense.transaction_category.pk)]['amount']
            expense_dict[str(expense.transaction_category.pk)]['amount'] = t_amount + expense.amount

        else:
            dic = {
                "amount" : expense.amount,
                "name" : expense.transaction_category.name,
            }
            expense_dict[str(expense.transaction_category.pk)] = dic

    
    if expenses :
        total_expense = expenses.aggregate(amount=Sum('amount')).get('amount',0)
    if incomes :
        total_income = incomes.aggregate(amount=Sum('amount')).get('amount',0)
    if other_incomes :
        total_other_income = other_incomes.aggregate(amount=Sum('amount')).get('amount',0)
    if bank_instances:
        total_distributor_bank_amount = bank_instances.aggregate(amount=Sum('amount')).get('amount',0)
    if cash_instances:
        total_distributor_cash_amount = cash_instances.aggregate(amount=Sum('amount')).get('amount',0)   

    total_distributor_balance_amount = total_income - total_expense 
    instances = None
    if collect_amounts : 
        for collect_amount in collect_amounts :
            total_collected_amount += collect_amount.collect_amount 
            if Transaction.objects.filter(collect_amount=collect_amount,transaction_mode="bank").exists() :
                    sale_transaction = Transaction.objects.filter(collect_amount=collect_amount,transaction_mode="bank")
                    collected_cheque_payment_total += collect_amount.collect_amount 
        # total_collected_amount = collect_amounts.aggregate(collect_amount=Sum('collect_amount')).get('collect_amount',0)  

    if Sale.objects.filter(distributor__user=request.user,shop=current_shop,is_deleted=False,time__month=date.month,time__year=date.year,time__day=date.day).exists():
        instances = Sale.objects.filter(distributor__user=request.user,shop=current_shop,is_deleted=False,time__month=date.month,time__year=date.year,time__day=date.day)
        sale_items = SaleItem.objects.filter(sale__in=instances,sale__shop=current_shop,sale__is_deleted=False)
        sales_count = instances.count()
        
        if instances :
            for instance in instances:
                sale_items = SaleItem.objects.filter(sale=instance)
                subtotal = 0
                total_taxable_amount = 0
                count = 0
                full_total = 0
                total_tax_amount = 0
                for sale_item in sale_items:
                    cost = sale_item.product.cost
                    price = sale_item.price
                    tax = sale_item.tax
                    cost_tax_amount = (((100*cost)/(100+tax)) * tax )/100
                    price_tax_amount = (price * tax )/100
                    qty = sale_item.qty
                    payable_tax_amount = (price_tax_amount - cost_tax_amount) * qty

                    tax_amount = sale_item.tax_amount  
                    subtotal = sale_item.subtotal
                    taxable_amount = subtotal - tax_amount
                    total_taxable_amount += taxable_amount
                    total_tax_amount += tax_amount
                    full_total += subtotal
                    total_payable_tax_amount += payable_tax_amount
                    count += 1
                    tax = sale_item.product.tax
                    if str(tax) in tax_percentage_dict:                   
                        t_amount = tax_percentage_dict[str(tax)]['tax_amount']
                        tax_percentage_dict[str(tax)]['tax_amount'] = t_amount + tax_amount

                        tb_amount = tax_percentage_dict[str(tax)]['taxable_amount']
                        tax_percentage_dict[str(tax)]['taxable_amount'] = tb_amount + taxable_amount

                    else:
                        dic = {
                            "tax_amount" : tax_amount,
                            "taxable_amount" : taxable_amount,
                        }
                        tax_percentage_dict[str(tax)] = dic

                total = instance.total
                payment_received = instance.payment_received
                balance = instance.balance
                special_discount = instance.special_discount
                commission_amount = instance.commission_amount

                sales_total += total
                total_commission_amount += commission_amount
                payment_received_total +=payment_received
                balance_total += balance
                total_tax_amount_total += total_tax_amount
                total_special_discount += special_discount 
                total_sale_taxable_amount += total_taxable_amount
                total_return_amount += instance.return_item_total
                if Transaction.objects.filter(sale=instance,first_transaction=True,transaction_mode="bank").exists() :
                    sale_transaction = Transaction.objects.filter(sale=instance,first_transaction=True,transaction_mode="bank")
                    cheque_payment_total += instance.payment_received
            

    context = {
        'title' : title,
        "today" : today,
        "date"  : date,
        "daily_report" : daily_report,
        "expenses" : expenses,
        "expense_dict" : expense_dict,

        "instances" : instances,
        "collect_amounts" : collect_amounts,
        "sales_count" : sales_count,
        "sales_total" : sales_total,
        "special_discount_total" : total_special_discount,
        "payment_received_total" : payment_received_total,
        "balance_total" : balance_total,
        "total_tax_amount_total" : total_tax_amount_total,
        "total_sale_taxable_amount" : total_sale_taxable_amount,
        "tax_percentage_dict" : tax_percentage_dict,
        "total_payable_tax_amount" : total_payable_tax_amount,
        "total_return_amount" : total_return_amount,

        "total_distributor_balance_amount" : total_distributor_balance_amount,
        "income_amount" : total_income,
        "expense_amount" : total_expense,
        "total_other_income" : total_other_income,
        "total_commission_amount" : total_commission_amount,
        "cheque_payment_total" : cheque_payment_total,
        "total_collected_amount" : total_collected_amount,
        "collected_cheque_payment_total" : collected_cheque_payment_total,


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
    return render(request,'reports/print_daily_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['distributor_report'])
def create_distributor_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = DistributorReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Distributor Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_distributor_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['distributor_report'])
def print_distributor_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()  
    date = request.GET.get('date')
    month = request.GET.get('month')
    year = request.GET.get('year')
    distributor = request.GET.get('distributor')
    sales_count = 0
    sales_total = 0
    total_customer_count = 0
    final_discount_amount = 0
    payment_received_total = 0
    balance_total = 0
    total_tax_amount_total = 0
    total_payable_tax_amount = 0 
    total_return_amount = 0
    title = "Day Report"
    expenses = Transaction.objects.filter(shop=current_shop,transaction_type="expense",is_deleted=False)
    incomes = Transaction.objects.filter(shop=current_shop,transaction_type="income",is_deleted=False)
    tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
    expense_category = TransactionCategory.objects.filter(is_deleted=False).values_list('name',flat=True)
    bank_instances = Transaction.objects.filter(is_deleted=False,cash_account=None)
    cash_instances = Transaction.objects.filter(is_deleted=False,bank_account=None)
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False)
    collect_amounts = CollectAmount.objects.filter(shop=current_shop,is_deleted=False)
    
    if distributor :
        distributor = Distributor.objects.get(pk=distributor)
        instances = Sale.objects.filter(distributor=distributor,shop=current_shop,is_deleted=False)
        expenses = Transaction.objects.filter(shop=current_shop,transaction_type="expense",is_deleted=False,creator=distributor.user)
        incomes = Transaction.objects.filter(shop=current_shop,transaction_type="income",is_deleted=False,creator=distributor.user)
        tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
        expense_category = TransactionCategory.objects.filter(is_deleted=False).values_list('name',flat=True)
        bank_instances = Transaction.objects.filter(is_deleted=False,cash_account=None,creator=distributor.user)
        cash_instances = Transaction.objects.filter(is_deleted=False,bank_account=None,creator=distributor.user)
        collect_amounts = CollectAmount.objects.filter(shop=current_shop,is_deleted=False,creator=distributor.user)

    counter = 0
    tax_percentage_dict = {}    
    total_sale_taxable_amount = 0
    daily_report = {}
    expense_dict = {}

    total_sale_count = 0
    total_sale_amount = 0
    total_payable_tax = 0
    total_taxable_amount = 0
    total_tax_amount = 0
    total_payment_received = 0
    total_balance = 0
    total_special_discount = 0
    special_discount = 0
    total_expense = 0
    total_income = 0
    total_other_income = 0
    total_commission_amount = 0
    profit_amount = 0
    return_subtotal = 0

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"
    if date :
        expenses = expenses.filter(transaction_category__name__in=expense_category,date__year=date.year, date__month=date.month, date__day=date.day).exclude(transaction_category__name='salereturn_payment')
        incomes = incomes.filter(date__year=date.year, date__month=date.month, date__day=date.day)
        other_incomes = incomes.filter(date__year=date.year, date__month=date.month, date__day=date.day).exclude(transaction_category__name='sale_payment')
        instances = instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)
        collect_amounts = collect_amounts.filter(date__month=date.month,date__year=date.year,date__day=date.day)
    else :
        if year:
            expenses = expenses.filter(transaction_category__name__in=expense_category,date__year=year).exclude(transaction_category__name='salereturn_payment')
            incomes = incomes.filter(date__year=year)
            other_incomes = incomes.filter(date__year=year).exclude(transaction_category__name='sale_payment')
            instances = instances.filter(time__year=year)       
            collect_amounts = collect_amounts.filter(date__year=year)       
        if month:
            if not month == '0' :
                expenses = expenses.filter(transaction_category__name__in=expense_category,date__month=month).exclude(transaction_category__name='salereturn_payment')
                incomes = incomes.filter(date__month=month)
                other_incomes = incomes.filter(date__month=month).exclude(transaction_category__name='sale_payment')    
                instances = instances.filter(time__month=month)
                collect_amounts = collect_amounts.filter(date__month=month)
    # Distributor Details
    total_distributor_income = 0
    total_distributor_bank_amount = 0
    total_distributor_cash_amount = 0  
    total_collected_amount = 0
    cheque_payment_total = 0
    collected_cheque_payment_total = 0

    for expense in expenses :
        if str(expense.transaction_category.pk) in expense_dict:                   
            t_amount = expense_dict[str(expense.transaction_category.pk)]['amount']
            expense_dict[str(expense.transaction_category.pk)]['amount'] = t_amount + expense.amount

        else:
            dic = {
                "amount" : expense.amount,
                "name" : expense.transaction_category.name,
            }
            expense_dict[str(expense.transaction_category.pk)] = dic

    
    if expenses :
        total_expense = expenses.aggregate(amount=Sum('amount')).get('amount',0)
    if incomes :
        total_income = incomes.aggregate(amount=Sum('amount')).get('amount',0)
    if other_incomes :
        total_other_income = other_incomes.aggregate(amount=Sum('amount')).get('amount',0)
    if bank_instances:
        total_distributor_bank_amount = bank_instances.aggregate(amount=Sum('amount')).get('amount',0)
    if cash_instances:
        total_distributor_cash_amount = cash_instances.aggregate(amount=Sum('amount')).get('amount',0)   

    total_distributor_balance_amount = total_income - total_expense 
    if collect_amounts : 
        for collect_amount in collect_amounts :
            total_collected_amount += collect_amount.collect_amount 
            if Transaction.objects.filter(collect_amount=collect_amount,transaction_mode="bank").exists() :
                    sale_transaction = Transaction.objects.filter(collect_amount=collect_amount,transaction_mode="bank")
                    collected_cheque_payment_total += collect_amount.collect_amount

        # total_collected_amount = collect_amounts.aggregate(collect_amount=Sum('collect_amount')).get('collect_amount',0) 
    if Sale.objects.filter(shop=current_shop,is_deleted=False).exists():        
        sales_count = instances.count()
        total_customers = instances.values_list('customer', flat=True).distinct()
        total_customer_count = total_customers.count()
        if instances :
            for instance in instances:
                sale_items = SaleItem.objects.filter(sale=instance)
                subtotal = 0
                total_taxable_amount = 0
                count = 0
                full_total = 0                
                total_tax_amount = 0
                for sale_item in sale_items:
                    cost = sale_item.product.cost
                    price = sale_item.price
                    tax = sale_item.tax
                    cost_tax_amount = (((100*cost)/(100+tax)) * tax )/100
                    price_tax_amount = (price * tax )/100
                    qty = sale_item.qty
                    payable_tax_amount = (price_tax_amount - cost_tax_amount) * qty

                    tax_amount = sale_item.tax_amount  
                    subtotal = sale_item.subtotal
                    taxable_amount = subtotal - tax_amount
                    total_taxable_amount += taxable_amount
                    total_tax_amount += tax_amount
                    full_total += subtotal
                    total_payable_tax_amount += payable_tax_amount
                    count += 1
                    if sale_item.return_item:
                        qty = sale_item.qty
                        price = sale_item.price
                        discount_amount = sale_item.discount_amount
                        return_subtotal += (qty * price) - discount_amount
                    if not sale_item.return_item:
                        profit_price = sale_item.tax_added_price
                        profit = ((profit_price - (cost+sale_item.product.packing_charge)) * qty) - sale_item.discount_amount
                        profit_amount += profit

                    tax = sale_item.product.tax
                    if str(tax) in tax_percentage_dict:                   
                        t_amount = tax_percentage_dict[str(tax)]['tax_amount']
                        tax_percentage_dict[str(tax)]['tax_amount'] = t_amount + tax_amount

                        tb_amount = tax_percentage_dict[str(tax)]['taxable_amount']
                        tax_percentage_dict[str(tax)]['taxable_amount'] = tb_amount + taxable_amount

                    else:
                        dic = {
                            "tax_amount" : tax_amount,
                            "taxable_amount" : taxable_amount,
                        }
                        tax_percentage_dict[str(tax)] = dic
                if Transaction.objects.filter(sale=instance,first_transaction=True,transaction_mode="bank").exists() :
                    sale_transaction = Transaction.objects.filter(sale=instance,first_transaction=True,transaction_mode="bank")
                    cheque_payment_total += instance.payment_received
                total = float(instance.total)
                payment_received = instance.payment_received
                balance = instance.balance
                special_discount = instance.special_discount
                commission_amount = instance.commission_amount
                sales_total += total
                total_commission_amount += commission_amount
                payment_received_total +=payment_received
                balance_total += balance
                total_tax_amount_total += total_tax_amount
                total_special_discount += special_discount 
                total_sale_taxable_amount += total_taxable_amount
                total_return_amount += instance.return_item_total
    context = {
        'title' : title,
        "today" : today,
        "date"  : date,
        "daily_report" : daily_report,
        "expenses" : expenses,
        "expense_dict" : expense_dict,

        "instances" : instances,
        "collect_amounts" : collect_amounts,
        "sales_count" : sales_count,
        "total_customer_count" : total_customer_count,
        "sales_total" : sales_total,
        "special_discount_total" : total_special_discount,
        "payment_received_total" : payment_received_total,
        "balance_total" : balance_total,
        "total_tax_amount_total" : total_tax_amount_total,
        "total_sale_taxable_amount" : total_sale_taxable_amount,
        "tax_percentage_dict" : tax_percentage_dict,
        "total_payable_tax_amount" : total_payable_tax_amount,
        "cheque_payment_total" : cheque_payment_total,
        "total_return_amount" : total_return_amount,

        "total_distributor_balance_amount" : total_distributor_balance_amount,
        "income_amount" : total_income,
        "expense_amount" : total_expense,
        "total_other_income" : total_other_income,
        "total_commission_amount" : total_commission_amount,
        "profit_amount" : profit_amount,
        "total_collected_amount" : total_collected_amount,
        "collected_cheque_payment_total" : collected_cheque_payment_total,


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
    return render(request,'reports/print_distributor_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['manufacture_report'])
def create_manufacture_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = MaufactureReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Manufacture Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_manufacture_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['manufacture_report'])
def print_manufacture_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    product = request.GET.get('product')
    date = request.GET.get('date')
    count = 0
    total_making_charge = 0
    total_material_charge = 0
    total_total_amount = 0
    balance_total = 0
    total_packing_charge = 0
    total_label_charge = 0
    total_profit = 0
    total_loss = 0
    total_product_cost = 0
    title = "Manufacturing Report"
    counter = 0  
    date_error = "no"

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"

    if product :
        instances = instances.filter(work_order__product__product=product) 

    if date:
        if date_error == "no":
            title = "Manufacturing Report : Date : %s" %(str(date))
            instances = instances.filter(work_order__date_added__month=date.month,work_order__date_added__year=date.year,work_order__date_added__day=date.day)
    else :
        if year:
            instances = instances.filter(work_order__date_added__year=year)

        if month:
            if not month == '0' :
                instances = instances.filter(work_order__date_added__month=month)     

    count = instances.count()
    if instances:
        sales_dict = instances.aggregate(Sum('making_charge'),Sum('material_charge'),Sum('product_cost'),Sum('packing_charge'),Sum('label_charge'),Sum('profit'),Sum('loss'))
        total_making_charge = sales_dict['making_charge__sum']
        total_profit = sales_dict['profit__sum']
        total_loss = sales_dict['loss__sum']
        total_packing_charge = sales_dict['packing_charge__sum']
        total_label_charge = sales_dict['label_charge__sum']
        total_product_cost = sales_dict['product_cost__sum']
        total_material_charge = sales_dict['material_charge__sum']

    context = {
        'title' : title,
        "count" : count,

        "total_making_charge" : total_making_charge,
        "total_profit" : total_profit,
        "total_loss" : total_loss,
        "balance_total" : balance_total,
        "total_product_cost" : total_product_cost,
        "total_packing_charge" : total_packing_charge,
        "total_label_charge" : total_label_charge,
        "total_material_charge" : total_material_charge,

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
    return render(request,'reports/print_manufacture_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['monthly_report'])
def create_monthly_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = ReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Monthly Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_month_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['monthly_report'])
def print_monthly_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()  
    month = request.GET.get('month')
    year = request.GET.get('year')
    category = request.GET.get('category')
    days = monthrange(int(year),int(month))[1]
    sales_count = 0
    sales_total = 0
    final_discount_amount = 0
    payment_received_total = 0
    balance_total = 0
    total_tax_amount_total = 0
    total_payable_tax_amount = 0 
    title = "Sales Monthly Report"
    tax_categories = TaxCategory.objects.filter(shop=current_shop,is_deleted=False)
    counter = 0
    tax_percentage_dict = {}    
    total_sale_taxable_amount = 0
    daily_report = {}

    total_sale_count = 0
    total_sale_amount = 0
    total_payable_tax = 0
    total_tax_amount = 0
    total_payment_received = 0
    total_balance = 0
    total_special_discount = 0
    special_discount = 0
    full_total_tax_amount = 0
    all_total_taxable_amount = 0
    daily_special_discount = 0
    for day in range(days) :
        
        sales_total = 0
        payment_received_total = 0
        balance_total = 0
        total_tax_amount_total = 0
        special_discount = 0
        total_sale_taxable_amount = 0
        total_payable_tax_amount = 0
        tax_percentage_dict = {}
        day = day+1
        if Sale.objects.filter(shop=current_shop,is_deleted=False,time__month=month,time__year=year,time__day=day).exists():
            instances = Sale.objects.filter(shop=current_shop,is_deleted=False,time__month=month,time__year=year,time__day=day)
            if category:
                if category == 'bb':
                    instances = instances.exclude(customer__gstin="")
                elif category == 'bc':
                    instances = instances.filter(customer__gstin="")
            sale_items = SaleItem.objects.filter(sale__in=instances,sale__shop=current_shop,sale__is_deleted=False)
            sales_count = instances.count()
            
            if instances :
                for instance in instances:
                    sale_items = SaleItem.objects.filter(sale=instance)
                    subtotal = 0
                    total_taxable_amount = 0
                    count = 0
                    full_total = 0
                    total_tax_amount = 0
                    for sale_item in sale_items:
                        price = sale_item.price-sale_item.discount_amount
                        tax_amount = sale_item.tax_amount
                        subtotal = sale_item.subtotal
                        cost = sale_item.product.cost
                        tax = sale_item.tax
                        cost_tax_amount = (((100*cost)/(100+tax)) * tax )/100
                        price_tax_amount = (price * tax )/100
                        qty = sale_item.qty
                        payable_tax_amount = (price_tax_amount - cost_tax_amount) * qty

                        taxable_amount = subtotal - tax_amount
                        total_taxable_amount += taxable_amount
                        total_tax_amount += tax_amount
                        full_total += subtotal
                        count += 1
                        tax = sale_item.product.tax
                        if str(tax) in tax_percentage_dict:                   
                            t_amount = tax_percentage_dict[str(tax)]['tax_amount']
                            tax_percentage_dict[str(tax)]['tax_amount'] = t_amount + tax_amount

                            tb_amount = tax_percentage_dict[str(tax)]['taxable_amount']
                            tax_percentage_dict[str(tax)]['taxable_amount'] = tb_amount + taxable_amount
                        else:
                            dic = {
                                "tax_amount" : tax_amount,
                                "taxable_amount" : taxable_amount
                            }
                            tax_percentage_dict[str(tax)] = dic
                    instance.collected_amount
                    total = round(full_total) - float(instance.special_discount)
                    payment_received = instance.payment_received
                    balance = instance.balance
                    special_discount = instance.special_discount

                    sales_total += total
                    payment_received_total +=float(payment_received)
                    balance_total += balance
                    total_tax_amount_total += total_tax_amount
                    daily_special_discount += special_discount 
                    total_sale_taxable_amount += total_taxable_amount
                    total_payable_tax_amount += payable_tax_amount
                   
                report = {
                    "instances" : instances,
                    "sales_count" : sales_count,
                    "sales_total" : sales_total,
                    "special_discount_total" : final_discount_amount,
                    "payment_received_total" : payment_received_total,
                    "balance_total" : balance_total,
                    "total_tax_amount_total" : total_tax_amount_total,
                    "total_sale_taxable_amount" : total_sale_taxable_amount,
                    "tax_percentage_dict" : tax_percentage_dict,
                    "total_payable_tax_amount" : total_payable_tax_amount,
                }
                daily_report[day] = report

                total_sale_count += sales_count
                total_sale_amount += sales_total
                total_payment_received += payment_received_total
                total_balance += balance_total
                all_total_taxable_amount += total_sale_taxable_amount
                total_payable_tax += total_payable_tax_amount
                full_total_tax_amount += total_tax_amount_total
                total_special_discount += daily_special_discount

    total_tax_percentage_dict = {}
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False,time__month=month,time__year=year)
    if category:
        if category == 'bb':
            instances = instances.exclude(customer__gstin="")
        elif category == 'bc':
            instances = instances.filter(customer__gstin="")
    sale_items = SaleItem.objects.filter(sale__in=instances,sale__shop=current_shop,sale__is_deleted=False)
    for tax in tax_categories:
        tax_amount = 0                 
        items = sale_items.filter(product__tax_category=tax)        
        taxable_amount = 0
        for sale_item in items:
            price = sale_item.price
            tax_amount = sale_item.tax_amount
            # if sale_item.product.vendor_price > 0:
            #     p_price = sale_item.product.vendor_price
            #     price = (100*p_price)/(100+sale_item.product.tax)
            #     tax_amount = sale_item.qty * (p_price - price)

            if str(tax) in total_tax_percentage_dict:                   
                t_amount = total_tax_percentage_dict[str(tax)]
                total_tax_percentage_dict[str(tax)] = t_amount + tax_amount
            else:
                total_tax_percentage_dict[str(tax)] = tax_amount
        # if items :
        #     tax_amount = items.aggregate(tax_amount=Sum('tax_amount')).get("tax_amount",0)
        

    context = {
        'title' : title,
        "today" : today,
        "month_no" : month,
        "month" : calendar.month_name[int(month)],
        "year"  : year,
        "daily_report" : daily_report,

        "total_sale_count" : total_sale_count,
        "total_sale_amount" : total_sale_amount, 
        "total_payment_received" : total_payment_received, 
        "total_balance" : total_balance,
        "all_total_taxable_amount" : all_total_taxable_amount,
        "total_payable_tax" : total_payable_tax,
        "total_tax_amount" : full_total_tax_amount,
        "total_special_discount" : total_special_discount,
        "total_tax_percentage_dict" : total_tax_percentage_dict,


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
    return render(request,'reports/print_monthly_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['collect_amount_report'])
def create_collect_amount_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = CollectAmountReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Collect Amount Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_collect_amount_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['collect_amount_report'])
def print_collect_amount_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    date = request.GET.get('date')
    instances = Transaction.objects.filter(shop=current_shop,collect_amount__isnull=False)
    count = 0
    total_making_charge = 0
    total_material_charge = 0
    total_total_amount = 0
    balance_total = 0
    total_packing_charge = 0
    total_label_charge = 0
    total_profit = 0
    total_loss = 0
    total_product_cost = 0
    title = "Collect Amount Report"
    counter = 0  
    date_error = "no"

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes" 

    if date:
        if date_error == "no":
            title = "Collect Amount Report : Date : %s" %(str(date))
            instances = instances.filter(date__month=date.month,date__year=date.year,date__day=date.day)
    else :
        if year:
            instances = instances.filter(date__year=year)

        if month:
            if not month == '0' :
                instances = instances.filter(date__month=month)     

    count = instances.count()

    context = {
        'title' : title,
        "count" : count,

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
    return render(request,'reports/print_collect_amount_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['performance_report'])
def create_performance_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = PerformanceReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Performance Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_performance_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['performance_report'])
def print_performance_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    date = request.GET.get('date')
    distributor = request.GET.get('distributor')
    sale_type = request.GET.get('sale_type')
    instances = SaleItem.objects.filter(sale__is_deleted=False)
    products = Product.objects.filter(shop=current_shop,is_deleted=False)
    product_items = products
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

    if date:
        if date_error == "no":
            title = "performance Report : Date : %s" %(str(date))
            instances = instances.filter(sale__time__month=date.month,sale__time__year=date.year,sale__time__day=date.day)         

    if year:
        title = "Report : Year - %s" %(str(year))
        instances = instances.filter(sale__time__year=year)

    if month:
        if not month == "0" :
            instances = instances.filter(sale__time__month=month)    

    if distributor :
        distributor = Distributor.objects.get(is_deleted=False,pk=distributor)
        instances = instances.filter(sale__distributor=distributor)
        distributor_products = DistributorStock.objects.filter(distributor=distributor).values('product')
        products = products.filter(pk__in=distributor_products)

    items = {}
    for product in products :
        qty = instances.filter(product=product).aggregate(qty=Sum('qty')).get('qty',0)
        if not qty:
            qty = 0

        if str(product.pk) in items:
            q = items[str(product.pk)]["qty"]
            items[str(product.pk)]["qty"] = q + qty
        else:
            dic = {
                "name" : product.name,
                "qty" : Decimal(qty),
                "code" : product.code,
                "category" : product.category,
            }
            items[str(product.pk)] = dic



    from collections import OrderedDict
    if sale_type == 'top_selling' :
        perfrmance_list = OrderedDict(sorted(items.items(), key=lambda x: x[1]['qty'],reverse=True))  
    else :
        perfrmance_list = OrderedDict(sorted(items.items(), key=lambda x: x[1]['qty']))

    context = {
        'title' : title,
        "filter_date" : filter_date,
        "year" : year,
        "month" : month,
        "instances" : perfrmance_list,

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
    return render(request,'reports/print_performance_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['customer_report'])
def create_customer_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = CustomerReportForm(initial={'year':today.year})

    context = {
        'title' : "Create Customer Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_customer_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['customer_report'])
def print_customer_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    date = request.GET.get('date')
    customer = request.GET.get('customer')

    instances = Sale.objects.filter(customer=customer,shop=current_shop,is_deleted=False)
    sale_items = SaleItem.objects.filter(sale__customer=customer,sale__shop=current_shop,sale__is_deleted=False)
    sale_return_instances = SaleReturn.objects.filter(customer=customer,is_deleted=False,sale__shop=current_shop)
    collect_amount_instances = CollectAmount.objects.filter(customer=customer,is_deleted=False,shop=current_shop)
    transaction_instances = Transaction.objects.filter(customer=customer,is_deleted=False,shop=current_shop)

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
    total_return_amount_total = 0
    collect_amount_total = 0
    title = "Customer Report"
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
        sale_return_instances = sale_return_instances.filter(time__year=year)
        collect_amount_instances = collect_amount_instances.filter(date__year=year)
        transaction_instances = transaction_instances.filter(date__year=year)

    if month:
        if not month == '0' :
            instances = instances.filter(time__month=month)    
            sale_return_instances = sale_return_instances.filter(time__month=month) 
            collect_amount_instances = collect_amount_instances.filter(date__month=month) 
            transaction_instances = transaction_instances.filter(date__month=month) 

    if date:
        title = "Report : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)
            sale_return_instances = sale_return_instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)
            collect_amount_instances = collect_amount_instances.filter(date__month=date.month,date__year=date.year,date__day=date.day)
            transaction_instances = transaction_instances.filter(date__month=date.month,date__year=date.year,date__day=date.day)

    if instances:
        sale_items = sale_items.filter(sale__in=instances)
        sales_dict = instances.aggregate(Sum('total'),Sum('special_discount'),Sum('payment_received'),Sum('balance'),Sum('total_discount_amount'),Sum('total_tax_amount'),Sum('return_item_total'))     

        sales_total  = sales_dict['total__sum']
        balance_total = sales_dict['balance__sum']        
        total_tax_amount_total = sales_dict['total_tax_amount__sum']
        sales_count = instances.count()

        if sale_items:
            for item in sale_items:
                cost = item.product.cost
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
        total_return_amount_total = sales_dict['return_item_total__sum']

        payment_received_total = sales_dict['payment_received__sum']

        final_profit_amount = profit_amount - total_special_discount - total_discount        

    if collect_amount_instances:
        collect_dict = collect_amount_instances.aggregate(Sum('collect_amount'))
        collect_amount_total = collect_dict['collect_amount__sum']

    if sale_return_instances :
        sale_return_dict = sale_return_instances.aggregate(Sum('commission_deducted'),Sum('returnable_amount'))
        sale_return_commission_deducted = sale_return_dict['commission_deducted__sum']
        sale_return_returnable_amount = sale_return_dict['returnable_amount__sum']

    return_transaction_count = 0
    return_transaction_total = 0
    return_total = 0
    if transaction_instances :
        return_transactions = transaction_instances.filter(is_cheque_returned=True)
        return_transaction_count = return_transactions.count()
        return_total = return_transactions.aggregate(amount=Sum('amount')).get('amount',0)
        if not return_total:
            return_total = 0
        for return_transaction in return_transactions :
            if return_transaction.bank_account :
                return_transaction_total += return_transaction.bank_account.cheque_return_charge

    context = {
        'title' : title,
        "sales_count" : sales_count,
        "sales_total" : sales_total + total_special_discount + total_discount,
        "special_discount_total" : total_special_discount,
        "payment_received_total" : payment_received_total,
        "balance_total" : balance_total,
        "total_tax_amount_total" : total_tax_amount_total,
        "tax_percentage_dict" : tax_percentage_dict,
        "total_discount" : total_discount,
        "filter_date" : filter_date,
        "year" : year,
        "month" : month,
        "profit_amount" : round(final_profit_amount,2),
        "sale_return_returnable_amount" : sale_return_returnable_amount,
        "sale_return_commission_deducted" : sale_return_commission_deducted,
        "collect_amount_total" : collect_amount_total,
        "total_return_amount_total" : total_return_amount_total,
        "return_transaction_count" : return_transaction_count,
        "return_transaction_total" : return_transaction_total,
        "return_total" : return_total,

        "instances" : instances,
        "collect_amount_instances" : collect_amount_instances,
        "sale_return_instances" : sale_return_instances,

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
    return render(request,'reports/print_customer_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['return_report'])
def create_return_report(request):
    current_shop = get_current_shop(request)
    today = datetime.datetime.today()
    form = ReturnReportForm(initial={'year':today.year,'month':today.month})

    context = {
        'title' : "Create Return Report",
        "form" : form,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'reports/create_return_report.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['return_report'])
def print_return_report(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()  
    date = request.GET.get('date')
    month = request.GET.get('month')
    year = request.GET.get('year')
    distributor = request.GET.get('distributor')
    title = "Return Product Report"
    instances = Sale.objects.filter(shop=current_shop,is_deleted=False)
    
    if distributor :
        distributor = Distributor.objects.get(pk=distributor)
        instances = Sale.objects.filter(distributor=distributor,shop=current_shop,is_deleted=False)

    return_subtotal = 0
    total_sale_count = 0

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"
    if date :        
        instances = instances.filter(time__month=date.month,time__year=date.year,time__day=date.day)
    else :
        if year:            
            instances = instances.filter(time__year=year)             
        if month:  
            if not month == '0' :          
                instances = instances.filter(time__month=month)

    items = {}
    if Sale.objects.filter(shop=current_shop,is_deleted=False).exists():    
        if instances :
            for instance in instances:
                sale_items = SaleItem.objects.filter(sale=instance)                
                for item in sale_items :
                    if item.return_item :
                        return_item = True
                        qty = item.qty 
                        product = item.product                   
                        if str(product.pk) in items:
                            q = items[str(product.pk)]["qty"]
                            items[str(product.pk)]["qty"] = q + qty
                        else:
                            dic = {
                                "name" : product.name,
                                "qty" : Decimal(qty),
                                "code" : product.code,
                                "category" : product.category,
                            }
                            items[str(product.pk)] = dic            
                    
                        return_subtotal += qty

    context = {
        'title' : title,
        "today" : today,
        "date"  : date,
        "instances" : items,
        
        "total_return_amount" : return_subtotal,

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
    return render(request,'reports/print_return_report.html',context)