from django.template import Library
from django.contrib.auth.models import User
register = Library()
from django.template.defaultfilters import stringfilter
from sales.models import SaleItem



@register.filter    
def check_default(value): 
	result = value
	if value == "default":
		result = "-"
	return result
                                                        
    
@register.filter
@stringfilter
def underscore_smallletter(value):
    value =  value.replace(" ", "_")
    return value
    

@register.filter
def to_fixed_two(value):
    return "{:10.2f}".format(value)


@register.filter
def tax_devide(value):
    return value/2


@register.filter
def row_index(value,arg):
    return (value*16) + arg


@register.filter
def row_index2(value,arg):
    return (value*27) + arg

@register.filter
def sub(value,arg):
    return value - arg

@register.filter
def rev_sub(value,arg):
    return arg - value


@register.filter
def div(value,arg):
    return value / arg

@register.filter
def add_to(value,arg):
    return round (value + arg)

@register.filter
def mul(value, arg):
    return value*arg


@register.filter
def get_profit(value):
    total_profit = 0
    sale_items = SaleItem.objects.filter(sale__pk=value)        
    for sale_item in sale_items:
        customer_discount = sale_item.discount
        if not sale_item.return_item:
            if customer_discount > 0 :
                price = sale_item.price
            else :
                price = sale_item.tax_added_price
            cost = sale_item.cost
            qty = sale_item.qty
            discount = sale_item.discount_amount
            profit = ((price - (cost)) * qty) - discount
            total_profit += profit
    return total_profit
