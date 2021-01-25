from dal import autocomplete
from django.db.models import Q
from staffs.models import Staff
from users.functions import get_current_shop
from finance.models import TaxCategory
from main.functions import get_auto_id,get_a_id
from decimal import Decimal


class StaffAutocomplete(autocomplete.Select2QuerySetView):
	
	def get_queryset(self):
		current_shop = get_current_shop(self.request)
		staff = Staff.objects.filter(is_deleted=False,shop=current_shop)

		if self.q:
			staff = staff.filter(name__istartswith=self.q)

		return staff


class TaxCategoryAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		items = TaxCategory.objects.filter(is_deleted=False)

		if self.q:
			items = items.filter(Q(name__istartswith=self.q)
								 )
		return items

	def create_object(self, text):
		current_shop = get_current_shop(self.request)
		auto_id = get_auto_id(TaxCategory)
		a_id = get_a_id(TaxCategory,self.request)

		return TaxCategory.objects.create(
			auto_id=auto_id,
			a_id=a_id,
			name = text + " %",
			tax=text,
			shop=current_shop,
			creator=self.request.user,
			updator=self.request.user
		)



class IncomeCategoryAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		items = TransactionCategory.objects.filter(is_deleted=False,category_type="income")

		if self.q:
			items = items.filter(Q(name__istartswith=self.q)
								 )
		return items

	def create_object(self, text):
		current_shop = get_current_shop(self.request)
		auto_id = get_auto_id(TransactionCategory)
		a_id = get_a_id(TransactionCategory,self.request)

		return TransactionCategory.objects.create(
			auto_id=auto_id,
			a_id=a_id,
			category_type="income",
			shop=current_shop,
			creator=self.request.user,
			updator=self.request.user
		)


class ExpenseCategoryAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		items = TransactionCategory.objects.filter(is_deleted=False,category_type="expense")

		if self.q:
			items = items.filter(Q(name__istartswith=self.q)
								 )
		return items

	def create_object(self, text):
		current_shop = get_current_shop(self.request)
		auto_id = get_auto_id(TransactionCategory)
		a_id = get_a_id(TransactionCategory,self.request)

		return TransactionCategory.objects.create(
			auto_id=auto_id,
			a_id=a_id,
			category_type="expense",
			shop=current_shop,
			creator=self.request.user,
			updator=self.request.user
		)