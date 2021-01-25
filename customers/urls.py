from django.conf.urls import url, include
from django.contrib import admin
from . import views
from customers.views import CustomerAutocomplete


urlpatterns = [
    url(r'^customer-autocomplete/$',CustomerAutocomplete.as_view(),name='customer_autocomplete'),

    url(r'^$', views.dashboard,name='dashboard'),

    url(r'^customer/create/$',views.create,name='create'),
    url(r'^customer/view/$',views.customers,name='customers'),
    url(r'^customer/edit/(?P<pk>.*)/$',views.edit,name='edit'),
    url(r'^customer/views/(?P<pk>.*)/$',views.customer,name='customer'),
    url(r'^customer/delete/(?P<pk>.*)/$',views.delete,name='delete'),
    url(r'^customer/delete-selected/$', views.delete_selected_customers, name='delete_selected_customers'),

    url(r'^get-debit/$', views.get_credit, name='get_credit'),
    url(r'^get-customer-discount/$', views.get_customer_discount, name='get_customer_discount'),
    url(r'^check-sale-restriction/$', views.check_sale_restriction, name='check_sale_restriction'),
]
