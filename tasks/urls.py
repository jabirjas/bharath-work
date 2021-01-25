from django.conf.urls import url
from . import views



urlpatterns = [
    url(r'^create-task/$', views.create_task, name='create_task'),
    url(r'^tasks/$', views.tasks, name='tasks'),
    url(r'^edit-task/(?P<pk>.*)/$', views.edit_task, name='edit_task'),
    url(r'^task/(?P<pk>.*)/$', views.task, name='task'),
    url(r'^delete-task/(?P<pk>.*)/$', views.delete_task, name='delete_task'),
    url(r'^delete-selected-tasks/$', views.delete_selected_tasks, name='delete_selected_tasks'),

    url(r'^create-reminder/$', views.create_reminder, name='create_reminder'),
    url(r'^reminders/$', views.reminders, name='reminders'),
    url(r'^edit-reminder/(?P<pk>.*)/$', views.edit_reminder, name='edit_reminder'),
    url(r'^reminder/(?P<pk>.*)/$', views.reminder, name='reminder'),
    url(r'^delete-reminder/(?P<pk>.*)/$', views.delete_reminder, name='delete_reminder'),
    url(r'^delete-selected-reminders/$', views.delete_selected_reminders, name='delete_selected_reminders'),

    url(r'^create-anniversary/$',views.create_anniversary , name='create_anniversary'),
    url(r'^anniversary/view/$',views.anniversaries , name='anniversaries'),
    url(r'^anniversary/single-view/(?P<pk>.*)$',views.anniversary , name='anniversary'),
    url(r'^edit-anniversary/(?P<pk>.*)/$',views.edit_anniversary, name='edit_anniversary'),
    url(r'^delete-anniversary/(?P<pk>.*)/$',views.delete_anniversary , name='delete_anniversary'),
    url(r'^delete-selected-anniversaries/$', views.delete_selected_anniversaries, name='delete_selected_anniversaries'),


    url(r'^create-holiday/$',views.create_holiday , name='create_holiday'),
    url(r'^holidays/view/$',views.holidays , name='holidays'),
    url(r'^holiday/single-view/(?P<pk>.*)$',views.holiday , name='holiday'),
    url(r'^edit-holiday/(?P<pk>.*)/$',views.edit_holiday, name='edit_holiday'),
    url(r'^delete-holiday/(?P<pk>.*)/$',views.delete_holiday , name='delete_holiday'),
    url(r'^delete-selected-holidays/$', views.delete_selected_holidays, name='delete_selected_holidays'),

    url(r'^events/$',views.events , name='events'),


]
