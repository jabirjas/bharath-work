from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^sale-report$', views.sale_report,name='sale_report'), 
    url(r'^print-report/$', views.print_report,name='print_report'), 
    url(r'^taxed-sale-items/$', views.taxed_sale_items,name='taxed_sale_items'),
    url(r'^export-report/$', views.export_report,name='export_report'),
    url(r'^gstr1/$', views.gstr1,name='gstr1'),
    url(r'^create-sale-report/$', views.create_sale_report,name='create_sale_report'),

    url(r'^print-daily-report/$', views.print_daily_report,name='print_daily_report'),
    url(r'^create-daily-report/$', views.create_daily_report,name='create_daily_report'),

    url(r'^print-distributor-report/$', views.print_distributor_report,name='print_distributor_report'),
    url(r'^create-distributor-report/$', views.create_distributor_report,name='create_distributor_report'),

    url(r'^print-manufacture-report/$', views.print_manufacture_report,name='print_manufacture_report'),
    url(r'^create-manufacture-report/$', views.create_manufacture_report,name='create_manufacture_report'),

    url(r'^print-monthly-report/$', views.print_monthly_report,name='print_monthly_report'),
    url(r'^create-monthly-report/$', views.create_monthly_report,name='create_monthly_report'),

    url(r'^print-collect_amount-report/$', views.print_collect_amount_report,name='print_collect_amount_report'),
    url(r'^create-collect_amount-report/$', views.create_collect_amount_report,name='create_collect_amount_report'),

    url(r'^create-performance-report/$', views.create_performance_report,name='create_performance_report'),    
    url(r'^print-performance-report/$', views.print_performance_report,name='print_performance_report'),

    url(r'^create-customer-report/$', views.create_customer_report,name='create_customer_report'),    
    url(r'^print-customer-report/$', views.print_customer_report,name='print_customer_report'),

    url(r'^create-return-report/$', views.create_return_report,name='create_return_report'),    
    url(r'^print-return-report/$', views.print_return_report,name='print_return_report'),
]
