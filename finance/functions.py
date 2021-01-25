from finance.models import Transaction,TransactionCategory,CashAccount, BankAccount, Journel
from main.functions import get_a_id, get_auto_id, get_current_shop
from django.shortcuts import get_object_or_404
import datetime


def add_transaction(request,transaction_form,data,amount,transaction_category_name,transaction_type,debit,credit):
	current_shop = get_current_shop(request)
	transaction_mode = transaction_form.cleaned_data['transaction_mode']
	payment_to = transaction_form.cleaned_data['payment_to']
	transaction_category = transaction_form.cleaned_data['transaction_category']
	transaction_categories = get_object_or_404(TransactionCategory.objects.filter(name=transaction_category_name,category_type=transaction_type,is_deleted=False)[:1])

	#create income
	transaction_data = transaction_form.save(commit=False)

	if transaction_category_name == "sale_payment":
		transaction_data.sale = data
		transaction_data.first_transaction = True
	if transaction_category_name == "purchase_payment":
		transaction_data.purchase = data
	if transaction_category_name == 'salary_payment':
		transaction_data.staff_salary = data
		
	if transaction_mode == "cash":
		transaction_data.payment_mode = None
		transaction_data.payment_to = "cash_account"
		transaction_data.bank_account = None
		transaction_data.cheque_details = None
		transaction_data.card_details = None
		transaction_data.is_cheque_withdrawed = False
		balance = transaction_data.cash_account.balance
		balance = balance + amount
		CashAccount.objects.filter(pk=transaction_data.cash_account.pk,shop=current_shop).update(balance=balance)
	elif transaction_mode == "bank":
		balance = 0
		balance = transaction_data.bank_account.balance
		balance = balance + amount
		BankAccount.objects.filter(pk=transaction_data.bank_account.pk,shop=current_shop).update(balance=balance)
		payment_mode = transaction_form.cleaned_data['payment_mode']
		if payment_mode == "cheque_payment":
			is_cheque_withdrawed = transaction_form.cleaned_data['is_cheque_withdrawed']
			transaction_data.card_details = None

			if not is_cheque_withdrawed:
				# transaction_data.payment_to = "bank_account"
				# transaction_data.bank_account = None
				transaction_data.cash_account = None

		elif payment_mode == "internet_banking":
			transaction_data.payment_to = "bank_account"
			transaction_data.cash_account = None
			transaction_data.cheque_details = None
			transaction_data.card_details = None
			transaction_data.is_cheque_withdrawed = False

		elif payment_mode == "card_payment":
			transaction_data.payment_to = "bank_account"
			transaction_data.cash_account = None
			transaction_data.cheque_details = None
			transaction_data.is_cheque_withdrawed = False

		if payment_to == "cash_account":
			transaction_data.bank_account = None
		elif payment_to == "bank_account":
			transaction_data.cash_account = None

	transaction_data.auto_id = get_auto_id(Transaction)
	transaction_data.a_id = get_a_id(Transaction,request)
	transaction_data.creator = request.user
	transaction_data.updator = request.user
	transaction_data.transaction_type = transaction_type
	transaction_data.transaction_category = transaction_categories
	transaction_data.amount = amount
	transaction_data.date = data.time
	transaction_data.shop = current_shop
	transaction_data.old_debit = debit
	transaction_data.old_credit = credit
	transaction_data.save()

	if transaction_mode == "cash":
		cash_debit = amount
		bank_debit = 0
	elif transaction_mode == "bank":
		cash_debit = 0
		bank_debit = amount

	if transaction_category_name == "purchase_payment" :
		Journel.objects.create(
			date = datetime.date.today(),
			shop = current_shop,
			cash_debit = cash_debit,
			bank_debit = bank_debit,
			transaction = transaction_data,
			purchase = data,
			expense = amount
		)
	elif transaction_category_name == "salary_payment" :
		Journel.objects.create(
			date = datetime.date.today(),
			shop = current_shop,
			cash_debit = cash_debit,
			bank_debit = bank_debit,
			transaction = transaction_data,
			expense = amount
		)
	elif transaction_category_name == 'sale_payment':
		Journel(
			date = datetime.date.today(),
			shop = current_shop,
			cash_debit = cash_debit,
			bank_debit = bank_debit,
			transaction = transaction_data,
			income = amount,
			sale = data
		).save() 
