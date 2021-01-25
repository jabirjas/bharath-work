from django.conf.urls import url, include
from django.contrib import admin
from . import views
from sales.views import SaleAutocomplete,ReturnableProductAutocomplete


urlpatterns = [               
    url(r'^sale-autocomplete/$',SaleAutocomplete.as_view(),name='sale_autocomplete'),
    url(r'^returnable_products-autocomplete/$',ReturnableProductAutocomplete.as_view(),name='returnable_product_autocomplete'),
    
    url(r'^$', views.dashboard,name='dashboard'), 
    url(r'^print-report/$', views.print_report,name='print_report'), 
    url(r'^taxed-sale-items/$', views.taxed_sale_items,name='taxed_sale_items'),
    url(r'^export-report/$', views.export_report,name='export_report'),
    
    url(r'^sale/create/$',views.create,name='create'),
    url(r'^sale/views/$',views.sales,name='sales'),
    url(r'^sale/edit/(?P<pk>.*)/$',views.edit,name='edit'),
    url(r'^sale/view/(?P<pk>.*)/$',views.sale,name='sale'),
    url(r'^sale/delete/(?P<pk>.*)/$',views.delete,name='delete'),
    url(r'^sale/delete-selected/$', views.delete_selected_sales, name='delete_selected_sales'),
    url(r'^invoice/(?P<pk>.*)/$',views.print_sale,name='print'),
    url(r'^email/(?P<pk>.*)/$',views.email_sale,name='email_sale'),
    url(r'^return-sale/views/$',views.return_sales,name='return_sales'),

    url(r'^collect-amount/create/$', views.create_collect_amount, name='create_collect_amount'),
    url(r'^collect-amount/view/(?P<pk>.*)/$', views.collect_amount, name='collect_amount'),
    url(r'^collect-amount/edit/(?P<pk>.*)/$', views.edit_collect_amount, name='edit_collect_amount'),
    url(r'^collect-amounts/$', views.collect_amounts, name='collect_amounts'),
    url(r'^collect-amount/delete/(?P<pk>.*)/$', views.delete_collect_amount, name='delete_collect_amount'),
    url(r'^collect-amount/delete-selected/$', views.delete_selected_collect_amounts, name='delete_selected_collect_amounts'),
    url(r'^collected-amount/print/(?P<pk>.*)/$',views.print_collected_amount,name='print_collected_amount'),
    url(r'^collected-amounts/print/$',views.print_collected_amounts,name='print_collected_amounts'),

    url(r'^customer-payment/create/$', views.create_customer_payment, name='create_customer_payment'),
    url(r'^customer-payment/view/(?P<pk>.*)/$', views.customer_payment, name='customer_payment'),
    url(r'^customer-payment/edit/(?P<pk>.*)/$', views.edit_customer_payment, name='edit_customer_payment'),
    url(r'^customer-payments/$', views.customer_payments, name='customer_payments'),
    url(r'^customer-payment/delete/(?P<pk>.*)/$', views.delete_customer_payment, name='delete_customer_payment'),
    url(r'^customer-payment/delete-selected/$', views.delete_selected_customer_payments, name='delete_selected_customer_payments'),
    url(r'^customer-payment/print/(?P<pk>.*)/$',views.print_customer_payment,name='print_customer_payment'),
    url(r'^customer-payments/print/$',views.print_customer_payments,name='print_customer_payments'),

    url(r'^create-sale-return/$',views.create_sale_return,name='create_sale_return'),
    url(r'^sale-returns/$',views.sale_returns,name='sale_returns'), 
    url(r'^sale-return/(?P<pk>.*)/$', views.sale_return, name='sale_return'),

    url(r'^print-sale-return/(?P<pk>.*)/$', views.print_sale_return, name='print_sale_return'),
    url(r'^delete-sale-return/(?P<pk>.*)/$', views.delete_sale_return, name='delete_sale_return'),

    url(r'^damaged-products/$',views.damaged_products,name='damaged_products'),
    url(r'^create-damaged-product/$',views.create_damaged_product,name='create_damaged_product'),
    
    url(r'^create-product-return/$',views.create_product_return,name='create_product_return'),
    url(r'^product-return/(?P<pk>.*)/$', views.product_return, name='product_return'),
    url(r'^product-returns/$',views.product_returns,name='product_returns'),
    url(r'^delete-product-return/(?P<pk>.*)/$', views.delete_product_return, name='delete_product_return'),
    url(r'^get-sale-items/$', views.get_sale_items,name='get_sale_items'),
    url(r'^get-return-items/$', views.get_return_items,name='get_return_items'),
    url(r'^get-vendor-return-items/$', views.get_vendor_return_items,name='get_vendor_return_items'),
    url(r'^get-customer/$', views.get_customer,name='get_customer'),

    url(r'^estimate/create/$',views.create_estimate,name='create_estimate'),
    url(r'^estimate/views/$',views.estimates,name='estimates'),
    url(r'^estimate/edit/(?P<pk>.*)/$',views.edit_estimate,name='edit_estimate'),
    url(r'^estimate/view/(?P<pk>.*)/$',views.estimate,name='estimate'),
    url(r'^estimate/delete/(?P<pk>.*)/$',views.delete_estimate,name='delete_estimate'),
    url(r'^estimate/delete-selected/$', views.delete_selected_estimates, name='delete_selected_estimates'),
    url(r'^print-estimate/(?P<pk>.*)/$',views.print_estimate,name='print_estimate'),
    url(r'^email-estimate/(?P<pk>.*)/$',views.email_estimate,name='email_estimate'),

    url(r'^stock/report/$',views.stock_report, name='stock_report'),

    url(r'^create-vendor-return/$',views.create_vendor_return,name='create_vendor_return'),
    url(r'^vendor-return/(?P<pk>.*)/$', views.vendor_return, name='vendor_return'),
    url(r'^vendor-returns/$',views.vendor_returns,name='vendor_returns'),
    url(r'^delete-vendor-return/(?P<pk>.*)/$', views.delete_vendor_return, name='delete_vendor_return'), 

    url(r'^purchase-request/create/$',views.create_purchase_request,name='create_purchase_request'),
    url(r'^purchase-request/views/$',views.purchase_requests,name='purchase_requests'),
    url(r'^purchase-request/edit/(?P<pk>.*)/$',views.edit_purchase_request,name='edit_purchase_request'),
    url(r'^purchase-request/view/(?P<pk>.*)/$',views.purchase_request,name='purchase_request'),
    url(r'^purchase-request/delete/(?P<pk>.*)/$',views.delete_purchase_request,name='delete_purchase_request'),
    url(r'^purchase-request/delete-selected/$', views.delete_selected_purchase_requests, name='delete_selected_purchase_requests'),
    url(r'^print-purchase-request/(?P<pk>.*)/$',views.print_purchase_request,name='print_purchase_request'),

    url(r'^purchase-request/returns/$',views.purchase_request_returns,name='purchase_request_returns'),

    url(r'^purchase-request-sale/create/(?P<pk>.*)/$',views.purchase_request_sale_create,name='purchase_request_sale_create'),
    url(r'^cheque-list/views/$',views.cheque_lists,name='cheque_lists'),
    url(r'^cheque_withdraw/(?P<pk>.*)/$',views.cheque_withdraw,name='cheque_withdraw'),
    url(r'^cheque_return/(?P<pk>.*)/$',views.cheque_return,name='cheque_return'),

]