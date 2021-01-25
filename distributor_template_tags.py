from django.template import Library
register = Library()
from distributors.models import Distributor, DistributorStock


@register.filter    
def distributor_stock_price(pk): 
	distributor = Distributor.objects.get(pk=pk)
	product_stocks = DistributorStock.objects.filter(distributor=distributor,is_deleted=False,stock__gt=0)
	total_amount = 0
	for product_stock in product_stocks:
		total_amount += product_stock.total_amount()
	return total_amount
    