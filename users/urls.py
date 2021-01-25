from django.conf.urls import url,include
from . import views


urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^view/(?P<pk>.*)/$', views.view, name='view'),
    
    url(r'^check-notification/$', views.check_notification, name='check_notification'),
    url(r'^notifications/$', views.notifications, name='notifications'),
    url(r'^notification/delete/(?P<pk>.*)/$', views.delete_notification, name='delete_notification'),
    url(r'^delete-selected-notifications/$', views.delete_selected_notifications, name='delete_selected_notifications'),
    url(r'^notification/read/(?P<pk>.*)/$', views.read_notification, name='read_notification'),
    url(r'^read-selected-notifications/$', views.read_selected_notifications, name='read_selected_notifications'),
    
    url(r'^set-user-timezone/$', views.set_user_timezone, name='set_user_timezone'),
    url(r'^settings/$', views.settings, name='settings'), 
    url(r'^settings/update-shop/$', views.update_shop, name='update_shop'),

    url(r'^user/create/(?P<pk>.*)/$', views.create_user, name='create_user'),
    url(r'^user/view/(?P<pk>.*)/$', views.view_user, name='view_user'),
    url(r'^users/$', views.users, name='users'), 
    url(r'^user/delete/(?P<pk>.*)/$', views.delete_user, name='delete_user'),
    url(r'^user/delete-selected/$', views.delete_selected_users, name='delete_selected_users'),
    url(r'^change-permissions/(?P<pk>.*)/$', views.change_permissions, name='change_permissions'),
    url(r'^change-password/(?P<pk>.*)/$', views.change_password, name='change_password'),

    url(r'^revoke-access/(?P<pk>.*)/$', views.revoke_access, name='revoke_access'), 

    url(r'^activities/$', views.user_activities, name='user_activities'),
    url(r'^activity/(?P<pk>.*)/$', views.user_activity, name='user_activity'),
    
    
]