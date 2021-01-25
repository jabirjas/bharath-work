from django.conf.urls import url
from . import views
from staffs.views import DesignationAutocomplete,StaffAutocomplete

urlpatterns = [
    url(r'^designation-autocomplete/$',DesignationAutocomplete.as_view(create_field='name'),name='designation_autocomplete'),
	url(r'^staff-autocomplete/$',StaffAutocomplete.as_view(),name='staffs_autocomplete'),

    url(r'^designation/create/$', views.create_designation, name='create_designation'),
    url(r'^designations/$', views.designations, name='designations'),
    url(r'^designation/edit/(?P<pk>.*)/$', views.edit_designation, name='edit_designation'),
    url(r'^designation/(?P<pk>.*)/$', views.designation, name='designation'),
    url(r'^delete-designation/(?P<pk>.*)/$', views.delete_designation, name='delete_designation'),
    url(r'^designation/delete-selected/$', views.delete_selected_designations, name='delete_selected_designations'),

    url(r'^staff/create/$', views.create_staff, name='create_staff'),
    url(r'^staffs/$', views.staffs, name='staffs'),
    url(r'^staff/edit/(?P<pk>.*)/$', views.edit_staff, name='edit_staff'),
    url(r'^staff/(?P<pk>.*)/$', views.staff, name='staff'),
    url(r'^staff-delete/(?P<pk>.*)/$', views.delete_staff, name='delete_staff'),
    url(r'^staff/delete-selected/$', views.delete_selected_staffs, name='delete_selected_staffs'),

    url(r'^staff-salary/create/$',views.create_staff_salary,name='create_staff_salary'),
    url(r'^staff-salaries/view/$',views.staff_salaries,name='staff_salaries'),
    url(r'^staff-salary/view/(?P<pk>.*)/$',views.staff_salary,name='staff_salary'),
    url(r'^staff-salary/edit/(?P<pk>.*)/$',views.edit_staff_salary,name='edit_staff_salary'),
    url(r'^staff-salary/delete/(?P<pk>.*)/$',views.delete_staff_salary,name='delete_staff_salary'),
    url(r'^delete-selected-staff-salaries/$', views.delete_selected_staff_salaries, name='delete_selected_staff_salaries'),

    url(r'^get-salary/$',views.get_salary,name='get_salary'),

]
