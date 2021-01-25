from django.shortcuts import render
from main.models import Mode, Shop, ShopAccess
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from main.functions import get_roles, get_shops, get_current_role
from users.functions import get_current_shop
import json
from staffs.models import Staff
from distributors.models import Distributor


def ajax_required(function):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return render(request,'error/400.html',{})
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap


def check_mode(function):
    def wrap(request, *args, **kwargs):
        mode = Mode.objects.get(id=1)
        readonly = mode.readonly
        maintenance = mode.maintenance
        down = mode.down

        if down:
            if request.is_ajax():
                response_data = {}
                response_data['status'] = 'false'
                response_data['message'] = "Application currently down. Please try again later."
                response_data['static_message'] = "true"
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                return HttpResponseRedirect(reverse('down'))
        elif readonly:
            if request.is_ajax():
                response_data = {}
                response_data['status'] = 'false'
                response_data['message'] = "Application now readonly mode. please try again later."
                response_data['static_message'] = "true"
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                return HttpResponseRedirect(reverse('read_only'))

        return function(request, *args, **kwargs)

    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap


def shop_required(function):
    def wrap(request, *args, **kwargs):
        if not ShopAccess.objects.filter(user=request.user,is_accepted=True).exists():
            return HttpResponseRedirect(reverse('create_shop'))
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap


def check_account_balance(function):
    def wrap(request, *args, **kwargs):
        current_balance = request.user.accountbalance.balance
        if current_balance <= 0:
            if request.is_ajax():
                response_data = {
                    "status" : "false",
                    "stable" : "false",
                    "title" : "Account Suspended",
                    "message" : "Please add some funds to your account"
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                return HttpResponseRedirect(reverse('payments:add_fund'))

        return function(request, *args, **kwargs)

    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap


def permissions_required(permissions,roles=['administrator','staff','vendor','customer','distributor'],all_permissions=False,all_roles=False,both_check=True,super_user_ok=True,allow_self=False,model=None):

    def _method_wrapper(view_method):

        def _arguments_wrapper(request, *args, **kwargs) :
            current_role = get_current_role(request)
            user_roles = get_roles(request)
            shop_access = get_shops(request)
            current_shop = get_current_shop(request)

            has_permission = False
            permission_ok = False
            role_ok = False

            if permissions:
                booleans = []
                if current_role == "staff":
                    staff_instance = Staff.objects.get(shop=current_shop,user=request.user)

                    for perm in permissions:
                        if perm in staff_instance.permissionlist():
                            booleans.append(1)
                        else:
                            booleans.append(0)
                elif current_role == "vendor" :
                    vendor_instance = Vendor.objects.get(shop=current_shop,user=request.user)

                    for perm in permissions:
                        if perm in vendor_instance.permissionlist():
                            booleans.append(1)
                        else:
                            booleans.append(0)
                elif current_role == "customer":
                    customer_instance = Customer.objects.get(shop=current_shop,user=request.user)

                    for perm in permissions:
                        if perm in customer_instance.permissionlist():
                            booleans.append(1)
                        else:
                            booleans.append(0)

                if booleans:
                    if all_permissions:
                        if 0 in booleans:
                            permission_ok = False
                        else:
                            permission_ok = True
                    else:
                        if 1 in booleans:
                            permission_ok = True
            else:
                permission_ok = True

            if roles:
                booleans = []
                for role in roles:
                    if role in user_roles:
                        booleans.append(1)
                    else:
                        booleans.append(0)

                if booleans:
                    if all_roles:
                        if 0 in booleans:
                            role_ok = False
                        else:
                            role_ok = True
                    else:
                        if 1 in booleans:
                            role_ok = True
            else:
                role_ok = True

            if both_check:
                if permission_ok and role_ok:
                    has_permission = True
                else:
                    has_permission = False
            else:
                if permission_ok or role_ok:
                    has_permission = True
                else:
                    has_permission = False

            if super_user_ok:
                if current_shop.creator == request.user:
                    has_permission = True
                if request.user.is_superuser:
                    has_permission = True

            if allow_self:
                pk = kwargs["pk"]
                instance = model.objects.get(pk=pk)
                if instance.creator == request.user:
                    has_permission = True

            if not has_permission:
                if request.is_ajax():
                    response_data = {}
                    response_data['status'] = 'false'
                    response_data['stable'] = 'true'
                    response_data['title'] = 'Permission Denied'
                    response_data['message'] = "You have no permission to do this action."
                    response_data['static_message'] = "true"
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    context = {
                        "is_need_select_picker": True,
                        "is_need_popup_box": True,
                        "is_need_custom_scroll_bar": True,
                        "is_need_wave_effect": True,
                        "is_need_bootstrap_growl": True,
                        "is_need_grid_system": True,
                        "is_need_datetime_picker" : True,
                        "title" : "Permission Denied"
                    }
                    return render(request, 'error/permission_denied.html', context)

            return view_method(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper


def role_required(roles):
    def _method_wrapper(view_method):
        def _arguments_wrapper(request, *args, **kwargs) :
            current_role = get_current_role(request)
            if not current_role in roles:
                if request.is_ajax():
                    response_data = {}
                    response_data['status'] = 'false'
                    response_data['stable'] = 'true'
                    response_data['title'] = 'Permission Denied'
                    response_data['message'] = "You have no permission to do this action."
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    context = {
                        "is_need_select_picker": True,
                        "is_need_popup_box": True,
                        "is_need_custom_scroll_bar": True,
                        "is_need_wave_effect": True,
                        "is_need_bootstrap_growl": True,
                        "is_need_grid_system": True,
                        "is_need_datetime_picker" : True,
                        "title" : "Permission Denied"
                    }
                    return render(request, 'error/permission_denied.html', context)

            return view_method(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper



def check_salesman(function):
    def wrap(request, *args, **kwargs):
        current_role = get_current_role(request)
        if current_role == "distributor":
            if Distributor.objects.get(user=request.user).is_salesman:
                context = {
                    "is_need_select_picker": True,
                    "is_need_popup_box": True,
                    "is_need_custom_scroll_bar": True,
                    "is_need_wave_effect": True,
                    "is_need_bootstrap_growl": True,
                    "is_need_grid_system": True,
                    "is_need_datetime_picker" : True,
                    "title" : "Permission Denied"
                }
                return render(request, 'error/permission_denied.html', context)

        return function(request, *args, **kwargs)

    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap