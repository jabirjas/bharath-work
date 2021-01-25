from distributors.models import Distributor, DistributorStock
from products.models import Product
from main.functions import get_current_shop


def update_distributor_credit_debit(pk,transaction_type,amount):
    if amount > 0:
        distributor = Distributor.objects.get(pk=pk)
        credit = distributor.credit
        debit = distributor.debit

        distributor_objects = Distributor.objects.filter(pk=pk)

        if transaction_type == "credit":
            if debit > 0:
                debit_balance = debit - amount
                if debit_balance < 0:
                    abs_debit_balance = abs(debit_balance)
                    distributor_objects.update(debit=0)
                    distributor_objects.update(credit=abs_debit_balance)
                else:
                    distributor_objects.update(debit=debit_balance)
            else:
                distributor_objects.update(credit=credit+amount)

        elif transaction_type == "debit":
            if credit > 0:
                credit_balance = credit - amount
                if credit_balance < 0:
                    abs_credit_balance = abs(credit_balance)
                    distributor_objects.update(credit=0,debit=abs_credit_balance)
                else:
                    distributor_objects.update(credit=credit_balance)
            else:
                distributor_objects.update(debit=debit+amount)


def get_distributor_credit(pk):
    distributor = Distributor.objects.get(pk=pk)
    credit = distributor.credit
    return credit


def get_distributor_debit(pk):
    distributor = Distributor.objects.get(pk=pk)
    debit = distributor.debit
    return debit


def distributor_stock_update(request,distributor_pk,pk,qty,status):
    distributor = Distributor.objects.get(pk=distributor_pk)
    product = Product.objects.get(pk=pk)
    current_shop = get_current_shop(request)
    if status == "increase":
        if DistributorStock.objects.filter(is_deleted=False,product=product,shop=current_shop,distributor=distributor).exists():
            distributor_stock = DistributorStock.objects.get(is_deleted=False,distributor=distributor,product=product,shop=current_shop)
            old_stock = distributor_stock.stock
            distributor_stock.stock = old_stock + qty
            distributor_stock.save()
        else:
            DistributorStock.objects.create(is_deleted=False,distributor=distributor,product=product,shop=current_shop,stock=qty)
    elif status == "decrease":
        if DistributorStock.objects.filter(is_deleted=False,distributor=distributor,product=product,shop=current_shop).exists():
            distributor_stock = DistributorStock.objects.get(is_deleted=False,distributor=distributor,product=product,shop=current_shop)
            old_stock = distributor_stock.stock
            distributor_stock.stock = old_stock - qty
            distributor_stock.save()
