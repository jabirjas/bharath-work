from django.conf.urls import url, include
from django.contrib import admin
from . import views
from products.views import CategoryAutocomplete, ProductAutocomplete,BrandAutocomplete,SubcategoryAutocomplete,AssetAutocomplete,BatchAutocomplete


urlpatterns = [
    url(r'^subcategory-autocomplete/$',SubcategoryAutocomplete.as_view(create_field='name'),name='subcategory_autocomplete'),
    url(r'^category-autocomplete/$',CategoryAutocomplete.as_view(create_field='name'),name='category_autocomplete'),
    url(r'^brand-autocomplete/$',BrandAutocomplete.as_view(create_field='name'),name='brand_autocomplete'),
    url(r'^batch-autocomplete/$',BatchAutocomplete.as_view(),name='batch_autocomplete'),
    url(r'^product-autocomplete/$',ProductAutocomplete.as_view(),name='product_autocomplete'),
    url(r'^asset-autocomplete/$',AssetAutocomplete.as_view(),name='asset_autocomplete'),
    url(r'^subcategory/autocomplete/$',SubcategoryAutocomplete.as_view(create_field='name'),name='subcategories_autocomplete'),
    url(r'^category/autocomplete/$',CategoryAutocomplete.as_view(),name='categories_autocomplete'),
    
    url(r'^$', views.dashboard,name='dashboard'), 
    
    url(r'^product/create/$',views.create,name='create'),
    url(r'^product/create-new-product/$',views.create_new_product,name='create_new_product'),
    url(r'^product/views/$',views.products,name='products'),
    url(r'^product/edit/(?P<pk>.*)/$',views.edit,name='edit'),
    url(r'^product/view/(?P<pk>.*)/$',views.product,name='product'),
    url(r'^product/delete/(?P<pk>.*)/$',views.delete,name='delete'),
    url(r'^product/delete-selected/$', views.delete_selected_products, name='delete_selected_products'),

    url(r'^get-product/$',views.get_product,name='get_product'),
    url(r'^get-asset/$',views.get_asset,name='get_asset'),
    url(r'^get-product-sub-categories/$', views.get_product_sub_categories, name='get_product_sub_categories'),
    url(r'^get-product-units/$', views.get_product_units, name='get_product_units'),
    url(r'^get-returnable-product/$',views.get_returnable_product,name='get_returnable_product'),
    url(r'^get-unit-price/$', views.get_unit_price, name='get_unit_price'),
    url(r'^get-unit-cost-price/$', views.get_unit_cost_price, name='get_unit_cost_price'),

    url(r'^get-expiry/$', views.get_expiry, name='get_expiry'),
    url(r'^get-purchase-items/$', views.get_purchase_items, name='get_purchase_items'),

    url(r'^product-expiry-date/edit/(?P<pk>.*)/$',views.edit_expiry_date,name='edit_expiry_date'),
    
    url(r'^upload-product-list/$', views.upload_product_list, name='upload_product_list'),
    
    url(r'^category/create/$',views.create_category,name='create_category'),
    url(r'^categories/$',views.categories,name='categories'),
    url(r'^category/edit/(?P<pk>.*)/$',views.edit_category,name='edit_category'),
    url(r'^category/view/(?P<pk>.*)/$',views.category,name='category'),
    url(r'^category/delete/(?P<pk>.*)/$',views.delete_category,name='delete_category'),
    url(r'^category/delete-selected/$', views.delete_selected_categories, name='delete_selected_categories'),

    url(r'^create-subcategory/$', views.create_subcategory, name='create_subcategory'),
    url(r'^subcategories/$', views.subcategories, name='subcategories'),
    url(r'^edit-subcategory/(?P<pk>.*)/$', views.edit_subcategory, name='edit_subcategory'),
    url(r'^subcategory/(?P<pk>.*)/$', views.subcategory, name='subcategory'),
    url(r'^delete-subcategory/(?P<pk>.*)/$', views.delete_subcategory, name='delete_subcategory'),
    url(r'^delete-selected-subcategories/$', views.delete_selected_subcategories, name='delete_selected_subcategories'),

    url(r'^brand/create/$',views.create_brand,name='create_brand'),
    url(r'^brands/$',views.brands,name='brands'),
    url(r'^brand/edit/(?P<pk>.*)/$',views.edit_brand,name='edit_brand'),
    url(r'^brand/view/(?P<pk>.*)/$',views.brand,name='brand'),
    url(r'^brand/delete/(?P<pk>.*)/$',views.delete_brand,name='delete_brand'),
    url(r'^brand/delete-selected/$', views.delete_selected_brands, name='delete_selected_brands'),

    url(r'^batch/create/$',views.create_batch,name='create_batch'),
    url(r'^batches/$',views.batches,name='batches'),
    url(r'^batch/edit/(?P<pk>.*)/$',views.edit_batch,name='edit_batch'),
    url(r'^batch/view/(?P<pk>.*)/$',views.batch,name='batch'),
    url(r'^batch/delete/(?P<pk>.*)/$',views.delete_batch,name='delete_batch'),
    url(r'^batch/delete-selected/$', views.delete_selected_batches, name='delete_selected_batches'),


    url(r'^unit/create/$',views.create_unit,name='create_unit'),
    url(r'^units/$',views.units,name='units'),
    url(r'^unit/edit/(?P<pk>.*)/$',views.edit_unit,name='edit_unit'),
    url(r'^unit/view/(?P<pk>.*)/$',views.unit,name='unit'),
    url(r'^unit/delete/(?P<pk>.*)/$',views.delete_unit,name='delete_unit'),
    url(r'^unit/delete-selected/$', views.delete_selected_units, name='delete_selected_units'),

    url(r'^asset/create/$', views.create_asset, name='create_asset'),
    url(r'^asset/view/(?P<pk>.*)/$', views.asset, name='asset'),
    url(r'^asset/edit/(?P<pk>.*)/$', views.edit_asset, name='edit_asset'),
    url(r'^assets/$', views.assets, name='assets'),
    url(r'^delete-asset/(?P<pk>.*)/$', views.delete_asset, name='delete_asset'),
    url(r'^delete-selected-assets/$', views.delete_selected_assets, name='delete_selected_assets'),

    url(r'^barcode/create/$', views.create_barcode, name='create_barcode'),
    url(r'^barcodes/print/$', views.print_barcodes, name='print_barcodes'),

    url(r'^products/export/$', views.export_products, name='export_products'),

    url(r'^products/distributor-stocks/$', views.distributor_product_stocks, name='distributor_product_stocks'),
    url(r'^products/stocks/$', views.product_stocks, name='product_stocks'),

    url(r'^inventory/create/$', views.create_inventory, name='create_inventory'),
    url(r'^inventory/view/$', views.inventory, name='inventory'),
    url(r'^inventory-report/create/$', views.create_inventory_report, name='create_inventory_report'),
    url(r'^inventory-adjustment/create/$', views.create_inventory_adjustment, name='create_inventory_adjustment'),
    url(r'^inventory-adjustment/views/$', views.inventory_adjustments, name='inventory_adjustments'),
    url(r'^inventory-adjustment/view/(?P<pk>.*)/$', views.inventory_adjustment, name='inventory_adjustment'),

    # url(r'^return/create/$', views.create_return, name='create_return'),
    # url(r'^stock-return/create/$', views.create_stock_return, name='create_stock_return'),
    # url(r'^stock-return/views/$', views.stock_returns, name='stock_returns'),

    url(r'^alternative-unit/create/$', views.create_alternative_unit, name='create_alternative_unit'),
    url(r'^alternative-unit/view/(?P<pk>.*)/$', views.alternative_unit, name='alternative_unit'),
    url(r'^alternative-unit/edit/(?P<pk>.*)/$', views.edit_alternative_unit, name='edit_alternative_unit'),
    url(r'^alternative-units/$', views.alternative_units, name='alternative_units'),
    url(r'^delete-alternative-unit/(?P<pk>.*)/$', views.delete_alternative_unit, name='delete_alternative_unit'),
    url(r'^delete-selected-alternative-units/$', views.delete_selected_alternative_units, name='delete_selected_alternative_units'),

    url(r'^measurement/create/$', views.create_measurement, name='create_measurement'),
    url(r'^measurement/view/(?P<pk>.*)/$', views.measurement, name='measurement'),
    url(r'^measurement/edit/(?P<pk>.*)/$', views.edit_measurement, name='edit_measurement'),
    url(r'^measurements/$', views.measurements, name='measurements'),
    url(r'^delete-measurement/(?P<pk>.*)/$', views.delete_measurement, name='delete_measurement'),
    url(r'^delete-selected-measurements/$', views.delete_selected_measurements, name='delete_selected_measurements'),

]