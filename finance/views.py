from django.shortcuts import render, get_object_or_404
from main.decorators import  ajax_required, check_mode
from django.contrib.auth.decorators import login_required
from finance.forms import TransactionForm, BankAccountForm, CashAccountForm,\
    TransactionCategoryForm, TransactionCategoryModelForm, SalaryPaymentForm,LedgerForm,TaxCategoryForm, CreditDebitForm, CashTransferForm
from django.urls import reverse
from main.functions import generate_form_errors
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from finance.models import TransactionCategory, Transaction, BankAccount,\
    CashAccount,TaxCategory, StaffSalaryPayment, CashTransfer, Journel
import datetime
from django.db.models import Q
from main.functions import get_auto_id,get_a_id, get_current_role
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from products.models import Product
from users.functions import get_current_shop
from staffs.models import Staff, StaffSalary
from distributors.models import Distributor
from django.db.models import Sum
from django.core import serializers


@check_mode
@login_required
@shop_required
@permissions_required(['can_manage_finance'])
def dashboard(request):
    return HttpResponseRedirect(reverse('finance:transactions'))


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_salary_payment'])
def create_salary_payment(request): 
    current_shop = get_current_shop(request) 
    transaction_category =get_object_or_404(TransactionCategory.objects.filter(is_system_generated=True,is_deleted=False,shop=current_shop,category_type="expense",name="staff_payment"))
    if request.method == "POST":
        form = SalaryPaymentForm(request.POST)
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        
        if form.is_valid(): 
            auto_id = get_auto_id(Transaction)
            a_id = get_a_id(Transaction,request)
            
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']
            amount = form.cleaned_data['amount']
            staff = form.cleaned_data['staff']

            amount_remaining = amount
            staff_salaries = StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff).order_by('date_added')

            latest_staff_salary = None
            if staff_salaries:
                latest_staff_salary = StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff).latest('date_added')

            if latest_staff_salary:
                advance_amount = latest_staff_salary.advance
                amount_remaining += advance_amount
            saved_salaries = []
            for staff_salary in staff_salaries:
                balance = staff_salary.balance
                advance = staff_salary.advance
                if balance > 0:
                    if balance <= amount_remaining:
                        staff_salary.balance = 0
                        staff_salary.paid = staff_salary.amount
                        staff_salary.save()
                        amount_remaining -= balance

                        dict_obj = {
                            "staff_salary" : staff_salary,
                            "amount" : staff_salary.amount,
                        }
                        saved_salaries.append(dict_obj)

                    else:
                        if amount_remaining > 0:
                            staff_salary.balance = staff_salary.balance - amount_remaining
                            staff_salary.paid = staff_salary.paid + amount_remaining
                            staff_salary.save()
                            amount_remaining -= balance

                            dict_obj = {
                                "staff_salary" : staff_salary,
                                "amount" : staff_salary.paid + amount_remaining,
                            }
                            saved_salaries.append(dict_obj)
                        else:
                            break

            if amount_remaining > 0:
                if StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff):
                    latest_staff_salary = StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff).latest('date_added')
                    latest_staff_salary.advance = amount_remaining
                    latest_staff_salary.save()

            #create salary payment
            data = form.save(commit=False)
            
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
                balance = data.bank_account.balance
                balance = balance - amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    data.card_details = None
                        
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
                
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id            
            data.transaction_type = "expense"
            data.shop = current_shop
            data.transaction_category = transaction_category
            data.staff_salary = staff_salary
            data.a_id = a_id
            data.title = "%s:%s" %(staff.designation,staff.name)
            data.save()

            if transaction_mode == "cash":
                cash_credit = amount
                bank_credit = 0
            elif transaction_mode == "bank":
                cash_credit = 0
                bank_credit = amount

            Journel.objects.create(
                date = datetime.date.today(),
                cash_credit = cash_credit,
                bank_credit = bank_credit,
                transaction = data,
                expense = amount
            )

            for saved_salary in saved_salaries:
                amount = saved_salary['amount']
                staff_salary = saved_salary['staff_salary']
            auto_id = get_auto_id(StaffSalaryPayment)
            a_id = get_a_id(StaffSalaryPayment,request)

            StaffSalaryPayment.objects.create(
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                transaction=data,
                amount=amount,
                staff_salary=staff_salary,
                creator=request.user,
                updator=request.user,
                )

            response_data = {
                "status" : 'true',
                "title" : "Successfully Created" ,
                "redirect" : "true",
                "redirect_url" : reverse('finance:transaction', kwargs = {'pk' : data.pk}),
                "message" : "Salary payment Successfully Created."
            }
        else:
            
            message = ''            
            message += generate_form_errors(form,formset=False) 
                  
            response_data = {
                "status" : 'false',
                "title" : "Form Validation Error" ,
                "stable" : "true",
                "message" : message,
            }
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:    
        form = SalaryPaymentForm()
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        context = {
            "form" : form,
            "title" : "Create Salary Payment ",
            "url" : reverse('finance:create_salary_payment'),

            "payment_page" : True,
            "is_create_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_salary_payment.html', context) 

    
@check_mode
@login_required
@shop_required
@permissions_required(['can_create_salary_payment'])
def create_salary_payment_ajax(request):
    current_shop = get_current_shop(request) 
    transaction_category =get_object_or_404(TransactionCategory.objects.filter(is_system_generated=True,is_deleted=False,shop=current_shop,category_type="expense",name="staff_payment"))
    if request.method == "POST":
        form = SalaryPaymentForm(request.POST)
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        
        if form.is_valid(): 
            auto_id = get_auto_id(Transaction)
            a_id = get_a_id(Transaction,request)
            
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']
            amount = form.cleaned_data['amount']
            staff = form.cleaned_data['staff']

            amount_remaining = amount
            staff_salaries = StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff).order_by('date_added')

            latest_staff_salary = None
            if staff_salaries:
                latest_staff_salary = StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff).latest('date_added')

            if latest_staff_salary:
                advance_amount = latest_staff_salary.advance
                amount_remaining += advance_amount
            saved_salaries = []
            for staff_salary in staff_salaries:
                balance = staff_salary.balance
                advance = staff_salary.advance
                if balance > 0:
                    if balance <= amount_remaining:
                        staff_salary.balance = 0
                        staff_salary.paid = staff_salary.amount
                        staff_salary.save()
                        amount_remaining -= balance

                        dict_obj = {
                            "staff_salary" : staff_salary,
                            "amount" : staff_salary.amount,
                        }
                        saved_salaries.append(dict_obj)

                    else:
                        if amount_remaining > 0:
                            staff_salary.balance = staff_salary.balance - amount_remaining
                            staff_salary.paid = staff_salary.paid + amount_remaining
                            staff_salary.save()
                            amount_remaining -= balance

                            dict_obj = {
                                "staff_salary" : staff_salary,
                                "amount" : staff_salary.paid + amount_remaining,
                            }
                            saved_salaries.append(dict_obj)
                        else:
                            break

            if amount_remaining > 0:
                if StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff):
                    latest_staff_salary = StaffSalary.objects.filter(shop=current_shop,is_deleted=False,staff=staff).latest('date_added')
                    latest_staff_salary.advance = amount_remaining
                    latest_staff_salary.save()

            #create salary payment
            data = form.save(commit=False)
            
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
                balance = data.bank_account.balance
                balance = balance - amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    data.card_details = None
                        
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

                
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id            
            data.transaction_type = "expense"
            data.shop = current_shop
            data.transaction_category = transaction_category
            data.staff_salary = staff_salary
            data.a_id = a_id
            data.title = "%s:%s" %(staff.designation,staff.first_name)
            data.save()

            if transaction_mode == "cash":
                cash_debit = amount
                bank_debit = 0
            elif transaction_mode == "bank":
                cash_debit = 0
                bank_debit = amount

            Journel.objects.create(
                date = datetime.date.today(),
                cash_debit = cash_debit,
                bank_debit = bank_debit,
                transaction = data,
                expense = amount
            )

            for saved_salary in saved_salaries:
                amount = saved_salary['amount']
                staff_salary = saved_salary['staff_salary']
            auto_id = get_auto_id(StaffSalaryPayment)
            a_id = get_a_id(StaffSalaryPayment,request)

            StaffSalaryPayment.objects.create(
                shop=current_shop,
                auto_id=auto_id,
                a_id=a_id,
                transaction=data,
                amount=amount,
                staff_salary=staff_salary,
                creator=request.user,
                updator=request.user,
                )

            response_data = {
                "status" : 'true',
                "title" : "Successfully Created" ,
                "redirect" : "true",
                "redirect_url" : reverse('finance:transaction', kwargs = {'pk' : data.pk}),
                "message" : "Salary payment Successfully Created."
            }
        else:
            
            message = ''            
            message += generate_form_errors(form,formset=False) 
                  
            response_data = {
                "status" : 'false',
                "title" : "Form Validation Error" ,
                "stable" : "true",
                "message" : message,
            }
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:  
        form = SalaryPaymentForm()
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        context = {
            "form" : form,
            "title" : "Create Salary Payment " ,
            "url" : reverse('finance:create_salary_payment'),
            "is_create_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_salary_payment.html', context) 
    
    
@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_salary_payment'])
def edit_salary_payment(request,pk): 
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    instance1 = instance.staff_salary
    edit_amount = instance.amount
    instance2 = instance.cash_account
    instance3 = instance.bank_account

    if request.method == "POST":
        form = SalaryPaymentForm(request.POST,instance=instance)
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        
        if form.is_valid(): 
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']
            amount = form.cleaned_data['amount']
            
            #Update salary payment
            data = form.save(commit=False)                                                                                                                                  
            
            balance = data.cash_account.balance
            balance1 = data.bank_account.balance

            if transaction_mode == "cash":
                if instance2 == None :
                    balance = balance - amount
                    balance1 = balance1 + amount
                else :
                    balance = balance + edit_amount - amount
                BankAccount.objects.filter(pk=data.bank_account.pk).update(balance=balance1)
                CashAccount.objects.filter(pk=data.cash_account.pk).update(balance=balance)
                
                data.payment_mode = None
                data.payment_to = "cash_account"
                data.bank_account = None
                data.cheque_details = None
                data.card_details = None
                data.is_cheque_withdrawed = False
                
            elif transaction_mode == "bank":
                if instance3 == None :
                    balance = balance + amount
                    balance1 = balance1 - amount
                else :
                    balance1 = balance1 + edit_amount -amount
                BankAccount.objects.filter(pk=data.bank_account.pk).update(balance=balance1)
                CashAccount.objects.filter(pk=data.cash_account.pk).update(balance=balance)
                
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    data.card_details = None
                        
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
            balance = instance1.balance
            paid = instance1.paid
            advance = instance1.advance
            salary_amount = instance1.amount
            if edit_amount != data.amount:   
                if paid == edit_amount:
                    paid = data.amount
                    balance = salary_amount-data.amount
                    if balance<0:
                        advance = data.amount-salary_amount
                else:
                    paid = paid-edit_amount + data.amount
                    balance = salary_amount- paid
                    if balance<0:
                        advance = paid -salary_amount
            StaffSalary.objects.filter(pk=instance1.pk,shop=current_shop).update(balance=balance,paid=paid,advance=advance)               
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.shop=current_shop
            data.save()
            
            response_data = {
                "status" : 'true',
                "title" : "Successfully Updated" ,
                "redirect" : "true",
                "redirect_url" : reverse('finance:transaction', kwargs = {'pk' : data.pk}),
                "message" : "Salary payment Successfully Updated."
            }
        else:
            
            message = ''            
            message += generate_form_errors(form,formset=False) 
                  
            response_data = {
                "status" : 'false',
                "title" : "Form Validation Error" ,
                "stable" : "true",
                "message" : message,
            }
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = SalaryPaymentForm(instance=instance)
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        context = {
            "form" : form,
            "title" : "Edit Salary Payment",
            'instance' : instance,
            "url" : reverse('finance:edit_salary_payment', kwargs={'pk':pk}),
            "payment_page" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_salary_payment.html', context)
  

@check_mode
@login_required
@shop_required
@permissions_required(['can_view_salary_payment'])
def salary_payments(request):
    current_shop = get_current_shop(request) 
 
    instances = Transaction.objects.filter(is_deleted=False,shop=current_shop,transaction_category__name='staff_salary')

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(staff__name__icontains=query) | Q(date__icontains=query) | Q(amount__icontains=query))
        
    title = "Salary Payments"
    context = {
        'title' : title,
        "instances" : instances,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_chosen_select" : True,
        "is_need_animations" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'finance/salary_payments.html',context)
    

@check_mode
@login_required
@shop_required
@permissions_required(['can_create_bank_account'])
def create_bank_account(request):

    current_shop = get_current_shop(request) 
    if request.method == "POST":
        response_data = {} 
        form = BankAccountForm(request.POST)
        
        if form.is_valid(): 

            first_balance = form.cleaned_data['first_time_balance']
            auto_id = get_auto_id(BankAccount)
            a_id = get_a_id(BankAccount,request)
                       
            #create Bank Account
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.balance = first_balance
            data.shop = current_shop
            data.save()
            
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Created"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:bank_account', kwargs = {'pk' : data.pk})
            response_data['message'] = "Bank account Successfully Created."
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"
            
            message = ''            
            message += generate_form_errors(form,formset=False)                
            response_data['message'] = form.errors
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = BankAccountForm()
        
        context = {
            "form" : form,
            "title" : "Create Bank Account",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_bank_account.html', context)
  

@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_bank_account'])
def edit_bank_account(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(BankAccount.objects.filter(pk=pk,is_deleted=False,shop=current_shop))  
    
    if request.method == "POST":
        response_data = {}
        form = BankAccountForm(request.POST,instance=instance)
        
        if form.is_valid(): 
                       
            #update Bank Account
            first_balance = form.cleaned_data['first_time_balance'] 
            data = form.save(commit=False)
            data.updator = request.user
            data.balance = first_balance
            data.date_updated = datetime.datetime.now()
            data.save()
            
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Updated"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:bank_account', kwargs = {'pk' : data.pk})
            response_data['message'] = "Bank Account Successfully Updated."
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"
            
            message = ''            
            message += generate_form_errors(form,formset=False)                
            response_data['message'] = message
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = BankAccountForm(instance=instance)
        
        context = {
            "form" : form,
            "title" : "Edit Bank Account : " + instance.name,
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
        return render(request, 'finance/entry_bank_account.html', context)
  

@check_mode
@login_required
@shop_required
@permissions_required(['can_view_bank_account'],roles=['distributor'],both_check=False)
def bank_accounts(request):
    current_shop = get_current_shop(request) 
    instances = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
    
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query) | Q(account_no__icontains=query))
        
    title = "Bank Accounts"
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
    return render(request,'finance/bank_accounts.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_bank_account'])
def bank_account(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(BankAccount.objects.filter(pk=pk,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Bank Account : " + instance.name,
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
    return render(request,'finance/bank_account.html',context)
    

@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_bank_account'])
def delete_bank_account(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(BankAccount.objects.filter(pk=pk,shop=current_shop))
    
    BankAccount.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted")
    
    response_data = {}
    response_data['status'] = 'true'        
    response_data['title'] = "Successfully Deleted"       
    response_data['redirect'] = 'true' 
    response_data['redirect_url'] = reverse('finance:bank_accounts')
    response_data['message'] = "Bank Account Successfully Deleted."
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_bank_account'])
def delete_selected_bank_accounts(request):
    current_shop = get_current_shop(request) 
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(BankAccount.objects.filter(pk=pk,is_deleted=False,shop=current_shop)) 
            BankAccount.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Bank Account(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('finance:bank_accounts')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some bank accounts first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_cash_account'])
def create_cash_account(request): 

    current_shop = get_current_shop(request)
    if request.method == "POST":
        response_data = {}
        form = CashAccountForm(request.POST)
        
        if form.is_valid(): 
            
            auto_id = get_auto_id(CashAccount)
            a_id = get_a_id(CashAccount,request)
                       
            #create Cash Account
            first_balance = form.cleaned_data['first_time_balance']
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.balance = first_balance
            data.shop = current_shop
            data.user = request.user
            data.save()
            
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Created"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:cash_account', kwargs = {'pk' : data.pk})
            response_data['message'] = "Cash account Successfully Created."
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"
            
            message = ''            
            message += generate_form_errors(form,formset=False)                
            response_data['message'] = form.errors
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = CashAccountForm()
        
        context = {
            "form" : form,
            "title" : "Create Cash Account",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_cash_account.html', context)
  

@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_cash_account'])
def edit_cash_account(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(CashAccount.objects.filter(pk=pk,shop=current_shop))  
    
    if request.method == "POST":
        response_data = {}
        form = CashAccountForm(request.POST,instance=instance)
        
        if form.is_valid(): 
                       
            #update Bank Account
            data = form.save(commit=False)
            first_balance = form.cleaned_data['first_time_balance']
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.balance = first_balance
            data.save()
            
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Updated"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:cash_account', kwargs = {'pk' : data.pk})
            response_data['message'] = "Cash Account Successfully Updated."
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"
            
            message = ''            
            message += generate_form_errors(form,formset=False)                
            response_data['message'] = message
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = CashAccountForm(instance=instance)
        
        context = {
            "form" : form,
            "title" : "Edit Cash Account : " + instance.name,
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
        return render(request, 'finance/entry_cash_account.html', context)
  

@check_mode
@login_required
@shop_required
@permissions_required(['can_view_cash_account'],roles=['distributor'],both_check=False)
def cash_accounts(request):
    current_shop = get_current_shop(request) 
    current_role = get_current_role(request) 
    instances = CashAccount.objects.filter(is_deleted=False,shop=current_shop)
    if current_role == "distributor":
        instances = instances.filter(user=request.user)
    
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))
        
    title = "Cash Accounts"
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
    return render(request,'finance/cash_accounts.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_cash_account'])
def cash_account(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(CashAccount.objects.filter(pk=pk,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Cash Account : " + instance.name,
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
    return render(request,'finance/cash_account.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_cash_account'])
def delete_cash_account(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(CashAccount.objects.filter(pk=pk,shop=current_shop,is_system_generated=False))

    CashAccount.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted")
    
    response_data = {}
    response_data['status'] = 'true'        
    response_data['title'] = "Successfully Deleted"       
    response_data['redirect'] = 'true' 
    response_data['redirect_url'] = reverse('finance:cash_accounts')
    response_data['message'] = "Cash Account Successfully Deleted."
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_cash_account'])
def delete_selected_cash_accounts(request):
    current_shop = get_current_shop(request) 
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(CashAccount.objects.filter(pk=pk,is_deleted=False,shop=current_shop,is_system_generated=False)) 
            CashAccount.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected CashAccount(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('finance:cash_accounts')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some cash accounts first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode    
@login_required
@shop_required
@permissions_required(['can_create_transaction_category'],roles=['distributor'],both_check=False)
def create_transaction_category(request): 

    current_shop = get_current_shop(request)
    if request.method == "POST":
        response_data = {} 
        form = TransactionCategoryModelForm(request.POST)
        
        if form.is_valid(): 
            name = form.cleaned_data['name']
            category_type = form.cleaned_data['category_type']
            names = name.split(',')
            for n in names:
                if not TransactionCategory.objects.filter(name=n,category_type=category_type).exists():
                    TransactionCategory(
                        name = n.strip(),
                        category_type = category_type,
                        creator = request.user,
                        updator = request.user,
                        auto_id = get_auto_id(TransactionCategory),
                        a_id = get_a_id(TransactionCategory,request),
                        shop = current_shop
                    ).save()
                    
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Created"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:transaction_categories')
            response_data['message'] = "Transaction categories Successfully Created."
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"
            
            message = ''            
            message += generate_form_errors(form,formset=False)                
            response_data['message'] = message
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = TransactionCategoryModelForm()
        
        context = {
            "form" : form,
            "title" : "Create Transaction Category",

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_transaction_category.html', context)
  
 
@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_transaction_category'],allow_self=True,model=TransactionCategory)
def edit_transaction_category(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(TransactionCategory.objects.filter(pk=pk,shop=current_shop))  
    
    if request.method == "POST":
        response_data = {}
        form = TransactionCategoryModelForm(request.POST,instance=instance)
        
        if form.is_valid(): 
            name = form.cleaned_data['name'].strip()
            category_type = form.cleaned_data['category_type']
            
            #update Transaction Category
            data = form.save(commit=False)
            data.name = name.strip()
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()
            
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Updated"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:transaction_category', kwargs = {'pk' : data.pk})
            response_data['message'] = "Transaction Category Successfully Updated."
            
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"
            
            message = ''            
            message += generate_form_errors(form,formset=False)                
            response_data['message'] = message
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = TransactionCategoryModelForm(instance=instance)
        
        context = {
            "form" : form,
            "title" : "Edit Transaction Category : " + instance.name,
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
        return render(request, 'finance/entry_transaction_category.html', context)
  
     
@check_mode
@login_required
@shop_required
@permissions_required(['can_view_transaction_category'])
def transaction_categories(request):
    current_shop = get_current_shop(request) 
    instances = TransactionCategory.objects.filter(is_system_generated=False,is_deleted=False,shop=current_shop)
    
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query) | Q(category_type__icontains=query))
        
    title = "Transaction Categories"
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
    return render(request,'finance/transaction_categories.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_transaction_category'],allow_self=True,model=TransactionCategory)
def transaction_category(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(TransactionCategory.objects.filter(pk=pk,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Transaction Category : " + instance.name,
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
    return render(request,'finance/transaction_category.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_transaction_category'],allow_self=True,model=TransactionCategory)
def delete_transaction_category(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(TransactionCategory.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    TransactionCategory.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted")
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Transaction Category Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('finance:transaction_categories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_transaction_category'])
def delete_selected_transaction_categories(request):
    current_shop = get_current_shop(request) 
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(TransactionCategory.objects.filter(pk=pk,is_deleted=False,shop=current_shop)) 
            TransactionCategory.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Transaction Category(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('finance:transaction_categories')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some transaction categories first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_income'],roles=['distributor'],both_check=False)
def create_income(request): 

    current_role = get_current_role(request)
    current_shop = get_current_shop(request)
    if request.method == "POST":
        response_data = {}
        form = CreditDebitForm(request.POST)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="income",is_system_generated=False) | Q(category_type="income",name="credit"))
    
        if form.is_valid():            
             
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']       
            transaction_category = form.cleaned_data['transaction_category']
            amount = form.cleaned_data['amount']
            
            #create income
            data = form.save(commit=False)
            
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
                balance = data.bank_account.balance
                balance = balance + amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = form.cleaned_data['is_cheque_withdrawed'] 
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
            if not transaction_category.name == "credit":
                data.shop_credit_user = None

            data.auto_id = get_auto_id(Transaction) 
            data.a_id = get_a_id(Transaction,request)            
            data.creator = request.user
            data.updator = request.user
            data.transaction_type = "income"
            data.shop = current_shop
            data.save()

            if transaction_mode == "cash":
                cash_debit = amount
                bank_debit = 0
            elif transaction_mode == "bank":
                cash_debit = 0
                bank_debit = amount

            Journel.objects.create(
                date = datetime.date.today(),
                cash_debit = cash_debit,
                bank_debit = bank_debit,
                transaction = data,
                income = amount
            )
            
            return HttpResponseRedirect(reverse('finance:transaction',kwargs={'pk':data.pk}))
        else:
            form = CreditDebitForm(request.POST)
            form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
            form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
            form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="income",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="income",name="credit",shop=current_shop))
        
            context = {
                "form" : form,
                "title" : "Create Income",
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
            return render(request, 'finance/entry_income.html', context)

    else: 
        form = CreditDebitForm()
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="income",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="income",name="credit",shop=current_shop))
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        if current_role == "distributor":
            TRANSACTION_MODE = (
                ("cash", "Cash"),
            )
            form.fields['transaction_mode'].choices = TRANSACTION_MODE

        context = {
            "form" : form,
            "title" : "Create Income",
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
        return render(request, 'finance/entry_income.html', context)
    
    
@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_income'],allow_self=True,model=Transaction)
def edit_income(request,pk):
    current_shop = get_current_shop(request)   
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,shop=current_shop))
    
    current_role = get_current_role(request)

    if request.method == "POST":
        form = CreditDebitForm(request.POST,instance=instance)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="income",is_system_generated=False,shop=current_shop) | Q(category_type="income",name="credit",shop=current_shop))
        
        if form.is_valid(): 
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']       
            transaction_category = form.cleaned_data['transaction_category']
            amount = form.cleaned_data['amount']
            
            #Update income
            data = form.save(commit=False)
            
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
                balance = data.bank_account.balance
                balance = balance + amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = form.cleaned_data['is_cheque_withdrawed'] 
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
                
            if not transaction_category.name == "credit":
                data.shop_credit_user = None                
                
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            
            data.save()
            
            return HttpResponseRedirect(reverse('finance:transaction',kwargs={'pk':data.pk}))
        else:
            form = CreditDebitForm(instance=instance)
            form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
            form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="income",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="income",name="credit",shop=current_shop))
            form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
            if current_role == "distributor":
                TRANSACTION_MODE = (
                    ("cash", "Cash"),
                )
                form.fields['transaction_mode'].choices = TRANSACTION_MODE
            context = {
                "form" : form,
                "title" : "Edit Income - " + instance.transaction_category.name,
                "instance" :instance,

                "is_need_select_picker" : True,
                "is_need_popup_box" : True,
                "is_need_custom_scroll_bar" : True,
                "is_need_wave_effect" : True,
                "is_need_bootstrap_growl" : True,
                "is_need_chosen_select" : True,
                "is_need_grid_system" : True,
                "is_need_datetime_picker" : True,
            }
            return render(request, 'finance/entry_income.html', context)

    else: 
        form = CreditDebitForm(instance=instance)
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="income",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="income",name="credit",shop=current_shop))
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        if current_role == "distributor":
            TRANSACTION_MODE = (
                ("cash", "Cash"),
            )
            form.fields['transaction_mode'].choices = TRANSACTION_MODE

        context = {
            "form" : form,
            "title" : "Edit Income - " + instance.transaction_category.name,
            "instance" :instance,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'finance/entry_income.html', context)
    

@check_mode
@login_required
@shop_required
@permissions_required(['can_view_transaction'],roles=['distributor'],both_check=False)
def transactions(request):
    current_shop = get_current_shop(request)
    current_role = get_current_role(request) 
    today = datetime.date.today()
    year = request.GET.get('year')
    month = request.GET.get('month')
    period = request.GET.get('period')
    date = request.GET.get('date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_type = request.GET.get('transaction_type')
    title = "Transactions"
    instances = Transaction.objects.filter(is_deleted=False,shop=current_shop)
    transaction_categories = TransactionCategory.objects.filter(is_system_generated=False,shop=current_shop)
    
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(transaction_type__icontains=query) | Q(transaction_mode__icontains=query) | Q(date__icontains=query))
        
    transaction_category = request.GET.get("transaction_category")
    if transaction_category:
        instances = instances.filter(Q(transaction_category=transaction_category))

    if transaction_type:
        instances = instances.filter(transaction_type=transaction_type)

    filter_date = date
    filter_from_date = from_date
    filter_to_date = to_date

    date_error = "no"
    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()          
        except ValueError:
            date_error = "yes"

    if year:
        instances = instances.filter(date__year=year)

    if month:
        instances = instances.filter(date__month=month)
            
    #filter by date created range   

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
            title = "Transactions : This Year"
            instances = instances.filter(date__year=today.year)
        elif period == 'month' :
            title = "Transactions : This Month"
            instances = instances.filter(date__year=today.year,date__month=today.month)
        elif period == "today" :
            title = "Transactions : Today"
            instances = instances.filter(date__year=today.year,date__month=today.month,date__day=today.day)

    elif filter_date_period:
        title = "Transactions : From %s to %s " %(str(filter_from_date),str(filter_to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, date__range=[from_date, to_date])
            
    elif date:
        title = "Transactions : Date : %s" %(str(date))
        if date_error == "no":
            instances = instances.filter(date__month=date.month,date__year=date.year,date__day=date.day)
        
    if current_role == "distributor":
        instances = instances.filter(creator=request.user)

    context = {
        'title' : title,
        "instances" : instances,
        "transaction_categories" : transaction_categories,

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
    return render(request,'finance/transactions.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_transaction'],allow_self=True,model=Transaction)
def transaction(request,pk):
    current_shop = get_current_shop(request) 
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,shop=current_shop))
    context = {
        "instance" : instance,
        "title" : "Transaction",
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
    return render(request,'finance/transaction.html',context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_transaction'],allow_self=True,model=Transaction)
def delete_transaction(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,is_deleted=False)) 
    balance = 0
    account = None
    if instance.cash_account:
        account = instance.cash_account
        balance = account.balance
        amount = instance.amount
        if instance.transaction_type == "income":
            account.balance = balance - amount
        elif instance.transaction_type == "expense":
            account.balance = balance + amount
        account.save()

    elif instance.bank_account:
        account = instance.bank_account
        balance = account.balance
        amount = instance.amount
        if instance.transaction_type == "income":
            account.balance = balance - amount
        elif instance.transaction_type == "expense":
            account.balance = balance + amount
        account.save()
    Transaction.objects.filter(pk=pk).update(is_deleted=True,shop=current_shop)
    
    response_data = {}
    response_data['status'] = 'true'        
    response_data['title'] = "Successfully Deleted"       
    response_data['redirect'] = 'true' 
    response_data['redirect_url'] = reverse('finance:transactions')
    response_data['message'] = "Transaction Successfully Deleted."
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_transaction'])
def delete_selected_transactions(request):
    current_shop = get_current_shop(request) 
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(Transaction.objects.filter(pk=pk,is_deleted=False,shop=current_shop)) 
            balance = 0
            account = None
            if instance.cash_account:
                account = instance.cash_account
                balance = account.balance
                amount = instance.amount
                if instance.transaction_type == "income":
                    account.balance = balance - amount
                elif instance.transaction_type == "expense":
                    account.balance = balance + amount
                account.save()

            elif instance.bank_account:
                account = instance.bank_account
                balance = account.balance
                amount = instance.amount
                if instance.transaction_type == "income":
                    account.balance = balance - amount
                elif instance.transaction_type == "expense":
                    account.balance = balance + amount
                account.save() 
            Transaction.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,transaction_mode=instance.transaction_mode + "_deleted_" + str(instance.auto_id))
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Transaction(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('finance:transactions')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some transactions first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_expense'],roles=['distributor'],both_check=False)
def create_expense(request):  
    
    current_shop = get_current_shop(request)
    current_role = get_current_role(request)
    if request.method == "POST":
        form = CreditDebitForm(request.POST)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="expense",is_system_generated=False,shop=current_shop) | Q(category_type="expense",name="debit",shop=current_shop))
        
        if form.is_valid(): 
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']       
            transaction_category = form.cleaned_data['transaction_category']
            amount = form.cleaned_data['amount']
            #create expense
            data = form.save(commit=False)
            
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
                balance = data.bank_account.balance
                balance = balance - amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    data.card_details = None
                        
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
            if not transaction_category.name == "debit":
                data.shop_credit_user = None     
                         
            data.creator = request.user
            data.updator = request.user
            data.transaction_type = "expense"
            data.auto_id = get_auto_id(Transaction)
            data.a_id = get_a_id(Transaction,request)
            data.shop = current_shop
            data.save()
            
            if transaction_mode == "cash":
                cash_debit = amount
                bank_debit = 0
            elif transaction_mode == "bank":
                cash_debit = 0
                bank_debit = amount

            Journel.objects.create(
                date = datetime.date.today(),
                cash_debit = cash_debit,
                bank_debit = bank_debit,
                transaction = data,
                expense = amount
            )
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Expense created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('finance:transaction',kwargs={'pk':data.pk})
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
        form = CreditDebitForm()
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="expense",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="expense",name="debit",shop=current_shop))
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        if current_role == "distributor":
            TRANSACTION_MODE = (
                ("cash", "Cash"),
            )
            form.fields['transaction_mode'].choices = TRANSACTION_MODE

        context = {
            "form" : form,
            "title" : "Create Expense",
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
        return render(request, 'finance/entry_expense.html', context)
 

@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_expense'],allow_self=True,model=Transaction)
def edit_expense(request,pk): 
    current_shop = get_current_shop(request)
    current_role = get_current_role(request) 
    instance = get_object_or_404(Transaction.objects.filter(pk=pk,shop=current_shop))
    
    if request.method == "POST":
        form = CreditDebitForm(request.POST,instance=instance )
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="expense",is_system_generated=False,shop=current_shop) | Q(category_type="expense",name="debit",shop=current_shop))
        
        if form.is_valid(): 
            transaction_mode = form.cleaned_data['transaction_mode']
            payment_to = form.cleaned_data['payment_to']       
            transaction_category = form.cleaned_data['transaction_category']
            amount = form.cleaned_data['amount']
            
            #Update expense
            data = form.save(commit=False)
            
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
                balance = data.bank_account.balance
                balance = balance - amount
                BankAccount.objects.filter(pk=data.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = form.cleaned_data['payment_mode'] 
                if payment_mode == "cheque_payment":
                    data.card_details = None
                        
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
                
            if not transaction_category.name == "debit":
                data.shop_credit_user = None                
                
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            
            data.save()
            
            return HttpResponseRedirect(reverse('finance:transaction',kwargs={'pk':data.pk}))
        else:
            form = CreditDebitForm(instance=instance)
            form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
            form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="expense",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="expense",name="debit",shop=current_shop))
            form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
            if current_role == "distributor":
                TRANSACTION_MODE = (
                    ("cash", "Cash"),
                )
                form.fields['transaction_mode'].choices = TRANSACTION_MODE
            context = {
                "form" : form,
                "title" : "Edit Expense",
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
            return render(request, 'finance/entry_expense.html', context) 

    else: 
        form = CreditDebitForm(instance=instance)
        form.fields['bank_account'].queryset = BankAccount.objects.filter(is_deleted=False,shop=current_shop)
        form.fields['transaction_category'].queryset = TransactionCategory.objects.filter(Q(category_type="expense",is_system_generated=False, is_deleted=False,shop=current_shop) | Q(category_type="expense",name="debit",shop=current_shop))
        form.fields['cash_account'].queryset = CashAccount.objects.filter(is_deleted=False,shop=current_shop,user=request.user)
        if current_role == "distributor":
            TRANSACTION_MODE = (
                ("cash", "Cash"),
            )
            form.fields['transaction_mode'].choices = TRANSACTION_MODE
        context = {
            "form" : form,
            "title" : "Edit Expense",
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
        return render(request, 'finance/entry_expense.html', context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_tax_category'])
def create_tax_category(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = TaxCategoryForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(TaxCategory)
            a_id = get_a_id(TaxCategory, request)
            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.creator = request.user
            data.updator = request.user
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Tax category created successfully.",
                "redirect": "true",
                "redirect_url": reverse('finance:tax_categories')
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
        form = TaxCategoryForm()

        context = {
            "title": "Create Tax Category",
            "form": form,
            "redirect": "true",

            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_chosen_select": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_datetime_picker": True,
            
        }
        return render(request, 'finance/entry_tax_category.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_tax_category'])
def tax_categories(request):
    current_shop = get_current_shop(request)
    instances = TaxCategory.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)) 

    context = {
        'instances': instances,
        "title": 'Tax Categories',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_select_picker" : True,
        "is_need_grid_system": True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
    }
    return render(request, "finance/tax_categories.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_tax_category'])
def edit_tax_category(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(TaxCategory.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)) 


    if request.method == "POST":
        form = TaxCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False) 
            tax = data.tax           
            Product.objects.filter(is_deleted=False,tax_category=pk).update(tax=tax)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Tax Category updated successfully.",
                "redirect": "true",
                "redirect_url": reverse('finance:tax_categories')
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
        form = TaxCategoryForm(instance=instance)

        context = {
            "instance": instance,
            "title": "Edit Tax Category :" + instance.name,
            "form": form,
            "redirect": "true",
            "url": reverse('finance:edit_tax_category', kwargs={'pk': instance.pk}),

            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_select_picker" : True,
            "is_need_bootstrap_growl": True,
            "is_need_grid_system": True,
            "is_need_animations": True,
            
        }
        return render(request, 'finance/entry_tax_category.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_tax_category'])
def tax_category(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(TaxCategory.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    context = {
        'instance': instance,
        'title': 'Tax Category',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_grid_system": True,
        "is_need_select_picker" : True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
        
    }
    return render(request, "finance/tax_category.html", context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_tax_category'])
def delete_tax_category(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(TaxCategory.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    TaxCategory.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    Product.objects.filter(is_deleted=False,tax_category=pk).update(tax=0,tax_category=None)
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Tax Category Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('finance:tax_categories')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_tax_category'])
def delete_selected_tax_categories(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(TaxCategory.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
            TaxCategory.objects.filter(pk=pk).update(
                is_deleted=True)
            Product.objects.filter(is_deleted=False,tax_category=instance).update(tax=0,tax_category=None)

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Tax Category Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('finance:tax_categories')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    

@check_mode
@login_required
@shop_required
@permissions_required(['can_create_cash_transfer'])
def create_cash_transfer(request): 
    current_shop = get_current_shop(request)
    if request.method == "POST":
        response_data = {} 
        form = CashTransferForm(request.POST)
        
        if form.is_valid(): 
            from_cash_account = form.cleaned_data['from_cash_account']
            to_cash_account = form.cleaned_data['to_cash_account']
            amount= form.cleaned_data['amount']

            is_ok = True
            message = ""

            if from_cash_account:
                if from_cash_account.balance < amount:
                    message += "Not enough cash in your account."
                    is_ok = False

            if is_ok :
                from_cash_account.balance = from_cash_account.balance - amount
                from_cash_account.save()  

                to_cash_account.balance = to_cash_account.balance + amount
                to_cash_account.save()  
                    
            data = form.save(commit=False)
            data.creator = request.user
            data.shop = current_shop
            data.updator = request.user
            data.auto_id = get_auto_id(CashTransfer)
            data.a_id = get_a_id(CashTransfer,request)
            data.save()
                    
            response_data['status'] = 'true'     
            response_data['title'] = "Successfully Transfered"       
            response_data['redirect'] = 'true' 
            response_data['redirect_url'] = reverse('finance:cash_transfers')
            response_data['message'] = "Cash Transfer Successfully Created."
        else:
            message = ''            
            message += generate_form_errors(form,formset=False)  
            response_data = {
                'status' : 'false',
                'title' : "Form validation error",
                'stable' : 'true',
                'message' : message,
            }
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = CashTransferForm()
        form.fields['from_cash_account'].queryset = CashAccount.objects.filter(user__is_superuser=False)
        form.fields['to_cash_account'].queryset = CashAccount.objects.filter(user=request.user)
        
        context = {
            "form" : form,
            "title" : "Create cash Transfer",
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
        return render(request, 'finance/entry_cash_transfer.html', context)


@check_mode
@login_required
@permissions_required(['can_view_cash_account'])
def cash_transfers(request): 
    current_role = get_current_role(request)
    instances = CashTransfer.objects.filter(is_deleted=False)

    if current_role == "distributor":
        instances = instances.filter(distributor_user=request.user)
    
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))
        
    title = "Cash Transfers"
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
        "is_need_datetime_picker" : True,
    }
    return render(request,'finance/cash_transfers.html',context)


@check_mode
@login_required
@permissions_required(['can_view_transaction'])
def cash_transfer(request,pk): 
    instance = get_object_or_404(CashTransfer.objects.filter(pk=pk))
    context = {
        "instance" : instance,
        "title" : "Cash Transfer : " + str(instance.amount) ,
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
    return render(request,'finance/cash_transfer.html',context)


@check_mode
@ajax_required
@login_required
@permissions_required(['can_delete_cash_account'])
def delete_cash_transfer(request,pk): 
    instance = get_object_or_404(CashTransfer.objects.filter(pk=pk))
    
    CashTransfer.objects.filter(pk=pk).update(is_deleted=True)

    if instance.from_cash_account:
        instance.from_cash_account.balance = instance.from_cash_account.balance + instance.amount
        instance.from_cash_account.save()

    if instance.to_cash_account:
        instance.to_cash_account.balance = instance.to_cash_account.balance - instance.amount
        instance.to_cash_account.save() 

    response_data = {}
    response_data['status'] = 'true'        
    response_data['title'] = "Successfully Deleted"       
    response_data['redirect'] = 'true' 
    response_data['redirect_url'] = reverse('finance:cash_transfers')
    response_data['message'] = "Cash transfer Successfully Deleted."
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@permissions_required(['can_delete_customer_badge'])
def delete_selected_cash_transfers(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]
        
        pks = pks.split(',')
        for pk in pks:      
            instance = get_object_or_404(CashTransfer.objects.filter(pk=pk,is_deleted=False)) 
            CashTransfer.objects.filter(pk=pk).update(is_deleted=True)

            if instance.from_cash_account:
                instance.from_cash_account.balance = instance.from_cash_account.balance + instance.amount
                instance.from_cash_account.save()

            if instance.to_cash_account:
                instance.to_cash_account.balance = instance.to_cash_account.balance - instance.amount
                instance.to_cash_account.save() 
    
        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected cash transfer(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('finance:cash_transfers')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }
        
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def get_cash_account_list(request):
    pk = request.GET.get('pk')
    distributor = Distributor.objects.get(pk=pk)
    instances = CashAccount.objects.filter(user=distributor.user,is_deleted=False)
    json_models = serializers.serialize("json", instances)
    return HttpResponse(json_models, content_type="application/javascript")


@check_mode
@ajax_required
@login_required
@shop_required
def get_cash_balance(request):
    pk = request.GET.get('id')
    instance = CashAccount.objects.get(pk=pk,is_deleted=False)

    if instance:
        response_data = {
            "status" : "true",
            'amount' : float(instance.balance)
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "0.00"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@check_mode
@ajax_required
@login_required
@shop_required
def get_tax(request):
    pk = request.GET.get('id')
    instance = TaxCategory.objects.get(pk=pk,is_deleted=False)

    if instance:
        response_data = {
            "status" : "true",
            'tax' : float(instance.tax)
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "0.00"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
def create_balance_sheet(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    if today.day > 3 :
        year = today.year 
    else :
        year = today.year - 1 
    from_date = datetime.date(year,4,1)
    form = LedgerForm(initial={'to_date':today,'from_date':from_date})

    context = {
        'title' : "Create Balance Sheet",
        "form" : form,
        "url" : reverse('finance:balance_sheet'),

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,

    }
    return render(request,'finance/create_balance_sheet.html',context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_balance_sheet'])
def balance_sheet(request):
    current_shop = get_current_shop(request)
    instances = Journel.objects.filter(is_deleted=False)   
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    date_error = "no"
    filter_date_period = False
    filter_from_date = from_date
    filter_to_date = to_date
    if from_date and to_date:
        try:
            from_date = datetime.datetime.strptime(from_date, '%m/%d/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%m/%d/%Y').date()            
        except ValueError:
            date_error = "yes"  
            
        filter_date_period = True
    
    if filter_date_period:
        title = "Report : From %s to %s " %(str(from_date),str(to_date))
        if date_error == "no":
            instances = instances.filter(is_deleted=False, date__range=[from_date, to_date])  

    income = instances.filter(transaction__isnull=False).aggregate(amount=Sum('income')).get('amount',0) or 0
    expence = instances.filter(transaction__isnull=False).aggregate(amount=Sum('expense')).get('amount',0) or 0

    loss = expence
    profit = income

    if loss > profit :
        net_profit = 0
        net_loss = loss - profit
        net_total = loss
    else :
        net_profit = profit - loss
        net_loss = 0 
        net_total = profit

    capital_account = 0 
    capital_account = capital_account + net_profit - net_loss
    
    cash_debit = instances.aggregate(amount=Sum('cash_debit')).get('amount',0) or 0
    cash_credit = instances.aggregate(amount=Sum('cash_credit')).get('amount',0) or 0
    bank_debit = instances.aggregate(amount=Sum('bank_debit')).get('amount',0) or 0
    bank_credit = instances.aggregate(amount=Sum('bank_credit')).get('amount',0) or 0

    cash_in_hand_amount = cash_debit 
    bank_asset_amount = bank_debit

    capital_amount = capital_account 
    loan = cash_credit 

    debit = cash_in_hand_amount + bank_asset_amount 
    credit = capital_amount + loan + bank_credit 

    context = {
        "capital_account" : capital_account,
        "capital_amount" : capital_amount,
        "cash_debit" : cash_debit,
        "cash_credit" : cash_credit,
        "bank_credit" : bank_credit,
        "bank_debit" : bank_debit,
        "credit" : credit,
        "debit" : debit,

        "bank_asset_amount" : bank_asset_amount,
        "cash_in_hand_amount" : cash_in_hand_amount,
        "loans_and_liability" : loan,

        "title" : 'Balance Sheet',

        "from_date" : filter_from_date,
        "to_date" : filter_to_date,

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
    return render(request,'finance/balance_sheet.html', context)
    
