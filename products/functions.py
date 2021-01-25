from products.models import Product,ProductBatch
from decimal import Decimal


def get_exact_qty(qty,unit):
    is_base = unit.is_base
    if not is_base:
        conversion_factor = unit.conversion_factor
        return Decimal(qty) * Decimal(conversion_factor)
    else:
        return qty


def update_sock(pk,qty,status):
    product = Product.objects.get(pk=pk)
    stock = product.stock
    if status == "increase":
        balance_stock = stock + qty
    elif status == "decrease":
        balance_stock = stock - qty
    #printstock

    product.stock=balance_stock
    product.save()


def update_store_item_stock(pk,qty,status):
    storeitem = StoreItem.objects.get(pk=pk)
    stock = storeitem.stock
    if status == "increase":
        balance_stock = stock + qty
    elif status == "decrease":
        balance_stock = stock - qty

    storeitem.stock=balance_stock
    storeitem.save()