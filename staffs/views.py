from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponse, HttpResponseRedirect
from staffs.forms import DesignationForm, StaffForm, StaffSalaryForm
from staffs.models import Designation, Staff, StaffSalary
from main.models import Shop
import json
import datetime
from users.functions import get_current_shop
from main.functions import get_auto_id, generate_form_errors, get_a_id
from django.urls import reverse
from dal import autocomplete
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from django.utils import timezone
from datetime import date, time
import datetime
from django.forms.formsets import formset_factory
from finance.models import Transaction, CashAccount, BankAccount,TransactionCategory,Journel
from finance.forms import TransactionForm
from decimal import Decimal
from finance.functions import add_transaction


class DesignationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        current_shop = get_current_shop(self.request)
        items = Designation.objects.filter(is_deleted=False,shop=current_shop)

        if self.q:
            items = items.filter(Q(name__istartswith=self.q)
                                 )

        return items

    def create_object(self, text):
        current_shop = get_current_shop(self.request)
        auto_id = get_auto_id(Designation)
        a_id = get_a_id(Designation,self.request)

        return Designation.objects.create(
            auto_id=auto_id,
            a_id=a_id,
            name=text,
            shop=current_shop,
            creator=self.request.user,
            updator=self.request.user
        )


class StaffAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        staffs = Staff.objects.filter(is_deleted=False)

        if self.q:
            staff = staffs.filter(Q(first_name__istartswith=self.q)
                                 )
        return staff


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_designation'])
def create_designation(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = DesignationForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Designation)
            a_id = get_a_id(Designation, request)
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
                "message": "Designation created successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:designations')
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
        form = DesignationForm()

        context = {
            "title": "Create Designation",
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
        return render(request, 'staffs/designations/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_designation'])
def designations(request):
    current_shop = get_current_shop(request)
    instances = Designation.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)) 

    context = {
        'instances': instances,
        "title": 'designations',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_select_picker" : True,
        "is_need_grid_system": True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
        "staffs" : True,
    }
    return render(request, "staffs/designations/designations.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_designation'])
def edit_designation(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Designation.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)) 


    if request.method == "POST":
        form = DesignationForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Designation updated successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:designations')
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
        form = DesignationForm(instance=instance)

        context = {
            "instance": instance,
            "title": "Edit Designation :" + instance.name,
            "form": form,
            "redirect": "true",
            "url": reverse('staffs:edit_designation', kwargs={'pk': instance.pk}),

            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_select_picker" : True,
            "is_need_bootstrap_growl": True,
            "is_need_grid_system": True,
            "is_need_animations": True,
            
        }
        return render(request, 'staffs/designations/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_designation'])
def designation(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Designation.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    context = {
        'instance': instance,
        'title': 'Designation',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_grid_system": True,
        "is_need_select_picker" : True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
        
    }
    return render(request, "staffs/designations/designation.html", context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_designation'])
def delete_designation(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Designation.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    Designation.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True,name=instance.name + "_deleted_" + str(instance.auto_id))
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Designation Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('staffs:designations')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_designation'])
def delete_selected_designations(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Designation.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
            Designation.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Designation Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('staffs:designations')
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
@permissions_required(['can_create_staff'])
def create_staff(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES)

        if form.is_valid():
            auto_id = get_auto_id(Staff)
            a_id = get_a_id(Staff, request)

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop 
            data.creator = request.user
            data.updator = request.user
            data.save()

            
            return HttpResponseRedirect(reverse('staffs:staff', kwargs={'pk': data.pk}))
        else:
            message = generate_form_errors(form, formset=False)
            form = StaffForm()

            context = {
            "title": "Create Staff",
            "form": form,
            "message" : message,

            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_chosen_select": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_datetime_picker": True,
            "is_need_fileinput" : True
          
        }
        return render(request, 'staffs/entry.html', context)
    else:
        form = StaffForm()

        context = {
            "title": "Create Staff",
            "form": form,
      
            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_chosen_select": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_datetime_picker": True,
            "is_need_fileinput" : True
        }
        return render(request, 'staffs/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_staff'])
def staffs(request):
    current_shop = get_current_shop(request)
    instances = Staff.objects.filter(is_deleted=False,shop=current_shop) 
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(first_name__icontains=query)|Q(last_name__icontains=query)|Q(designation__name=query)|Q(salary__icontains=query)|Q(phone__icontains=query)|Q(sex__icontains=query)|Q(dob__icontains=query)) 
         

    context = {
        'instances': instances,
        "title": 'Staffs',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_grid_system": True,
        "is_need_select_picker" : True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
        "is_need_datetime_picker": True,
      
    }
    return render(request, "staffs/staffs.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_staff'])
def edit_staff(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(first_name__icontains=query)|Q(last_name__icontains=query)|Q(designation__icontains=query)|Q(salary__icontains=query)|Q(phone__icontains=query)|Q(sex__icontains=query)|Q(dob__icontains=query)) 
    

    if request.method == "POST":
        form = StaffForm(request.POST, request.FILES,instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()
            
            return HttpResponseRedirect(reverse('staffs:staff', kwargs={'pk': data.pk}))

        else:
            message = generate_form_errors(form, formset=False)
            form = StaffForm(instance=instance)
            context = {
            "title": "Edit Staff",
            "form": form,
            "message" : message,

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
        return render(request, 'staffs/entry.html', context)
    else:
        form = StaffForm(instance=instance)

        context = {
            "instance": instance,
            "form": form,
            "title": 'Edit Staffs',
            "redirect": "true",
            "url": reverse('staffs:edit_staff', kwargs={'pk': instance.pk}),

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
        return render(request, 'staffs/entry.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_staff'])
def staff(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False,shop=current_shop))


    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(first_name__icontains=query)|Q(last_name__icontains=query)|Q(designation__icontains=query)|Q(salary__icontains=query)|Q(phone__icontains=query)|Q(sex__icontains=query)|Q(dob__icontains=query)) 
    
    context = {
        'instance': instance,
        'title': 'Staff',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl": True,
        "is_need_grid_system": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
        "is_need_datetime_picker": True,
      
    }
    return render(request, "staffs/staff.html", context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_staff'])
def delete_staff(request,pk):
    Staff.objects.filter(id=pk).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Staff deleted successfully.",
        "redirect": "true",
        "redirect_url": reverse('staffs:staffs')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_staff'])
def delete_selected_staffs(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
            Staff.objects.filter(pk=pk).update(
                is_deleted=True, first_name=instance.first_name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Staffs Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('staffs:staffs')

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
@permissions_required(['can_create_designation'])
def create_staff_salary(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = StaffSalaryForm(request.POST)
        transaction_form = TransactionForm(request.POST)

        if form.is_valid() and transaction_form.is_valid():
            auto_id = get_auto_id(StaffSalary)
            a_id = get_a_id(StaffSalary, request)

            total_amount = 0
            days = form.cleaned_data['days']
            allowance = form.cleaned_data['allowance']
            deduction = form.cleaned_data['deduction']
            basic_salary = form.cleaned_data['basic_salary']
            commission_amount = form.cleaned_data['commission_amount']
            staff = form.cleaned_data['staff']

            total_amount = Decimal(days * basic_salary) + allowance - deduction + commission_amount

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.creator = request.user
            data.updator = request.user
            data.total_amount = total_amount
            data.save()

            if staff.distributor:
                distributor_commission_amount = staff.distributor.commission_tobe_paid
                staff.distributor.commission_tobe_paid = distributor_commission_amount - commission_amount
                staff.distributor.save()

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']       
            transaction_category = transaction_form.cleaned_data['transaction_category']
            amount = total_amount
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(shop=current_shop,name='staff_payment',category_type="expense",is_deleted=False,is_system_generated=True))
        
            #create income
            transaction = transaction_form.save(commit=False)
            
            if transaction_mode == "cash":
                transaction.payment_mode = None
                transaction.payment_to = "cash_account"
                transaction.bank_account = None
                transaction.cheque_details = None
                transaction.card_details = None
                transaction.is_cheque_withdrawed = False
                balance = transaction.cash_account.balance
                balance = balance - amount
                CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
            elif transaction_mode == "bank":
                balance = 0
                balance = transaction.bank_account.balance
                balance = balance - amount
                BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = transaction_form.cleaned_transaction['payment_mode'] 
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = transaction_form.cleaned_transaction['is_cheque_withdrawed'] 
                    transaction.card_details = None

                    if not is_cheque_withdrawed:
                        transaction.payment_to = None
                        transaction.bank_account = None
                        transaction.cash_account = None

                elif payment_mode == "internet_banking":
                    transaction.payment_to = "bank_account"
                    transaction.cash_account = None
                    transaction.cheque_details = None
                    transaction.card_details = None
                    transaction.is_cheque_withdrawed = False
                
                elif payment_mode == "card_payment":
                    transaction.payment_to = "bank_account"
                    transaction.cash_account = None
                    transaction.cheque_details = None
                    transaction.is_cheque_withdrawed = False
            
                if payment_to == "cash_account":
                    transaction.bank_account = None
                elif payment_to == "bank_account":
                    transaction.cash_account = None
                
            transaction.auto_id = get_auto_id(Transaction) 
            transaction.a_id = get_a_id(Transaction,request)            
            transaction.creator = request.user
            transaction.updator = request.user
            transaction.transaction_type = "expense"
            transaction.description = "Salary Payment"
            transaction.transaction_category = transaction_categories
            transaction.amount = amount
            transaction.date = data.time
            transaction.staff_salary = data
            transaction.first_transaction = True
            transaction.shop = current_shop
            transaction.save()

            if transaction_mode == "cash":
                cash_credit = amount
                bank_credit = 0
            elif transaction_mode == "bank":
                cash_credit = 0
                bank_credit = amount

            Journel.objects.create(
                date = data.time,
                shop = current_shop,
                cash_credit = cash_credit,
                bank_credit = bank_credit,
                transaction = transaction,
                expense = amount
            )

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Staff Salary created successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:staff_salaries')
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
        form = StaffSalaryForm()
        transaction_form = TransactionForm()
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False,user=request.user)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "title": "Create Staff Salary",
            "form": form,
            "transaction_form" : transaction_form,
            "redirect": "true",
            "is_create_page": True,

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
        return render(request, 'staffs/create_staff_salary.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_designation'])
def staff_salaries(request):
    current_shop = get_current_shop(request)
    instances = StaffSalary.objects.filter(is_deleted=False,shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query)) 

    context = {
        'instances': instances,
        "title": 'Staff Salries',

        "is_need_select_picker": True,
        "is_need_popup_box": True,
        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_grid_system": True,
        "is_need_datetime_picker": True,
        "staffs" : True,
    }
    return render(request, "staffs/staff_salaries.html", context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_modify_designation'])
def edit_staff_salary(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(StaffSalary.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
    transaction = None
    if Transaction.objects.filter(staff_salary=instance,shop=current_shop,first_transaction=True).exists():
        transaction = Transaction.objects.get(staff_salary=instance,shop=current_shop,first_transaction=True)

    if request.method == "POST":
        form = StaffSalaryForm(request.POST, instance=instance)
        transaction_form = TransactionForm(request.POST,instance=transaction)

        old_staff = instance.staff
        old_commission_amount = instance.commission_amount

        if form.is_valid() and  transaction_form.is_valid():
            total_amount = 0
            days = form.cleaned_data['days']
            allowance = form.cleaned_data['allowance']
            deduction = form.cleaned_data['deduction']
            basic_salary = form.cleaned_data['basic_salary']

            old_paid = StaffSalary.objects.get(pk=pk).total_amount
            old_transaction = get_object_or_404(Transaction.objects.filter(staff_salary=pk,collect_amount=None,is_deleted=False))

            commission_amount = form.cleaned_data['commission_amount']
            staff = form.cleaned_data['staff']

            total_amount = Decimal(days * basic_salary) + allowance - deduction + commission_amount

            if old_staff.distributor:
                distributor_commission_amount = old_staff.distributor.commission_tobe_paid
                old_staff.distributor.commission_tobe_paid = distributor_commission_amount + old_commission_amount
                old_staff.distributor.save()

            data = form.save(commit=False)
            data.shop = current_shop
            data.creator = request.user
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.total_amount = total_amount
            data.save()

            if staff.distributor:
                distributor_commission_amount = staff.distributor.commission_tobe_paid
                staff.distributor.commission_tobe_paid = distributor_commission_amount - commission_amount
                staff.distributor.save()

            if Transaction.objects.filter(staff_salary=pk).exists():
                if old_transaction.cash_account:
                    balance = old_transaction.cash_account.balance - old_paid
                    CashAccount.objects.filter(pk=old_transaction.cash_account.pk,shop=current_shop).update(balance=balance)
                else  :
                    balance = old_transaction.bank_account.balance - old_paid
                    BankAccount.objects.filter(pk=old_transaction.bank_account.pk,shop=current_shop).update(balance=balance)

            transaction_mode = transaction_form.cleaned_data['transaction_mode']
            payment_to = transaction_form.cleaned_data['payment_to']       
            transaction_category = transaction_form.cleaned_data['transaction_category']
            amount = total_amount
            transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name='staff_payment',category_type="expense",is_deleted=False,is_system_generated=True))
        
            #create income
            transaction = transaction_form.save(commit=False)
            
            if transaction_mode == "cash":
                transaction.payment_mode = None
                transaction.payment_to = "cash_account"
                transaction.bank_account = None
                transaction.cheque_details = None
                transaction.card_details = None
                transaction.is_cheque_withdrawed = False
                balance = transaction.cash_account.balance
                balance = balance + amount
                CashAccount.objects.filter(pk=transaction.cash_account.pk,shop=current_shop).update(balance=balance)
            elif transaction_mode == "bank":
                balance = 0
                balance = transaction.bank_account.balance
                balance = balance + amount
                BankAccount.objects.filter(pk=transaction.bank_account.pk,shop=current_shop).update(balance=balance)
                payment_mode = transaction_form.cleaned_transaction['payment_mode'] 
                if payment_mode == "cheque_payment":
                    is_cheque_withdrawed = transaction_form.cleaned_transaction['is_cheque_withdrawed'] 
                    transaction.card_details = None

                    if not is_cheque_withdrawed:
                        transaction.payment_to = None
                        transaction.bank_account = None
                        transaction.cash_account = None

                elif payment_mode == "internet_banking":
                    transaction.payment_to = "bank_account"
                    transaction.cash_account = None
                    transaction.cheque_details = None
                    transaction.card_details = None
                    transaction.is_cheque_withdrawed = False
                
                elif payment_mode == "card_payment":
                    transaction.payment_to = "bank_account"
                    transaction.cash_account = None
                    transaction.cheque_details = None
                    transaction.is_cheque_withdrawed = False
            
                if payment_to == "cash_account":
                    transaction.bank_account = None
                elif payment_to == "bank_account":
                    transaction.cash_account = None
                            
            transaction.transaction_type = "expense"
            transaction.description = "Salary Payment"
            transaction.transaction_category = transaction_categories
            transaction.amount = amount
            transaction.date = data.time
            transaction.staff_salary = data
            transaction.shop = current_shop
            transaction.updator = request.user
            if not transaction:
                transaction.a_id = get_a_id(Transaction,request)
                transaction.auto_id = get_auto_id(Transaction)
                transaction.creator = request.user
                transaction.updator = request.user
                transaction.first_transaction = True
            transaction.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "StaffSalary updated successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:staff_salaries')
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
        form = StaffSalaryForm(instance=instance)
        transaction_form = TransactionForm(instance=transaction)
        transaction_form.fields['cash_account'].queryset = CashAccount.objects.filter(shop=current_shop,is_deleted=False,user=request.user)
        transaction_form.fields['bank_account'].queryset = BankAccount.objects.filter(shop=current_shop,is_deleted=False)
        context = {
            "instance": instance,
            "title": "Edit Staff Salry :" + instance.staff.first_name,
            "form": form,
            "redirect": "true",
            'transaction_form' :transaction_form,
            "url": reverse('staffs:edit_staff_salary', kwargs={'pk': instance.pk}),

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
        return render(request, 'staffs/create_staff_salary.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_designation'])
def staff_salary(request, pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(StaffSalary.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    context = {
        'instance': instance,
        'title': 'StaffSalary',

        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_grid_system": True,
        "is_need_select_picker" : True,
        "is_need_chosen_select": True,
        "is_need_animations": True,
        "is_need_popup_box": True,
        
    }
    return render(request, "staffs/staff_salary.html", context)


def delete_staff_salary_fun(instance):
    staff = instance.staff
    commission_amount = instance.commission_amount
    total_amount = instance.total_amount

    if staff.distributor:
        distributor_commission_amount = staff.distributor.commission_tobe_paid
        staff.distributor.commission_tobe_paid = distributor_commission_amount + commission_amount
        staff.distributor.save()

    #update account balance
    if Transaction.objects.filter(staff_salary=instance,transaction_category__name='staff_payment').exists():
        transaction = get_object_or_404(Transaction.objects.filter(staff_salary=instance,transaction_category__name='staff_payment'))
        if transaction.cash_account:
            balance = transaction.cash_account.balance + total_amount
            CashAccount.objects.filter(pk=transaction.cash_account.pk).update(balance=balance)
        else  :
            balance = transaction.bank_account.balance + total_amount
            BankAccount.objects.filter(pk=transaction.bank_account.pk).update(balance=balance)

        transaction.is_deleted=True
        transaction.save()


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_designation'])
def delete_staff_salary(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(StaffSalary.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    delete_staff_salary_fun(instance)
    StaffSalary.objects.filter(pk=pk,shop=current_shop).update(is_deleted=True)
    
    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "StaffSlary Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('staffs:staff_salaries')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_designation'])
def delete_selected_staff_salaries(request):
    current_shop = get_current_shop(request)
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(StaffSalary.objects.filter(pk=pk, is_deleted=False,shop=current_shop))
            delete_staff_salary_fun(instance)
            StaffSalary.objects.filter(pk=pk).update(
                is_deleted=True)

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected StaffSalary Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('staffs:staff_salaries')
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
def get_salary(request):
    pk = request.GET.get('id')
    current_shop = get_current_shop(request)
    instance = Staff.objects.get(pk=pk,shop=current_shop,is_deleted=False)
    if instance.salary_type == 'daily':
        salary = instance.salary
    else:
        salary = instance.salary / 30
        
    if instance:
        response_data = {
            "status" : "true", 
            'salary' : str(salary), 
        }
    else:
        response_data = {
            "status" : "false",
            "message" : "Salry Error"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')