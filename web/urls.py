from django.conf.urls import url,include
from . import views
from web.views import ProductCategoryAutocomplete,WebProductAutocomplete


urlpatterns = [
    url(r'^$', views.index,name='index'), 
    url(r'^product-category-autocomplete/$',ProductCategoryAutocomplete.as_view(),name='product_category_autocomplete'),
    url(r'^web-product-autocomplete/$',WebProductAutocomplete.as_view(),name='web_product_autocomplete'),

    url(r'^create-about/$',views.create_about,name='create_about'),
    url(r'^edit-about/(?P<pk>.*)/$',views.edit_about,name='edit_about'),
    url(r'^view-abouts/$',views.abouts,name='abouts'),
    url(r'^view-about/(?P<pk>.*)/$',views.about,name='about'),
    url(r'^delete-about/(?P<pk>.*)/$',views.delete_about,name='delete_about'),
    url(r'^delete-selected-abouts/$', views.delete_selected_abouts, name='delete_selected_abouts'),

    url(r'^category/create/$',views.create_category,name='create_category'),
    url(r'^categories/$',views.categories,name='categories'),
    url(r'^category/edit/(?P<pk>.*)/$',views.edit_category,name='edit_category'),
    url(r'^category/view/(?P<pk>.*)/$',views.category,name='category'),
    url(r'^category/delete/(?P<pk>.*)/$',views.delete_category,name='delete_category'),
    url(r'^category/delete-selected/$', views.delete_selected_categories, name='delete_selected_categories'),

    url(r'^offer/create/$',views.create_offer,name='create_offer'),
    url(r'^offer/view/$',views.offers,name='offers'),
    url(r'^offer/edit/(?P<pk>.*)/$',views.edit_offer,name='edit_offer'),
    url(r'^offer/view/(?P<pk>.*)/$',views.offer,name='offer'),
    url(r'^offer/delete/(?P<pk>.*)/$',views.delete_offer,name='delete_offer'),
    url(r'^offer/delete-selected-offers/$', views.delete_selected_offers, name='delete_selected_offers'), 

    url(r'^product/create/$',views.create_product,name='create_product'),
    url(r'^product/views/$',views.products,name='products'),
    url(r'^product/edit/(?P<pk>.*)/$',views.edit_product,name='edit_product'),
    url(r'^product/view/(?P<pk>.*)/$',views.product,name='product'),
    url(r'^product/delete/(?P<pk>.*)/$',views.delete_product,name='delete_product'),
    url(r'^product/delete-selected/$', views.delete_selected_products, name='delete_selected_products'),

    url(r'^get-products/$',views.get_products,name='get_products'),

]