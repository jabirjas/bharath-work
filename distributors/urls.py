from django.conf.urls import url, include
from django.contrib import admin
from . import views
from distributors.views import DistributorAutocomplete


urlpatterns = [
    url(r'^distributor-autocomplete/$',DistributorAutocomplete.as_view(),name='distributor_autocomplete'),

    url(r'^$', views.dashboard,name='dashboard'),

    url(r'^distributor/create/$',views.create,name='create'),
    url(r'^distributor/view/$',views.distributors,name='distributors'),
    url(r'^distributor/edit/(?P<pk>.*)/$',views.edit,name='edit'),
    url(r'^distributor/views/(?P<pk>.*)/$',views.distributor,name='distributor'),
    url(r'^distributor/delete/(?P<pk>.*)/$',views.delete,name='delete'),
    url(r'^distributor/delete-selected/$', views.delete_selected_distributors, name='delete_selected_distributors'),

    url(r'^get-debit/$', views.get_credit, name='get_credit'),

    url(r'^distributor-stock/view/$',views.distributor_stocks,name='distributor_stocks'),
    url(r'^distributor-stock/print/$',views.print_distributor_stocks,name='print_distributor_stocks'),
    url(r'^distributor-stock/views/(?P<pk>.*)/$',views.distributor_stock,name='distributor_stock'),
    url(r'^distributor-stock/delete/(?P<pk>.*)/$',views.delete_distributor_stock,name='delete_distributor_stock'),

    url(r'^stock-transfer/create/$',views.create_stock_transfer,name='create_stock_transfer'),
    url(r'^stock-transfer/view/$',views.stock_transfers,name='stock_transfers'),
    url(r'^stock-transfer/edit/(?P<pk>.*)/$',views.edit_stock_transfer,name='edit_stock_transfer'),
    url(r'^stock-transfer/views/(?P<pk>.*)/$',views.stock_transfer,name='stock_transfer'),
    url(r'^stock-transfer/delete/(?P<pk>.*)/$',views.delete_stock_transfer,name='delete_stock_transfer'),
    url(r'^stock-transfer/delete-selected/$', views.delete_selected_stock_transfers, name='delete_selected_stock_transfers'),

    url(r'^distributor-stock-transfer/create/$',views.create_distributor_stock_transfer,name='create_distributor_stock_transfer'),
    url(r'^distributor-stock-transfer/view/$',views.distributor_stock_transfers,name='distributor_stock_transfers'),
    url(r'^distributor-stock-transfer/edit/(?P<pk>.*)/$',views.edit_distributor_stock_transfer,name='edit_distributor_stock_transfer'),
    url(r'^distributor-stock-transfer/views/(?P<pk>.*)/$',views.distributor_stock_transfer,name='distributor_stock_transfer'),
    url(r'^distributor-stock-transfer/delete/(?P<pk>.*)/$',views.delete_distributor_stock_transfer,name='delete_distributor_stock_transfer'),
    url(r'^distributor-stock-transfer/delete-selected/$', views.delete_selected_distributor_stock_transfers, name='delete_selected_distributor_stock_transfers'),

    url(r'^direct-stock-transfer/create/$',views.create_direct_stock_transfer,name='create_direct_stock_transfer'),
    url(r'^direct-stock-transfer/view/$',views.direct_stock_transfers,name='direct_stock_transfers'),
    url(r'^direct-stock-transfer/edit/(?P<pk>.*)/$',views.edit_direct_stock_transfer,name='edit_direct_stock_transfer'),
    url(r'^direct-stock-transfer/views/(?P<pk>.*)/$',views.direct_stock_transfer,name='direct_stock_transfer'),
    url(r'^direct-stock-transfer/delete/(?P<pk>.*)/$',views.delete_direct_stock_transfer,name='delete_direct_stock_transfer'),
    url(r'^direct-stock-transfer/delete-selected/$', views.delete_selected_direct_stock_transfers, name='delete_selected_direct_stock_transfers'),

    url(r'^user/create/(?P<pk>.*)/$',views.create_user,name='create_user'),
    url(r'^get-distributor/$',views.get_distributor,name='get_distributor'),
]
