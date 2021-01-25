from django.shortcuts import render,get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse,HttpResponseRedirect
from purchases.forms import PurchaseForm, PurchaseItemForm,EmailPurchaseForm,\
EmailInvoiceForm,PurchaseInvoiceForm,PurchaseInvoiceItemForm,PaidAmountForm,CollectAmountsForm,\
AssetPurchaseItemForm,AssetPurchaseForm, PurchaseItemSplitForm
from purchases.models import Purchase, PurchaseItem,PaidAmount,CollectAmounts,PurchaseInvoice,\
    PurchaseInvoiceItem,AssetPurchaseItem,AssetPurchase, PurchaseCollectAmountHistory, PurchaseItemSplit
from products.models import Product,Asset,ProductExpiryDate
from vendors.models import Vendor
from main.models import Shop
from finance.forms import BankAccountForm, CashAccountForm, TransactionCategoryForm, TransactionForm
from finance.models import BankAccount, CashAccount, TransactionCategory, Transaction, Journel
from finance.models import TaxCategory
from finance.forms import TaxCategoryForm
from django.forms import formset_factory
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from products.models import Product,Measurement
from django.forms.widgets import TextInput,Select
from dal import autocomplete
from django.db.models import Q
import json
import datetime
from main.functions import get_auto_id, generate_form_errors, get_a_id
from django.template.loader import render_to_string
from users.functions import get_current_shop, send_email
from products.functions import update_sock,get_exact_qty
from decimal import Decimal
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date, time
from vendors.functions import update_vendor_credit_debit
from products.forms import ProductForm, ProductAlternativeUnitPriceForm, ProductExpiryForm, NewProductForm
from decimal import Decimal


class PurchaseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        purchases = Purchase.objects.filter(is_deleted=False)

        if self.q:
            purchases = Purchases.filter(Q(name__istartswith=self.q)
                                 )

        return purchases


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_purchase'])
def create_purchase(request):
    PurchaseItemFormset = formset_factory(PurchaseItemForm, extra=1)
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        purchase_item_formset = PurchaseItemFormset(request.POST,prefix='purchase_item_formset')

        for item in purchase_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)

        if form.is_valid() and purchase_item_formset.is_valid() and transaction_form.is_valid() :

            auto_id = get_auto_id(Purchase)
            a_id = get_a_id(Purchase,request)
            vendor = form.cleaned_data['vendor']
            special_discount = form.cleaned_data['special_discount']
            tax_category = form.cleaned_data['tax_category']
            tax_instance = None
            tax = 0
            if tax_category:
                tax_instance = get_object_or_404(TaxCategory.objects.filter(is_deleted=False,pk=tax_category.pk))
                tax = tax_instance.tax
            paid_amount = form.cleaned_data['paid_amount']
            date = form.cleaned_data['time']
            data1 = form.save(commit=False)
            data1.auto_id = auto_id
            data1.a_id = a_id
            data1.shop = current_shop
            data1.creator = request.user
            data1.updator = request.user
            data1.save()

            main_subtotal = 0
            for f in purchase_item_formset:
                product = f.cleaned_data['product']
                qty = f.cleaned_data['qty']
                unit = f.cleaned_data['unit']
                price = f.cleaned_data['price']
                selling_price = f.cleaned_data['selling_price']
                exact_qty = get_exact_qty(qty,unit)
                subtotal = (qty * price)
                main_subtotal += subtotal

                PurchaseItem(
                    purchase = data1,
                    product = product,
                    unit = unit,
                    qty = qty,
                    price = price,
                    selling_price = selling_price,
                    subtotal = subtotal,
                    qty_to_split = qty
                ).save()

                update_sock(product.pk,exact_qty,"increase")
                Product.objects.filter(pk=product.pk).update(vendor=vendor,price=selling_price,cost=price)

            credit=0
            debit=0
            if vendor:
                credit = vendor.credit
                debit = vendor.debit

            Vendor.objects.filter(pk=vendor.pk,is_deleted=False).update(credit=0,debit=0)
            tax_amount = main_subtotal * (tax / 100)
            non_credit_added_total = main_subtotal - special_discount + tax_amount
            main_total = non_credit_added_total - credit + debit
            balance = main_total - paid_amount
            balance = Decimal(balance)

            #update credit

            if balance > 0:
                balance = balance
                update_vendor_credit_debit(data1.vendor.pk,"debit",balance)
            elif balance < 0:
                balance = abs(balance)
                update_vendor_credit_debit(data1.vendor.pk,"credit",balance)
                balance = 0

            #update purchase
            vendor = Vendor.objects.get(pk=data1.vendor.pk)
            credit_amount_added = 0
            if credit > vendor.credit:
                credit_amount_added = credit - vendor.credit

            # If any old balance purchase exists , The extra amount will go to that purchase.
            if debit > vendor.debit:
                debit_amount = debit - vendor.debit
                payment_pending_purchases = Purchase.objects.filter(balance__gt=0,vendor=vendor,shop=current_shop,is_deleted=False).order_by('date_added')
                for payment_pending_purchase in payment_pending_purchases:

                    purchase_balance = payment_pending_purchase.balance

                    paid_amount_added = payment_pending_purchase.paid_amount_added

                    amount_added_to_purchase = 0
                    if purchase_balance > debit_amount:
                        amount_added_to_purchase = debit_amount
                        debit_amount = 0
                    else:
                        amount_added_to_purchase = purchase_balance
                        debit_amount -= purchase_balance

                    PurchaseCollectAmountHistory.objects.create(
                        purchase=payment_pending_purchase,
                        paid_from_purchase = data1,
                        amount = amount_added_to_purchase
                    )
                    payment_pending_purchase.paid_amount_added = paid_amount_added + amount_added_to_purchase
                    payment_pending_purchase.balance = purchase_balance - amount_added_to_purchase
                    payment_pending_purchase.save()

                    if debit_amount==0:
                        break

            data1.credit_amount_added = credit_amount_added
            data1.subtotal = main_subtotal
            data1.special_discount = special_discount
            data1.total = non_credit_added_total
            data1.balance = balance
            data1.tax = tax_amount
            data1.old_credit = credit
            data1.old_debit = debit
            data1.save()

            amount = form.cleaned_data['paid_amount']

            if amount > 0 :
                transaction_mode = transaction_form.cleaned_data['transaction_mode']
                payment_to = transaction_form.cleaned_data['payment_to']

                transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='purchase_payment',category_type="expense",is_deleted=False)[:1])
                transaction_category = transaction_categories.name
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
                            data.payment_to = None
                            data.bank_account = None
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
                    data.purchase = data1
                    data.shop = current_shop
                    data.first_transaction = True
                    data.save()

                    if transaction_mode == "cash":
                        cash_credit = amount
                        bank_credit = 0
                    elif transaction_mode == "bank":
                        cash_credit = 0
                        bank_credit = amount                    

                    Journel.objects.create(
                        date = date,
                        shop = current_shop,
                        cash_credit = cash_credit,
                        bank_credit = bank_credit,
                        transaction = data,
                        expense = amount,
                        purchase = data1
                    ) 
            new_window_url = reverse('products:create_barcode')
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Purchase created successfully.",                
                'new_redirect_window' : 'true',
                "new_window_url" : new_window_url
            }

        else:
            message = generate_form_errors(form, formset=False)
            #printform.errors
            #printpurchase_item_formset.errors
            #printtransaction_form.errors
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        product_form = NewProductForm(initial={'shop':current_shop})
        form = PurchaseForm()
        transaction_form = TransactionForm()
        purchase_item_formset = PurchaseItemFormset(prefix='purchase_item_formset')
        for item in purchase_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,unit_type="quantity",is_deleted=False)
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)

        AlternativeUnitFormset = formset_factory(ProductAlternativeUnitPriceForm,extra=1)
        alternative_unit_formset = AlternativeUnitFormset(prefix='alternative_unit_formset')
        for alternative_form in alternative_unit_formset:
            alternative_form.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,is_base=False,is_deleted=False)
            alternative_form.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)
        context = {
            "purchase_item_formset" : purchase_item_formset,
            "product_form" :product_form,
            "title" : "Create purchase",
            "form" : form,
            "transaction_form" : transaction_form,
            "alternative_unit_formset" : alternative_unit_formset,
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "redirect" : True,
            "is_need_animations": True,
            "block_payment_form_media" : True,
            "is_create" : True
        }
        return render(request,'purchases/entry.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase'])
def purchases(request):
    current_shop = get_current_shop(request)
    instances = Purchase.objects.filter(is_deleted=False,shop=current_shop).order_by('-a_id')
    vendors = Vendor.objects.filter(is_deleted=False,shop=current_shop)
    today = datetime.date.today()
    vendor = request.GET.get('vendor')
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

    if vendor:
        instances = instances.filter(vendor_id=vendor)

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    if payment :
        if payment == "full":
            instances = instances.filter(balance=0)
        elif payment == "no":
            for instance in instances:
                paid_amount = instance.paid_amount
                if paid_amount != 0:
                    instances = instances.exclude(pk = instance.pk)
        elif payment == "extra":
            for instance in instances:
                total = instance.total
                paid_amount= instance.paid_amount
                if total >= paid_amount:
                    instances = instances.exclude(pk=instance.pk)
        elif payment == "partial":
            for instance in instances:
                total = instance.total
                paid_amount = instance.paid_amount
                if total <= paid_amount or paid_amount == 0:
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
        'purchases' :purchases,
        "title" : 'Purchases',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "purchases" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,

        }
    return render(request, "purchases/purchases.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_purchase'])
def edit_purchase(request, pk):
    current_shop = get_current_shop(request)
    instance = Purchase.objects.get(pk=pk,is_deleted=False,shop=current_shop)
    transaction = None
    old_credit = instance.old_credit
    old_debit = instance.old_debit
    if Transaction.objects.filter(purchase=instance,shop=current_shop,first_transaction=True).exists():
        transaction = get_object_or_404(Transaction.objects.filter(purchase=instance,shop=current_shop,first_transaction=True))
    if PurchaseItem.objects.filter(purchase=instance).exists():
        extra = 0
    else:
        extra= 1
    PurchaseItemFormset = inlineformset_factory(
        Purchase,
        PurchaseItem,
        can_delete = True,
        extra = extra,
        exclude = ['creator','updator','auto_id','is_deleted','a_id','purchase','subtotal','qty_to_split'],
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'price' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Price'}),
            'selling_price' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Selling Price'}),
            'subtotal': TextInput(attrs={'disabled' : 'disabled','class': 'required form-control','placeholder' : 'Subtotal'}),
            }
        )

    if request.method == "POST":
        form = PurchaseForm(request.POST, instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        purchase_item_formset = PurchaseItemFormset(request.POST,prefix='purchase_item_formset',instance=instance)

        if form.is_valid() and purchase_item_formset.is_valid() and transaction_form.is_valid():

            old_balance = Purchase.objects.get(pk=pk).balance
            old_paid = Purchase.objects.get(pk=pk).paid_amount
            items = {}
            total_discount_amount = 0
            total_tax_amount = 0

            for f in purchase_item_formset:
                if f not in purchase_item_formset.deleted_forms:
                    product = f.cleaned_data['product']

                    qty = f.cleaned_data['qty']
                    price = f.cleaned_data['price']
                    selling_price = f.cleaned_data['selling_price']
                    unit = f.cleaned_data['unit']
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
                            "selling_price" : selling_price,
                            "price" : price,
                            "unit" :unit.pk,

                        }
                        items[str(new_pk)] = dic

            #update purchase
            special_discount = form.cleaned_data['special_discount']
            payment_received = form.cleaned_data['paid_amount']
            tax_category = form.cleaned_data['tax_category']
            tax_instance = None
            tax = 0
            if tax_category:
                tax_instance = get_object_or_404(TaxCategory.objects.filter(is_deleted=False,pk=tax_category.pk))
                tax = tax_instance.tax
            vendor = form.cleaned_data['vendor']

            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.total_discount_amount = total_discount_amount
            data1.total_tax_amount = total_tax_amount
            data1.save()

            all_subtotal = 0

            #delete previous items and update stock

            previous_purchase_items = PurchaseItem.objects.filter(purchase=instance)
            ProductExpiryDate.objects.filter(purchase=instance).delete()
            for p in previous_purchase_items:
                qty = p.qty
                unit = p.unit
                exact_qty = get_exact_qty(qty,unit)
                update_sock(p.product.pk,exact_qty,"decrease")
            previous_purchase_items.delete()

            #save items
            for key, value in items.iteritems():
                product_pk = key.split("_")[0]
                product = Product.objects.get(pk=product_pk)
                qty = value["qty"]
                price = value["price"]
                selling_price = value["selling_price"]
                unit = value["unit"]
                unit = Measurement.objects.get(pk=unit)
                exact_qty = get_exact_qty(qty,unit)
                subtotal = (qty * price)

                all_subtotal += subtotal

                PurchaseItem(
                    purchase = data1,
                    product = product,
                    unit = unit,
                    qty = qty,
                    price = price,                    
                    selling_price = selling_price,
                    subtotal = subtotal,
                    qty_to_split = qty
                ).save()

                update_sock(product.pk,exact_qty,"increase")

            credit=0
            debit=0
            if vendor:
                credit = vendor.credit
                debit = vendor.debit            

            tax_amount = all_subtotal * (tax / 100)
            non_credit_added_total = all_subtotal - special_discount +tax_amount
            main_total = non_credit_added_total - old_credit + old_debit
            balance = main_total - payment_received
            balance = Decimal(balance)
            #update credit
            Vendor.objects.filter(pk=vendor.pk,is_deleted=False).update(credit=0,debit=0)
            if balance > 0:
                balance = balance
                update_vendor_credit_debit(data1.vendor.pk,"debit",balance)
            elif balance < 0:
                balance = abs(balance)
                update_vendor_credit_debit(data1.vendor.pk,"credit",balance)
                balance = 0

            #update purchase
            vendor = Vendor.objects.get(pk=data1.vendor.pk)
            credit_amount_added = 0
            if credit > vendor.credit:
                credit_amount_added = credit - vendor.credit

            # If any old balance purchase exists , The extra amount will go to that purchase.
            if debit > vendor.debit:
                debit_amount = debit - vendor.debit
                payment_pending_purchases = Purchase.objects.filter(balance__gt=0,vendor=vendor,shop=current_shop,is_deleted=False).order_by('date_added')
                for payment_pending_purchase in payment_pending_purchases:

                    purchase_balance = payment_pending_purchase.balance

                    paid_amount_added = payment_pending_purchase.paid_amount_added

                    amount_added_to_purchase = 0
                    if purchase_balance > debit_amount:
                        amount_added_to_purchase = debit_amount
                        debit_amount = 0
                    else:
                        amount_added_to_purchase = purchase_balance
                        debit_amount -= purchase_balance

                    PurchaseCollectAmountHistory.objects.create(
                        purchase=payment_pending_purchase,
                        paid_from_purchase = data1,
                        amount = amount_added_to_purchase
                    )
                    payment_pending_purchase.paid_amount_added = paid_amount_added + amount_added_to_purchase
                    payment_pending_purchase.balance = purchase_balance - amount_added_to_purchase
                    payment_pending_purchase.save()

                    if debit_amount==0:
                        break

            data1.credit_amount_added=credit_amount_added
            data1.subtotal=all_subtotal
            data1.special_discount=special_discount
            data1.total=non_credit_added_total
            data1.balance=balance
            data1.tax_category=tax_category
            data1.tax=tax_amount
            data1.save()

            #update account balance
            if transaction:
                if transaction.cash_account:
                    balance = transaction.cash_account.balance + old_paid
                    CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = transaction.bank_account.balance + old_paid
                    BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            amount = form.cleaned_data['paid_amount']
            date = form.cleaned_data['time']
            transaction_category = get_object_or_404(TransactionCategory.objects.filter(name='purchase_payment',category_type="expense",is_deleted=False,shop=current_shop)[:1])

            data = transaction_form.save(commit=False)

            if transaction_mode == "cash":
                cash_credit = amount
                bank_credit = 0
            elif transaction_mode == "bank":
                cash_credit = 0
                bank_credit = amount
            
            if Journel.objects.filter(transaction=data).exists():
                Journel.objects.filter(transaction=data).update(cash_credit=cash_credit,
                                                            bank_credit=bank_credit,
                                                            expense=amount)

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
                        data.payment_to = None
                        data.bank_account = None
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

            data.updator = request.user
            data.amount = amount
            data.date = date
            data.purchase = data1
            data.shop = current_shop
            data.transaction_type = "expense"
            data.transaction_category = transaction_category
            if not transaction:
                data.first_transaction = True
                data.auto_id = get_auto_id(Transaction)
                data.a_id = get_a_id(Transaction,request)
                data.creator = request.user
                data.updator = request.user
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "purchase updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:purchase',kwargs={"pk":instance.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(transaction_form, formset=False)
            message += generate_form_errors(purchase_item_formset, formset=True)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = PurchaseForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        purchase_item_formset = PurchaseItemFormset(prefix='purchase_item_formset',instance=instance)
        for item in purchase_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop)
            item.fields['unit'].queryset = Measurement.objects.filter(shop=current_shop,unit_type="quantity")
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)
        context = {
            "purchase_item_formset" : purchase_item_formset,
            "title" : "Edit purchase",
            "form" : form,
            "instance" : instance,
            "transaction_form" : transaction_form,
            "credit" : old_credit,
            "debit" : old_debit,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            'redirect':True,
            "block_payment_form_media" : True,
        }
        return render(request,'purchases/edit.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase'])
def purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Purchase.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    transactions = Transaction.objects.filter(purchase=instance,shop=current_shop,is_deleted=False)
    product_splits = PurchaseItemSplit.objects.filter(purchase_item__purchase=instance)

    purchase_items = PurchaseItem.objects.filter(purchase=instance)
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(time__icontains=query)|Q(vendor__icontains=query)|Q(subtotal__icontains=query)|Q(discount__icontains=query)|Q(total__icontains=query))
    context = {
        'instance': instance,
        "transactions" : transactions,
        "purchase_items" : purchase_items,
        "product_splits" : product_splits,
        'title':'Purchase',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "purchases" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request, "purchases/purchase.html", context)


def delete_purchase_fun(instance):
    old_balance = instance.balance
    old_paid = instance.paid_amount
    #update credit debit
    update_vendor_credit_debit(instance.vendor.pk,"credit",old_balance)

    #update stock
    purchase_items = PurchaseItem.objects.filter(purchase=instance)
    for p in purchase_items:
        qty = p.qty
        unit = p.unit
        exact_qty = get_exact_qty(qty,unit)
        update_sock(p.product.pk,exact_qty,"decrease")

    #update account balance

    if Transaction.objects.filter(purchase=instance).exists():
        old_transaction = get_object_or_404(Transaction.objects.filter(purchase=instance))
        if old_transaction.cash_account:
            balance = old_transaction.cash_account.balance + old_paid
            CashAccount.objects.filter(pk=old_transaction.cash_account.pk).update(balance=balance)
        else  :
            balance = old_transaction.bank_account.balance + old_paid
            BankAccount.objects.filter(pk=old_transaction.bank_account.pk).update(balance=balance)

    instance.is_deleted=True
    instance.save()


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_purchase'])
def delete_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Purchase.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    delete_purchase_fun(instance)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Purchase deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('purchases:purchases')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_purchase'])
def delete_selected_purchases(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            Purchase.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Purchase Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('purchases:purchases')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Purchase.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    purchase_items = PurchaseItem.objects.filter(purchase=instance)

    context = {
        "instance" : instance,
        "title" : "Purchase : #" + str(instance.auto_id),
        "single_page" : True,
        "purchase_items" : purchase_items,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'purchases/print_purchase.html',context)


def print_purchases(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    title = "Purchases"
    instances = Purchase.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get('q')
    if query :
        instances = instances.filter(Q(auto_id__icontains=query) | Q(vendor__name__icontains=query))

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

            instances = instances.filter(time__year=today.year, time__month=today.month, time__day=today.day)
            total_purchases_created = instances.count()

        elif period == "month":
            title = "Purchases : This Month"
            instances = instances.filter(time__year=today.year, time__month=today.month)

        elif period == "year":
            title = "Purchases : This Year"
            instances = purchases.filter(date__year=today.year)
    elif filter_date_period:
        title = "Purchases : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(time__range=[from_date, to_date])
            total_purchases_created = instances.count()
    elif date:
        title = "Purchases : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(time__year=date.year, time__month=date.month, time__day=date.day)
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
    return render(request,'purchases/print_purchases.html',context)


@login_required
def email_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Purchase.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        form = EmailPurchaseForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']
            content += "<br />"
            link = request.build_absolute_uri(reverse('purchases:print',kwargs={'pk':pk}))
            content += '<a href="%s">%s</a>' %(link,link)

            template_name = 'email/email.html'
            subject = "Purchase Details (#%s) | %s" %(str(instance.a_id),current_shop.name)
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
                "message" : "Purchase Successfully Sent.",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:purchase',kwargs={'pk':pk})
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
        email = instance.vendor.email
        name = instance.vendor.name
        content = "Thanks for your service %s. Please follow the below link for your service details." %current_shop.name

        form = EmailPurchaseForm(initial={'name' : name, 'email' : email, 'content' : content})

        context = {
            "instance" : instance,
            "title" : "Email Purchase : #" + str(instance.a_id),
            "single_page" : True,
            'form' : form,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_animations" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'purchases/email_purchase.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_paid'])
def create_paid(request):
    current_shop = get_current_shop(request)
    if request.method == "POST":

        form = PaidAmountForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        if form.is_valid() and transaction_form.is_valid():

            auto_id = get_auto_id(PaidAmount)
            a_id = get_a_id(PaidAmount,request)
            paid = form.cleaned_data['paid']
            vendor = form.cleaned_data['vendor']
            date = form.cleaned_data['date']
            instance = Vendor.objects.get(pk=vendor.pk,is_deleted=False,shop=current_shop)
            balance = instance.debit

            remaining_balance = balance - paid
            debit = remaining_balance
            credit = vendor.credit
            if remaining_balance <= 0:
                debit = 0
                if vendor.credit > 0:
                    credit = abs(remaining_balance) + vendor.credit
                else:
                    credit = abs(remaining_balance)

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

            if Purchase.objects.filter(is_deleted=False,vendor=data1.vendor,shop=current_shop).exists():
                latest_purchase = Purchase.objects.filter(is_deleted=False,vendor=data1.vendor,shop=current_shop).latest('date_added')
                paid_amount = latest_purchase.paid + paid
                latest_purchase = Purchase.objects.filter(pk=latest_purchase.pk)
                if remaining_balance < 0:
                    remaining_balance = -credit
                latest_purchase.update(balance=remaining_balance,paid=paid_amount)

            vendor = Vendor.objects.filter(pk= data1.vendor.pk)
            if vendor.exists():
                vendor.update(credit=credit,debit=debit)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            amount = form.cleaned_data['paid']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='purchase_payment',category_type="expense",is_deleted=False)[:1])
            transaction_category = transaction_categories.name
            #create income
            data = transaction_form.save(commit=False)

            if transaction_mode == "cash":
                cash_credit = paid
                bank_credit = 0
            elif transaction_mode == "bank":
                cash_credit = 0
                bank_credit = paid    
            Journel.objects.create(
                date = date,
                shop = current_shop,
                cash_credit = cash_credit,
                bank_credit = bank_credit,
                expense = paid,
                transaction = data,
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
                        data.payment_to = None
                        data.bank_account = None
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
                if Purchase.objects.filter(is_deleted=False,vendor=data1.vendor,shop=current_shop).exists():
                    latest_purchase = Purchase.objects.filter(is_deleted=False,vendor=data1.vendor,shop=current_shop).latest('date_added')
                    data.purchase = latest_purchase
                data.paid = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Created",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:paid',kwargs = {'pk' :data1.pk}),
                "message" : "Amount paid Successfully."
            }
        else:
            message = generate_form_errors(form,formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : transaction_form.errors
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PaidAmountForm()
        transaction_form = TransactionForm()

        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Purchase payment",
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
        return render(request, 'purchases/entry_paid.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_paid'],allow_self=True,model=PaidAmount)
def edit_paid(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PaidAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(paid=instance,shop=current_shop))
    if request.method == "POST":
        response_data = {}
        old_paid = instance.paid
        balance = 0
        form = PaidAmountForm(request.POST,instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        if form.is_valid() and transaction_form.is_valid():

            #update vendor credit
            update_vendor_credit_debit(instance.vendor.pk,"debit",old_paid)
            amount = form.cleaned_data['paid']
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.save()
            update_vendor_credit_debit(instance.vendor.pk,"credit",amount)
            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            date = form.cleaned_data['date']

            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='purchase_payment',category_type="expense",is_deleted=False)[:1])
            transaction_category = transaction_categories.name

            #update account balance
            if Transaction.objects.filter(paid=pk).exists():
                if transaction.cash_account:
                    balance = transaction.cash_account.balance + old_paid
                    CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = transaction.bank_account.balance + old_paid
                    BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)
            data = transaction_form.save(commit=False)

            if Journel.objects.filter(transaction=data).exists():
                Journel.objects.filter(transaction=data).update(cash_credit=amount,expense=amount)
            
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
                        data.payment_to = None
                        data.bank_account = None
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
                latest_purchase = Purchase.objects.filter(is_deleted=False,vendor=data1.vendor,shop=current_shop).latest('date_added')
                data.purchase = latest_purchase
                data.paid = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Updated",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:paid', kwargs = {'pk' :pk}),
                "message" : "Paid Amount Successfully Updated."
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
        form = PaidAmountForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Edit Paid Amount : " + str(instance.paid),
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
        return render(request, 'purchases/entry_paid.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_paids'])
def paids(request):
    current_shop = get_current_shop(request)
    instances = PaidAmount.objects.filter(is_deleted=False,shop=current_shop)

    title = "Paid Amounts"

    #filter by query
    query = request.GET.get("q")
    if query:
        title = "Paid Amount (Query - %s)" % query
        instances = instances.filter(Q(paid__icontains=query) | Q(date__icontains=query) | Q(vendor__name__icontains=query))

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
    return render(request,'purchases/paids.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_paid'],allow_self=True,model=PaidAmount)
def paid(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PaidAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(paid=instance,shop=current_shop))
    context = {
        "instance" : instance,
        "transaction" : transaction,
        "title" : "Paid Amount: " + str(instance.paid),

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'purchases/paid.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_paid'],allow_self=True,model=PaidAmount)
def delete_paid(request,pk):
    PaidAmount.objects.filter(pk=pk).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Succesfully Deleted",
        "redirect" : "true",
        "redirect_url" : reverse('purchases:paids'),
        "message" : "Paid Amount Successfully Deleted."
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_paid'])
def delete_selected_paids(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(PaidAmount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            PaidAmount.objects.filter(pk=pk).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected PaidAmount(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('purchases:paids')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some Paid Amount first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_collect_amounts'])
def create_collect_amount(request):
    current_shop = get_current_shop(request)
    if request.method == "POST":

        form = CollectAmountsForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        if form.is_valid() and transaction_form.is_valid():

            auto_id = get_auto_id(CollectAmounts)
            a_id = get_a_id(CollectAmounts,request)
            collect_amount = form.cleaned_data['collect_amount']
            vendor = form.cleaned_data['vendor']
            date = form.cleaned_data['date']
            instance = Vendor.objects.get(pk=vendor.pk,is_deleted=False)
            balance = instance.credit

            remaining_balance = balance - collect_amount
            credit = remaining_balance
            debit = vendor.debit
            if remaining_balance <= 0:
                credit = 0
                if vendor.debit > 0:
                    debit = abs(remaining_balance) + vendor.debit
                else:
                    debit = abs(remaining_balance)

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

            vendor = Vendor.objects.filter(pk= data1.vendor.pk)
            if vendor.exists():
                vendor.update(credit=credit,debit=debit)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            transaction_category = transaction_form.cleaned_data['transaction_category']
            amount = form.cleaned_data['collect_amount']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='vendor_payment',category_type="income",is_deleted=False)[:1])

            #create income
            data = transaction_form.save(commit=False)

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
                        data.payment_to = None
                        data.bank_account = None
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
                data.vender_payment = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Created",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:collect_amount',kwargs = {'pk' :data1.pk}),
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
        form = CollectAmountsForm()
        transaction_form = TransactionForm()

        context = {
            "form" : form,
            "transaction_form" : transaction_form,
            "title" : "Amount Collection",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,

        }
        return render(request, 'purchases/entry_collect_amount.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_collect_amounts'],allow_self=True,model=CollectAmounts)
def edit_collect_amount(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CollectAmounts.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(vender_payment=instance,shop=current_shop))

    if request.method == "POST":
        response_data = {}
        old_collect_amount = instance.collect_amount
        balance = 0
        form = CollectAmountsForm(request.POST,instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        if form.is_valid() and transaction_form.is_valid():

            #update vendor credit
            update_vendor_credit_debit(instance.vendor.pk,"credit",old_collect_amount)
            amount = form.cleaned_data['collect_amount']
            date = form.cleaned_data['date']
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.save()
            if Journel.objects.filter(transaction=transaction,shop=current_shop).exists():
                Journel.objects.filter(transaction=transaction,shop=current_shop).update(income=amount,cash_debit=amount)
           
            update_vendor_credit_debit(instance.vendor.pk,"debit",amount)
            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            transaction_category = transaction_form.cleaned_data['transaction_category']

            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='vendor_payment',category_type="income",is_deleted=False)[:1])

            #update account balance
            if Transaction.objects.filter(vender_payment=pk).exists():
                if transaction.cash_account:
                    balance = transaction.cash_account.balance - old_collect_amount
                    CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = transaction.bank_account.balance - old_collect_amount
                    BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)
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
                        data.payment_to = None
                        data.bank_account = None
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
                data.vender_payment = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Succesfully Updated",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:collect_amount', kwargs = {'pk' :pk}),
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
        form = CollectAmountsForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
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
        return render(request, 'purchases/entry_collect_amount.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_collect_amounts'])
def collect_amounts(request):
    current_shop = get_current_shop(request)
    instances = CollectAmounts.objects.filter(is_deleted=False,shop=current_shop)

    title = "Collect Amounts"

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
    return render(request,'purchases/collect_amounts.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_collect_amounts'],allow_self=True,model=CollectAmounts)
def collect_amount(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(CollectAmounts.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(vender_payment=instance,shop=current_shop))
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
    return render(request,'purchases/collect_amount.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_collect_amounts'],allow_self=True,model=CollectAmounts)
def delete_collect_amount(request,pk):
    CollectAmounts.objects.filter(pk=pk).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Succesfully Deleted",
        "redirect" : "true",
        "redirect_url" : reverse('purchases:collect_amounts'),
        "message" : "Collect Amount Successfully Deleted."
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_collect_amounts'])
def delete_selected_collect_amounts(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(CollectAmounts.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            CollectAmounts.objects.filter(pk=pk).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected CollectAmounts(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('purchases:collect_amounts')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some Collect Amount first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_collected_amount(request,pk):
    instance = get_object_or_404(CollectAmounts.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    current_shop = get_current_shop(request)
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
    return render(request,'purchases/print_collected_amount.html',context)


def print_collected_amounts(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    title = "Sale payment"
    instances = CollectAmounts.objects.filter(is_deleted=False,shop=current_shop)
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
    return render(request,'purchases/print_collected_amounts.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_purchase_invoice'])
def create_purchase_invoice(request):
    current_shop = get_current_shop(request)
    PurchaseInvoiceItemFormset = formset_factory(PurchaseInvoiceItemForm, extra=1)

    if request.method == "POST":
        response_data = {}
        form = PurchaseInvoiceForm(request.POST)
        purchase_invoice_item_formset = PurchaseInvoiceItemFormset(request.POST,prefix='purchase_invoice_item_formset')
        for item in purchase_invoice_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)

        if form.is_valid() and purchase_invoice_item_formset.is_valid():

            message = ""
            is_ok = True
            products = request.POST.getlist('product_pk')
            units = request.POST.getlist('returned_product_unit')
            qtys = request.POST.getlist('returned_qty')
            items = zip(products,units,qtys)
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

                if Product.objects.filter(pk=product_instance.pk,unit=unit_instance).exists():
                    purchase_invoice_item = Product.objects.get(pk=product_instance.pk,unit=unit_instance)
                    pr_ins = {
                        "product" : product_instance,
                        "unit" : unit_instance,
                        "qty" : qty,
                        "cost" : purchase_invoice_item.cost
                    }
                    returned_items.append(pr_ins)

                else:
                    message += "Product with this unit is not in this list. Please don't edit hidden values."
                    is_ok = False

            error_messages = ""
            title = ""

            if is_ok:
                vendor = form.cleaned_data['vendor']
                #Save Sale Return
                data = form.save(commit=False)
                data.creator = request.user
                data.updator = request.user
                data.shop = current_shop
                data.a_id = get_a_id(PurchaseInvoice,request)
                data.auto_id = get_auto_id(PurchaseInvoice)
                data.vendor = vendor
                data.save()

                #Save Sale Return Item
                for f in returned_items:

                    product = f['product']
                    unit = f['unit']
                    qty = f['qty']
                    exact_qty = Decimal(get_exact_qty(qty,unit))

                    PurchaseInvoiceItem(
                        invoice = data,
                        product = product,
                        unit = unit,
                        qty = qty,

                    ).save()

                for f in purchase_invoice_item_formset:
                    product = f.cleaned_data['product']
                    qty = f.cleaned_data['qty']
                    unit = f.cleaned_data['unit']

                    PurchaseInvoiceItem(
                        invoice = data,
                        product = product,
                        unit = unit,
                        qty = qty
                    ).save()

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Invoice Generated successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('purchases:invoices')
                }
            else:
                response_data['status'] = 'false'
                response_data['title'] = "Error in input values"
                response_data['stable'] = "true"
                response_data['message'] = message

        else:
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(purchase_invoice_item_formset, formset=True)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : form.errors
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:

        purchase_invoice_item_formset = PurchaseInvoiceItemFormset(prefix='purchase_invoice_item_formset')
        for item in purchase_invoice_item_formset:
            item.fields['product'].queryset = Product.objects.filter(shop=current_shop,is_deleted=False)
            item.fields['unit'].queryset = Measurement.objects.none()
            item.fields['unit'].label_from_instance = lambda obj: "%s (%s)" % (obj.unit_name, obj.code)

        purchase_invoice_items_list = []
        instances = Product.objects.filter(is_deleted=False,shop=current_shop)
        if instances:
            for instance in instances:
                if instance.stock <= instance.low_stock_limit:
                    purchase_invoice_items_list.append(instance)

        form = PurchaseInvoiceForm()

        context = {
            "title" : "Create purchase invoice",
            "form" : form,
            "purchase_invoice_items_list" : purchase_invoice_items_list,
            "purchase_invoice_item_formset" : purchase_invoice_item_formset,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "is_need_formset" : True,
            "redirect" : True,
            "is_create_page" : True,
        }
        return render(request,'purchases/entry_invoice.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase_invoice'])
def purchase_invoices(request):
    current_shop = get_current_shop(request)
    instances = PurchaseInvoice.objects.filter(is_deleted=False,shop=current_shop)
    vendors = Vendor.objects.filter(is_deleted=False,shop=current_shop)
    today = datetime.date.today()
    vendor = request.GET.get('vendor')
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = "yes"

    if vendor:
        instances = instances.filter(vendor_id=vendor)

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
        "title" : 'Purchase Invoices',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "purchases" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,

        }
    return render(request, "purchases/purchase_invoices.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase_invoice'])
def purchase_invoice(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseInvoice.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    purchase_invoice_items = PurchaseInvoiceItem.objects.filter(invoice=instance)
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(time__icontains=query)|Q(vendor__icontains=query)|Q(subtotal__icontains=query)|Q(discount__icontains=query)|Q(total__icontains=query))

    context = {
        'instance': instance,
        "purchase_invoice_items" : purchase_invoice_items,

        'title':'Purchase Invoice',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "purchases" : True,
    }
    return render(request, "purchases/purchase_invoice.html", context)


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_purchase_invoice'])
def delete_purchase_invoice(request, pk):
    current_shop = get_current_shop(request)
    PurchaseInvoice.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Purchase invoice deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('purchases:invoices')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_purchase_invoice'])
def delete_selected_purchase_invoices(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            PurchaseInvoice.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Purchase Invoice Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('purchases:invoices')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_purchase_invoice(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseInvoice.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    purchase_invoice_items = PurchaseInvoiceItem.objects.filter(invoice=instance)
    current_shop = get_current_shop(request)
    context = {
        "instance" : instance,
        "title" : "Purchase : #" + str(instance.auto_id),
        "single_page" : True,
        "purchase_invoice_items" : purchase_invoice_items,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'purchases/print_purchase_invoice.html',context)


@check_mode
@login_required
def email_invoice(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseInvoice.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        form = EmailInvoiceForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']
            content += "<br />"
            link = request.build_absolute_uri(reverse('purchases:print_invoice',kwargs={'pk':pk}))
            content += '<a href="%s">%s</a>' %(link,link)

            template_name = 'email/email.html'
            subject = "Invoice Details (#%s) | %s" %(str(instance.auto_id),current_shop.name)
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
                "message" : "Invoice Successfully Sent.",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:invoice',kwargs={'pk':pk})
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
        email = ""
        name = ""
        if instance.vendor:
            email = instance.vendor.email
            name = instance.vendor.name
        content = "Please follow the below link for your invoice details."

        form = EmailInvoiceForm(initial={'name' : name, 'email' : email, 'content' : content})

        context = {
            "instance" : instance,
            "title" : "Email Purchase Invoice : #" + str(instance.auto_id),
            "single_page" : True,
            'form' : form,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
        }
        return render(request,'purchases/email_invoice.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_asset_purchase'])
def create_asset_purchase(request):
    AssetPurchaseItemFormset = formset_factory(AssetPurchaseItemForm, extra=1)
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = AssetPurchaseForm(request.POST)
        transaction_form = TransactionForm(request.POST)
        asset_purchase_item_formset = AssetPurchaseItemFormset(request.POST,prefix='asset_purchase_item_formset')

        if form.is_valid() and asset_purchase_item_formset.is_valid() and transaction_form.is_valid() :

            auto_id = get_auto_id(AssetPurchase)
            a_id = get_a_id(AssetPurchase,request)
            vendor = form.cleaned_data['vendor']
            special_discount = form.cleaned_data['special_discount']
            paid_amount = form.cleaned_data['paid_amount']
            data1 = form.save(commit=False)
            data1.auto_id = auto_id
            data1.a_id = a_id
            data1.shop = current_shop
            data1.creator = request.user
            data1.updator = request.user
            data1.save()

            main_subtotal = 0
            tax = 0
            for f in asset_purchase_item_formset:
                asset = f.cleaned_data['asset']
                qty = f.cleaned_data['qty']
                unit = f.cleaned_data['unit']
                price = f.cleaned_data['price']
                exact_qty = get_exact_qty(qty,unit)
                discount = f.cleaned_data['discount']
                subtotal = (qty * price)- discount
                main_subtotal += subtotal

                AssetPurchaseItem(
                    purchase = data1,
                    asset = asset,
                    unit = unit,
                    qty = qty,
                    price = price,
                    subtotal = subtotal,
                    discount = discount,

                ).save()

            main_total = main_subtotal - special_discount
            rounded_total = round(main_total)
            extra = round(main_total) - float(main_total)
            round_off = format(extra, '.2f')
            balance = rounded_total - float(paid_amount)
            balance = Decimal(balance)

            if balance > 0:
                balance = balance
                update_vendor_credit_debit(data1.vendor.pk,"debit",balance)
            elif balance < 0:
                balance = abs(balance)
                update_vendor_credit_debit(data1.vendor.pk,"credit",balance)
                balance = 0

            #update purchase

            AssetPurchase.objects.filter(pk=data1.pk).update(subtotal=main_subtotal,special_discount= special_discount,total=rounded_total,balance=balance,round_off=round_off)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            amount = form.cleaned_data['paid_amount']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='purchase_payment',category_type="expense",is_deleted=False)[:1])
            transaction_category = transaction_categories.name
            #create income
            data = transaction_form.save(commit=False)

            if transaction_mode == "cash":
                cash_credit = paid_amount
                bank_credit = 0
            elif transaction_mode == "bank":
                cash_credit = 0
                bank_credit = paid_amount

            Journel.objects.create(
                date = datetime.date.today(),
                shop = current_shop,
                expense = main_total,
                cash_credit = cash_credit,
                bank_credit = bank_credit,
                transaction = data,   
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
                        data.payment_to = None
                        data.bank_account = None
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
                data.date = datetime.datetime.now()
                data.asset_purchase = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Purchased successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:purchases')
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
        form = AssetPurchaseForm()
        transaction_form = TransactionForm()
        asset_purchase_item_formset = AssetPurchaseItemFormset(prefix='asset_purchase_item_formset')

        context = {
            "asset_purchase_item_formset" : asset_purchase_item_formset,
            "title" : "Create purchase",
            "form" : form,
            "transaction_form" : transaction_form,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "redirect" : True
        }
        return render(request,'purchases/entry_asset_purchase.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_asset_purchase'])
def asset_purchases(request):
    current_shop = get_current_shop(request)
    instances = AssetPurchase.objects.filter(is_deleted=False,shop=current_shop)
    vendors = Vendor.objects.filter(is_deleted=False,shop=current_shop)
    today = datetime.date.today()
    vendor = request.GET.get('vendor')
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

    if vendor:
        instances = instances.filter(vendor_id=vendor)

    if year:
        instances = instances.filter(time__year=year)

    if month:
        instances = instances.filter(time__month=month)

    if payment :
        if payment == "full":
            instances = instances.filter(balance=0)
        elif payment == "no":
            for instance in instances:
                paid_amount = instance.paid_amount
                if paid_amount != 0:
                    instances = instances.exclude(pk = instance.pk)
        elif payment == "extra":
            for instance in instances:
                total = instance.total
                paid_amount= instance.paid_amount
                if total >= paid_amount:
                    instances = instances.exclude(pk=instance.pk)
        elif payment == "partial":
            for instance in instances:
                total = instance.total
                paid_amount = instance.paid_amount
                if total <= paid_amount or paid_amount == 0:
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
        "title" : 'Asset Purchases',

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "purchases" : True,
        "is_need_grid_system" : True,
        "is_need_animations": True,
        "is_need_datetime_picker" : True,

        }
    return render(request, "purchases/asset_purchases.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_asset_purchase'])
def edit_asset_purchase(request, pk):
    current_shop = get_current_shop(request)
    instance = AssetPurchase.objects.get(pk=pk,is_deleted=False,shop=current_shop)
    transaction = get_object_or_404(Transaction.objects.filter(purchase=instance,shop=current_shop,paid=None))
    if AssetPurchaseItem.objects.filter(purchase=instance).exists():
        extra = 0
    else:
        extra= 1
    AssetPurchaseItemFormset = inlineformset_factory(
        AsssetPurchase,
        AssetPurchaseItem,
        can_delete = True,
        extra = extra,
        exclude = ['creator','updator','auto_id','is_deleted','a_id','purchase','subtotal'],
        widgets = {
            'asset': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Asset', 'data-minimum-input-length': 1},),
            'qty' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Qty'}),
            'unit' : Select(attrs={'class': 'required form-control selectpicker'}),
            'price' : TextInput(attrs={'class': 'required form-control','placeholder' : 'Price'}),
            'cost' : TextInput(attrs={'class': 'required form-control','placeholder' : 'cost'}),
            'discount': TextInput(attrs={'class': 'required form-control','placeholder' : 'Discount'}),
            'subtotal': TextInput(attrs={'class': 'required form-control','placeholder' : 'Subtotal'}),
            }
        )

    if request.method == "POST":
        form = AssetPurchaseForm(request.POST, instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)
        asset_purchase_item_formset = AssetPurchaseItemFormset(request.POST,prefix='asset_purchase_item_formset',instance=instance)

        if form.is_valid() and asset_purchase_item_formset.is_valid() and transaction_form.is_valid():

            old_balance = AssetPurchase.objects.get(pk=pk).balance
            old_paid = AssetPurchase.objects.get(pk=pk).paid_amount
            old_transaction = get_object_or_404(Transaction.objects.filter(purchase=pk,paid=None))
            items = {}
            total_discount_amount = 0
            total_tax_amount = 0

            for f in asset_purchase_item_formset:
                if f not in asset_purchase_item_formset.deleted_forms:
                    asset = f.cleaned_data['asset']

                    qty = f.cleaned_data['qty']
                    price = f.cleaned_data['price']
                    discount_amount = f.cleaned_data['discount']
                    unit = f.cleaned_data['unit']
                    exact_qty = get_exact_qty(qty,unit)

                    total_discount_amount += discount_amount

                    if str(asset.pk) in items:
                        q = items[str(asset.pk)]["qty"]
                        items[str(asset.pk)]["qty"] = q + qty

                        d = items[str(asset.pk)]["discount_amount"]
                        items[str(asset.pk)]["discount_amount"] = d + discount_amount

                    else:
                        dic = {
                            "qty" : qty,
                            "price" : price,
                            "discount_amount" :discount_amount,
                            "unit" :unit.pk
                        }
                        items[str(asset.pk)] = dic

            #update purchase
            special_discount = form.cleaned_data['special_discount']
            payment_received = form.cleaned_data['paid_amount']
            data1 = form.save(commit=False)
            data1.updator = request.user
            data1.date_updated = datetime.datetime.now()
            data1.total_discount_amount = total_discount_amount
            data1.total_tax_amount = total_tax_amount
            data1.save()

            all_subtotal = 0

            #delete previous items

            previous_asset_purchase_items = AssetPurchaseItem.objects.filter(purchase=instance)
            previous_asset_purchase_items.delete()

            #save items
            for key, value in items.iteritems():
                asset = Asset.objects.get(pk=key)
                qty = value["qty"]
                price = value["price"]
                discount_amount = value["discount_amount"]
                unit = value["unit"]
                unit = Measurement.objects.get(pk=unit)
                subtotal = (qty * price) - discount_amount

                all_subtotal += subtotal

                AsssetPurchaseItem(
                    purchase = data1,
                    product = product,
                    qty = qty,
                    price = price,
                    discount = discount_amount,
                    subtotal = subtotal,
                    unit = unit
                ).save()

            total = all_subtotal - special_discount
            rounded_total = Decimal(round(total))
            balance = rounded_total - payment_received
            extra = Decimal(round(total)) - total
            round_off = Decimal(format(extra, '.2f'))
            balance = Decimal(balance)

            AssetPurchase.objects.filter(pk=data1.pk).update(subtotal=all_subtotal,total=rounded_total,balance=balance,round_off=round_off)

            #update credit
            update_vendor_credit_debit(data1.vendor.pk,"credit",old_balance)

            if balance > 0:
                balance = balance
                update_vendor_credit_debit(data1.vendor.pk,"debit",balance)
            elif balance < 0:
                balance = abs(balance)
                update_vendor_credit_debit(data1.vendor.pk,"credit",balance)

            #update account balance
            if Transaction.objects.filter(purchase=pk).exists():
                if old_transaction.cash_account:
                    #printold_paid
                    balance = old_transaction.cash_account.balance + old_paid
                    #printbalance
                    CashAccount.objects.filter(pk=old_transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = old_transaction.bank_account.balance + old_paid
                    BankAccount.objects.filter(pk=old_transaction.bank_account.pk,shop=current_shop).update(balance=balance)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']
            amount = form.cleaned_data['paid_amount']
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='purchase_payment',category_type="expense",is_deleted=False)[:1])
            transaction_category = transaction_categories.name

            data = transaction_form.save(commit=False)

            if Journel.objects.filter(transaction=data).exists():
                Journel.objects.filter(transaction=data).update(expense=total,cash_credit=payment_received) 
           
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
                        data.payment_to = None
                        data.bank_account = None
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
                data.amount = amount
                data.date = datetime.datetime.now()
                data.asset_purchase = data1
                data.shop = current_shop
                data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Asset purchase updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:asset_purchases')
            }

        else:
            message = generate_form_errors(form, formset=False )

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
                }

        return HttpResponse(json.dumps(response_data),content_type='application/javascript')
    else:
        form = AssetPurchaseForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        asset_purchase_item_formset = AssetPurchaseItemFormset(prefix='asset_purchase_item_formset',instance=instance)

        context = {
            "asset_purchase_item_formset" : asset_purchase_item_formset,
            "title" : "Edit purchase",
            "form" : form,
            "transaction_form" : transaction_form,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            'redirect':True
        }
        return render(request,'purchases/edit_asset_purchase.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_purchase'])
def asset_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(AssetPurchase.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    transaction = get_object_or_404(Transaction.objects.filter(AssetPurchase=instance,shop=current_shop,paid=None))
    asset_purchase_items = AssetPurchaseItem.objects.filter(purchase=instance)
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(time__icontains=query)|Q(vendor__icontains=query)|Q(subtotal__icontains=query)|Q(discount__icontains=query)|Q(total__icontains=query))


    context = {
        'instance': instance,
        "transaction" : transaction,
        "asset_purchase_items" : asset_purchase_items,
        'title':'Purchase',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
    }
    return render(request, "purchases/asset_purchase.html", context)


def delete_asset_purchase_fun(instance):
    old_balance = instance.balance
    old_paid = instance.paid_amount
    #update credit debit
    update_vendor_credit_debit(instance.vendor.pk,"credit",old_balance)

    #update account balance

    if Transaction.objects.filter(asset_purchase=instance).exists():
        old_transaction = get_object_or_404(Transaction.objects.filter(asset_purchase=instance))
        if old_transaction.cash_account:
            balance = old_transaction.cash_account.balance + old_paid
            CashAccount.objects.filter(pk=old_transaction.cash_account.pk).update(balance=balance)
        else  :
            balance = old_transaction.bank_account.balance + old_paid
            BankAccount.objects.filter(pk=old_transaction.bank_account.pk).update(balance=balance)

    instance.is_deleted=True
    instance.save()


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_asset_purchase'])
def delete_asset_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(AssetPurchase.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    delete_purchase_fun(instance)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Asset Purchase deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('purchases:asset_purchases')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_purchase'])
def delete_selected_asset_purchases(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            AssetPurchase.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Asset Purchase Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('purchases:asset_purchases')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def print_asset_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(AssetPurchase.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    asset_purchase_items = AssetPurchaseItem.objects.filter(purchase=instance)

    context = {
        "instance" : instance,
        "title" : "Purchase : #" + str(instance.auto_id),
        "single_page" : True,
        "asset_purchase_items" : asset_purchase_items,
        "current_shop" : current_shop,

        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
    }
    return render(request,'purchases/print_asset_purchase.html',context)


def print_asset_purchases(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    title = "Asset Purchases"
    instances = AssetPurchase.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get('q')
    if query :
        instances = instances.filter(Q(auto_id__icontains=query) | Q(vendor__name__icontains=query))

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

            instances = instances.filter(time__year=today.year, time__month=today.month, time__day=today.day)
            total_purchases_created = instances.count()

        elif period == "month":
            title = "Purchases : This Month"
            instances = instances.filter(time__year=today.year, time__month=today.month)

        elif period == "year":
            title = "Purchases : This Year"
            instances = purchases.filter(date__year=today.year)
    elif filter_date_period:
        title = "Purchases : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(time__range=[from_date, to_date])
            total_purchases_created = instances.count()
    elif date:
        title = "Purchases : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(time__year=date.year, time__month=date.month, time__day=date.day)
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
    return render(request,'purchases/print_asset_purchases.html',context)


@login_required
def email_asset_purchase(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(AssetPurchase.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == 'POST':
        form = EmailAssetPurchaseForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']
            content += "<br />"
            link = request.build_absolute_uri(reverse('purchases:print',kwargs={'pk':pk}))
            content += '<a href="%s">%s</a>' %(link,link)

            template_name = 'email/email.html'
            subject = "Asset Purchase Details (#%s) | %s" %(str(instance.a_id),current_shop.name)
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
                "message" : "Purchase Successfully Sent.",
                "redirect" : "true",
                "redirect_url" : reverse('purchases:asset_purchase',kwargs={'pk':pk})
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
        email = instance.vendor.email
        name = instance.vendor.name
        content = "Thanks for your service %s. Please follow the below link for your service details." %current_shop.name

        form = EmailAssetPurchaseForm(initial={'name' : name, 'email' : email, 'content' : content})

        context = {
            "instance" : instance,
            "title" : "Email Purchase : #" + str(instance.a_id),
            "single_page" : True,
            'form' : form,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_animations" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'purchases/email_asset_purchase.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_purchase'])
def purchase_item_split(request,pk):
    PurchaseItemSplitFormset = formset_factory(PurchaseItemSplitForm, extra=1)
    current_shop = get_current_shop(request)
    instance = get_object_or_404(PurchaseItem.objects.filter(is_deleted=False,pk=pk))

    if request.method == 'POST':
        purchase_item_split_formset = PurchaseItemSplitFormset(request.POST,prefix='purchase_item_split_formset')
        old_qty = instance.qty_to_split
        total_taken_sum = 0

        if purchase_item_split_formset.is_valid():
            main_product_unit = instance.product.unit

            for f in purchase_item_split_formset:
                conversion = f.cleaned_data['conversion']
                qty = f.cleaned_data['qty']
                total_taken = conversion * qty
                total_taken_sum += total_taken
            is_ok = True
            if old_qty < total_taken_sum:
                is_ok = False
                message = "Sum of split values are higher than actual qty"
            if is_ok:
                for f in purchase_item_split_formset:
                    product = f.cleaned_data['product']
                    qty = f.cleaned_data['qty']
                    unit = instance.product.unit
                    exact_qty = get_exact_qty(qty,unit)
                    conversion = f.cleaned_data['conversion']
                    total_packing_charge = product.packing_charge * qty
                    total_taken = conversion * qty


                    total_exact_qty = get_exact_qty(total_taken,main_product_unit)

                    PurchaseItemSplit(
                        product = product,
                        purchase_item = instance,
                        qty = qty,
                        conversion = conversion,
                        packing_charge = total_packing_charge,
                        total_taken = total_taken
                    ).save()

                    update_sock(product.pk,exact_qty,"increase")
                    update_sock(instance.product.pk,total_exact_qty,"decrease")

                if old_qty > total_taken_sum:
                    qty_to_split = old_qty - total_taken_sum
                    instance.qty_to_split = qty_to_split
                else:
                    instance.is_split = True
                    instance.qty_to_split = 0
                    
                instance.save()

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Split Purchase Item created successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('purchases:purchase',kwargs={"pk":instance.purchase.pk})
                }
            else:
                response_data = {
                    "status" : "false",
                    "stable" : "true",
                    "title" : "Value mismatching",
                    "message" : message
                }

        else:
            message = generate_form_errors(purchase_item_split_formset, formset=True)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        purchase_item_split_formset = PurchaseItemSplitFormset(prefix='purchase_item_split_formset')

        context = {
            "purchase_item_split_formset" : purchase_item_split_formset,
            "instance" : instance,
            "title" : "Split purchase item",
            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "purchases" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
            "redirect" : True,
            "is_need_animations": True,
            "block_payment_form_media" : True,
        }
        return render(request,'purchases/purchase_item_split.html',context)