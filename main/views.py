from django.shortcuts import render
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, ajax_required,\
    check_account_balance
from customers.models import Customer
from sales.models import Sale, SaleReturn, SaleItem
from purchases.models import Purchase
from products.models import Product
from main.forms import ShopForm
from main.functions import get_auto_id, generate_form_errors, promo_code_amount,\
    invite_code_amount, get_a_id, get_current_role
import json
from main.models import Shop, ShopAccess, App
from django.views.decorators.http import require_GET
from users.functions import get_current_shop, shop_access
from users.models import NotificationSubject, Notification
from django.db.models import Sum
from django.contrib.auth.models import Group
from products.models import Measurement
from finance.models import CashAccount, TransactionCategory, Transaction, CashTransfer
import datetime
from calendar import monthrange
from distributors.models import DistributorStock, Distributor
from django.utils import timezone
from vendors.models import Vendor
from purchases.models import Purchase, PurchaseItemSplit
from decimal import Decimal


@check_mode
@login_required
@shop_required
def app(request):
    return HttpResponseRedirect(reverse('dashboard'))


@check_mode
@login_required
@shop_required
def dashboard(request):
    today = datetime.date.today()
    current_shop = get_current_shop(request)
    recent_customers = Customer.objects.filter(shop=current_shop,is_deleted=False,is_system_generated=False,).order_by('-date_added')[:5]
    recent_sales = Sale.objects.filter(shop=current_shop,is_deleted=False).order_by('-date_added')[:5]
    recent_purchase = Purchase.objects.filter(shop=current_shop,is_deleted=False).order_by('-date_added')[:5]
    recent_products = Product.objects.filter(shop=current_shop,is_deleted=False).order_by('-date_added')[:5]

    current_role = get_current_role(request)
    product_stocks = []

    total_commission_amount = 0

    if current_role == "distributor":
        if Distributor.objects.filter(user=request.user):
            distributor = Distributor.objects.get(user=request.user)
        recent_sales = Sale.objects.filter(shop=current_shop,is_deleted=False,creator=request.user).order_by('-date_added')[:5]
        recent_customers = Customer.objects.filter(shop=current_shop,is_deleted=False,is_system_generated=False,creator=request.user).order_by('-date_added')[:5]
        product_stocks = DistributorStock.objects.filter(distributor__user=request.user)
        total_commission_amount = Sale.objects.filter(shop=current_shop,is_deleted=False,distributor=distributor).aggregate(amount=Sum('commission_amount')).get('amount',0)
        total_commission_deducted = SaleReturn.objects.filter(shop=current_shop,is_deleted=False,distributor=distributor).aggregate(amount=Sum('commission_deducted')).get('amount',0)
        
    context = {
        "title" : "Dashboard",
        "today" : today,
        "recent_customers" : recent_customers,
        "recent_sales" : recent_sales,
        "recent_purchase" :recent_purchase,
        "recent_products" : recent_products,
        "product_stocks" : product_stocks,

        "total_commission_amount" : total_commission_amount,

        "is_dashboard" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
        "is_dashboard" :True,
        "is_need_bootstrap_growl" : True,

    }
    return render(request,"base.html",context)


@check_mode
@login_required
@shop_required
@ajax_required
@require_GET
def reports(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request)
    total_bank_amount = 0
    total_cash_amount = 0
    
    if current_role == 'distributor':
        if Distributor.objects.filter(user=request.user):
            distributor = Distributor.objects.get(user=request.user)
        expenses = Transaction.objects.filter(shop=current_shop,transaction_type="expense",is_deleted=False,creator=request.user)
        incomes = Transaction.objects.filter(shop=current_shop,transaction_type="income",is_deleted=False,creator=request.user)
        sales = Sale.objects.filter(shop=current_shop,is_deleted=False,distributor=distributor)
        sale_returns = SaleReturn.objects.filter(shop=current_shop,is_deleted=False,distributor=distributor)
        bank_instances = Transaction.objects.filter(is_deleted=False,cash_account=None,creator=request.user)
        cash_instances = Transaction.objects.filter(is_deleted=False,bank_account=None,creator=request.user)
        
    else:
        expenses = Transaction.objects.filter(shop=current_shop,transaction_type="expense",is_deleted=False)
        incomes = Transaction.objects.filter(shop=current_shop,transaction_type="income",is_deleted=False)
        sales = Sale.objects.filter(shop=current_shop,is_deleted=False)
        sale_returns = SaleReturn.objects.filter(shop=current_shop,is_deleted=False)
        bank_instances = Transaction.objects.filter(is_deleted=False,cash_account=None)
        cash_instances = Transaction.objects.filter(is_deleted=False,bank_account=None)

    expense_category = TransactionCategory.objects.filter(is_deleted=False).values_list('name',flat=True)
    income_category = TransactionCategory.objects.filter(is_deleted=False).values_list('name',flat=True)

    cash_transfers = CashTransfer.objects.filter(shop=current_shop,is_deleted=False)
    purchase_expenses = Transaction.objects.filter(shop=current_shop,transaction_type="expense",transaction_category__name="purchase_payment",is_deleted=False)
    purchases = Purchase.objects.filter(shop=current_shop,is_deleted=False)
    total_vendors_count = Vendor.objects.filter(shop=current_shop,is_deleted=False).count()
    total_products_split = PurchaseItemSplit.objects.filter(purchase_item__purchase__shop=current_shop,purchase_item__purchase__is_deleted=False)

    if current_role == "distributor":
        expenses = expenses.filter(creator=request.user)
        incomes = incomes.filter(creator=request.user)
        sales = sales.filter(distributor=distributor)
        sale_returns = sale_returns.filter(distributor=distributor)    

    expense_category = TransactionCategory.objects.filter(is_deleted=False,shop=current_shop).values_list('name',flat=True)
    income_category = TransactionCategory.objects.filter(is_deleted=False,shop=current_shop).values_list('name',flat=True)

    customers = Customer.objects.filter(shop=current_shop,is_deleted=False)
    customer_credit_amount = 0
    customer_debit_amount = 0
    if customers:
        customer_dict = customers.aggregate(Sum('credit'),Sum('debit'))
        customer_credit_amount = customer_dict['credit__sum']
        customer_debit_amount = customer_dict['debit__sum']

    # Distributor Details 
    distributors = Distributor.objects.filter(shop=current_shop,is_deleted=False)
    distributor_stocks = DistributorStock.objects.filter(shop=current_shop,is_deleted=False)
    distributor_commission_amount = 0
    if distributors:
        distributor_dict = distributors.aggregate(Sum('commission_tobe_paid'))
        distributor_commission_amount = distributor_dict['commission_tobe_paid__sum']
    total_distributors =distributors.count()
    total_distributor_cost = 0
    total_distributor_price = 0  
    total_distributor_stock = 0
    if distributor_stocks :
        total_distributor_stock = distributor_stocks.aggregate(stock=Sum('stock')).get('stock',0)
        for distributor_stock in distributor_stocks :
            total_distributor_cost += distributor_stock.stock * distributor_stock.product.cost
            total_distributor_price += distributor_stock.stock * distributor_stock.product.price  

   
    month = request.GET.get('month')
    year = request.GET.get('year')
    today = timezone.now()
    date = request.GET.get('date')
    date_error = "no"
    period = request.GET.get('period')
    filter_period = None

    total_expense = 0
    total_income = 0
    monthly_profit = 0
    total_profit_monthly = 0

    this_period_expenses = []
    this_period_incomes = []
    date_list = []
    income_amounts = []
    expense_amounts = []
    this_period_work_order_checkouts = []
    this_period_purchases = []
    this_period_total_products_split = []
    this_period_purchase_expenses = []

    total_distributor_balance_amount = 0
    this_period_distributor_stocks = []

    #sales and purchase relation calculation for chart
    chart_purchases = Purchase.objects.filter(is_deleted=False,shop=current_shop)
    chart_sales = Sale.objects.filter(is_deleted=False,shop=current_shop)
    this_month = today.month
    this_year = today.year
    this_month = int(this_month)
    this_year = int(this_year)
    if this_month and this_year:
        title = "Report : " +  str(this_month) + " " + str(this_year)
        this_period_transaction_expense = expenses.filter(date__year=this_year,date__month=this_month)
        this_period_vendor_expense = expenses.filter(date__year=this_year,date__month=this_month,vendor__isnull=False)
        this_period_expenses = chart_purchases.filter(time__year=this_year,time__month=this_month)
        this_period_store_expenses = chart_store_item_purchases.filter(time__year=this_year,time__month=this_month)
        this_period_purchase_expenses = purchase_expenses.filter(date__year=this_year,date__month=this_month)
        this_period_incomes = chart_sales.filter(time__year=this_year,time__month=this_month)
        no_of_days = monthrange(this_year, this_month)[1]
        for i in range(1, no_of_days+1):
            date_obj = datetime.date(this_year, this_month, i)
            date_list.append(date_obj)

    if this_period_incomes:
        total_income = this_period_incomes.aggregate(total=Sum('total')).get('total',0)
        for date_list_obj in date_list:
            income_amount = 0
            if this_period_incomes.filter(time__date=date_list_obj).exists():
                income_amount = this_period_incomes.filter(time__date=date_list_obj).aggregate(total=Sum('total')).get('total',0)

            income_amounts.append(str(income_amount))

    if this_period_transaction_expense:
        total_expense = this_period_transaction_expense.aggregate(amount=Sum('amount')).get('amount',0)
        # if this_period_store_expenses:
        #     total_expense += this_period_store_expenses.aggregate(total=Sum('total')).get('total',0)
    total_vendor_expense = 0
    total_other_expense = 0
    if this_period_vendor_expense:
        total_vendor_expense = this_period_vendor_expense.aggregate(amount=Sum('amount')).get('amount',0)
        total_other_expense = total_expense - total_vendor_expense
    if this_period_expenses:
        for date_list_obj in date_list:
            expense_amount = 0
            store_expense_amount = 0
            if this_period_expenses.filter(time__date=date_list_obj).exists():
                expense_amount = this_period_expenses.filter(time__date=date_list_obj).aggregate(total=Sum('total')).get('total',0)
            if this_period_store_expenses.filter(time__date=date_list_obj).exists():
                store_expense_amount = this_period_store_expenses.filter(time__date=date_list_obj).aggregate(total=Sum('total')).get('total',0)
            expense_amounts.append(str(expense_amount+store_expense_amount))

    counter = 0
    for date_obj in date_list:
        date_list[counter] = str(date_obj.day)
        counter += 1

    total_amount = total_income + total_expense
    total_profit_monthly = total_income - total_expense

    income_percentage = 0
    expense_percentage = 0

    if total_amount > 0:
        income_percentage = total_income/total_amount * 100
        expense_percentage = total_expense/total_amount * 100

    total_creadit_debit_amount = customer_debit_amount + customer_credit_amount
    customer_debit_percentage = 0
    customer_credit_percentage = 0

    if total_creadit_debit_amount > 0:
        customer_debit_percentage = customer_debit_amount/total_creadit_debit_amount * 100
        customer_credit_percentage = customer_credit_amount/total_creadit_debit_amount * 100

    #total income and expense calculation
    if period:
        if period == "today" or period == "month" or period == "year":
            filter_period = period

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_date_period = False

    if from_date and to_date:
        try:
            from_date = datetime.datetime.strptime(from_date, '%m/%d/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%m/%d/%Y').date() + datetime.timedelta(days=1)
        except ValueError:
            date_error = "yes"

        filter_date_period = True    

    total_sales_created = 0
    total_sales_payment_amount_this_period = 0
    total_sales_amount_this_period = 0
    total_sales_amount = 0
    total_sales_payment_amount = 0
    total_special_discount = 0
    total_profit_amount = 0
    discount = 0
    current_balance = 0
    total_income_amount = 0
    total_profit = 0
    total_discount = 0
    total_sale_return_amount = 0
    this_period_total_expense_amount = 0
    total_other_income_amount = 0
    total_expense_amount = 0
    total_balance = 0
    payment_received = 0
    total_return_count = 0
    total_sales_collected_amount = 0
    this_period_total_transfer_amount = 0
    total_sale_return_cost = 0
    total_sale_return_paid_amount = 0
    total_profits = 0
    this_period_total_purchase_expense_amount = 0
    this_period_total_income_amount = 0
    full_expense_amount = 0
    return_item_total = 0
    cost_return_item_total = 0
    sale_return_qty = 0

    this_period_sales = []
    total_sales = []
    this_period_sale_returns = []
    this_period_total_income = []
    this_period_total_expense = []
    this_period_total_other_income = []
    this_period_work_order_checkouts = []
    this_period_purchases = []

    this_period_total_transfers = []

    this_period_total_expense = expenses
    if filter_period:
        if period == "today":
            title = "Today"
            this_period_sales = sales.filter(time__year=today.year, time__month=today.month, time__day=today.day)
            this_period_sale_returns = sale_returns.filter(time__year=today.year, time__month=today.month, time__day=today.day)
            this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__year=today.year, purchase_item__purchase__time__month=today.month, purchase_item__purchase__time__day=today.day)
            this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__year=today.year, work_order__date_added__month=today.month, work_order__date_added__day=today.day)
            this_period_purchases = purchases.filter(time__year=today.year, time__month=today.month, time__day=today.day)

            this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__year=today.year, date__month=today.month, date__day=today.day).exclude(transaction_category__name='salereturn_payment')
            this_period_purchase_expenses = purchase_expenses.filter(date__year=today.year, date__month=today.month, date__day=today.day)
            this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year, date__month=today.month, date__day=today.day)
            this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year, date__month=today.month, date__day=today.day,collect_amount__isnull=False)

            this_period_total_transfers = cash_transfers.filter(date_added__year=today.year, date_added__month=today.month, date_added__day=today.day)

            bank_instances = bank_instances.filter(date__year=today.year, date__month=today.month, date__day=today.day)
            cash_instances = cash_instances.filter(date__year=today.year, date__month=today.month, date__day=today.day)            

        elif period == "month":
            title = "This Month"

            title = "month"
            this_period_sales = sales.filter(time__year=today.year,time__month=today.month)
            this_period_sale_returns = sale_returns.filter(time__year=today.year,time__month=today.month)
            this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__year=today.year, purchase_item__purchase__time__month=today.month)
            this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__year=today.year, date__month=today.month).exclude(transaction_category__name='salereturn_payment')
            this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year, date__month=today.month)
            this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year, date__month=today.month,collect_amount__isnull=False)
            this_period_total_transfers = cash_transfers.filter(date_added__year=today.year,date_added__month=today.month)
            this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__year=today.year, work_order__date_added__month=today.month)
            this_period_purchases = purchases.filter(time__year=today.year, time__month=today.month)
            this_period_purchase_expenses = purchase_expenses.filter(date__year=today.year, date__month=today.month)

            bank_instances = bank_instances.filter(date__year=today.year, date__month=today.month)
            cash_instances = cash_instances.filter(date__year=today.year, date__month=today.month)

        elif period == "year":
            title = "This Year"
            title = "year"

            this_period_sales = sales.filter(time__year=today.year)
            this_period_sale_returns = sale_returns.filter(time__year=today.year)
            this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__year=today.year)
            this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__year=today.year).exclude(transaction_category__name='salereturn_payment')
            this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year)
            this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year,collect_amount__isnull=False)
            this_period_total_transfers = cash_transfers.filter(date_added__year=today.year)
            this_period_purchase_expenses = purchase_expenses.filter(date__year=today.year)
            this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__year=today.year)
            this_period_purchases = purchases.filter(time__year=today.year)

            bank_instances = bank_instances.filter(date__year=today.year)
            cash_instances = cash_instances.filter(date__year=today.year) 

    elif filter_date_period:
        if date_error == "yes":
            response_data = {
                'message' : date_error
            }
            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        else:
            this_period_sales = sales.filter(time__range=[from_date, to_date])
            this_period_sale_returns = sale_returns.filter(time__range=[from_date, to_date])

            this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__range=[from_date, to_date]).exclude(transaction_category__name='salereturn_payment')
            this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__range=[from_date, to_date])
            this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__range=[from_date, to_date],collect_amount__isnull=False)
            this_period_purchase_expenses = purchase_expenses.filter(date__range=[from_date, to_date])
            this_period_total_transfers = cash_transfers.filter(date_added__range=[from_date, to_date])
            this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__range=[from_date, to_date])

            this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__range=[from_date, to_date])
            this_period_purchases = purchases.filter(time__range=[from_date, to_date])

            bank_instances = bank_instances.filter(date__range=[from_date, to_date])
            cash_instances = cash_instances.filter(date__range=[from_date, to_date])

            to_date = to_date -  datetime.timedelta(days=1)
            title = from_date.strftime('%b %d %Y') + " to " + to_date.strftime('%b %d %Y')

    elif date:

        if date:
            try:
                date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
            except ValueError:
                date_error = "yes"
        title = str(date)

        this_period_sales = sales.filter(time__date=date)
        this_period_sale_returns = sale_returns.filter(time__date=date)

        this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date=date).exclude(transaction_category__name='salereturn_payment')
        this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date=date)
        this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date=date,collect_amount__isnull=False)

        this_period_total_transfers = cash_transfers.filter(date_added__date=date)
        this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__date=date)
        this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__date=date)
        this_period_purchases = purchases.filter(time__date=date)
        this_period_purchase_expenses = purchase_expenses.filter(date=date)

        bank_instances = bank_instances.filter(date__date=date)
        cash_instances = cash_instances.filter(date__date=date)

    elif month and year:
        title = str(month)

        this_period_sales = sales.filter(time__year=year,time__month=month)
        this_period_sale_returns = sale_returns.filter(time__year=year,time__month=month)
        this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__year=year, purchase_item__purchase__time__month=month)
        this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__year=year,date__month=month).exclude(transaction_category__name='salereturn_payment')
        this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__year=year,date__month=month)
        this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__year=year,date__month=month,collect_amount__isnull=False)

        this_period_total_transfers = cash_transfers.filter(date_added__year=year,date_added__month=month)

        this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__year=year, work_order__date_added__month=month)
        this_period_work_orders = work_orders.filter(date_added__year=year, date_added__month=month)
        this_period_purchases = purchases.filter(time__year=year, time__month=month)
        this_period_purchase_expenses = purchase_expenses.filter(date__year=year, date__month=month)

        bank_instances = bank_instances.filter(date__date=date,date__month=month)
        cash_instances = cash_instances.filter(date__date=date,date__month=month)

    elif month:
        title = str(month)

        this_period_sales = sales.filter(time__month=month)
        this_period_sale_returns = sale_returns.filter(time__month=month)
        this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__month=today.month)
        this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__month=month).exclude(transaction_category__name='salereturn_payment')
        this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__month=month)
        this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__month=month,collect_amount__isnull=False)

        this_period_total_transfers = cash_transfers.filter(date_added__month=month)
        this_period_purchase_expenses = purchase_expenses.filter(date_added__month=month)
        this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__month=month)
        this_period_work_orders = work_orders.filter(date_added__month=month)
        this_period_purchases = purchases.filter(time__month=month)

        bank_instances = bank_instances.filter(date__month=month)
        cash_instances = cash_instances.filter(date__month=month)

    elif year:
        title = str(year)
        this_period_sales = sales.filter(time__year=year)
        this_period_sale_returns = sale_returns.filter(time__year=year)
        this_period_total_products_split = total_products_split.filter(purchase_item__purchase__time__year=today.year)

        this_period_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__year=year).exclude(transaction_category__name='salereturn_payment')
        this_period_total_income = incomes.filter(transaction_category__name__in=income_category,date__year=year)
        this_period_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__year=year,collect_amount__isnull=False)
        this_period_purchase_expenses = purchase_expenses.filter(date_added__month=year)
        this_period_total_transfers = cash_transfers.filter(date_added__year=year)

        this_period_work_order_checkouts = work_order_checkouts.filter(work_order__date_added__year=year)
        this_period_work_orders = work_orders.filter(date_added__year=year)
        this_period_purchases = purchases.filter(time__year=year)

        bank_instances = bank_instances.filter(date__year=year)
        cash_instances = cash_instances.filter(date__year=year)    

    if this_period_sales:
        sale_items = SaleItem.objects.filter(sale__in=this_period_sales)        
        for sale_item in sale_items:
            customer_discount = sale_item.discount
            if not sale_item.return_item:
                if customer_discount > 0 :
                    price = sale_item.product.mrp
                else :
                    price = sale_item.tax_added_price
                cost = sale_item.product.cost
                qty = sale_item.qty
                discount = sale_item.discount_amount
                profit = ((price - (cost+sale_item.product.packing_charge)) * qty) - discount
                total_profit += profit
            else :                
                qty = sale_item.qty
                sale_return_qty += qty
                price = sale_item.price
                cost = sale_item.product.cost
                discount_amount = sale_item.discount_amount
                tax = sale_item.tax
                if customer_discount > 0 :
                    return_item_total += (qty * price) - discount_amount
                    cost_return_item_total += (qty * cost)
                else :
                    tax_amount = qty * (price - discount_amount) * tax / 100
                    return_item_total += (qty * price) - discount_amount + tax_amount
                    cost_return_item_total += (qty * cost)


        sales_dict = this_period_sales.aggregate(Sum('total'),Sum('special_discount'),Sum('payment_received'),Sum('balance'),Sum('total_discount_amount'),Sum('total_tax_amount'),Sum('collected_amount'),Sum('subtotal'))
        total_sales_amount  = sales_dict['total__sum']
        total_sales_collected_amount  = sales_dict['collected_amount__sum']

        total_sales_payment_amount = sales_dict['payment_received__sum']
        total_special_discount = sales_dict['special_discount__sum']
        total_discount = sales_dict['total_discount_amount__sum']
        total_balance = sales_dict['balance__sum']

        total_profits = total_profit - total_special_discount
        total_profit_amount += total_profits
        discount = total_special_discount

        total_sales_created = this_period_sales.count()
    if this_period_sale_returns:
        total_sale_return_amount = this_period_sale_returns.aggregate(amount=Sum('returnable_amount')).get('amount',0)
        total_return_count = this_period_sale_returns.count()
        for sale_return in this_period_sale_returns:
            total_sale_return_cost += sale_return.t()['total_cost']
            total_sale_return_paid_amount += sale_return.t()['return_amount']

    if this_period_total_transfers:
        this_period_total_transfer_amount = this_period_total_transfers.aggregate(amount=Sum('amount')).get('amount',0)

    if this_period_total_expense:
        this_period_total_expense_amount = this_period_total_expense.aggregate(amount=Sum('amount')).get('amount',0)
        

    if this_period_purchase_expenses:
        this_period_total_purchase_expense_amount = this_period_purchase_expenses.aggregate(amount=Sum('amount')).get('amount',0)

    if this_period_total_other_income:
        total_other_income_amount = this_period_total_other_income.aggregate(amount=Sum('amount')).get('amount',0)

    if this_period_total_income:
        this_period_total_income_amount = this_period_total_income.aggregate(amount=Sum('amount')).get('amount',0)


    if bank_instances:
        total_bank_amount = bank_instances.aggregate(amount=Sum('amount')).get('amount',0)

    if cash_instances:
        total_cash_amount = cash_instances.aggregate(amount=Sum('amount')).get('amount',0)


    work_order_checkout_dict ={}
    this_period_checkout_final_profit_loss = 0
    this_period_checkout_profit_amount = 0
    this_period_checkout_loss_amount = 0
    this_period_checkout_making_charge_amount = 0
    total_packing_charge_amount = 0
    total_label_charge_amount = 0
    if this_period_work_order_checkouts:
        work_order_checkout_dict = this_period_work_order_checkouts.aggregate(Sum('profit'),Sum('loss'),Sum('making_charge'),Sum('packing_charge'),Sum('label_charge'))

    if work_order_checkout_dict:
        this_period_checkout_loss_amount = work_order_checkout_dict['loss__sum']
        this_period_checkout_profit_amount = work_order_checkout_dict['profit__sum']
        total_packing_charge_amount = work_order_checkout_dict['packing_charge__sum']
        total_label_charge_amount = work_order_checkout_dict['label_charge__sum']
        this_period_checkout_making_charge_amount = work_order_checkout_dict['making_charge__sum']
        this_period_checkout_final_profit_loss = this_period_checkout_profit_amount -this_period_checkout_loss_amount

    work_orders_dict = {}
    total_work_orders_created = 0
    total_making_charge_amount = 0
    total_material_charge_amount = 0
    work_order_amount = 0
    if this_period_work_orders:
        work_orders_dict = this_period_work_orders.aggregate(Sum('making_charge'),Sum('material_charge'),Sum('total'))
        total_work_orders_created = this_period_work_orders.count()

    if work_orders_dict :
        total_making_charge_amount = work_orders_dict['making_charge__sum']
        total_material_charge_amount = work_orders_dict['material_charge__sum']
        work_order_amount = work_orders_dict['total__sum']

    purchases_dict = {}
    total_purchase_amount = 0
    total_purchase_balance_amount = 0
    total_purchase_paid_amount = 0
    total_purchases_count = 0
    if this_period_purchases:
        purchases_dict = this_period_purchases.aggregate(Sum('total'),Sum('balance'))
        total_purchases_count = this_period_purchases.count()

    if purchases_dict:
        total_purchase_balance_amount = purchases_dict['balance__sum']
        total_purchase_amount = purchases_dict['total__sum']
        total_purchase_paid_amount = total_purchase_amount - total_purchase_balance_amount

    product_split_packing_charge = 0
    products_split_dict = {}
    if this_period_total_products_split:
        products_split_dict = this_period_total_products_split.aggregate(Sum('packing_charge'))
        product_split_packing_charge = products_split_dict['packing_charge__sum']

    payment_received = total_sales_payment_amount
    total_income_amount = payment_received + total_other_income_amount
    if current_role == "distributor":
        total_sale_return_cost = total_sale_return_amount


    
    full_expense_amount = Decimal(total_sale_return_cost) + Decimal(this_period_total_expense_amount)

    current_balance = total_income_amount - this_period_total_expense_amount
    # total_profit_amount -= (this_period_total_expense_amount + Decimal(total_sale_return_cost)) - this_period_total_purchase_expense_amount

    total_completed_works = 0
    total_pending_works = 0
    if this_period_work_orders:
        total_completed_works = this_period_work_orders.filter(is_checkout=True).count()
        total_pending_works = this_period_work_orders.filter(is_checkout=False).count()

    final_making_charge_profit_loss = total_making_charge_amount - this_period_checkout_making_charge_amount

    # This Month Calculation
    sale_this_month_total_profit = 0
    this_month_total_monthly_expense_amount = 0
    total_monthly_sale_return_amount = 0
    total_monthly_sale_return_cost = 0
    this_month_total_monthly_purchase_expense_amount = 0
    distributor_commission_amount = 0
    total_monthly_profit_amount = 0
    this_month_total_special_discount = 0
    month_cost_return_item_total = 0
    month_return_item_total = 0
    monthly_sale_return_qty = 0 


    this_month_sales = []
    this_month_sale_returns = []
    this_month_total_expense = []
    this_month_total_income = []
    this_month_purchase_expenses = []

    this_month_sales = sales.filter(time__year=today.year,time__month=today.month)
    this_month_sale_returns = sale_returns.filter(time__year=today.year,time__month=today.month)
    this_month_total_expense = expenses.filter(transaction_category__name__in=expense_category,date__year=today.year, date__month=today.month).exclude(transaction_category__name='salereturn_payment')
    this_month_total_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year, date__month=today.month)

    this_month_total_other_income = incomes.filter(transaction_category__name__in=income_category,date__year=today.year, date__month=today.month,collect_amount__isnull=False)
    this_month_purchase_expenses = purchase_expenses.filter(date__year=today.year, date__month=today.month)
    if this_month_sales:
        sale_items = SaleItem.objects.filter(sale__in=this_month_sales)
        for sale_item in sale_items:
            if not sale_item.return_item:
                price = sale_item.price
                cost = sale_item.cost
                qty = sale_item.qty
                discount = sale_item.discount_amount

                profit = ((price - cost) * qty) - discount
                sale_this_month_total_profit += profit
            else :
                customer_discount = sale_item.discount
                qty = sale_item.qty
                monthly_sale_return_qty += qty
                price = sale_item.price
                cost = sale_item.cost
                discount_amount = sale_item.discount_amount
                tax = sale_item.tax
                if customer_discount > 0 :
                    month_return_item_total += (qty * price) - discount_amount
                    month_cost_return_item_total += (qty * cost) - discount_amount
                else :
                    tax_amount = qty * (price - discount_amount) * tax / 100
                    month_return_item_total += (qty * price) - discount_amount + tax_amount
                    month_cost_return_item_total += (qty * cost) - discount_amount + tax_amount

        sales_dict = this_month_sales.aggregate(Sum('total'),Sum('special_discount'),Sum('payment_received'),Sum('balance'),Sum('total_discount_amount'),Sum('total_tax_amount'),Sum('collected_amount'))        
        this_month_total_special_discount = sales_dict['special_discount__sum']

        total_profits = sale_this_month_total_profit - this_month_total_special_discount
        total_monthly_profit_amount += total_profits

    if this_month_sale_returns:
        total_monthly_sale_return_amount = this_month_sale_returns.aggregate(amount=Sum('returnable_amount')).get('amount',0)

        for sale_return in this_month_sale_returns:
            total_monthly_sale_return_cost += sale_return.t()['total_cost']
    total_monthly_income_amount = 0
    if this_month_total_expense:
        this_month_total_monthly_expense_amount = this_month_total_expense.aggregate(amount=Sum('amount')).get('amount',0)

    if this_month_purchase_expenses:
        this_month_total_monthly_purchase_expense_amount = this_month_purchase_expenses.aggregate(amount=Sum('amount')).get('amount',0)

    if this_month_total_income:
        total_monthly_income_amount = this_month_total_income.aggregate(amount=Sum('amount')).get('amount',0)

    payment_received = total_monthly_income_amount
    total_monthly_income_amount = payment_received
    if current_role == "distributor":
        total_monthly_sale_return_cost = total_monthly_sale_return_amount
    
    total_expense_amount = Decimal(total_monthly_sale_return_cost) + Decimal(this_month_total_monthly_expense_amount)
    total_monthly_balance = total_income - total_expense
    # total_monthly_balance = total_monthly_income_amount - this_month_total_monthly_expense_amount
    total_monthly_profit_amount -= (this_month_total_monthly_expense_amount + Decimal(total_monthly_sale_return_cost)) - this_month_total_monthly_purchase_expense_amount
   
    # Distributor Details
    total_distributor_sale_amount = 0
    total_distributor_sale_return_amount = 0
    total_distributor_expense = 0
    total_distributor_income = 0
    total_distributor_bank_amount = 0
    total_distributor_cash_amount = 0  
    if this_period_sales :
        distributor_sales = this_period_sales.filter(distributor__isnull=False)
        if distributor_sales:
            total_distributor_sale_amount = distributor_sales.aggregate(total=Sum('total')).get('total',0)
    if this_period_sale_returns:
        distributor_sale_returns = this_period_sale_returns.filter(distributor__isnull=False)
        total_distributor_sale_return_amount = distributor_sale_returns.aggregate(returnable_amount=Sum('returnable_amount')).get('returnable_amount',0)
    distributor_users = []
    for distributor in distributors:
        distributor_users.append(distributor.user)
    if this_period_total_expense :
        distributor_expenses = this_period_total_expense.filter(creator__in=distributor_users)
        total_distributor_expense = distributor_expenses.aggregate(amount=Sum('amount')).get('amount',0)

    if bank_instances.filter(creator__in=distributor_users).exists():
        total_distributor_bank_amount = bank_instances.filter(creator__in=distributor_users).aggregate(amount=Sum('amount')).get('amount',0)
    if cash_instances.filter(creator__in=distributor_users).exists():
        total_distributor_cash_amount = cash_instances.filter(creator__in=distributor_users).aggregate(amount=Sum('amount')).get('amount',0)

    distributor_incomes = []
    if this_period_total_income :
        distributor_incomes = this_period_total_income.filter(creator__in=distributor_users)
    if distributor_incomes:
        total_distributor_income = distributor_incomes.aggregate(amount=Sum('amount')).get('amount',0)

    total_distributor_balance_amount = total_distributor_sale_amount - this_period_total_transfer_amount
    if current_role == 'distributor':
        total_return_amount_by_sale =  return_item_total 
    else:
        total_return_amount_by_sale = cost_return_item_total
    result = {
        "status" : "true",
        "title" :title,
        "expense_amounts" : expense_amounts,
        "income_amounts" : income_amounts,
        "date_list" : date_list,

        "total_distributor_sale_amount" : str(round(total_distributor_sale_amount,2)),
        "total_distributor_sale_return_amount" : str(total_return_amount_by_sale),
        "total_distributors" : str(total_distributors),
        "total_distributor_cost" : str(round(total_distributor_cost,2)),
        "total_distributor_price" : str(round(total_distributor_price,2)),
        "total_distributor_stock" : str(total_distributor_stock),
        "total_distributor_expense" : str(total_distributor_expense),
        "total_distributor_income" : str(total_distributor_income),
        "total_transfer_amount" : str(round(this_period_total_transfer_amount,2)),
        "total_distributor_balance_amount" : str(round(total_distributor_balance_amount,2)),
        "full_expense_amount" : str(round(full_expense_amount,2)),

        "total_making_charge_amount" : str(total_making_charge_amount),
        "total_packing_charge_amount" : str(total_packing_charge_amount),
        "total_label_charge_amount" : str(total_label_charge_amount),
        "total_material_charge_amount" : str(total_material_charge_amount),
        "total_work_orders_created" : str(total_work_orders_created),
        "work_order_amount" : str(work_order_amount),
        "sale_total_balance" : str(total_balance),
        "total_sales_collected_amount" : str(total_sales_collected_amount),
        "total_purchase_amount" : str(total_purchase_amount),
        "total_purchase_paid_amount" : str(total_purchase_paid_amount),
        "total_purchases_count" : str(total_purchases_count),
        "total_purchase_balance_amount" : str(total_purchase_balance_amount),
        "total_sale_return_cost" : str(total_return_amount_by_sale),
        "sale_total_profit" : str(round(total_profits,2)),

        "product_split_packing_charge" : str(product_split_packing_charge),

        "total_vendors_count" : str(total_vendors_count),

        "this_period_checkout_loss_amount" : str(this_period_checkout_loss_amount),
        "this_period_checkout_final_profit_loss" : str(this_period_checkout_final_profit_loss),
        "this_period_checkout_profit_amount" : str(this_period_checkout_profit_amount),

        "total_expense" : str(total_expense),
        "total_income" : str(total_income),
        "expense_percentage" : str(expense_percentage),
        "income_percentage" : str(income_percentage),

        "total_pending_works" : str(total_pending_works),
        "total_completed_works" : str(total_completed_works),

        "final_making_charge_profit_loss" : str(final_making_charge_profit_loss),

        "customer_debit_amount" : str(customer_debit_amount),
        "customer_credit_amount" : str(customer_credit_amount),
        "customer_debit_percentage" : str(customer_debit_percentage),
        "customer_credit_percentage" : str(customer_credit_percentage),

        "total_income_amount" : str(total_income_amount),
        "total_profit_monthly" : str(total_profit_monthly),
        "total_expense_amount" : str(full_expense_amount),
        "total_sales_created" : str(total_sales_created),
        "total_sales_amount" : str(payment_received),
        "total_sales_amount_total" : str(total_sales_amount),
        "total_other_income" : str(total_other_income_amount),
        "total_sale_return_amount"  : str(round(total_sale_return_cost)),
        "total_return_count" : str(sale_return_qty),
        "this_period_total_expense_amount" : str(this_period_total_expense_amount),
        "total_monthly_profit_amount" : str(round(total_monthly_profit_amount,2)),
        "total_monthly_balance" : str(total_monthly_balance),
        "total_profit_amount" : str(round(total_profit_amount,2)),
        "current_balance" : str(current_balance),
        "this_period_total_transfer_amount" : str(this_period_total_transfer_amount),
        "total_vendor_expense" : str(total_vendor_expense),
        "total_other_expense" : str(total_other_expense)
    }

    return HttpResponse(json.dumps(result),content_type='text/plain')


def create_shop_request(request):
    context = {
        "title" : "Create Shop",

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'users/create_shop_request.html',context)


def download_app(request):
    app_list = App.objects.all()
    app = None
    file = None
    if app_list:
        app = app_list.latest('date_added')
        file = app.application.url
        if request.is_ajax():
            protocol = "http://"
            if request.is_secure():
                protocol = "https://"

            web_host = request.get_host()
            file_url = protocol + web_host + file

            response_data = {
                "status" : "true",
                "file_url" : file_url
            }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')
        else:
            return HttpResponseRedirect(file)
    else:
        return HttpResponse("File not uploaded.")


@check_mode
@login_required
def create_shop(request):

    if request.method == 'POST':
        form = ShopForm(request.POST,request.FILES)

        if form.is_valid():

            auto_id = get_auto_id(Shop)

            #create shop
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.save()

            Customer(
                auto_id = get_auto_id(Customer),
                a_id = get_a_id(Customer,request),
                shop = data,
                name = "default",
                address = "default",
                creator = request.user,
                updator= request.user,
                is_system_generated= True
            ).save()

            current_shop = data

            #create shop access

            group = Group.objects.get(name="administrator")
            is_default= True
            if ShopAccess.objects.filter(user=request.user).exists():
                is_default = False
            ShopAccess(user=request.user,shop=current_shop,group=group,is_accepted=True,is_default=is_default).save()

            request.session["current_shop"] = str(data.pk)

            # create initial product units
            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(
                code='CM',
                unit_type='distance',
                unit_name='centimeter',
                is_base=False,
                conversion_factor=0.01,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(
                code='MT',
                unit_type='distance',
                unit_name='meter',
                is_base=True,
                conversion_factor=0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='MM',
                unit_type='distance',
                unit_name='millimeter',
                is_base=False,
                conversion_factor=0.001,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='YD',
                unit_type='distance',
                unit_name='yard',
                is_base=False,
                conversion_factor=0.9144,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='IN',
                unit_type='distance',
                unit_name='inch',
                is_base=False,
                conversion_factor=0.0254,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='FT',
                unit_type='distance',
                unit_name='foot',
                is_base=False,
                conversion_factor=0.3048,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='SQ',
                unit_type='area',
                is_base=True,
                unit_name='square_feet',
                conversion_factor=0.0,
                shop=current_shop,
                creator=request.user,
                updator=request.user,
                auto_id=auto_id,
                a_id=a_id,
                is_system_generated=True
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='EA',
                unit_type='quantity',
                unit_name='each',
                is_base=True,
                conversion_factor=0.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='DZ',
                unit_type='quantity',
                unit_name='dozen',
                is_base=False,
                conversion_factor=12.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='HR',
                unit_type='time',
                unit_name='hour',
                is_base=False,
                conversion_factor=60.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='DY',
                unit_type='time',
                unit_name='day',
                is_base=False,
                conversion_factor=1440.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='MI',
                unit_type='time',
                unit_name='minute',
                is_base=True,
                conversion_factor=0.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='LI',
                unit_type='volume',
                unit_name='liter',
                is_base=True,
                conversion_factor=0.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='ML',
                unit_type='volume',
                unit_name='milliliter',
                is_base=False,
                conversion_factor=0.001,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='MG',
                unit_type='weight',
                unit_name='milligram',
                is_base=False,
                conversion_factor=.001,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='GR',
                unit_type='weight',
                unit_name='gram',
                is_base=False,
                conversion_factor=.001,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='LB',
                unit_type='weight',
                unit_name='pound',
                is_base=False,
                conversion_factor=0.453,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='KG',
                unit_type='weight',
                unit_name='kilogram',
                is_base=True,
                conversion_factor=1000.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id = get_auto_id(Measurement)
            a_id = get_a_id(Measurement,request)
            Measurement(code='BOX',
                unit_type='box',
                unit_name='box',
                is_base=True,
                conversion_factor=0.0,
                is_system_generated=True,
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(CashAccount)
            a_id = get_a_id(CashAccount,request)

            CashAccount.objects.create(
                auto_id=auto_id,
                a_id=a_id,
                shop=current_shop,
                name='General',
                user=request.user,
                creator=request.user,
                updator=request.user,
                first_time_balance=0,
                is_system_generated=True,
            )

            #create initial income categories

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="customer_payment",
                shop=current_shop,
                category_type="income",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="sale_payment",
                shop=current_shop,
                category_type="income",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="service_payment",
                shop=current_shop,
                category_type="income",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="service_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="vendor_payment",
                shop=current_shop,
                category_type="income",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="staff_payment",
                shop=current_shop,
                category_type="income",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="credit_user_payment",
                shop=current_shop,
                category_type="income",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="credit",
                category_type="income",
                shop=current_shop,
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="debit",
                category_type="income",
                shop=current_shop,
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="purchase_payment",
                category_type="income",
                shop=current_shop,
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            #create initital expense categories
            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="customer_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="vendor_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="purchase_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="staff_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="credit_user_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="debit",
                category_type="expense",
                shop=current_shop,
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="credit",
                category_type="expense",
                shop=current_shop,
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            auto_id=get_auto_id(TransactionCategory)
            a_id = get_a_id(TransactionCategory,request)
            TransactionCategory(
                auto_id = auto_id,
                a_id= a_id,
                name="salereturn_payment",
                shop=current_shop,
                category_type="expense",
                is_system_generated=True,
                creator=request.user,
                updator=request.user
            ).save()

            return HttpResponseRedirect(reverse('app'))

        else:
            print(form.errors)
            context = {
                "title" : "Create Shop",
                "form" : form,
                "url" : reverse('create_shop'),

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,
            }
            return render(request,'users/create_shop.html',context)
    else:
        form = ShopForm()
        context = {
            "title" : "Create Shop ",
            "form" : form,
            "url" : reverse('create_shop'),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'users/create_shop.html',context)


@login_required
@ajax_required
@require_GET
def switch_shop(request):
    pk = request.GET.get('pk')
    if Shop.objects.filter(creator=request.user,pk=pk,is_deleted=False).exists():
        request.session["current_shop"] = pk
        response_data = {}
        response_data['status'] = 'true'
        response_data['title'] = "Success"
        response_data['message'] = 'Shop switched successfully.'
    else:
        response_data = {}
        response_data['status'] = 'false'
        response_data['title'] = "No Access"
        response_data['stable'] = "true"
        response_data['message'] = 'You have no access to this shop.'

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
@require_GET
def switch_theme(request):
    current_shop = get_current_shop(request)
    theme = request.GET.get('pk')
    if theme:
        current_shop.theme = theme
        current_shop.save()
        response_data = {}
        response_data['status'] = 'true'
        response_data['title'] = "Success"
        response_data['message'] = 'Theme switched successfully.'
    else:
        response_data = {}
        response_data['status'] = 'false'
        response_data['title'] = "Something Wrong!!!"
        response_data['stable'] = "true"
        response_data['message'] = 'Sorry Try again later.'

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def delete_shop(request,pk):
    current_shop = get_current_shop(request)

    Shop.objects.filter(pk=current_shop.pk).update(is_deleted=True)
    request.session["current_shop"] = ''

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Shop Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('app')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

from reportlab.lib.units import mm, inch
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart


class MyBarcodeDrawing(Drawing):
    def __init__(self, text_value, *args, **kw):
        barcode = createBarcodeDrawing('Code128', value=text_value,  barHeight=.7*inch, barWidth = 1.6, humanReadable=True)
        Drawing.__init__(self,barcode.width,barcode.height,*args,**kw)
        self.add(barcode, name='barcode')


@login_required
def create_barcode(request,code):
    #instantiate a drawing object
    d = MyBarcodeDrawing(code)
    binaryStuff = d.asString('gif')
    return HttpResponse(binaryStuff, 'image/gif')


@check_mode
@login_required
def create_shop_request(request):
    context = {
        "title" : "Create Shop Request",

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'users/create_shop_request.html',context)