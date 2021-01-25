from django.conf.urls import url, include
from django.contrib import admin
from main import views as general_views
from django.conf import settings
from registration.backends.default.views import RegistrationView
from users.forms import RegForm
from users.backend import user_created
from django.views.static import serve

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^web/', include(('web.urls', 'web'), namespace="web")),

    url(r'^$',general_views.app,name='app'),
    url(r'^app/$',general_views.app,name='app'),
    url(r'^app/android/$',general_views.download_app,name='download_app'),
    url(r'^app/dashboard/$',general_views.dashboard,name='dashboard'),
    url(r'^app/shop/create/$',general_views.create_shop,name='create_shop'),
    url(r'^app/shop/switch/$', general_views.switch_shop, name='switch_shop'),
    url(r'^app/theme/switch/$', general_views.switch_theme, name='switch_theme'),
    url(r'^app/shop/delete/(?P<pk>.*)/$', general_views.delete_shop, name='delete_shop'),
    url(r'^app/report/$',general_views.reports,name='report'),

    url(r'^app/accounts/', include('registration.backends.default.urls')),
    url(r'^app/accounts/register/$', RegistrationView.as_view(form_class=RegForm),name='registration_register'),

    url(r'^app/customers/', include(('customers.urls','customers'), namespace="customers")),
    url(r'^app/products/', include(('products.urls','products'), namespace="products")),
    url(r'^app/sales/', include(('sales.urls','sales'), namespace="sales")),
    url(r'^app/staffs/', include(('staffs.urls','staffs'), namespace='staffs')),
    url(r'^app/vendors/', include(('vendors.urls','vendors'), namespace='vendors')),
    url(r'^app/purchases/', include(('purchases.urls', 'purchases'), namespace='purchases')),
    url(r'^app/finance/', include(('finance.urls', 'finance'), namespace="finance")),
    url(r'^app/tasks/', include(('tasks.urls','tasks'), namespace="tasks")),
    url(r'^app/distributors/', include(('distributors.urls', 'distributors'), namespace="distributors")),

    url(r'^app/users/', include(('users.urls','users'), namespace="users")),

    url(r'^app/reports/', include(('reports.urls','reports'), namespace="reports")),

    url(r'^app/barcode/create/(?P<code>.*)/$', general_views.create_barcode, name='create_barcode'),

    url(r'^create-shop-request/$', general_views.create_shop_request, name="create_shop_request"),

    url(r'^media/(?P<path>.*)$', serve, { 'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve, { 'document_root': settings.STATIC_FILE_ROOT}),
]
