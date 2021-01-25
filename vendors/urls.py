from django.conf.urls import url
from vendors.views import VendorAutocomplete
from . import views


urlpatterns = [

    url(r'^vendor-autocomplete/$',VendorAutocomplete.as_view(),name='vendor_autocomplete'),


    url(r'^vendor/create/$', views.create_vendor, name='create_vendor'),
    url(r'^vendors/$', views.vendors, name='vendors'),
    url(r'^vendor/edit/(?P<pk>.*)/$', views.edit_vendor, name='edit_vendor'),
    url(r'^vendor/view/(?P<pk>.*)/$', views.vendor, name='vendor'),
    url(r'^vendor/delete/(?P<pk>.*)/$', views.delete_vendor, name='delete_vendor'),
    url(r'^vendor/delete-selected/$', views.delete_selected_vendors, name='delete_selected_vendors'),

    url(r'^get-debit/$', views.get_debit, name='get_debit'),
]
