from django.conf.urls import url
from . import views


urlpatterns = [


    url(r'^purchase/create/$', views.create_purchase, name='create_purchase'),
    url(r'^purchases/$', views.purchases, name='purchases'),
    url(r'^purchase/edit/(?P<pk>.*)/$', views.edit_purchase, name='edit_purchase'),
    url(r'^purchase/view/(?P<pk>.*)/$', views.purchase, name='purchase'),
    url(r'^purchase/delete/(?P<pk>.*)/$', views.delete_purchase, name='delete_purchase'),
    url(r'^purchase/delete-selected/$', views.delete_selected_purchases, name='delete_selected_purchases'),

    url(r'^purchase/item/split/(?P<pk>.*)/$', views.purchase_item_split, name='purchase_item_split'),

    url(r'^invoice/(?P<pk>.*)/$',views.print_purchase,name='print'),
    url(r'^email/(?P<pk>.*)/$',views.email_purchase,name='email_purchase'),
    url(r'^purchases/print/$',views.print_purchases,name='print_purchases'),

    url(r'^paid/create/$', views.create_paid, name='create_paid'),
    url(r'^paid/view/(?P<pk>.*)/$', views.paid, name='paid'),
    url(r'^paid/edit/(?P<pk>.*)/$', views.edit_paid, name='edit_paid'),
    url(r'^paids/$', views.paids, name='paids'),
    url(r'^paid/delete/(?P<pk>.*)/$', views.delete_paid, name='delete_paid'),
    url(r'^paids/delete-selected/$', views.delete_selected_paids, name='delete_selected_paids'), 

    url(r'^collect-amount/create/$', views.create_collect_amount, name='create_collect_amount'),
    url(r'^collect-amount/view/(?P<pk>.*)/$', views.collect_amount, name='collect_amount'),
    url(r'^collect-amount/edit/(?P<pk>.*)/$', views.edit_collect_amount, name='edit_collect_amount'),
    url(r'^collect-amounts/$', views.collect_amounts, name='collect_amounts'),
    url(r'^collect-amount/delete/(?P<pk>.*)/$', views.delete_collect_amount, name='delete_collect_amount'),
    url(r'^collect-amount/delete-selected/$', views.delete_selected_collect_amounts, name='delete_selected_collect_amounts'),
    url(r'^collected-amount/print/(?P<pk>.*)/$',views.print_collected_amount,name='print_collected_amount'),
    url(r'^collected-amounts/print/$',views.print_collected_amounts,name='print_collected_amounts'), 

    url(r'^purchase/invoice/create/$', views.create_purchase_invoice, name='create_invoice'),
    url(r'^purchase/invoices/$', views.purchase_invoices, name='invoices'),
    url(r'^purchase/invoice/view/(?P<pk>.*)/$', views.purchase_invoice, name='invoice'),
    url(r'^purchase/invoice/delete/(?P<pk>.*)/$', views.delete_purchase_invoice, name='delete_purchase_invoice'),
    url(r'^purchase/invoice/delete-selected/$', views.delete_selected_purchase_invoices, name='delete_selected_purchase_invoices'),

    url(r'^purchase/invoice/print/(?P<pk>.*)/$',views.print_purchase_invoice,name='print_invoice'),      
    url(r'^purchase/invoice/email/(?P<pk>.*)/$',views.email_invoice,name='email_invoice'),
    
    url(r'^asset_purchase/create/$', views.create_asset_purchase, name='create_asset_purchase'),
    url(r'^asset_purchases/$', views.asset_purchases, name='asset_purchases'),
    url(r'^asset_purchase/edit/(?P<pk>.*)/$', views.edit_asset_purchase, name='edit_asset_purchase'),
    url(r'^asset_purchase/view/(?P<pk>.*)/$', views.asset_purchase, name='asset_purchase'),
    url(r'^asset_purchase/delete/(?P<pk>.*)/$', views.delete_asset_purchase, name='delete_asset_purchase'),
    url(r'^asset_purchase/delete-selected/$', views.delete_selected_asset_purchases, name='delete_selected_asset_purchases'),


    url(r'^asset/email/(?P<pk>.*)/$',views.email_asset_purchase,name='email_asset_purchase'),
    url(r'^asset_purchases/print/$',views.print_asset_purchases,name='print_asset_purchases'),
    url(r'^asset_purchase/print/(?P<pk>.*)/$',views.print_asset_purchase,name='print_asset_purchase')

    
]
